# Dual Dimension

> Platform 2D dengan mekanik perpindahan dimensi untuk bertahan hidup dari jebakan mematikan.

![1766021761804](image/README/1766021761804.png)

---

## Deskripsi

**Dual Dimension** adalah game platformer 2D di mana pemain dapat beralih antara dua dimensi berbeda untuk menghindari jebakan dan musuh. Platform yang aman di satu dimensi bisa menjadi berbahaya di dimensi lainnya. Gunakan ingatan dan strategi untuk mencapai pintu keluar di setiap level!

---

## Gameplay

### Tujuan Utama

- Bertahan hidup dan mencapai pintu keluar di setiap level
- Gunakan ingatan untuk mengatasi rintangan
- Jangan sampai kehabisan nyawa atau progres akan direset

### Narasi

Karakter utama terperangkap dalam realitas yang tidak stabil antara dunia nyata dan "dimensi gema" yang berbahaya. Untuk melarikan diri, ia harus menguasai kemampuan berpindah dimensi. Platform kokoh bisa berubah menjadi jebakan mematikan hanya dengan satu shift. Satu-satunya jalan keluar adalah menemukan pintu di setiap level.

---

## Alur Game

```
Menu Utama → Level 1 → Level 2 → ... → Level Akhir → End Screen
     ↓          ↓                            ↓
  Keluar    Checkpoint               Restart/Menu
```

### 1. Menu Utama

Layar awal dengan pilihan:

- **Lanjutkan** - Melanjutkan dari save terakhir
- **Mulai Baru** - Memulai game dari awal
- **Keluar** - Menutup game

### 2. Gameplay

- Mulai dari Level 1 atau lanjutkan dari progress terakhir
- Api unggun sebagai **checkpoint**
  - Kehilangan 1 nyawa → kembali ke checkpoint terakhir
  - Kehilangan semua nyawa → **Game Over**, restart dari Level 1

### 3. End Game

Setelah level terakhir selesai:

- **Restart** - Ulangi dari level 1
- **Menu Utama** - Kembali ke menu

### 4. Menu Pause

Tekan **ESC** untuk pause, dengan opsi:

- **Lanjutkan** - Resume game
- **Ulangi** - Kembali ke checkpoint terakhir
- **Pengaturan** - Toggle musik on/off
- **Menu Utama** - Kembali ke menu (progress tersimpan)

---

## Kontrol & Mekanik

### Gerakan Dasar

| Tombol                  | Aksi                 |
| ----------------------- | -------------------- |
| **A / ←**        | Gerak ke kiri        |
| **D / →**        | Gerak ke kanan       |
| **Space / ↑**    | Lompat               |
| **Klik Touchpad** | Serangan             |
| **Shift**         | Berpindah dimensi    |
| **E**             | Interaksi dengan NPC |
| **ESC**           | Pause game           |
| **F3**            | Toggle debug mode    |

### Sistem Dimensi

**Mekanik inti game** - Beralih antara dua dimensi kapan saja:

- **Dimensi Normal** - Dunia cerah dengan platform tertentu
- **Dimensi Gema** - Dunia gelap dengan layout berbeda

> **Tip**: Platform dan musuh berbeda di setiap dimensi. Gunakan shift untuk mengakses jalan baru atau menghindari bahaya!

### Sistem Nyawa

- Mulai dengan **5 nyawa** per level
- Terkena jebakan/musuh = **-1 nyawa** + kembali ke checkpoint
- **0 nyawa** = Game Over → restart dari Level 1

### Sistem Combat

- Serang musuh dengan **Klik Touchpad**
- Boss memiliki HP dan attack pattern khusus
- Musuh patrol dan chaser dengan AI berbeda

### NPC & Dialog

- **NPC Oldman/Woman** - Tutorial umum dan tips
- **NPC Bearded** - Tutorial shift dimensi
- **NPC Hat-man** - Peringatan bahaya
- Tekan **E** untuk berinteraksi

---

## Struktur Kode

