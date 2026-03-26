import os
import pygame
from typing import Optional
from entity.entity import Entity
from utils.exception import AssetLoadError


class BossSpell:
    """Spell effect that appears above player position and stays in place."""
    def __init__(self, x: int, y: int, frames: list[pygame.Surface], start_frame: int = 0):
        self.x = x
        self.y = y
        self.frames = frames
        self.frame_index = float(start_frame)  # Start from specific frame for sync
        self.animation_speed = 1.0  # Faster animation speed for smooth playback
        self.animation_finished = False
        self.is_active = True
        self.damage_dealt = False
        
        # Spell only deals damage on frames 6-12 (index 5-11)
        self.damage_frames = set(range(5, 12))  # frames 6-12 (0-indexed = 5-11)
        
        # Hazard rect for collision - spell is 40x100, use most of it for damage
        if frames:
            # Use most of the spell sprite as damage area: 30x80 centered
            self.hazard_rect = pygame.Rect(x + 5, y + 10, 30, 80)
        else:
            self.hazard_rect = pygame.Rect(x + 5, y + 10, 30, 80)
    
    def is_hazardous(self) -> bool:
        """Check if spell is currently in damage frames."""
        current_frame = int(self.frame_index)
        return self.is_active and not self.damage_dealt and current_frame in self.damage_frames
    
    def update(self):
        if self.animation_finished:
            return
        
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.frames):
            self.animation_finished = True
            self.is_active = False
            self.frame_index = len(self.frames) - 1
    
    def draw(self, screen: pygame.Surface, camera_offset_x: float, camera_offset_y: float):
        # Don't draw if animation is finished (spell disappears)
        if self.animation_finished:
            return
        
        if self.frames:
            idx = int(self.frame_index) % len(self.frames)
            img = self.frames[idx]
            screen.blit(img, (self.x - camera_offset_x, self.y - camera_offset_y))
    
    def get_hazard_rect(self) -> pygame.Rect:
        """Return hazard rectangle for damage detection."""
        return self.hazard_rect


