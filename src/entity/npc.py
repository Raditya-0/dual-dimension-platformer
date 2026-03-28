# src/entity/npc.py
import pygame
from pathlib import Path
from .entity import Entity   

TALK_KEY = pygame.K_e

# --- Dialog Presets ---
NPC_DIALOGS = {
    'oldman_normal': (
        "Halo, traveler!",
        "Didepanmu ada banyak bahaya.",
        "Gunakan kemampuanmu dengan bijak.",
        "Semoga perjalananmu lancar!"
    ),
    'oldman_gema': (
        "Ini adalah dimensi gema.",
        "Semuanya di sini berbeda dari dunia normal.",
        "Platform dan musuh bisa berbeda.",
        "Untuk mengalahkan musuh,\n   klik touchpad saat dekat.",
        "Berhati-hatilah di sini.",
        "Jangan lupa untuk kembali ke dimensi normal!"
    ),
    'woman_normal': (
        "Halo, traveler!",
        "Selamat datang di dunia Dual Dimension.",
        "Di sini kamu bisa berpindah antara dua dimensi.",
        "Untuk mengalahkan musuh,\n klik touchpad saat dekat.",
        "Gunakan kemampuanmu dengan bijak.",
        "Semoga perjalananmu lancar!"
    ),
    'woman_gema': (
        "Ini adalah dimensi gema.",
        "Semuanya di sini berbeda dari dunia normal.",
        "Platform dan musuh bisa berbeda.",
        "Untuk mengalahkan musuh,\n klik touchpad saat dekat.",
        "Berhati-hatilah di sini.",
        "Jangan lupa untuk kembali ke dimensi normal!"
    ),
    'bearded_normal': (
        "Hati-hati dengan jebakan di depan!",
        "Mereka sangat berbahaya."
    ),
    'bearded_gema': (
        "Oh, kamu sudah di dimensi gema!",
        "Dimensi ini penuh misteri dan bahaya.",
        "Beberapa platform hanya muncul di dimensi ini.",
        "Tekan [SHIFT] untuk kembali ke dimensi normal.",
        "Jangan terlalu lama di sini!"
    ),
    'hat-man_normal': (
        "Hati-hati dengan jebakan di depan!",
        "Mereka sangat berbahaya."
    ),
    'hat-man_gema': (
        "Selamat datang di dimensi gema.",
        "Di sini semuanya berbeda.",
        "Berhati-hatilah dalam melangkah.",
        "Hindari Trap."
    ),
}

def get_npc_dialog(variant, dim):
    """Helper function untuk mendapatkan dialog preset berdasarkan variant dan dimensi"""
    key = f"{variant}_{dim}"
    return NPC_DIALOGS.get(key, NPC_DIALOGS.get(f"{variant}_normal", (
        "Halo! Tekan [E] untuk lanjut.",
        "Selamat datang di Dual Dimension!",
        "Hati-hati jebakan dan semoga sukses!",
    )))

# --- Helper aset (tanpa ketergantungan file lain) ---
def project_root_from_this_file() -> Path:
    # .../src/entity/npc.py -> .../ (root ProjectGame-GIGA)
    return Path(__file__).resolve().parents[2]

def load_images_dir(*parts, key_exts=(".png", ".jpg", ".jpeg", ".bmp", ".gif")):
    base = project_root_from_this_file() / "Assets" / "npc"  
    folder = base.joinpath(*parts)
    if not folder.exists():
        print(f"[WARNING] Folder {folder} tidak ditemukan.")
        return []
    files = sorted([p for p in folder.iterdir() if p.suffix.lower() in key_exts],
                   key=lambda p: p.name.lower())
    frames = []
    for p in files:
        surf = pygame.image.load(str(p)).convert_alpha()
        frames.append(surf)
    return frames


def load_font_rel(path_in_assets: str, size=22):
    fpath = project_root_from_this_file() / "Assets" / path_in_assets
    return pygame.font.Font(str(fpath), size)

# NPC Type Configuration
NPC_TYPES = {
    'A': {'variant': 'oldman', 'dim': 'normal'},
    'a': {'variant': 'oldman', 'dim': 'normal'},
    'Q': {'variant': 'bearded', 'dim': 'normal'},
    'q': {'variant': 'bearded', 'dim': 'normal'},
    'W': {'variant': 'hat-man', 'dim': 'normal'},
    'w': {'variant': 'hat-man', 'dim': 'normal'},
}

