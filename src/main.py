"""
Main Game - Entry point dan main game loop.
Refactored untuk lebih modular dengan separation of concerns.
"""
import pygame
import os

# Core controllers
from core.game_state import GameStateEnum
from core.game_setup import GameSetup

# UI
from graphics import UI
from utils.settings import FPS, PLAYER_SPEED, JUMP_STRENGTH
from utils.exception import AssetLoadError, AudioLoadError


class Game:
    """Main game class - orchestrates all game systems."""
    
    def __init__(self):
        # Initialize Pygame and display
        self.screen, self.game_surface, self.clock, self.font = GameSetup.init_pygame()
        self.game_surface_width = self.game_surface.get_width()
        self.game_surface_height = self.game_surface.get_height()
        
        # Core systems
        self.running = True
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize controllers
        controllers = GameSetup.init_controllers(base_path, self.game_surface_width, self.game_surface_height)
        self.state_controller = controllers['state_controller']
        self.level_controller = controllers['level_controller']
        self.entity_manager = controllers['entity_manager']
        self.camera = controllers['camera']
        self.save_manager = controllers['save_manager']
        
        # Initialize asset loader
        try:
            self.asset_loader = GameSetup.init_asset_loader(base_path, self.game_surface_height)
        except (AssetLoadError, AudioLoadError) as e:
            print(f"Asset loading error: {e}")
            self.running = False
            return
        
        # Initialize gameplay systems
        systems = GameSetup.init_gameplay_systems(self.entity_manager, self.game_surface, self.screen)
        self.gameplay = systems['gameplay']
        self.renderer = systems['renderer']
        
        # Level data
        self.platforms = []
        self.trigger_traps = []
        self.end_triggers = []
        self.level_width_pixels = 0
        
        # Cached level data to prevent re-parsing
        self._cached_normal_data = None
        self._cached_gema_data = None
        
        # Parallax
        self.parallax_layers = []
        self.moon_object = None
        self.moon_shadow_object = None
        
        # Input lock (for end sequence)
        self.input_locked = False
        
        # Settings
        self.is_music_paused = False
        self.is_settings_open = False
        
        # Click cooldown to prevent spam clicking
        self.last_click_time = 0
        self.click_cooldown_ms = 300  # 300ms between clicks
    
    def setup_level(self, new_game=False, force_reparse=False):
        """Setup current level from level controller."""
        if new_game:
            self.platforms = []
            self.trigger_traps = []
            self.end_triggers = []
            self.camera.set_right_limit(None)
            self.level_width_pixels = 0
            self.entity_manager.clear_all()
            self._cached_normal_data = None
            self._cached_gema_data = None
        
        # Get level file paths
        normal_path, gema_path = self.level_controller.get_level_paths()
        
        # Parse or use cached data
        if force_reparse or self._cached_normal_data is None or self._cached_gema_data is None:
            normal_data = self.level_controller.parse_level_file(normal_path)
            gema_data = self.level_controller.parse_level_file(gema_path)
            self._cached_normal_data = normal_data
            self._cached_gema_data = gema_data
        else:
            normal_data = self._cached_normal_data
            gema_data = self._cached_gema_data
        
        # Setup level elements using GameSetup
        self.platforms = GameSetup.setup_platforms(normal_data, gema_data)
        self.trigger_traps = GameSetup.setup_trigger_traps(normal_data, gema_data)
        self.end_triggers = GameSetup.setup_end_triggers(normal_data, gema_data)
        
        # Setup entities
        if new_game or not self.entity_manager.player:
            start_pos = normal_data['start_pos'] or (100, 100)
            self.entity_manager.create_player(start_pos[0], start_pos[1])
        
        # Setup enemies, NPCs, campfires
        if new_game:
            GameSetup.setup_enemies(
                self.entity_manager, normal_data, gema_data, 
                self.level_controller.tile_size
            )
            GameSetup.setup_npcs(
                self.entity_manager, 
                normal_data['npc_spawns'], gema_data['npc_spawns'],
                self.snap_actor_to_ground
            )
            GameSetup.setup_campfires(
                self.entity_manager,
                normal_data['campfires'], gema_data['campfires']
            )
        
        # Setup parallax
        if new_game:
            result = GameSetup.setup_parallax(self.asset_loader)
            self.parallax_layers, self.moon_object, self.moon_shadow_object = result
        
        # Camera and level bounds
        self.level_width_pixels = max(normal_data['max_width'], gema_data['max_width']) + 40
        if normal_data['camera_right_limit'] or gema_data['camera_right_limit']:
            limit = normal_data['camera_right_limit'] or gema_data['camera_right_limit']
            self.camera.set_right_limit(limit)
        
        # Reset gameplay handler state
        self.gameplay.reset_state()
    
    def respawn_player(self):
        """Respawn player and reset level state."""
        self.entity_manager.respawn_player()
        self.entity_manager.respawn_all_enemies()
        
        # Reset gameplay state
        self.gameplay.reset_state()
        self.input_locked = False
        self.camera.unlock_camera()
        
        for trap in self.trigger_traps:
            trap.is_active = False
            trap.frame_index = 0.0
            trap.animation_finished = False
    
    def quick_restart_level(self):
        """Quick restart current level without re-parsing files."""
        print("[DEBUG] Starting quick_restart_level...")
        
        # Reset game state flags
        self.gameplay.reset_state()
        self.input_locked = False
        self.camera.unlock_camera()
        
        # Use GameSetup to rebuild level from cache
        level_data = GameSetup.quick_restart_from_cache(
            self._cached_normal_data, 
            self._cached_gema_data
        )
        
        self.platforms = level_data['platforms']
        self.trigger_traps = level_data['trigger_traps']
        self.end_triggers = level_data['end_triggers']
        
        # Respawn player and enemies
        self.respawn_player()
        print("[DEBUG] quick_restart_level completed")
    
    def start_end_sequence(self, mode: str):
        """Start level end sequence."""
        self.gameplay.start_end_sequence(mode)
        self.input_locked = True
        self.camera.lock_camera(self.entity_manager.player.rect.centerx)
    
    def update_end_sequence(self, active_platforms):
        """Update end sequence animation."""
        player = self.entity_manager.player
        
        self.gameplay.update_end_sequence(player, active_platforms, PLAYER_SPEED, JUMP_STRENGTH)
        
        # Check if sequence complete
        camera_offset = self.camera.get_offset(player.rect)
        
        if self.gameplay.check_end_sequence_complete(
            player, camera_offset, self.game_surface_width, self.level_width_pixels
        ):
            self.gameplay.end_sequence_active = False
            self.input_locked = False
            self.camera.unlock_camera()
            self.go_to_next_level()
    
    def go_to_next_level(self):
        """Advance to next level (SAFE for demo)."""
        current_hearts = self.entity_manager.player.hearts

        # Gunakan advance_level() method dari LevelController
        has_next_level = self.level_controller.advance_level()

        # Jika masih ada level berikutnya
        if has_next_level:
            self.save_manager.save_progress(
                self.level_controller.current_level,
                current_hearts
            )
            self.setup_level(new_game=True)
            self.entity_manager.player.hearts = current_hearts
        else:
            # Semua level selesai → WIN SCREEN
            self.state_controller.change_state(GameStateEnum.GAME_OVER_WIN)

    
    def update(self):
        """Main update loop."""
        player = self.entity_manager.player
        
        # Update invincibility
        self.gameplay.update_invincibility()
        
        # Get active platforms for current dimension
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        active_platforms = [p['rect'] for p in self.platforms if p['dim'] in [current_dim, 'both']]
        
        # Update based on game state
        if self.gameplay.end_sequence_active:
            self.update_end_sequence(active_platforms)
        else:
            # Normal gameplay
            player.update(active_platforms)
            
            # Update all entities
            for enemy in self.entity_manager.enemies:
                if getattr(enemy, 'dim', 'both') in (current_dim, 'both'):
                    enemy.update(active_platforms, player)
            
            # Update NPCs
            for npc in self.entity_manager.npcs:
                if getattr(npc, 'dim', 'both') in (current_dim, 'both'):
                    npc.update(player.rect)
            
            # Handle interactions
            if player.is_alive:
                # Check triggers
                end_mode = self.gameplay.handle_triggers(player, self.trigger_traps, self.end_triggers)
                if end_mode:
                    self.gameplay.start_end_sequence(end_mode)
                    self.input_locked = True
                
                # Handle damage and combat
                self.gameplay.handle_damage(player, self.trigger_traps)
                self.gameplay.handle_enemy_blocking(player)
                self.gameplay.handle_combat(player)
        
        # Update animated elements
        for trap in self.trigger_traps:
            trap.update(self.asset_loader.spike_frames)
        
        for campfire in self.entity_manager.campfires:
            campfire.update(self.asset_loader.campfire_frames)
            # Checkpoint collision logic
            if player.rect.colliderect(campfire.rect):
                # Update respawn point to this campfire
                new_start = (campfire.rect.left, campfire.rect.bottom)
                if self.entity_manager.start_pos != new_start:
                    self.entity_manager.start_pos = new_start
        
        # Handle death
        if not player.is_alive:
            if self.gameplay.check_death_delay_complete(player):
                if player.hearts <= 0:
                    self.state_controller.change_state(GameStateEnum.GAME_OVER)
                else:
                    self.respawn_player()
            elif not self.gameplay.is_in_death_delay and player.hearts <= 0:
                self.state_controller.change_state(GameStateEnum.GAME_OVER)
        
        # Cleanup dead enemies
        self.entity_manager.cleanup_dead_enemies()
    
    def draw(self):
        """Main draw loop - delegates to renderer."""
        # Only show tutorial if in PLAYING state (not Main Menu)
        is_playing = self.state_controller.current == GameStateEnum.PLAYING
        
        self.renderer.render(
            entity_manager=self.entity_manager,
            camera=self.camera,
            asset_loader=self.asset_loader,
            platforms=self.platforms,
            trigger_traps=self.trigger_traps,
            parallax_layers=self.parallax_layers,
            moon_object=self.moon_object,
            moon_shadow_object=self.moon_shadow_object,
            current_level_num=self.level_controller.current_level,
            is_playing=is_playing
        )
    
    def snap_actor_to_ground(self, actor_rect, dim='normal', max_dx=160):
        """Snap actor to nearest ground platform - delegates to level controller."""
        return self.level_controller.snap_actor_to_ground(
            self.platforms, actor_rect, dim, max_dx
        )
    
    def run(self):
        """Main game loop."""
        # Load saved progress
        save_data = self.save_manager.load_progress()
        self.level_controller.set_level(save_data.get('current_level', 1))
        self.setup_level(new_game=True)
        
        # UI buttons
        from graphics.ui_buttons import UIButtons
        ui_buttons = UIButtons()
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Event handling
            try:
                events_list = pygame.event.get()
            except Exception:
                pygame.event.clear()
                events_list = []
            
            for event in events_list:
                if event.type == pygame.QUIT:
                    self.running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state_controller.is_state(GameStateEnum.PLAYING):
                            self.state_controller.toggle_pause()
                    elif event.key == pygame.K_p:
                        if self.state_controller.is_state(GameStateEnum.PAUSED):
                            self.state_controller.toggle_pause()
                    elif event.key == pygame.K_F3:
                        self.renderer.toggle_debug()
                
                # Player input - check if any NPC is talking
                any_npc_talking = any(
                    npc.talking for npc in self.entity_manager.npcs
                    if getattr(npc, 'dim', 'both') in (
                        'gema' if self.entity_manager.player.in_gema_dimension else 'normal', 
                        'both'
                    )
                )
                
                # Lock player input when NPC is talking
                if self.entity_manager.player:
                    self.entity_manager.player.input_locked = any_npc_talking
                
                if self.state_controller.is_state(GameStateEnum.PLAYING) and not self.input_locked:
                    # Handle NPC dialog input (always allow E key for dialog)
                    player = self.entity_manager.player
                    current_dim = 'gema' if player.in_gema_dimension else 'normal'
                    for npc in self.entity_manager.npcs:
                        if getattr(npc, 'dim', 'both') in (current_dim, 'both'):
                            npc.handle_event(event, player.rect, player)  # Pass player object
                    
                    # Only allow player movement if no NPC is talking
                    if not any_npc_talking:
                        if self.entity_manager.player:
                            self.entity_manager.player.handle_event(event)
                
                # UI input
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    ui_buttons.handle_click(self, mouse_pos)
            
            # Update
            if self.state_controller.is_state(GameStateEnum.PLAYING):
                self.update()
            
            # Draw
            self.draw()
            
            # Draw UI
            ui_buttons.draw_ui(self, mouse_pos)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
