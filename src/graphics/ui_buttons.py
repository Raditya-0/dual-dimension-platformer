"""
UI Button Handler - Mengelola semua button interactions.
Memisahkan UI logic dari main game loop.
"""
import pygame
from utils.settings import SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_START_HEARTS
from core.game_state import GameStateEnum


class UIButtons:
    """Handler untuk semua UI buttons."""
    
    def __init__(self):
        # Main menu buttons
        self.continue_button = pygame.Rect(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 - 40, 200, 50)
        self.new_game_button = pygame.Rect(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 + 35, 200, 50)
        self.exit_button = pygame.Rect(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 + 110, 200, 50)
        
        # In-game buttons
        self.pause_button = pygame.Rect(SCREEN_WIDTH - 50, 10, 40, 40)
        
        # Pause menu buttons (will be set by UI module)
        self.resume_button = None
        self.restart_button = None
        self.settings_button = None
        self.main_menu_button = None
        self.music_button = None
        self.back_button = None
    
    def handle_click(self, game, mouse_pos):
        """Handle mouse click on buttons."""
        # Prevent spam clicking
        current_time = pygame.time.get_ticks()
        if current_time - game.last_click_time < game.click_cooldown_ms:
            return
        
        game.last_click_time = current_time
        
        state = game.state_controller.current
        
        if state == GameStateEnum.MAIN_MENU:
            self._handle_main_menu_click(game, mouse_pos)
        elif state == GameStateEnum.PLAYING:
            self._handle_playing_click(game, mouse_pos)
        elif state == GameStateEnum.PAUSED:
            self._handle_paused_click(game, mouse_pos)
        elif state == GameStateEnum.GAME_OVER:
            self._handle_game_over_click(game, mouse_pos)
        elif state == GameStateEnum.GAME_OVER_WIN:
            self._handle_game_over_win_click(game, mouse_pos)
    
    def _handle_main_menu_click(self, game, mouse_pos):
        """Handle main menu button clicks."""
        # Continue button
        if self.continue_button.collidepoint(mouse_pos):
            save_data = game.save_manager.load_progress()
            game.level_controller.set_level(save_data.get('current_level', 1))
            game.setup_level(new_game=True)
            game.entity_manager.player.hearts = save_data.get('hearts', PLAYER_START_HEARTS)
            game.state_controller.change_state(GameStateEnum.PLAYING)
        
        # New game button
        elif self.new_game_button.collidepoint(mouse_pos):
            game.level_controller.reset_to_first_level()
            game.setup_level(new_game=True)
            game.entity_manager.player.hearts = PLAYER_START_HEARTS
            game.save_manager.save_progress(1, PLAYER_START_HEARTS)
            game.state_controller.change_state(GameStateEnum.PLAYING)
        
        # Exit button
        elif self.exit_button.collidepoint(mouse_pos):
            game.running = False
    
    def _handle_playing_click(self, game, mouse_pos):
        """Handle playing state button clicks."""
        if self.pause_button.collidepoint(mouse_pos):
            game.state_controller.toggle_pause()
    
    def _handle_paused_click(self, game, mouse_pos):
        """Handle pause menu button clicks."""
        if game.is_settings_open:
            if hasattr(game, 'music_button') and game.music_button and game.music_button.collidepoint(mouse_pos):
                game.is_music_paused = not game.is_music_paused
                if game.is_music_paused:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            
            if hasattr(game, 'back_button') and game.back_button and game.back_button.collidepoint(mouse_pos):
                game.is_settings_open = False
        else:
            # Ensure buttons are created (they are created in draw_ui)
            screen_width = game.screen.get_width()
            screen_height = game.screen.get_height()
            
            # Define button rects here to ensure they exist
            resume_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2 - 75, 200, 50)
            restart_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2, 200, 50)
            settings_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2 + 75, 200, 50)
            main_menu_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2 + 150, 200, 50)
            
            if resume_button.collidepoint(mouse_pos):
                print("[UI] Resume button clicked")
                game.state_controller.change_state(GameStateEnum.PLAYING)
            
            elif restart_button.collidepoint(mouse_pos):
                # Show loading indicator
                print("[UI] Restart button clicked - Restarting level...")
                
                # Process events to prevent freeze
                pygame.event.pump()
                pygame.display.flip()
                
                # Use quick restart to avoid re-parsing level files
                try:
                    game.quick_restart_level()
                    print("[UI] Changing state to PLAYING")
                    game.state_controller.change_state(GameStateEnum.PLAYING)
                    print("[UI] Level restarted successfully")
                except Exception as e:
                    print(f"[ERROR] Error restarting level: {e}")
                    import traceback
                    traceback.print_exc()
            
            elif settings_button.collidepoint(mouse_pos):
                print("[UI] Settings button clicked")
                game.is_settings_open = True
            
            elif main_menu_button.collidepoint(mouse_pos):
                print("[UI] Main menu button clicked")
                # Save progress
                game.save_manager.save_progress(
                    game.level_controller.current_level,
                    game.entity_manager.player.hearts
                )
                # Load saved level for background
                save_data = game.save_manager.load_progress()
                game.level_controller.set_level(save_data.get('current_level', 1))
                game.setup_level(new_game=True)
                game.state_controller.change_state(GameStateEnum.MAIN_MENU)
    
    def _handle_game_over_click(self, game, mouse_pos):
        """Handle game over screen button clicks."""
        # Define button rects here to ensure they exist
        screen_width = game.screen.get_width()
        screen_height = game.screen.get_height()
        restart_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2, 200, 50)
        main_menu_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2 + 75, 200, 50)
        
        if restart_button.collidepoint(mouse_pos):
            print("[UI] Game Over - Restart button clicked")
            pygame.event.pump()
            pygame.display.flip()
            
            try:
                game.entity_manager.player.hearts = PLAYER_START_HEARTS
                game.respawn_player()
                game.state_controller.change_state(GameStateEnum.PLAYING)
                print("[UI] Game restarted successfully")
            except Exception as e:
                print(f"[ERROR] Error restarting game: {e}")
                import traceback
                traceback.print_exc()
        
        elif main_menu_button.collidepoint(mouse_pos):
            print("[UI] Game Over - Main menu button clicked")
            # Load saved level for background
            save_data = game.save_manager.load_progress()
            game.level_controller.set_level(save_data.get('current_level', 1))
            game.setup_level(new_game=True)
            game.state_controller.change_state(GameStateEnum.MAIN_MENU)

    def _handle_game_over_win_click(self, game, mouse_pos):
        """Handle win screen button clicks."""
        # Define button rects here to ensure they exist
        screen_width = game.screen.get_width()
        screen_height = game.screen.get_height()
        restart_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2, 200, 50)
        main_menu_button = pygame.Rect(screen_width / 2 - 100, screen_height / 2 + 75, 200, 50)
        
        if restart_button.collidepoint(mouse_pos):
            print("[UI] Win Screen - Mulai Baru button clicked")
            pygame.event.pump()
            pygame.display.flip()
            
            try:
                # Reset to first level
                game.level_controller.reset_to_first_level()
                game.setup_level(new_game=True, force_reparse=True)
                game.entity_manager.player.hearts = PLAYER_START_HEARTS
                game.state_controller.change_state(GameStateEnum.PLAYING)
                print("[UI] Game restarted successfully")
            except Exception as e:
                print(f"[ERROR] Error restarting game: {e}")
                import traceback
                traceback.print_exc()
        
        elif main_menu_button.collidepoint(mouse_pos):
            print("[UI] Win Screen - Main menu button clicked")
            game.level_controller.set_level(1)
            game.setup_level(new_game=True)
            game.state_controller.change_state(GameStateEnum.MAIN_MENU)
    
    def draw_ui(self, game, mouse_pos):
        """Draw UI elements based on current state."""
        from graphics import UI
        
        state = game.state_controller.current
        
        if state == GameStateEnum.PLAYING or state == GameStateEnum.PAUSED:
            # Draw hearts
            for i in range(game.entity_manager.player.hearts):
                game.screen.blit(game.asset_loader.heart_icon, (10 + i * 35, 10))
            
            # Draw pause button
            pygame.draw.circle(game.screen, (100, 100, 100), self.pause_button.center, 20)
            if self.pause_button.collidepoint(mouse_pos):
                pygame.draw.circle(game.screen, (150, 150, 150), self.pause_button.center, 20)
            UI.draw_text(game, "||", 32, (255, 255, 255), self.pause_button.centerx, 
                        self.pause_button.centery, shadow_color=None)
        
        if state == GameStateEnum.MAIN_MENU:
            self._draw_main_menu(game, mouse_pos)
        elif state == GameStateEnum.PAUSED:
            if game.is_settings_open:
                UI.draw_settings_menu(game)
            else:
                UI.draw_pause_menu(game)
        elif state == GameStateEnum.GAME_OVER_WIN:
            UI.draw_win_screen(game)
        elif state == GameStateEnum.GAME_OVER:
            UI.draw_game_over_screen(game)
    
    def _draw_main_menu(self, game, mouse_pos):
        """Draw main menu."""
        from graphics import UI
        
        UI.draw_text(game, "Dual Dimension", 80, (255, 255, 255), 
                    SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, shadow_color=(20, 20, 20))
        
        # Continue button
        continue_color = (150, 150, 150) if self.continue_button.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, continue_color, self.continue_button, border_radius=10)
        UI.draw_text(game, "Lanjutkan", 32, (255, 255, 255), 
                    self.continue_button.centerx, self.continue_button.centery)
        
        # New game button
        new_game_color = (150, 150, 150) if self.new_game_button.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, new_game_color, self.new_game_button, border_radius=10)
        UI.draw_text(game, "Mulai Baru", 32, (255, 255, 255), 
                    self.new_game_button.centerx, self.new_game_button.centery)
        
        # Exit button
        exit_color = (150, 150, 150) if self.exit_button.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, exit_color, self.exit_button, border_radius=10)
        UI.draw_text(game, "Keluar", 32, (255, 255, 255), 
                    self.exit_button.centerx, self.exit_button.centery)