# Gema variants
NPC_TYPES_GEMA = {
    'A': {'variant': 'woman', 'dim': 'gema'},
    'a': {'variant': 'woman', 'dim': 'gema'},
    'Q': {'variant': 'bearded', 'dim': 'gema'},
    'q': {'variant': 'bearded', 'dim': 'gema'},
    'W': {'variant': 'hat-man', 'dim': 'gema'},
    'w': {'variant': 'hat-man', 'dim': 'gema'},
}

class NPC(Entity):
    # Jarak dimana NPC akan tetap menatap player setelah dialog
    WATCH_DISTANCE = 200
    # Jarak untuk kembali ke default direction
    RETURN_TO_DEFAULT_DISTANCE = 250
    
    def __init__(self, x, y, variant="oldman", dialog_lines=None, patrol=None,
                 font_path="fonts/freesansbold.ttf", dim='both', auto_snap=True,
                 facing='right'):
        # load frames dulu
        self.variant = variant
        self.idle_frames = load_images_dir(f"{variant}-idle")
        self.walk_frames = load_images_dir(f"{variant}-walk")

        if not self.idle_frames:
            surf = pygame.Surface((48, 64), pygame.SRCALPHA)
            surf.fill((255, 200, 0, 255))
            self.idle_frames = [surf]

        # ambil gambar pertama untuk dikirim ke Entity
        first_image = self.idle_frames[0]
        super().__init__(x, y, first_image)
        self.image = first_image
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.dim = dim
        self.frame_index = 0.0
        self.anim_speed = 0.08
        self.auto_snap = auto_snap
        
        # Direction tracking
        self.default_direction = -1 if facing == 'left' else 1  # Arah awal/default
        self.direction = self.default_direction  # Arah saat ini
        self.has_talked = False  # Flag apakah pernah ngobrol
        self.is_watching_player = False  # Flag apakah sedang menatap player (freeze animasi)
        self.watch_session_ended = False  # Flag apakah sesi menatap sudah selesai (player sudah menjauh)
 
        # Jarak interaksi
        self.INTERACT_MAX_DIST = 120  # Jarak maksimum untuk bisa ngobrol
        self.INTERACT_MIN_DIST = 30   # Jarak minimum (tidak boleh terlalu dekat/overlap)
        
        # interaksi
        self.show_prompt = False
        self.can_interact = False  # True jika dalam jarak yang tepat (tidak terlalu dekat/jauh)
        self.talking = False
        self.is_transitioning_to_talk = False  # untuk smooth transition
        # Simpan dialog sebagai tuple (immutable) untuk memastikan urutan tidak berubah
        if dialog_lines is not None:
            self.dialog_lines = tuple(dialog_lines)
        else:
            # Gunakan preset dialog berdasarkan variant dan dim
            self.dialog_lines = get_npc_dialog(variant, dim if dim in ('normal', 'gema') else 'normal')
        self.dialog_index = 0
        
        # Simpan total dialog untuk safety check
        self.total_dialogs = len(self.dialog_lines)

        # patrol opsional
        self.patrol = patrol  # contoh: ((200, 420), 0.8)
        # penyimpanan patrol saat sedang diajak bicara
        self._saved_patrol = None

        # font UI
        try:
            self.font = load_font_rel(font_path, size=16)
        except Exception:
            self.font = pygame.font.SysFont(None, 16)

    def update(self, player_rect: pygame.Rect):
        # Hitung jarak ke player dulu (dibutuhkan untuk beberapa kondisi)
        dist_x = abs(self.rect.centerx - player_rect.centerx)
        dist_y = abs(self.rect.centery - player_rect.centery)
        total_dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
        
        # Update watching state - HANYA jika sudah pernah ngobrol DAN sesi watch belum selesai
        if self.has_talked and not self.talking and not self.watch_session_ended:
            if total_dist < self.WATCH_DISTANCE:
                self.is_watching_player = True
            else:
                # Player sudah menjauh, sesi watch selesai PERMANEN
                self.is_watching_player = False
                self.watch_session_ended = True  # Tidak akan menatap lagi
        else:
            # Belum pernah ngobrol, sedang ngobrol, atau sesi watch sudah selesai
            if not self.talking:
                self.is_watching_player = False
        
        # Smooth transition: jika sedang transisi, lanjutkan animasi sampai kembali ke frame 0
        if self.is_transitioning_to_talk:
            if len(self.idle_frames) > 1:
                self.frame_index = (self.frame_index + self.anim_speed) % len(self.idle_frames)
                self.image = self.idle_frames[int(self.frame_index)]
                
                # Cek apakah sudah kembali ke frame 0 atau sangat dekat
                if int(self.frame_index) == 0 and self.frame_index < self.anim_speed * 1.5:
                    # Selesai transisi, freeze di frame 0
                    self.is_transitioning_to_talk = False
                    self.frame_index = 0.0
                    self.image = self.idle_frames[0]
            else:
                # Tidak ada animasi, langsung selesai transisi
                self.is_transitioning_to_talk = False
                
        # Jika sedang berbicara atau menatap player, tetap diam di frame pertama
        elif self.talking or self.is_watching_player:
            # pastikan image dihentikan di frame pertama
            if len(self.idle_frames) > 0:
                self.frame_index = 0.0
                self.image = self.idle_frames[0]
            # jangan lanjutkan patrol/anim
        else:
            # animasi normal
            if len(self.idle_frames) > 1:
                self.frame_index = (self.frame_index + self.anim_speed) % len(self.idle_frames)
                self.image = self.idle_frames[int(self.frame_index)]

            # patrol sederhana (hanya jalankan jika tidak sedang berbicara)
            if self.patrol:
                (x1, x2), speed = self.patrol
                self.rect.x += speed
                if self.rect.x < min(x1, x2) or self.rect.x > max(x1, x2):
                    self.patrol = ((x1, x2), -speed)

        # deteksi jarak untuk prompt
        # Player harus dalam jarak yang tepat: tidak terlalu jauh DAN tidak terlalu dekat
        in_max_range = (dist_x < self.INTERACT_MAX_DIST and dist_y < self.INTERACT_MAX_DIST)
        too_close = (dist_x < self.INTERACT_MIN_DIST and dist_y < self.INTERACT_MAX_DIST)  # Terlalu dekat secara horizontal
        
        self.can_interact = in_max_range and not too_close
        self.show_prompt = self.can_interact
        
        # Update direction: ikuti arah player HANYA jika sedang watching
        if self.is_watching_player:
            # Sedang menatap player
            if player_rect.centerx < self.rect.centerx:
                self.direction = -1  # Hadap kiri
            else:
                self.direction = 1   # Hadap kanan
        elif self.has_talked and self.watch_session_ended:
            # Sesi watch sudah selesai, tetap di arah default
            self.direction = self.default_direction

    def handle_event(self, event: pygame.event.Event, player_rect: pygame.Rect = None, player=None):
        # player_rect: optional, used to make NPC face the player when conversation starts
        # player: optional, player object to make player face the NPC
        if event.type == pygame.KEYDOWN and event.key == TALK_KEY and self.can_interact:
            if not self.talking:
                # Mulai percakapan dari awal (index 0)
                self.talking = True
                self.is_transitioning_to_talk = True  # aktifkan smooth transition
                self.dialog_index = 0
                # Reset watch session untuk sesi baru setelah ngobrol
                self.watch_session_ended = False
                # simpan state patrol dan hentikan NPC supaya tetap diam saat bicara
                self._saved_patrol = self.patrol
                self.patrol = None
                # JANGAN langsung set ke frame 0, biar transisi selesaikan animasi dulu
                # Make NPC face the player
                if player_rect is not None:
                    if player_rect.centerx < self.rect.centerx:
                        self.direction = -1
                    else:
                        self.direction = 1
                # Make player face the NPC
                if player is not None:
                    if self.rect.centerx < player_rect.centerx:
                        player.direction = -1  # NPC di kiri, player hadap kiri
                    else:
                        player.direction = 1   # NPC di kanan, player hadap kanan
            else:
                # Lanjut ke dialog berikutnya
                self.dialog_index += 1
                # Pastikan index tidak melebihi jumlah dialog
                if self.dialog_index >= len(self.dialog_lines):
                    # Selesai, tutup dialog dan reset ke 0
                    self.talking = False
                    self.has_talked = True  # Flag bahwa pernah ngobrol
                    self.dialog_index = 0
                    # restore patrol state jika ada
                    if getattr(self, '_saved_patrol', None) is not None:
                        self.patrol = self._saved_patrol
                        self._saved_patrol = None

    def draw(self, screen, camera_offset_x=0, camera_offset_y=0):
        # gambar sprite npc (gunakan Entity.draw agar respect pada self.direction)
        try:
            super().draw(screen, camera_offset_x, camera_offset_y)
        except Exception:
            # fallback: langsung gambar tanpa flip jika ada masalah
            screen.blit(self.image, (self.rect.x - camera_offset_x, self.rect.y - camera_offset_y))
        # UI (prompt/dialog)
        if self.talking:
            self._draw_dialog_box(screen, camera_offset_x, camera_offset_y)
        elif self.show_prompt:
            self._draw_prompt(screen, camera_offset_x, camera_offset_y)

    def _draw_prompt(self, screen, camera_offset_x, camera_offset_y):
        text = self.font.render("Tekan [E] untuk bicara", True, (255, 255, 255))
        w, h = text.get_size()
        pad = 6
        x = self.rect.centerx - w // 2 - camera_offset_x
        y = self.rect.y - 25 - camera_offset_y  # Diturunkan dari -36 ke -25
        pygame.draw.rect(screen, (0, 0, 0), (x - pad, y - pad, w + 2*pad, h + 2*pad), border_radius=8)
        screen.blit(text, (x, y))

    def _draw_dialog_box(self, screen, camera_offset_x, camera_offset_y):
        # Safety check: pastikan index valid
        if self.dialog_index < 0 or self.dialog_index >= len(self.dialog_lines):
            self.dialog_index = 0
            
        # Ambil dialog sesuai index saat ini
        dlg = self.dialog_lines[self.dialog_index]
        
        # Split by newline untuk multi-line support
        lines = dlg.split('\n')
        text_surfaces = [self.font.render(line, True, (255, 255, 255)) for line in lines]
        
        # Hitung ukuran box berdasarkan line terpanjang dan jumlah baris
        max_w = max(surf.get_width() for surf in text_surfaces)
        line_height = text_surfaces[0].get_height()
        total_h = line_height * len(lines) + (len(lines) - 1) * 5  # 5px spacing antar baris
        
        pad = 10
        x = self.rect.centerx - max_w // 2 - camera_offset_x
        y = self.rect.y - 25 - total_h - camera_offset_y  # Diturunkan dan konsisten dengan prompt
        
        # Draw background box
        pygame.draw.rect(screen, (20, 20, 20), (x - pad, y - pad, max_w + 2*pad, total_h + 2*pad), border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), (x - pad, y - pad, max_w + 2*pad, total_h + 2*pad), 2, border_radius=10)
        
        # Draw each line
        current_y = y
        for surf in text_surfaces:
            screen.blit(surf, (x, current_y))
            current_y += line_height + 5
    
    @staticmethod
    def spawn_from_maps(normal_spawns: dict, gema_spawns: dict) -> list:
        """
        Spawn NPCs from map data.
        
        Args:
            normal_spawns: Dict dengan keys 'A', 'Q', 'W' berisi list spawn info
            gema_spawns: Dict dengan keys 'A', 'Q', 'W' berisi list spawn info
            
        Returns:
            List of NPC instances
        """
        npcs = []
        
        # Process normal map spawns
        for npc_char, spawn_list in normal_spawns.items():
            config = NPC_TYPES.get(npc_char)
            if not config:
                continue
                
            for spawn_info in spawn_list:
                spawn_rect = spawn_info['rect']
                facing = spawn_info.get('facing', 'right')
                
                npc = NPC(
                    spawn_rect.x,
                    spawn_rect.y,
                    variant=config['variant'],
                    dim=config['dim'],
                    facing=facing
                )
                npcs.append(npc)
        
        # Process gema map spawns
        for npc_char, spawn_list in gema_spawns.items():
            config = NPC_TYPES_GEMA.get(npc_char)
            if not config:
                continue
                
            for spawn_info in spawn_list:
                spawn_rect = spawn_info['rect']
                facing = spawn_info.get('facing', 'right')
                
                npc = NPC(
                    spawn_rect.x,
                    spawn_rect.y,
                    variant=config['variant'],
                    dim=config['dim'],
                    facing=facing
                )
                npcs.append(npc)
        
        return npcs