class Boss(Entity):
    """Boss enemy with Idle, Walk, Death, Hurt, and Cast spell abilities."""
    def __init__(self, x: int, y: int, size=(140, 93), speed: float = 1.5, facing: str = 'right'):
        base_path = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_path, '..', '..'))
        boss_dir = os.path.join(project_root, 'Assets', 'Boss', 'Bringer-Of-Death')
        
        def load_folder(folder: str) -> list[pygame.Surface]:
            frames = []
            try:
                if os.path.isdir(folder):
                    files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
                    files.sort()
                    for f in files:
                        img = pygame.image.load(os.path.join(folder, f)).convert_alpha()
                        if size:
                            img = pygame.transform.scale(img, size)
                        frames.append(img)
            except Exception as e:
                print(str(AssetLoadError(folder, e)))
            return frames
        
        # Load all animations
        idle_frames = load_folder(os.path.join(boss_dir, 'Idle'))
        walk_frames = load_folder(os.path.join(boss_dir, 'Walk'))
        death_frames = load_folder(os.path.join(boss_dir, 'Death'))
        hurt_frames = load_folder(os.path.join(boss_dir, 'Hurt'))
        cast_frames = load_folder(os.path.join(boss_dir, 'Cast'))
        attack_frames = load_folder(os.path.join(boss_dir, 'Attack'))
        
        # Load spell effect frames (not scaled to boss size)
        spell_frames = []
        spell_dir = os.path.join(boss_dir, 'Spell')
        try:
            if os.path.isdir(spell_dir):
                files = [f for f in os.listdir(spell_dir) if f.lower().endswith('.png')]
                files.sort()
                for f in files:
                    img = pygame.image.load(os.path.join(spell_dir, f)).convert_alpha()
                    # Scale spell to 40x100
                    img = pygame.transform.scale(img, (40, 80))
                    spell_frames.append(img)
        except Exception as e:
            print(str(AssetLoadError(spell_dir, e)))
        
        if not idle_frames:
            fallback = pygame.Surface(size, pygame.SRCALPHA)
            fallback.fill((128, 0, 128))
            idle_frames = [fallback]
        
        initial_img = idle_frames[0]
        super().__init__(x, y, initial_img)
        
        # Override rect to be smaller for better collision and positioning
        # Smaller collision box so player can get close and attack
        collision_width = 45
        collision_height = 60
        bottom_y = self.rect.bottom
        center_x = self.rect.centerx
        self.rect = pygame.Rect(0, 0, collision_width, collision_height)
        self.rect.centerx = center_x
        self.rect.bottom = bottom_y
        
        self.animations = {
            'idle': idle_frames,
            'walk': walk_frames if walk_frames else idle_frames,
            'death': death_frames if death_frames else idle_frames,
            'hurt': hurt_frames if hurt_frames else [],
            'cast': cast_frames if cast_frames else idle_frames,
            'attack': attack_frames if attack_frames else idle_frames
        }
        self.spell_frames = spell_frames if spell_frames else [pygame.Surface((80, 100), pygame.SRCALPHA)]
        
        self.non_looping_states = {'death', 'hurt', 'cast', 'attack'}
        
        self.speed = abs(speed)
        self.direction = 1 if facing == 'right' else -1
        self.state = 'idle'
        self.base_faces_right = False  # Boss sprite faces left by default
        
        # Boss stats
        self.health = 100
        self.is_dying = False
        self.blocks_player = True  # Boss has invisible wall to block player
        
        # AI behavior
        self.alerted = False
        self.detect_range_x = 200
        self.detect_range_y = 100
        
        # Melee attack
        self.melee_range = 50  # Distance to trigger melee attack
        self.attack_cooldown_ms = 1500  # 1.5 seconds between melee attacks
        self.last_attack_time = 0
        
        # Cast spell timing
        self.cast_cooldown_ms = 3000  # 3 seconds between casts
        self.last_cast_time = 0
        self.is_casting = False
        self.cast_target_x = 0
        self.cast_target_y = 0
        
        # Active spells
        self.active_spells: list[BossSpell] = []
        
        # Melee attack hit frames - only frames 5-7 are dangerous
        self.melee_hit_frames = {4, 5, 6}  # Frames 5, 6, 7 (0-indexed = 4, 5, 6)
        
        # No vertical offset to prevent position issues
        self.draw_offset_y = 0
    
    def _player_in_proximity(self, player: Entity) -> bool:
        if player is None:
            return False
        dx = abs(player.rect.centerx - self.rect.centerx)
        dy = abs(player.rect.centery - self.rect.centery)
        return dx <= self.detect_range_x and dy <= self.detect_range_y
    
    def _in_melee_range(self, player: Entity) -> bool:
        """Check if player is in melee attack range."""
        if player is None:
            return False
        dx = abs(player.rect.centerx - self.rect.centerx)
        dy = abs(player.rect.centery - self.rect.centery)
        return dx <= self.melee_range and dy <= 40
    
    def _can_melee_attack(self) -> bool:
        """Check if boss can perform melee attack (cooldown expired)."""
        now = pygame.time.get_ticks()
        return now - self.last_attack_time >= self.attack_cooldown_ms
    
    def _can_cast_spell(self) -> bool:
        """Check if boss can cast spell (cooldown expired)."""
        now = pygame.time.get_ticks()
        return now - self.last_cast_time >= self.cast_cooldown_ms
    
    def _start_melee_attack(self):
        """Start melee attack animation."""
        self.state = 'attack'
        self.frame_index = 0
        self.animation_finished = False
        self.velocity.x = 0
        self.last_attack_time = pygame.time.get_ticks()
    
    def _start_cast(self, target_x: int, target_y: int):
        """Start casting spell animation."""
        self.is_casting = True
        self.state = 'cast'
        self.frame_index = 0
        self.animation_finished = False
        self.cast_target_x = target_x  # Player's horizontal position
        self.cast_target_y = target_y  # Ground level (boss's bottom)
        self.velocity.x = 0
        self.last_cast_time = pygame.time.get_ticks()
    
    def _spawn_spell(self, start_frame: int = 0):
        """Spawn spell effect at target position."""
        # X follows player horizontal position, Y spawns from ground level
        # Spell is 40x100, so adjust centering offset
        spell_x = self.cast_target_x - 20  # Center spell sprite visually on player (half of 40)
        spell_y = self.cast_target_y - 80  # Spell appears above ground (100px from boss ground level)
        
        spell = BossSpell(spell_x, spell_y, self.spell_frames, start_frame=start_frame)
        self.active_spells.append(spell)
    
    def compute_state(self) -> str:
        if self.is_dying or not self.is_alive:
            return self.state if self.state in ('hurt', 'death') else 'death'
        if self.state in ('cast', 'hurt', 'attack'):
            return self.state
        return 'walk' if self.alerted else 'idle'
    
    def update(self, platforms: list[pygame.Rect], player: Optional[Entity] = None):
        # Handle death
        if self.is_dying:
            self.velocity.x = 0
            if self.state not in ('hurt', 'death'):
                self.state = 'hurt' if self.animations.get('hurt') else 'death'
                self.frame_index = 0
                self.animation_finished = False
                self.remove_at_ms = pygame.time.get_ticks() + 5000
            self.step(platforms)
            if self.state == 'hurt' and self.animation_finished:
                self.state = 'death'
                self.frame_index = 0
                self.animation_finished = False
                self.remove_at_ms = pygame.time.get_ticks() + 2000
            return
        
        # Handle casting
        if self.state == 'cast':
            self.velocity.x = 0
            self.step(platforms)
            
            # Spawn spell at frame 6 so spell starts from frame 0
            # This way spell damage frames (6-12) align with boss cast motion
            if int(self.frame_index) == 6 and not hasattr(self, '_spell_spawned_this_cast'):
                self._spawn_spell(start_frame=0)
                self._spell_spawned_this_cast = True
            
            if self.animation_finished:
                self.state = 'walk' if self.alerted else 'idle'
                self.is_casting = False
                if hasattr(self, '_spell_spawned_this_cast'):
                    delattr(self, '_spell_spawned_this_cast')
            return
        
        # Handle melee attack
        if self.state == 'attack':
            self.velocity.x = 0
            self.step(platforms)
            if self.animation_finished:
                self.state = 'walk' if self.alerted else 'idle'
            return
        
        # Handle hurt
        if self.state == 'hurt':
            self.velocity.x = 0
            self.step(platforms)
            if self.animation_finished:
                self.state = 'walk' if self.alerted else 'idle'
            return
        
        # AI behavior
        if player:
            # Detect player
            if not self.alerted and self._player_in_proximity(player):
                self.alerted = True
            
            if self.alerted:
                # Face player
                self.direction = 1 if player.rect.centerx >= self.rect.centerx else -1
                
                # Priority 1: Melee attack if in range
                if self._in_melee_range(player) and self._can_melee_attack():
                    self._start_melee_attack()
                    return
                
                # Priority 2: Cast spell if available
                if self._can_cast_spell() and not self.is_casting:
                    # X follows player, Y is at boss's ground level (boss.rect.bottom)
                    self._start_cast(player.rect.centerx, self.rect.bottom)
                    return
                
                # Walk towards player if not attacking/casting
                if not self.is_casting:
                    dx = abs(player.rect.centerx - self.rect.centerx)
                    if dx > self.melee_range:  # Walk closer
                        if self._has_ground_ahead(platforms, self.direction):
                            self.velocity.x = self.speed * self.direction
                        else:
                            self.velocity.x = 0
                            self.state = 'idle'
                            self.alerted = False
                    else:
                        self.velocity.x = 0
                        self.state = 'idle'
        else:
            self.velocity.x = 0
        
        self.step(platforms)
        
        # Update active spells
        for spell in self.active_spells:
            spell.update()
        
        # Remove finished spells completely (don't keep them in list)
        self.active_spells = [s for s in self.active_spells if not s.animation_finished]
    
    def draw(self, screen: pygame.Surface, camera_offset_x: float, camera_offset_y: float):
        """Draw boss with custom anchor at x=105px from left (character center in sprite)."""
        flip = (self.direction == -1 and self.base_faces_right) or (self.direction == 1 and not self.base_faces_right)
        final_image = pygame.transform.flip(self.image, True, False) if flip else self.image
        
        # Character center is at 105px from left edge of sprite
        sprite_center_offset = 105
        
        # When flipped, mirror the offset
        if flip:
            # Flipped: character center is at (width - 105) from left
            anchor_x = final_image.get_width() - sprite_center_offset
        else:
            # Normal: character center is at 105 from left
            anchor_x = sprite_center_offset
        
        # Draw so that sprite's character center aligns with rect.centerx
        draw_x = self.rect.centerx - anchor_x - camera_offset_x
        draw_y = self.rect.bottom - final_image.get_height() - camera_offset_y
        
        screen.blit(final_image, (draw_x, draw_y))
    
    def draw_spells(self, screen: pygame.Surface, camera_offset_x: float, camera_offset_y: float):
        """Draw all active spells."""
        for spell in self.active_spells:
            spell.draw(screen, camera_offset_x, camera_offset_y)
    
    def get_spell_hazards(self) -> list[pygame.Rect]:
        """Get hazard rectangles from all active spells that are in damage frames."""
        hazards = []
        for spell in self.active_spells:
            if spell.is_hazardous():  # Only hazardous on frames 6-12
                hazards.append(spell.get_hazard_rect())
        return hazards
    
    def is_melee_active(self) -> bool:
        """Check if boss melee attack is in hit frames."""
        return self.state == 'attack' and int(self.frame_index) in self.melee_hit_frames
    
    def get_melee_hazard_rect(self) -> pygame.Rect:
        """Get melee attack hitbox."""
        block = self.get_block_rect()
        w = 40
        h = 35
        y = int(block.centery - h // 2)
        if self.direction == 1:
            x = block.right
        else:
            x = block.left - w
        return pygame.Rect(x, y, w, h)
    
    def mark_spell_damage_dealt(self, spell_rect: pygame.Rect):
        """Mark that a spell has dealt damage to prevent multiple hits."""
        for spell in self.active_spells:
            if spell.get_hazard_rect() == spell_rect:
                spell.damage_dealt = True
                break
    
    def get_block_rect(self, width: int = 40, height: int = 40) -> pygame.Rect:
        """Boss collision rect - smaller so player can attack from sides."""
        cx, cy = self.rect.centerx, self.rect.centery
        left = int(cx - width // 2)
        top = int(cy - height // 2)
        return pygame.Rect(left, top, width, height)
    
    def get_invisible_wall_rect(self) -> pygame.Rect:
        """Get invisible wall rect that blocks player from passing through boss easily.
        
        Wall dimensions from sprite:
        - Left edge: 92px from left of sprite
        - Width: 27px (ending at 119px from left)
        - Height: 55px from bottom of sprite
        """
        # Get sprite dimensions and flip state
        flip = (self.direction == -1 and self.base_faces_right) or (self.direction == 1 and not self.base_faces_right)
        sprite_width = 140  # Boss sprite width
        sprite_height = 93  # Boss sprite height
        
        # Character center is at 105px from left edge of sprite
        sprite_center_offset = 105
        
        # Calculate sprite's left position
        if flip:
            anchor_x = sprite_width - sprite_center_offset
        else:
            anchor_x = sprite_center_offset
        
        sprite_left = self.rect.centerx - anchor_x
        sprite_bottom = self.rect.bottom
        
        # Wall position relative to sprite
        if flip:
            # When flipped, mirror the wall position
            # Original: 92px from left, becomes (140 - 92 - 27) = 21px from left when flipped
            wall_left_offset = sprite_width - 92 - 27
        else:
            # Normal: 92px from left of sprite
            wall_left_offset = 92
        
        wall_x = sprite_left + wall_left_offset
        wall_y = sprite_bottom - 55  # 55px up from bottom
        wall_width = 27
        wall_height = 55
        
        return pygame.Rect(wall_x, wall_y, wall_width, wall_height)
    
    def take_damage(self, amount: int = 1):
        """Boss takes damage from player attack."""
        if self.is_dying or not self.is_alive:
            return
        
        self.health -= amount
        
        if self.health <= 0:
            self.on_killed_by_player()
        else:
            # Play hurt animation
            self.state = 'hurt'
            self.frame_index = 0
            self.animation_finished = False
    
    def on_killed_by_player(self):
        """Boss death sequence."""
        self.is_dying = True
        self.state = 'hurt' if self.animations.get('hurt') else 'death'
        self.frame_index = 0
        self.animation_finished = False
        self.is_alive = True
        self.remove_at_ms = pygame.time.get_ticks() + 5000
    
    def _has_ground_ahead(self, platforms: list[pygame.Rect], direction: int | None = None, ahead_px: int = 10) -> bool:
        """Check if there's ground ahead to prevent falling off edges."""
        if direction is None:
            direction = self.direction
        front_x = self.rect.centerx + direction * (self.rect.width // 2 + max(1, ahead_px))
        probe = pygame.Rect(front_x, self.rect.bottom + 1, 2, 3)
        for plat in platforms:
            if plat.colliderect(probe):
                return True
        return False
