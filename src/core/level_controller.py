"""
Level Controller - Mengelola level loading, setup, dan progression.
Memisahkan logic level dari main game class.
"""
import pygame
import os
from typing import List, Tuple, Dict, Optional
from utils.exception import LevelFileNotFound


class LevelController:
    """Controller untuk mengelola level progression dan loading."""
    
    def __init__(self, levels_dir: str, tile_size: int = 40):
        self.levels_dir = levels_dir
        self.tile_size = tile_size
        self.current_level_index = 0
        
        # Level definitions (normal, gema pairs)
        self.level_files = [
            ("tutorial_normal.txt", "tutorial_gema.txt"),
            ("level_1_normal.txt", "level_1_gema.txt"),
            ("level_2_normal.txt", "level_2_gema.txt"),
            ("level_3_normal.txt", "level_3_gema.txt"),
            ("level_4_normal.txt", "level_4_gema.txt")
        ]
        
    @property
    def total_levels(self) -> int:
        """Get total number of levels."""
        return len(self.level_files)
    
    @property
    def current_level(self) -> int:
        """Get current level number (1-indexed)."""
        return self.current_level_index + 1
    
    def get_level_paths(self, level_index: Optional[int] = None) -> Tuple[str, str]:
        """Get file paths for a level (normal and gema)."""
        if level_index is None:
            level_index = self.current_level_index
            
        if level_index >= len(self.level_files):
            raise IndexError(f"Level index {level_index} out of range")
            
        normal_file, gema_file = self.level_files[level_index]
        return (
            os.path.join(self.levels_dir, normal_file),
            os.path.join(self.levels_dir, gema_file)
        )
    
    def advance_level(self) -> bool:
        """
        Advance to next level.
        Returns True if there's a next level, False if completed all levels.
        """
        self.current_level_index += 1
        return self.current_level_index < len(self.level_files)
    
    def reset_to_first_level(self):
        """Reset to first level."""
        self.current_level_index = 0
    
    def set_level(self, level_number: int):
        """Set current level by number (1-indexed)."""
        level_index = level_number - 1
        if 0 <= level_index < len(self.level_files):
            self.current_level_index = level_index
        else:
            self.current_level_index = 0
    
    def parse_level_file(self, filepath: str) -> Dict:
        """
        Parse a level file and return level data.
        Returns dict with platforms, enemy_spawns, triggers, etc.
        """
        level_data = {
            'platforms': [],
            'triggers': [],
            'trap_zones': [],
            'enemy_spawns': [],
            'npc_spawns': {'A': [], 'Q': [], 'W': []},
            'campfires': [],
            'end_triggers': [],
            'start_pos': None,
            'left_markers': {},
            'right_markers': {},
            'camera_right_limit': None,
            'max_width': 0
        }
        
        try:
            line_count = 0
            max_lines = 1000  # Safety limit to prevent infinite loops
            
            with open(filepath, 'r') as file:
                for y, line in enumerate(file):
                    line_count += 1
                    if line_count > max_lines:
                        print(f"Warning: Level file {filepath} exceeded {max_lines} lines, stopping parse")
                        break
                    
                    for x, char in enumerate(line):
                        world_x = x * self.tile_size
                        world_y = y * self.tile_size
                        rect = pygame.Rect(world_x, world_y, self.tile_size, self.tile_size)
                        
                        if world_x > level_data['max_width']:
                            level_data['max_width'] = world_x
                        
                        # Parse different tile types
                        self._parse_tile(char, rect, world_x, world_y, y, level_data)
                        
        except FileNotFoundError:
            raise LevelFileNotFound(filepath)
        except Exception as e:
            print(f"Error parsing level file {filepath}: {e}")
            raise
        
        return level_data
    
    def _parse_tile(self, char: str, rect: pygame.Rect, world_x: int, world_y: int, row: int, level_data: Dict):
        """Parse individual tile character and update level_data."""
        # Ground tiles
        if char in 'Gg':
            level_data['platforms'].append({'rect': rect, 'char': 'G'})
        
        # Platform tiles
        elif char in 'Pp':
            plat_rect = pygame.Rect(world_x, world_y, self.tile_size, 20)
            level_data['platforms'].append({'rect': plat_rect, 'char': 'P'})
        
        # Enemies
        elif char in 'Hh':
            facing = 'right' if char == 'H' else 'left'
            level_data['enemy_spawns'].append({
                'rect': rect, 'type': 'patrol', 'facing': facing
            })
        elif char in 'Nn':
            facing = 'right' if char == 'N' else 'left'
            level_data['enemy_spawns'].append({
                'rect': rect, 'type': 'chaser_heavy', 'facing': facing
            })
        elif char in 'Ff':
            facing = 'right' if char == 'F' else 'left'
            level_data['enemy_spawns'].append({
                'rect': rect, 'type': 'chaser', 'facing': facing
            })
        elif char in 'Bb':
            facing = 'right' if char == 'B' else 'left'
            level_data['enemy_spawns'].append({
                'rect': rect, 'type': 'boss', 'facing': facing
            })
        
        # Triggers and traps
        elif char in 'Tt':
            level_data['triggers'].append(rect)
        elif char in 'jJyY':
            level_data['trap_zones'].append(rect)
        
        # Start position
        elif char in 'Ss':
            level_data['start_pos'] = (world_x, world_y + self.tile_size)
        
        # End triggers
        elif char == 'D':
            level_data['end_triggers'].append({'rect': rect, 'mode': 'jump_walk'})
        elif char == 'd':
            level_data['end_triggers'].append({'rect': rect, 'mode': 'walk'})
        
        # Campfires
        elif char in 'Cc':
            level_data['campfires'].append(rect)
        
        # Patrol markers
        elif char in 'lL':
            level_data['left_markers'].setdefault(row, []).append(world_x + self.tile_size // 2)
        elif char in 'rR':
            level_data['right_markers'].setdefault(row, []).append(world_x + self.tile_size // 2)
        
        # NPCs
        elif char in 'Aa':
            facing = 'left' if char == 'A' else 'right'
            level_data['npc_spawns']['A'].append({'rect': rect, 'facing': facing})
        elif char in 'Qq':
            facing = 'left' if char == 'Q' else 'right'
            level_data['npc_spawns']['Q'].append({'rect': rect, 'facing': facing})
        elif char in 'Ww':
            facing = 'left' if char == 'W' else 'right'
            level_data['npc_spawns']['W'].append({'rect': rect, 'facing': facing})
        
        # Camera limit
        elif char == 'K':
            level_data['camera_right_limit'] = world_x + self.tile_size // 2
    
    # Platform utility methods
    def ground_rect_at_or_near(self, platforms: list, x: float, dim: str = 'normal', max_dx: int = 160):
        """
        Find ground rect at or near x position.
        
        Args:
            platforms: List of platform dicts with 'rect' and 'dim' keys
            x: X position to search near
            dim: Dimension to filter by ('normal', 'gema', 'both')
            max_dx: Maximum distance to search
        
        Returns:
            pygame.Rect or None
        """
        # Find exact matches (x is within platform bounds)
        exact = [p['rect'] for p in platforms
                if p['dim'] in [dim, 'both'] and p['rect'].left <= x <= p['rect'].right]
        if exact:
            return min(exact, key=lambda r: r.top)
        
        # Find nearby platforms
        near = [(abs(x - r.centerx), r) for r in
                (p['rect'] for p in platforms if p['dim'] in [dim, 'both'])]
        near = [t for t in near if t[0] <= max_dx]
        if near:
            return min(near, key=lambda t: (t[0], t[1].top))[1]
        
        return None
    
    def snap_actor_to_ground(self, platforms: list, actor_rect, dim: str = 'normal', max_dx: int = 160) -> bool:
        """
        Snap actor rect to nearest ground platform.
        
        Args:
            platforms: List of platform dicts with 'rect' and 'dim' keys
            actor_rect: pygame.Rect to snap (modified in place)
            dim: Dimension to filter by
            max_dx: Maximum horizontal distance to search
        
        Returns:
            True if snapped, False if no ground found
        """
        ground = self.ground_rect_at_or_near(platforms, actor_rect.centerx, dim, max_dx)
        if ground:
            actor_rect.bottom = ground.top
            actor_rect.centerx = max(
                ground.left + actor_rect.width // 2,
                min(ground.right - actor_rect.width // 2, actor_rect.centerx)
            )
            return True
        return False
