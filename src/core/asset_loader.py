"""
Asset Loader - Centralized asset loading dan caching.
"""
import pygame
import os
from typing import Dict, List, Optional
from utils.exception import AssetLoadError, AudioLoadError
from utils import assets
from environment.trap import load_spike_frames
from environment.campfire import load_campfire_frames


class AssetLoader:
    """Loader untuk semua game assets."""
    
    def __init__(self, assets_path: str):
        self.assets_path = assets_path
        
        # Cached assets
        self.tile_images: Dict[str, pygame.Surface] = {}
        self.spike_frames: List[pygame.Surface] = []
        self.campfire_frames: List[pygame.Surface] = []
        self.forest_layers: List[pygame.Surface] = []
        self.moon_image: Optional[pygame.Surface] = None
        self.moon_shadow_image: Optional[pygame.Surface] = None
        self.heart_icon: Optional[pygame.Surface] = None
        self.tutorial_image: Optional[pygame.Surface] = None
        
        # Menu assets
        self.menu_assets: Dict[str, pygame.Surface] = {}
        
    def load_all_assets(self, game_surface_height: int):
        """Load all game assets."""
        self.load_tiles()
        self.load_spike_frames()
        self.load_campfire_frames()
        self.load_background_layers(game_surface_height)
        self.load_ui_assets()
        self.load_menu_assets()
        self.load_tutorial_assets()
        
    def load_tutorial_assets(self):
        """Load tutorial images."""
        try:
            tutorial_path = os.path.join(self.assets_path, 'Tutorial', 'Keyboard Tutorial.png')
            if os.path.exists(tutorial_path):
                img = pygame.image.load(tutorial_path).convert_alpha()
                img = pygame.transform.scale_by(img, 0.5)
                
                self.tutorial_image = img
        except pygame.error as e:
            print(f"Failed to load tutorial image: {e}")
    
    def load_tiles(self):
        """Load tile images."""
        try:
            ground_path = os.path.join(self.assets_path, 'Tiles', 'ground.png')
            platform_path = os.path.join(self.assets_path, 'Tiles', 'platform.png')
            
            self.tile_images = {
                'G': pygame.image.load(ground_path).convert_alpha(),
                'P': pygame.image.load(platform_path).convert_alpha(),
            }
        except pygame.error as e:
            raise AssetLoadError("Tiles (ground/platform)", e)
    
    def load_spike_frames(self):
        """Load spike animation frames."""
        self.spike_frames = load_spike_frames(self.assets_path)
    
    def load_campfire_frames(self):
        """Load campfire animation frames."""
        self.campfire_frames = load_campfire_frames(self.assets_path)
    
    def load_background_layers(self, game_surface_height: int):
        """Load parallax background layers."""
        try:
            self.forest_layers = []
            for i in range(10):
                path = os.path.join(self.assets_path, 'Background', f'forest_layer_{i}.png')
                image = pygame.image.load(path).convert_alpha()
                
                # Scale to match game surface height
                aspect_ratio = image.get_width() / image.get_height()
                scaled_width = int(game_surface_height * aspect_ratio)
                scaled_image = pygame.transform.scale(image, (scaled_width, game_surface_height))
                
                self.forest_layers.append(scaled_image)
            
            # Load moon images
            moon_path = os.path.join(self.assets_path, 'Background', 'moon.png')
            moon_shadow_path = os.path.join(self.assets_path, 'Background', 'moon_shadow.png')
            
            self.moon_image = pygame.image.load(moon_path).convert_alpha()
            self.moon_shadow_image = pygame.image.load(moon_shadow_path).convert_alpha()
            
        except pygame.error as e:
            raise AssetLoadError("Background layers", e)
    
    def load_ui_assets(self):
        """Load UI assets like heart icon."""
        self.heart_icon = assets.create_heart_surface()
    
    def load_menu_assets(self):
        """Load main menu assets (background and buttons)."""
        try:
            menu_path = os.path.join(self.assets_path, 'menu')
            
            self.menu_assets = {
                'background': pygame.image.load(os.path.join(menu_path, 'background.jpg')).convert(),
                'btn_lanjutkan': pygame.image.load(os.path.join(menu_path, 'btn_lanjutkan.png')).convert_alpha(),
                'btn_mulai_baru': pygame.image.load(os.path.join(menu_path, 'btn_mulai_baru.png')).convert_alpha(),
                'btn_keluar': pygame.image.load(os.path.join(menu_path, 'btn_keluar.png')).convert_alpha(),
            }
        except pygame.error as e:
            raise AssetLoadError("Menu assets", e)
    
    def load_music(self, music_file: str):
        """Load and play background music."""
        try:
            music_path = os.path.join(self.assets_path, 'Sound', music_file)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            raise AudioLoadError(music_path, e)
