"""
Renderer - Menangani semua rendering/drawing game.
Memisahkan render logic dari main game class.
"""
import pygame
from typing import List, Dict, Any, TYPE_CHECKING
from utils.settings import COLOR_BG_NORMAL, COLOR_BG_GEMA

if TYPE_CHECKING:
    from core.entity_manager import EntityManager
    from core.camera_controller import CameraController
    from core.asset_loader import AssetLoader


class Renderer:
    """
    Renderer class untuk menangani semua drawing operations.
    Menggunakan Composition - Game class meng-compose renderer ini.
    """
    
    def __init__(self, game_surface: pygame.Surface, screen: pygame.Surface):
        self.game_surface = game_surface
        self.screen = screen
        self.debug_draw = False
    
    def toggle_debug(self):
        """Toggle debug drawing mode."""
        self.debug_draw = not self.debug_draw
    
    def render(self, 
               entity_manager: 'EntityManager',
               camera: 'CameraController',
               asset_loader: 'AssetLoader',
               platforms: List[Dict],
               trigger_traps: List,
               parallax_layers: List,
               moon_object: Any,
               moon_shadow_object: Any,
               current_level_num: int = 1,
               is_playing: bool = True):
        """
        Main render method - draws everything to screen.
        
        Args:
            entity_manager: Entity manager with player, enemies, npcs, campfires
            camera: Camera controller for offset
            asset_loader: Asset loader with tile images and animation frames
            platforms: List of platform dictionaries
            trigger_traps: List of trap objects
            parallax_layers: List of parallax layer objects
            moon_object: Moon drawable object
            moon_shadow_object: Moon shadow drawable object
            current_level_num: Current level number (for tutorial, etc)
            is_playing: Whether the game is in active playing state
        """
        player = entity_manager.player
        camera_offset = camera.get_offset(player.rect)
        
        # Get current dimension
        current_dim = 'gema' if player.in_gema_dimension else 'normal'
        
        # Clear screen with background color
        bg_color = COLOR_BG_GEMA if current_dim == 'gema' else COLOR_BG_NORMAL
        self.game_surface.fill(bg_color)
        
        # Draw parallax background
        self._draw_parallax(parallax_layers, camera_offset)
        
        # Draw moon (gema dimension only)
        if current_dim == 'gema':
            moon_shadow_object.draw(self.game_surface, camera_offset[0])
            moon_object.draw(self.game_surface, camera_offset[0])
        
        # Draw platforms
        self._draw_platforms(platforms, current_dim, camera_offset, asset_loader)
        
        # Draw traps
        self._draw_traps(trigger_traps, current_dim, camera_offset, asset_loader)
        
        # Draw campfires
        self._draw_campfires(entity_manager.campfires, camera_offset, asset_loader, current_level_num, is_playing)
        
        # Draw entities (player, enemies, NPCs)
        entity_manager.draw_all(self.game_surface, camera_offset[0], camera_offset[1])
        
        # Debug drawing
        if self.debug_draw:
            self._draw_debug(entity_manager, camera_offset, current_dim)
        
        # Scale to screen
        self.screen.blit(
            pygame.transform.scale(self.game_surface, self.screen.get_size()), 
            (0, 0)
        )
    
    def _draw_parallax(self, parallax_layers: List, camera_offset: tuple):
        """Draw parallax background layers."""
        for layer in reversed(parallax_layers):
            layer.draw(self.game_surface, camera_offset[0], 0)
    
    def _draw_platforms(self, platforms: List[Dict], current_dim: str, 
                        camera_offset: tuple, asset_loader: 'AssetLoader'):
        """Draw all visible platforms."""
        for p in platforms:
            if p['dim'] in [current_dim, 'both']:
                tile_image = asset_loader.tile_images.get(p['char'])
                if tile_image:
                    scaled_image = pygame.transform.scale(
                        tile_image, 
                        (p['rect'].width, p['rect'].height)
                    )
                    self.game_surface.blit(
                        scaled_image, 
                        (p['rect'].x - camera_offset[0], p['rect'].y - camera_offset[1])
                    )
    
    def _draw_traps(self, trigger_traps: List, current_dim: str,
                    camera_offset: tuple, asset_loader: 'AssetLoader'):
        """Draw all active traps."""
        for trap in trigger_traps:
            if trap.is_active and trap.dim in [current_dim, 'both']:
                trap.draw(
                    self.game_surface, 
                    camera_offset[0], 
                    camera_offset[1], 
                    asset_loader.spike_frames
                )
    
    def _draw_campfires(self, campfires: List, camera_offset: tuple, 
                        asset_loader: 'AssetLoader', current_level_num: int = 1, is_playing: bool = True):
        """Draw all campfires."""
        for campfire in campfires:
            campfire.draw(
                self.game_surface, 
                camera_offset[0], 
                camera_offset[1], 
                asset_loader.campfire_frames
            )
            # Draw tutorial image above campfire in Level 1 only if playing
            if current_level_num == 1 and asset_loader.tutorial_image and is_playing:
                tut_img = asset_loader.tutorial_image
                tut_rect = tut_img.get_rect(midbottom=(
                    campfire.rect.centerx - camera_offset[0],
                    campfire.rect.top - camera_offset[1] - 50  
                ))
                self.game_surface.blit(tut_img, tut_rect)
    
    def _draw_debug(self, entity_manager: 'EntityManager', 
                    camera_offset: tuple, current_dim: str):
        """Draw debug hitboxes for all entities."""
        player = entity_manager.player
        
        # Player hitbox (green)
        pygame.draw.rect(
            self.game_surface, (0, 255, 0),
            pygame.Rect(
                player.rect.x - camera_offset[0], 
                player.rect.y - camera_offset[1],
                player.rect.width, 
                player.rect.height
            ), 1
        )
        
        # Attack hitbox (orange)
        if hasattr(player, "get_attack_hitbox"):
            atk_rect = player.get_attack_hitbox()
            if atk_rect:
                pygame.draw.rect(
                    self.game_surface, (255, 165, 0),
                    pygame.Rect(
                        atk_rect.x - camera_offset[0], 
                        atk_rect.y - camera_offset[1],
                        atk_rect.width, 
                        atk_rect.height
                    ), 1
                )
        
        # Enemy hitboxes (gray)
        for enemy in entity_manager.enemies:
            pygame.draw.rect(
                self.game_surface, (180, 180, 180),
                pygame.Rect(
                    enemy.rect.x - camera_offset[0], 
                    enemy.rect.y - camera_offset[1],
                    enemy.rect.width, 
                    enemy.rect.height
                ), 1
            )
        
        # NPC hitboxes (cyan)
        for npc in entity_manager.npcs:
            if getattr(npc, "dim", "both") in (current_dim, "both"):
                pygame.draw.rect(
                    self.game_surface, (0, 255, 255),
                    pygame.Rect(
                        npc.rect.x - camera_offset[0], 
                        npc.rect.y - camera_offset[1],
                        npc.rect.width, 
                        npc.rect.height
                    ), 1
                )