```
ProjectGame-GIGA/
├── src/
│   ├── main.py                 # Entry point game
│   ├── core/                   # Core systems
│   │   ├── interfaces.py       # Abstract interfaces
│   │   ├── entity_base.py      # Base entity class
│   │   ├── game_state.py       # State management
│   │   ├── game_setup.py       # Game initialization
│   │   ├── asset_loader.py     # Asset loading
│   │   ├── camera_controller.py
│   │   ├── entity_manager.py
│   │   ├── level_controller.py
│   │   └── gameplay_handler.py
│   ├── entity/                 # Game entities
│   │   ├── player.py
│   │   ├── enemy.py
│   │   ├── boss.py
│   │   └── npc.py
│   ├── environment/            # Environment objects
│   │   ├── trap.py
│   │   └── campfire.py
│   ├── graphics/               # Rendering & UI
│   │   ├── renderer.py
│   │   ├── parallax.py
│   │   ├── UI.py
│   │   └── ui_buttons.py
│   ├── managers/               # High-level managers
│   │   ├── save_manager.py
│   │   └── state_manager.py
│   ├── systems/                # Game systems
│   │   ├── camera_system.py
│   │   ├── collision_system.py
│   │   ├── input_system.py
│   │   └── render_system.py
│   ├── utils/                  # Utilities
│   │   ├── settings.py
│   │   ├── exception.py
│   │   └── assets.py
│   └── levels/                 # Level files
│       ├── level_1_normal.txt
│       ├── level_1_gema.txt
│       ├── SOP Level.md
│       └── ...
├── Assets/                     # Game assets
│   ├── Background/
│   ├── Player/
│   ├── Enemies/
│   ├── Boss/
│   ├── npc/
│   ├── menu/
│   ├── Tiles/
│   └── Sound/
├── saves/                      # Save files
│   └── player_save.json
└── README.md
```

---

## Penerapan Konsep OOP

Project ini menerapkan konsep-konsep Object-Oriented Programming (OOP) secara menyeluruh:

### 1. Class & Object

Setiap entitas game direpresentasikan sebagai class dengan instance object-nya:

```python
# Class definition
class Player(Entity):
    def __init__(self, x, y, image):
        super().__init__(x, y, image)
        self.velocity = pygame.math.Vector2(0, 0)
        self.hearts = 5

# Object instantiation
player = Player(100, 100, player_image)
enemy = Enemy(500, 300, enemy_image)
```

**Implementasi**: `Player`, `Enemy`, `Boss`, `NPC`, `TriggerTrap`, `Campfire`

### 2. Encapsulation

Data dan method dikapsulasi dalam class dengan access modifier:

```python
class SaveManager:
    def __init__(self):
        self._save_file = "saves/player_save.json"  # Private attribute
      
    def save_progress(self, level, hearts):
        # Public method
        self._write_to_file(data)  # Private method
  
    def _write_to_file(self, data):
        # Private helper method
        with open(self._save_file, 'w') as f:
            json.dump(data, f)
```

**Implementasi**: Semua manager classes (`SaveManager`, `EntityManager`, `LevelController`)

### 3. Inheritance

Hierarchy class untuk code reuse dan extensibility:

```python
# Base class
class Entity:
    def __init__(self, x, y, image):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_alive = True
  
    def update(self, platforms):
        pass  # To be overridden

# Derived classes
class Player(Entity):
    def update(self, platforms):
        # Player-specific update logic
        super().update(platforms)

class Enemy(Entity):
    def update(self, platforms, player):
        # Enemy-specific update logic
        super().update(platforms)
```

**Hierarchy**:

- `Entity` → `Player`, `Enemy`, `Boss`, `NPC`
- `Enemy` → `PatrollingEnemy`, `ChaserEnemy`

### 4. Polymorphism

Method overriding untuk behavior berbeda pada class turunan:

```python
class Entity:
    def draw(self, screen, offset_x, offset_y):
        screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))

class Player(Entity):
    def draw(self, screen, offset_x, offset_y):
        # Override dengan animasi spesifik player
        current_frame = self.get_current_animation_frame()
        screen.blit(current_frame, (self.rect.x - offset_x, self.rect.y - offset_y))

class Boss(Entity):
    def draw(self, screen, offset_x, offset_y):
        # Override dengan health bar dan spell effects
        super().draw(screen, offset_x, offset_y)
        self.draw_health_bar(screen, offset_x, offset_y)
        self.draw_spells(screen, offset_x, offset_y)
```

**Implementasi**: Semua entity memiliki `update()`, `draw()`, `handle_event()` yang di-override

### 5. Composition

Object terdiri dari object lain (Has-A relationship):

