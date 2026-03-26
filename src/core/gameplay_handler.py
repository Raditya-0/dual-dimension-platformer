"""
Gameplay Handler - Mengelola game mechanics seperti damage, combat, triggers, dll.
Memisahkan gameplay logic dari main game class.
"""
import pygame
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from utils.settings import SCREEN_HEIGHT

if TYPE_CHECKING:
    from entity.player import Player
    from core.entity_manager import EntityManager


class GameplayHandler:
    """
    Handler untuk gameplay mechanics.
    Menggunakan Composition - Game class meng-compose handler ini.
    """
    
    def __init__(self, entity_manager: 'EntityManager'):
        self.entity_manager = entity_manager
        
        # Death delay state
        self.is_in_death_delay = False
        self.death_delay_timer = 0
        self.death_delay_start_time = 0
        
        # Spawn invincibility
        self.spawn_invincibility_timer = 0
        self.spawn_invincibility_duration = 10
        
        # End sequence state
        self.end_sequence_active = False
        self.end_sequence_mode = None
        self.end_sequence_dir = 1
        self.end_jump_started = False
    
    def reset_state(self):
        """Reset all gameplay state."""
        self.is_in_death_delay = False
        self.death_delay_timer = 0
        self.death_delay_start_time = 0
        self.spawn_invincibility_timer = self.spawn_invincibility_duration
        self.end_sequence_active = False
        self.end_sequence_mode = None
        self.end_sequence_dir = 1
        self.end_jump_started = False
    
    def update_invincibility(self):
        """Update spawn invincibility timer."""
        if self.spawn_invincibility_timer > 0:
            self.spawn_invincibility_timer -= 1
    
    @property
    def is_invincible(self) -> bool:
        """Check if player is currently invincible."""
        return self.spawn_invincibility_timer > 0
    
    def handle_triggers(self, player: 'Player', trigger_traps: List, end_triggers: List) -> Optional[str]:
        """
        Handle trigger activation.
        Returns end sequence mode if triggered, None otherwise.
        """
        if not player.is_alive:
            return None
        
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        
        # Activate traps
        for trap in trigger_traps:
            trap.try_activate(player.rect, current_dim)
        
        # Check end triggers
        if not self.end_sequence_active:
            for end_t in end_triggers:
                if end_t['dim'] in [current_dim, 'both'] and player.collides(end_t['rect']):
                    return end_t['mode']
        
        return None
    
    def handle_damage(self, player: 'Player', trigger_traps: List) -> Optional[Dict]:
        """
        Handle player damage from hazards.
        Returns damage result dict if damaged, None otherwise.
        """
        from entity.enemy import PatrollingEnemy, ChaserEnemy
        from entity.boss import Boss
        
        if self.is_invincible or not player.is_alive or self.is_in_death_delay:
            return None
        
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        active_hazards = []
        chaser_that_hit = None
        
        # Collect trap hazards
        for trap in trigger_traps:
            if trap.is_active and trap.dim in [current_dim, 'both']:
                active_hazards.append(trap.get_hazard_rect())
        
        # Collect enemy hazards
        for enemy in self.entity_manager.enemies:
            if getattr(enemy, 'dim', 'both') not in (current_dim, 'both'):
                continue
            
            if getattr(enemy, 'is_dying', False):
                continue
            
            if hasattr(enemy, 'is_hazard_active') and enemy.is_hazard_active():
                hazard_rect = enemy.get_hazard_rect() if hasattr(enemy, 'get_hazard_rect') else enemy.rect
                active_hazards.append(hazard_rect)
                
                # Handle enemy contact
                if isinstance(enemy, PatrollingEnemy) and hazard_rect.colliderect(player.rect):
                    if hasattr(enemy, 'on_player_contact') and enemy.is_alive:
                        enemy.on_player_contact()
                
                if isinstance(enemy, ChaserEnemy) and hazard_rect.colliderect(player.rect):
                    chaser_that_hit = enemy
            
            # Boss special attacks
            if isinstance(enemy, Boss):
                active_hazards.extend(enemy.get_spell_hazards())
                if hasattr(enemy, 'is_melee_active') and enemy.is_melee_active():
                    active_hazards.append(enemy.get_melee_hazard_rect())
        
        # Apply damage
        result = player.apply_hazards(active_hazards, SCREEN_HEIGHT, is_invincible=False)
        
        if result:
            # Handle temporary death
            if result.get('temporary_death'):
                self.is_in_death_delay = True
                self.death_delay_timer = result.get('delay_ms', 500)
                self.death_delay_start_time = pygame.time.get_ticks()
        
        return result
    
    def handle_combat(self, player: 'Player') -> List:
        """
        Handle player attacks on enemies.
        Returns list of enemies that were hit.
        """
        from entity.boss import Boss
        
        attack_rect = player.get_attack_hitbox() if hasattr(player, 'get_attack_hitbox') else None
        
        if not attack_rect:
            return []
        
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        enemies_hit = []
        
        for enemy in self.entity_manager.get_active_enemies():
            if getattr(enemy, 'dim', 'both') not in (current_dim, 'both'):
                continue
                
            if attack_rect.colliderect(enemy.rect):
                enemies_hit.append(enemy)
                
                if isinstance(enemy, Boss):
                    if hasattr(enemy, 'take_damage'):
                        enemy.take_damage(1)
                elif hasattr(enemy, 'on_killed_by_player'):
                    enemy.on_killed_by_player()
        
        return enemies_hit
    
    def handle_enemy_blocking(self, player: 'Player'):
        """Handle enemy blocking player movement."""
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        for enemy in self.entity_manager.enemies:
            if getattr(enemy, 'dim', 'both') not in (current_dim, 'both'):
                continue
                
            if getattr(enemy, 'is_dying', False):
                continue
            
            if not getattr(enemy, 'blocks_player', True):
                continue
            
            # Get blocking rect
            if hasattr(enemy, 'get_invisible_wall_rect'):
                block_rect = enemy.get_invisible_wall_rect()
            elif hasattr(enemy, 'get_block_rect'):
                block_rect = enemy.get_block_rect()
            else:
                block_rect = enemy.rect
            
            # Check collision and push player
            if player.rect.colliderect(block_rect):
                if player.velocity.x > 0:
                    player.rect.right = block_rect.left
                elif player.velocity.x < 0:
                    player.rect.left = block_rect.right
                else:
                    if player.rect.centerx < block_rect.centerx:
                        player.rect.right = block_rect.left
                    else:
                        player.rect.left = block_rect.right
                player.velocity.x = 0
    
    def start_end_sequence(self, mode: str):
        """Start level end sequence."""
        self.end_sequence_active = True
        self.end_sequence_mode = mode
        self.end_sequence_dir = 1
        self.end_jump_started = False
    
    def update_end_sequence(self, player: 'Player', active_platforms: List, 
                           player_speed: float, jump_strength: float):
        """
        Update end sequence animation.
        Returns True if sequence should continue, False if completed.
        """
        player.is_walking = True
        player.direction = 1 if self.end_sequence_dir >= 0 else -1
        player.velocity.x = player_speed * 0.8 * player.direction
        
        if self.end_sequence_mode == 'jump_walk' and not self.end_jump_started:
            if getattr(player, 'is_on_ground', False):
                player.velocity.y = -jump_strength * 0.6
                self.end_jump_started = True
        
        player.step(active_platforms)
        return True
    
    def check_end_sequence_complete(self, player: 'Player', camera_offset: tuple,
                                    game_surface_width: int, level_width: int) -> bool:
        """
        Check if end sequence is complete.
        Returns True if player has exited the level.
        """
        player_screen_x = player.rect.x - camera_offset[0]
        
        return (player_screen_x > game_surface_width + 40 or 
                player_screen_x + player.rect.width < -40 or 
                player.rect.left > level_width + 40)
    
    def check_death_delay_complete(self, player: 'Player') -> bool:
        """
        Check if death delay timer has completed.
        Also checks if death animation is ready.
        """
        if not self.is_in_death_delay:
            return False
        
        # Check if animation is ready
        is_animation_ready = (player.state == 'death' and player.animation_finished) or (player.state != 'death')
        if not is_animation_ready:
            return False
        
        current_time = pygame.time.get_ticks()
        return current_time - self.death_delay_start_time > self.death_delay_timer
    
    def clear_death_delay(self):
        """Clear death delay state."""
        self.is_in_death_delay = False
        self.death_delay_timer = 0
        self.death_delay_start_time = 0
