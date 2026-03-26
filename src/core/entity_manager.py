"""
Entity Manager - Mengelola entities (player, enemies, NPCs).
Centralized management untuk semua game entities.
"""
import pygame
from typing import List, Dict, Optional
from entity.player import Player
from entity.enemy import PatrollingEnemy, ChaserEnemy
from entity.boss import Boss
from entity.npc import NPC
from environment.campfire import Campfire


class EntityManager:
    """Manager untuk mengelola semua entities dalam game."""
    
    def __init__(self):
        self.player: Optional[Player] = None
        self.enemies: List = []
        self.npcs: List[NPC] = []
        self.campfires: List[Campfire] = []
        
        # Store spawn information for respawning
        self.enemy_spawns: List[Dict] = []
        self.start_pos: tuple = (100, 100)
        
    def create_player(self, x: float, y: float) -> Player:
        """Create player at position."""
        self.player = Player(x, y)
        self.start_pos = (x, y)
        return self.player
    
    def respawn_player(self):
        """Respawn player at start position."""
        if self.player:
            print(f"[DEBUG] Respawning player at {self.start_pos}")
            self.player.respawn(self.start_pos)
            print(f"[DEBUG] Player respawned - hearts: {self.player.hearts}, alive: {self.player.is_alive}")
    
    def add_enemy(self, enemy_type: str, rect: pygame.Rect, facing: str = 'right', 
                  left_bound: Optional[float] = None, right_bound: Optional[float] = None, 
                  dim: str = 'both'):
        """Add enemy to manager."""
        enemy = None
        
        if enemy_type == 'chaser':
            enemy = ChaserEnemy(rect.x, rect.bottom, size=(50, 50), speed=2.5, facing=facing)
        elif enemy_type == 'chaser_heavy':
            enemy = ChaserEnemy(rect.x, rect.bottom, size=(50, 50), speed=2.2, 
                              facing=facing, asset_folder='Heavy Bandit')
        elif enemy_type == 'boss':
            enemy = Boss(rect.x, rect.bottom, size=(140, 93), speed=1.5, facing=facing)
        elif enemy_type == 'patrol':
            enemy = PatrollingEnemy(rect.x, rect.bottom, left_bound, right_bound, 
                                   size=(30, 30), speed=2.0)
            enemy.direction = 1 if facing == 'right' else -1
        
        if enemy:
            enemy.dim = dim
            self.enemies.append(enemy)
            
            # Store spawn info for respawning
            self.enemy_spawns.append({
                'x': rect.x,
                'y': rect.bottom,
                'type': enemy_type,
                'facing': facing,
                'left_bound': left_bound,
                'right_bound': right_bound,
                'dim': dim
            })
        
        return enemy
    
    def respawn_all_enemies(self):
        """Respawn all enemies from spawn data."""
        print(f"[DEBUG] Respawning {len(self.enemy_spawns)} enemies")
        self.enemies.clear()
        
        # Store enemy_spawns temporarily to avoid duplication during add_enemy
        spawns_copy = list(self.enemy_spawns)
        self.enemy_spawns.clear()
        
        for spawn_info in spawns_copy:
            self.add_enemy(
                spawn_info['type'],
                pygame.Rect(spawn_info['x'], spawn_info['y'] - 40, 40, 40),
                spawn_info['facing'],
                spawn_info.get('left_bound'),
                spawn_info.get('right_bound'),
                spawn_info.get('dim', 'both')
            )
        print(f"[DEBUG] Enemies respawned - total: {len(self.enemies)}")
    
    def add_npc(self, npc: NPC):
        """Add NPC to manager."""
        self.npcs.append(npc)
    
    def add_campfire(self, campfire: Campfire):
        """Add campfire to manager."""
        self.campfires.append(campfire)
    
    def update_all(self, active_platforms: List[pygame.Rect], dt: float = 1.0):
        """Update all entities."""
        # Update player
        if self.player and self.player.is_alive:
            self.player.update(active_platforms)
        
        # Update enemies
        if self.player:
            current_dim = 'gema' if self.player.in_gema_dimension else 'normal'
            for enemy in self.enemies:
                if getattr(enemy, 'dim', 'both') in (current_dim, 'both'):
                    enemy.update(active_platforms, self.player)
        else:
            for enemy in self.enemies:
                enemy.update(active_platforms, None)
        
        # Update NPCs (filter by dimension)
        if self.player:
            current_dim = 'gema' if self.player.in_gema_dimension else 'normal'
            for npc in self.npcs:
                if getattr(npc, 'dim', 'both') in (current_dim, 'both'):
                    npc.update(self.player.rect)
    
    def draw_all(self, surface: pygame.Surface, offset_x: float, offset_y: float):
        """Draw all entities."""
        # Draw campfires first (background)
        for campfire in self.campfires:
            campfire.draw(surface, offset_x, offset_y, [])  # Frames passed separately
        
        current_dim = 'normal'
        if self.player:
            current_dim = 'gema' if self.player.in_gema_dimension else 'normal'

        # Draw enemies
        for enemy in self.enemies:
            if getattr(enemy, 'dim', 'both') in (current_dim, 'both'):
                enemy.draw(surface, offset_x, offset_y)
        
        # Draw boss spells (if any)
        for enemy in self.enemies:
            if getattr(enemy, 'dim', 'both') in (current_dim, 'both'):
                if isinstance(enemy, Boss):
                    enemy.draw_spells(surface, offset_x, offset_y)
        
        # Draw NPCs (filter by dimension)
        if self.player:
            for npc in self.npcs:
                if getattr(npc, 'dim', 'both') in (current_dim, 'both'):
                    npc.draw(surface, offset_x, offset_y)
        
        # Draw player last (on top)
        if self.player:
            self.player.draw(surface, offset_x, offset_y)
    
    def cleanup_dead_enemies(self):
        """Remove enemies that are done dying."""
        now_ms = pygame.time.get_ticks()
        self.enemies = [
            e for e in self.enemies 
            if not (getattr(e, 'is_dying', False) and 
                   now_ms >= getattr(e, 'remove_at_ms', 0))
        ]
    
    def get_active_enemies(self) -> List:
        """Get list of alive enemies."""
        return [e for e in self.enemies if e.is_alive and not getattr(e, 'is_dying', False)]
    
    def clear_all(self):
        """Clear all entities."""
        self.enemies.clear()
        self.npcs.clear()
        self.campfires.clear()
        self.enemy_spawns.clear()
