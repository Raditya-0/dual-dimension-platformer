import os
import pygame
from utils.settings import *
from entity.entity import Entity
from utils.exception import AssetLoadError, SpriteSheetError

base_path = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(base_path, '..', '..'))
assets_path = os.path.join(project_root, 'Assets')

class Player(Entity):
    def __init__(self, x, y):
        self._load_animations_from_spritesheet()
        self._load_attack_animations()
        self.non_looping_states = {'death', 'attack1', 'attack2'}
        initial_image = self.animations['idle'][0]
        super().__init__(x, y, initial_image)
        
        self.hearts = PLAYER_START_HEARTS
        self.in_gema_dimension = False
        self.input_locked = False  # Lock input during NPC dialog

        self.attack_state: str | None = None
        self.combo_buffer: bool = False
        
        # Invincibility properties
        self.invincible_end_time: int = 0
        self.invincible_duration: int = 2000  # 2 seconds I-frames
        self.is_visible: bool = True

    def _load_animations_from_spritesheet(self):
        self.animations = {'idle': [], 'run': [], 'jump': [], 'fall': [], 'death': []}
        player_asset_path = os.path.join(assets_path, 'Player')

        try:
            idle_sheet_path = os.path.join(player_asset_path, '_Idle.png')
            idle_sheet = pygame.image.load(idle_sheet_path).convert_alpha() 
            frame_width, frame_height, frame_count = 21, 38, 10
            left_margin, gap_width, top_margin = 44, 99, 42
            for i in range(frame_count):
                x_pos = left_margin + i * (frame_width + gap_width)
                frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_surface.blit(idle_sheet, (0, 0), (x_pos, top_margin, frame_width, frame_height))
                self.animations['idle'].append(frame_surface)
        except Exception as e:
            print(str(SpriteSheetError(os.path.join(player_asset_path, '_Idle.png'), e)))
            self.animations['idle'].append(pygame.Surface((21, 38)))

        try:
            run_sheet_path = os.path.join(player_asset_path, '_Run.png')
            run_sheet = pygame.image.load(run_sheet_path).convert_alpha() 
            frame_width, frame_height, frame_count = 30, 40, 10
            left_margin, gap_width, top_margin = 43, 90, 40
            for i in range(frame_count):
                x_pos = left_margin + i * (frame_width + gap_width)
                frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_surface.blit(run_sheet, (0, 0), (x_pos, top_margin, frame_width, frame_height))
                self.animations['run'].append(frame_surface)
        except Exception as e:
            print(str(SpriteSheetError(os.path.join(player_asset_path, '_Run.png'), e)))
            self.animations['run'].append(pygame.Surface((30, 40)))
            
        try:
            jump_sheet_path = os.path.join(player_asset_path, '_Jump.png')
            jump_sheet = pygame.image.load(jump_sheet_path).convert_alpha() 
            frame_width, frame_height, frame_count = 25, 38, 3
            left_margin, gap_width, top_margin = 44, 95, 42
            for i in range(frame_count):
                x_pos = left_margin + i * (frame_width + gap_width)
                frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_surface.blit(jump_sheet, (0, 0), (x_pos, top_margin, frame_width, frame_height))
                self.animations['jump'].append(frame_surface)
        except Exception as e:
            print(str(SpriteSheetError(os.path.join(player_asset_path, '_Jump.png'), e)))
            self.animations['jump'].append(pygame.Surface((30, 40)))
            
        try:
            fall_sheet_path = os.path.join(player_asset_path, '_Fall.png')
            fall_sheet = pygame.image.load(fall_sheet_path).convert_alpha() 
            frame_width, frame_height, frame_count = 29, 38, 3
            left_margin, gap_width, top_margin = 39, 91, 42
            for i in range(frame_count):
                x_pos = left_margin + i * (frame_width + gap_width)
                frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_surface.blit(fall_sheet, (0, 0), (x_pos, top_margin, frame_width, frame_height))
                self.animations['fall'].append(frame_surface)
        except Exception as e:
            print(str(SpriteSheetError(os.path.join(player_asset_path, '_Fall.png'), e)))
            self.animations['fall'].append(pygame.Surface((30, 40)))

        frame_count = 10
        asset_folder = os.path.join(player_asset_path, 'Death')
        self.animations['death'] = [] 

        try:
            for i in range(1, frame_count + 1):
                file_name = f'_Death{i}.png'
                full_path = os.path.join(asset_folder, file_name)

                frame_surface = pygame.image.load(full_path).convert_alpha()
                self.animations['death'].append(frame_surface)

            print("Death animation loaded successfully.")

        except Exception as e:
            print(str(AssetLoadError(os.path.join(asset_folder, '_Death#.png'), e)))
            self.animations['death'].append(pygame.Surface((30, 40), pygame.SRCALPHA))

    def _load_attack_animations(self):
        player_asset_path = os.path.join(assets_path, 'Player')
        attack1_dir = os.path.join(player_asset_path, 'Attack')
        attack2_dir = os.path.join(player_asset_path, 'Attack2')

        self.animations.setdefault('attack1', [])
        self.animations.setdefault('attack2', [])

        def load_frames(folder: str) -> list[pygame.Surface]:
            frames: list[pygame.Surface] = []
            try:
                if os.path.isdir(folder):
                    names = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
                    names.sort()
                    for name in names:
                        img = pygame.image.load(os.path.join(folder, name)).convert_alpha()
                        frames.append(img)
                else:
                    raise FileNotFoundError(folder)
            except Exception as e:
                print(str(AssetLoadError(folder, e)))
            return frames

        attack1_frames = load_frames(attack1_dir)
        attack2_frames = load_frames(attack2_dir)

        if not attack1_frames:
            attack1_frames = [pygame.Surface((30, 40), pygame.SRCALPHA)]
        if not attack2_frames:
            attack2_frames = [pygame.Surface((30, 40), pygame.SRCALPHA)]

        self.animations['attack1'] = attack1_frames
        self.animations['attack2'] = attack2_frames

    def _get_input(self):
        if not self.is_alive: return
        # Block movement input when locked (during NPC dialog)
        if self.input_locked:
            self.velocity.x = 0
            self.is_walking = False
            return
        self.is_walking = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.velocity.x = -PLAYER_SPEED; self.direction = -1; self.is_walking = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.velocity.x = PLAYER_SPEED; self.direction = 1; self.is_walking = True
        else: self.velocity.x = 0
            
    def _apply_physics(self, platforms):
        if not self.is_alive:
            self.velocity.x = 0 
            self.velocity.y += GRAVITY
            self.rect.y += self.velocity.y
            for platform in platforms:
                if self.rect.colliderect(platform) and self.velocity.y > 0:
                    self.rect.bottom = platform.top
                    self.velocity.y = 0
            return

        self.rect.x += self.velocity.x
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity.x > 0: self.rect.right = platform.left
                elif self.velocity.x < 0: self.rect.left = platform.right
        self.velocity.y += GRAVITY
        self.rect.y += self.velocity.y
        self.is_on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform):
                if self.velocity.y > 0: self.rect.bottom = platform.top; self.velocity.y = 0; self.is_on_ground = True
                elif self.velocity.y < 0: self.rect.top = platform.bottom; self.velocity.y = 0

    def compute_state(self) -> str:
        if not self.is_alive:
            return 'death'
        if self.attack_state in ('attack1', 'attack2'):
            return self.attack_state
        if not self.is_on_ground:
            return 'jump' if self.velocity.y < 0 else 'fall'
        return 'run' if getattr(self, 'is_walking', False) else 'idle'

    def jump(self):
        if self.is_on_ground and self.is_alive: self.velocity.y = -JUMP_STRENGTH

    def shift_dimension(self):
        if self.is_alive: self.in_gema_dimension = not self.in_gema_dimension

    def take_damage(self):
        if self.is_alive:
            self.hearts -= 1
            print(f"Hati berkurang! Sisa: {self.hearts}")
            if self.hearts <= 0:
                self.die()
    
    def die(self):
        if self.is_alive:
            self.is_alive = False
            self.animation_finished = False
            self.frame_index = 0
            # Cancel any ongoing attack
            self.attack_state = None
            self.combo_buffer = False
            print("Pemain masuk ke state mati.")

    def respawn(self, pos):
        self.rect.bottomleft = pos
        self.velocity.x = 0
        self.velocity.y = 0
        self.is_on_ground = True
        self.is_alive = True
        self.animation_finished = False
        
        self.frame_index = 0
        self.state = 'idle'
        if len(self.animations['idle']) > 0:
            self.image = self.animations['idle'][self.frame_index]
        
        if self.hearts <= 0:
            self.hearts = PLAYER_START_HEARTS

    def update(self, platforms):
        self._get_input()
        if self.attack_state is not None:
            self.velocity.x = 0
        self._update_attack_state_machine()
        self.step(platforms)
        
        # Update invincibility blinking
        current_time = pygame.time.get_ticks()
        if current_time < self.invincible_end_time:
            # Blink effect: toggle visibility every 100ms
            self.is_visible = (current_time // 100) % 2 == 0
        else:
            self.is_visible = True

    def draw(self, screen: pygame.Surface, camera_offset_x: float, camera_offset_y: float):
        if not self.is_visible:
            return
            
        img = self.image
        if self.direction == -1:
            img = pygame.transform.flip(img, True, False)

        draw_x = self.rect.x - camera_offset_x
        draw_y = (self.rect.bottom - img.get_height()) - camera_offset_y
        if getattr(self, 'state', '') in ['attack1', 'attack2']:
            # Align attack pose: mirror offset by facing
            attack_shift = 0
            draw_x += attack_shift if self.direction == 1 else -attack_shift

        screen.blit(img, (draw_x, draw_y))

    # Combat helpers
    def is_attack_active(self) -> bool:
        return (self.attack_state in ('attack1', 'attack2')) and not getattr(self, 'animation_finished', False)

    def get_attack_hitbox(self, width: int = 20) -> pygame.Rect | None:
        if not self.is_attack_active():
            return None
        if self.direction == 1:
            return pygame.Rect(self.rect.right, self.rect.top, width, self.rect.height)
        else:
            return pygame.Rect(self.rect.left - width, self.rect.top, width, self.rect.height)

    def handle_event(self, event):
        if not self.is_alive: return

        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
                self.jump()
            if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                self.shift_dimension()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.attack_state is None:
                self._start_attack('attack1')
            elif self.attack_state == 'attack1':
                self.combo_buffer = True

    def _start_attack(self, which: str):
        if which not in ('attack1', 'attack2'):
            return
        self.attack_state = which
        self.state = which
        self.animation_finished = False
        self.frame_index = 0

    def _end_attack(self):
        self.attack_state = None
        self.combo_buffer = False

    def _update_attack_state_machine(self):
        if self.attack_state == 'attack1':
            if self.state == 'attack1' and getattr(self, 'animation_finished', False):
                if self.combo_buffer and len(self.animations.get('attack2', [])) > 0:
                    self.combo_buffer = False
                    self._start_attack('attack2')
                else:
                    self._end_attack()
        elif self.attack_state == 'attack2':
            if self.state == 'attack2' and getattr(self, 'animation_finished', False):
                self._end_attack()

    def apply_hazards(self, hazard_rects, fall_limit_y, is_invincible=False):
        current_time = pygame.time.get_ticks()
        if is_invincible or not self.is_alive or current_time < self.invincible_end_time:
            return None

        damage_source = None
        # Deteksi jatuh lebih cepat dengan menggunakan centery alih-alih top
        if self.rect.centery > fall_limit_y:
            damage_source = 'fall'
        else:
            for r in hazard_rects:
                if self.rect.colliderect(r):
                    damage_source = 'trap'
                    break

        if not damage_source:
            return None

        self.take_damage()

        if damage_source == 'fall':
            # Jika jatuh, langsung mati sementara untuk respawn ke checkpoint terakhir
            # Bahkan jika hearts > 0, karena tidak mungkin blink di dasar jurang
            self.die()
            return {'source': damage_source, 'temporary_death': True, 'delay_ms': 100}

        if not self.is_alive:
            # Nyawa habis karena trap/enemy
            return {'source': damage_source, 'temporary_death': True, 'delay_ms': 1000}

        # Jika masih hidup dan kena trap/enemy ruang darat, set i-frames saja
        self.invincible_end_time = current_time + self.invincible_duration
        
        # Kembalikan dict tanpa trigger temporary_death agar tidak delay & respawn
        return {'source': damage_source, 'temporary_death': False, 'delay_ms': 0}