```python
class Game:
    def __init__(self):
        # Game composed of multiple managers
        self.entity_manager = EntityManager()
        self.level_controller = LevelController()
        self.camera = CameraController()
        self.asset_loader = AssetLoader()
        self.save_manager = SaveManager()

class EntityManager:
    def __init__(self):
        # EntityManager composed of entity lists
        self.player = None
        self.enemies = []
        self.npcs = []
        self.campfires = []
```

**Implementasi**: `Game` class mengkomposisi berbagai manager dan system

### 6. Abstract Class

Blueprint untuk class turunan menggunakan ABC:

```python
from abc import ABC, abstractmethod

class IDrawable(ABC):
    @abstractmethod
    def draw(self, screen, offset_x, offset_y):
        """All drawable objects must implement this"""
        pass

class IUpdatable(ABC):
    @abstractmethod
    def update(self, *args):
        """All updatable objects must implement this"""
        pass

# Implementation
class Player(Entity, IDrawable, IUpdatable):
    def draw(self, screen, offset_x, offset_y):
        # Concrete implementation
        pass
  
    def update(self, platforms):
        # Concrete implementation
        pass
```

**Implementasi**: `interfaces.py` - `IDrawable`, `IUpdatable`, `ICollidable`

### 7. Exception Handling

Custom exception untuk error handling yang lebih baik:

```python
# Custom exceptions
class AssetLoadError(Exception):
    def __init__(self, asset_name, original_error):
        self.message = f"Failed to load asset: {asset_name}"
        super().__init__(self.message)

class LevelFileNotFound(Exception):
    def __init__(self, filepath):
        self.message = f"Level file not found: {filepath}"
        super().__init__(self.message)

# Usage
try:
    image = pygame.image.load(path)
except pygame.error as e:
    raise AssetLoadError(path, e)

try:
    with open(level_file, 'r') as f:
        data = f.read()
except FileNotFoundError:
    raise LevelFileNotFound(level_file)
```

**Implementasi**: `exception.py` - `AssetLoadError`, `LevelFileNotFound`, `AudioLoadError`

---

## Design Patterns

### Separation of Concerns

- **Core** - Logic inti game
- **Managers** - High-level orchestration
- **Systems** - Specific game systems (camera, collision, render)
- **Entity** - Game objects dengan behavior
- **Graphics** - Rendering dan UI

### Key Patterns

- **Singleton** - ResourceManager, SaveManager
- **Composition** - Entity dengan components
- **State Pattern** - GameStateEnum
- **Observer** - Event handling
- **Factory** - Entity creation

---

## Sistem Progress

### Penyimpanan Otomatis

Game secara otomatis menyimpan:

- Level terakhir yang dicapai
- Jumlah nyawa saat ini
- Progress tersimpan di `saves/player_save.json`

### Progression

- **Linear** - Level 1 → 2 → 3 → 4
- Unlock level berikutnya dengan menyelesaikan level sebelumnya
- Kompleksitas jebakan meningkat setiap level

---

## Asset Credits

Terima kasih kepada para artist yang asset-nya digunakan:

### Graphics

- [Trap Platformer](https://bdragon1727.itch.io/free-trap-platformer) by bdragon1727
- [Pixel Campfire](https://srobinson111.itch.io/pixel-campfire) by srobinson111
- [Forest Background](https://edermunizz.itch.io/free-pixel-art-forest) by edermunizz
- [Fantasy Knight](https://aamatniekss.itch.io/fantasy-knight-free-pixelart-animated-character) by aamatniekss
- [Eclipse Assets](https://bruno-farias.itch.io/eclipse) by bruno-farias
- [Sunny Land](https://ansimuz.itch.io/sunny-land-pixel-game-art) by Ansimuz
- [Bringer of Death](https://clembod.itch.io/bringer-of-death-free) by Clembod
- [Bandits](https://sventhole.itch.io/bandits) by Sventhole
- [Gothicvania Town](https://assetstore.unity.com/packages/2d/characters/gothicvania-town-101407)

---

## Cara Bermain

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Jalankan game: `python src/main.py`
4. Gunakan **Shift** untuk berpindah dimensi
5. Hindari jebakan dan capai pintu keluar!

---

## Tim Pengembang

**Dual Dimension** - Project OOP Semester 3

- Muhammad Farhan & Raditya Akmal

---

**Selamat bermain!**
