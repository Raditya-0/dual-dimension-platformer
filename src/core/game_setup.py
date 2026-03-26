"""
Game Setup - Menangani semua initialization dan setup game.
Memisahkan setup logic dari main game class.
"""
import pygame
import os
from typing import Dict, List, Tuple, Any, Optional

# Core controllers
from core.game_state import GameStateController
from core.level_controller import LevelController
from core.entity_manager import EntityManager
from core.camera_controller import CameraController
from core.asset_loader import AssetLoader
from core.gameplay_handler import GameplayHandler

# Game systems
from environment.trap import TriggerTrap
from environment.campfire import Campfire
from graphics.parallax import ParallaxLayer, ParallaxObject
from graphics.renderer import Renderer
from entity.npc import NPC

# Managers
from managers.save_manager import SaveManager

# Settings
from utils.settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, 
    CAMERA_ZOOM_DIVIDER, CAMERA_MANUAL_OFFSET_X, CAMERA_MANUAL_OFFSET_Y
)
from utils.exception import AssetLoadError, AudioLoadError


class GameSetup:
    """
    Handles all game initialization and setup.
    Uses composition pattern - Game class composes this.
    """
    
    @staticmethod
    def init_pygame() -> Tuple[pygame.Surface, pygame.Surface, pygame.time.Clock, pygame.font.Font]:
        """
        Initialize Pygame and create display surfaces.
        
        Returns:
            tuple: (screen, game_surface, clock, font)
        """
        pygame.init()
        pygame.mixer.init()
        
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        
        game_surface_width = SCREEN_WIDTH // CAMERA_ZOOM_DIVIDER
        game_surface_height = SCREEN_HEIGHT // CAMERA_ZOOM_DIVIDER
        game_surface = pygame.Surface((game_surface_width, game_surface_height))
        
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 40)
        
        return screen, game_surface, clock, font
    
    @staticmethod
    def init_controllers(base_path: str, game_surface_width: int, game_surface_height: int) -> Dict[str, Any]:
        """
        Initialize all game controllers.
        
        Args:
            base_path: Base path of the game
            game_surface_width: Width of game surface
            game_surface_height: Height of game surface
            
        Returns:
            dict: Dictionary containing all controllers
        """
        return {
            'state_controller': GameStateController(),
            'level_controller': LevelController(os.path.join(base_path, "levels")),
            'entity_manager': EntityManager(),
            'camera': CameraController(
                game_surface_width,
                game_surface_height,
                CAMERA_MANUAL_OFFSET_X,
                CAMERA_MANUAL_OFFSET_Y
            ),
            'save_manager': SaveManager()
        }
    
    @staticmethod
    def init_asset_loader(base_path: str, game_surface_height: int) -> AssetLoader:
        """
        Initialize and load all game assets.
        
        Args:
            base_path: Base path of the game
            game_surface_height: Height of game surface
            
        Returns:
            AssetLoader instance with loaded assets
        """
        assets_path = os.path.join(base_path, '..', 'Assets')
        asset_loader = AssetLoader(assets_path)
        asset_loader.load_all_assets(game_surface_height)
        asset_loader.load_music('music_platformer.ogg')
        return asset_loader
    
    @staticmethod
    def init_gameplay_systems(entity_manager: EntityManager, game_surface: pygame.Surface, 
                              screen: pygame.Surface) -> Dict[str, Any]:
        """
        Initialize gameplay-related systems.
        
        Args:
            entity_manager: Entity manager instance
            game_surface: Game surface for rendering
            screen: Main screen surface
            
        Returns:
            dict: Dictionary containing gameplay systems
        """
        return {
            'gameplay': GameplayHandler(entity_manager),
            'renderer': Renderer(game_surface, screen)
        }
    
    @staticmethod
    def setup_platforms(normal_data: Dict, gema_data: Dict) -> List[Dict]:
        """
        Setup platforms from level data.
        
        Args:
            normal_data: Parsed normal dimension data
            gema_data: Parsed gema dimension data
            
        Returns:
            List of platform dictionaries
        """
        platforms = []
        
        for p in normal_data['platforms']:
            platforms.append({
                'rect': p['rect'].copy(), 
                'dim': 'normal', 
                'char': p['char']
            })
        
        for p in gema_data['platforms']:
            platforms.append({
                'rect': p['rect'].copy(), 
                'dim': 'gema', 
                'char': p['char']
            })
        
        return platforms
    
    @staticmethod
    def setup_trigger_traps(normal_data: Dict, gema_data: Dict) -> List[TriggerTrap]:
        """
        Setup trigger traps from level data.
        
        Args:
            normal_data: Parsed normal dimension data
            gema_data: Parsed gema dimension data
            
        Returns:
            List of TriggerTrap instances
        """
        traps = []
        
        for trigger_rect, trap_rect in zip(normal_data['triggers'], normal_data['trap_zones']):
            traps.append(TriggerTrap(trigger_rect.copy(), trap_rect.copy(), dim='normal'))
        
        for trigger_rect, trap_rect in zip(gema_data['triggers'], gema_data['trap_zones']):
            traps.append(TriggerTrap(trigger_rect.copy(), trap_rect.copy(), dim='gema'))
        
        return traps
    
    @staticmethod
    def setup_end_triggers(normal_data: Dict, gema_data: Dict) -> List[Dict]:
        """
        Setup end triggers from level data.
        
        Args:
            normal_data: Parsed normal dimension data
            gema_data: Parsed gema dimension data
            
        Returns:
            List of end trigger dictionaries
        """
        end_triggers = []
        
        for et in normal_data['end_triggers']:
            end_triggers.append({
                'rect': et['rect'].copy(), 
                'dim': 'normal', 
                'mode': et['mode']
            })
        
        for et in gema_data['end_triggers']:
            end_triggers.append({
                'rect': et['rect'].copy(), 
                'dim': 'gema', 
                'mode': et['mode']
            })
        
        return end_triggers
    
    @staticmethod
    def setup_enemies(entity_manager: EntityManager, normal_data: Dict, 
                      gema_data: Dict, tile_size: int):
        """
        Setup enemies from level data.
        
        Args:
            entity_manager: Entity manager to add enemies to
            normal_data: Parsed normal dimension data
            gema_data: Parsed gema dimension data
            tile_size: Size of each tile
        """
        def add_enemies_from_data(data: Dict, dim: str):
            for spawn in data['enemy_spawns']:
                spawn_rect = spawn['rect']
                row = spawn_rect.y // tile_size
                
                # Calculate patrol bounds
                left_list = data['left_markers'].get(row, [])
                right_list = data['right_markers'].get(row, [])
                sx = spawn_rect.centerx
                left_bound = max([lx for lx in left_list if lx <= sx], default=sx - 80)
                right_bound = min([rx for rx in right_list if rx >= sx], default=sx + 80)
                
                # Bosses exist in both dimensions to maintain state
                actual_dim = 'both' if spawn['type'] == 'boss' else dim

                entity_manager.add_enemy(
                    spawn['type'], spawn_rect, spawn['facing'],
                    left_bound, right_bound, actual_dim
                )

        add_enemies_from_data(normal_data, 'normal')
        add_enemies_from_data(gema_data, 'gema')
    
    @staticmethod
    def setup_npcs(entity_manager: EntityManager, normal_spawns: List, 
                   gema_spawns: List, snap_func) -> List:
        """
        Setup NPCs from level data.
        
        Args:
            entity_manager: Entity manager to add NPCs to
            normal_spawns: Normal dimension NPC spawns
            gema_spawns: Gema dimension NPC spawns
            snap_func: Function to snap actors to ground
            
        Returns:
            List of NPC instances
        """
        npcs = NPC.spawn_from_maps(normal_spawns, gema_spawns)
        entity_manager.npcs = npcs
        
        # Snap NPCs to ground
        for npc in npcs:
            dim = getattr(npc, 'dim', 'normal')
            if getattr(npc, 'auto_snap', True):
                snap_func(npc.rect, dim=dim, max_dx=200)
        
        return npcs
    
    @staticmethod
    def setup_campfires(entity_manager: EntityManager, normal_campfires: List, 
                        gema_campfires: List):
        """
        Setup campfires from level data.
        
        Args:
            entity_manager: Entity manager to add campfires to
            normal_campfires: Normal dimension campfire rects
            gema_campfires: Gema dimension campfire rects
        """
        for rect in normal_campfires:
            entity_manager.add_campfire(Campfire(rect))
        for rect in gema_campfires:
            entity_manager.add_campfire(Campfire(rect))
    
    @staticmethod
    def setup_parallax(asset_loader: AssetLoader) -> Tuple[List[ParallaxLayer], ParallaxObject, ParallaxObject]:
        """
        Setup parallax layers.
        
        Args:
            asset_loader: Asset loader with loaded images
            
        Returns:
            tuple: (parallax_layers, moon_object, moon_shadow_object)
        """
        parallax_layers = []
        speeds = [0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1]
        
        for i, image in enumerate(asset_loader.forest_layers):
            if i < len(speeds):
                layer = ParallaxLayer(image, speeds[i])
                parallax_layers.append(layer)
        
        moon_object = ParallaxObject(asset_loader.moon_image, 0.045, 50, x_offset=150)
        moon_shadow_object = ParallaxObject(asset_loader.moon_shadow_image, 0.05, 60, x_offset=160)
        
        return parallax_layers, moon_object, moon_shadow_object
    
    @staticmethod
    def quick_restart_from_cache(cached_normal_data: Dict, cached_gema_data: Dict) -> Dict:
        """
        Quick restart level using cached data (no file re-parsing).
        
        Args:
            cached_normal_data: Cached normal dimension data
            cached_gema_data: Cached gema dimension data
            
        Returns:
            Dict with 'platforms', 'trigger_traps', 'end_triggers'
        """
        result = {
            'platforms': [],
            'trigger_traps': [],
            'end_triggers': []
        }
        
        if not cached_normal_data or not cached_gema_data:
            return result
        
        # Setup platforms from cache
        for p in cached_normal_data['platforms']:
            result['platforms'].append({
                'rect': p['rect'].copy(), 
                'dim': 'normal', 
                'char': p['char']
            })
        for p in cached_gema_data['platforms']:
            result['platforms'].append({
                'rect': p['rect'].copy(), 
                'dim': 'gema', 
                'char': p['char']
            })
        
        # Setup trigger traps from cache
        for trigger_rect, trap_rect in zip(
            cached_normal_data['triggers'], 
            cached_normal_data['trap_zones']
        ):
            result['trigger_traps'].append(
                TriggerTrap(trigger_rect.copy(), trap_rect.copy(), dim='normal')
            )
        for trigger_rect, trap_rect in zip(
            cached_gema_data['triggers'], 
            cached_gema_data['trap_zones']
        ):
            result['trigger_traps'].append(
                TriggerTrap(trigger_rect.copy(), trap_rect.copy(), dim='gema')
            )
        
        # Setup end triggers from cache
        for et in cached_normal_data['end_triggers']:
            result['end_triggers'].append({
                'rect': et['rect'].copy(), 
                'dim': 'normal', 
                'mode': et['mode']
            })
        for et in cached_gema_data['end_triggers']:
            result['end_triggers'].append({
                'rect': et['rect'].copy(), 
                'dim': 'gema', 
                'mode': et['mode']
            })
        
        return result
