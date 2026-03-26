import pygame

def draw_text(game, text, size, color, x, y, center_aligned=True, shadow_color=None, shadow_offset=3):
    font = pygame.font.Font(None, size)

    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()

    if shadow_color:
        shadow_surface = font.render(text, True, shadow_color)
        shadow_rect = shadow_surface.get_rect()
        if center_aligned:
            shadow_rect.center = (x + shadow_offset, y + shadow_offset)
        else:
            shadow_rect.topleft = (x + shadow_offset, y + shadow_offset)
        game.screen.blit(shadow_surface, shadow_rect)

    if center_aligned:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    game.screen.blit(text_surface, text_rect)


def draw_pause_menu(game):
    overlay = pygame.Surface((game.screen.get_width(), game.screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    game.screen.blit(overlay, (0, 0))

    draw_text(game, "Paused", 80, (255, 255, 255), game.screen.get_width() / 2, game.screen.get_height() / 4, shadow_color=(20, 20, 20))

    game.resume_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 - 75, 200, 50)
    game.restart_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2, 200, 50)
    game.settings_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 + 75, 200, 50)
    game.main_menu_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 + 150, 200, 50)

    buttons = [
        (game.resume_button, "Lanjutkan"),
        (game.restart_button, "Ulangi"),
        (game.settings_button, "Pengaturan"),
        (game.main_menu_button, "Menu Utama"),
    ]
    mouse_pos = pygame.mouse.get_pos()
    for rect, text in buttons:
        color = (150, 150, 150) if rect.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, color, rect, border_radius=10)
        draw_text(game, text, 32, (255, 255, 255), rect.centerx, rect.centery)


def draw_settings_menu(game):
    overlay = pygame.Surface((game.screen.get_width(), game.screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    game.screen.blit(overlay, (0, 0))

    draw_text(game, "Pengaturan", 60, (255, 255, 255), game.screen.get_width() / 2, game.screen.get_height() / 4, shadow_color=(20, 20, 20))

    game.music_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2, 200, 50)
    game.back_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 + 75, 200, 50)

    music_text = "Musik: Off" if game.is_music_paused else "Musik: On"
    mouse_pos = pygame.mouse.get_pos()
    music_color = (150, 150, 150) if game.music_button.collidepoint(mouse_pos) else (100, 100, 100)
    pygame.draw.rect(game.screen, music_color, game.music_button, border_radius=10)
    draw_text(game, music_text, 32, (255, 255, 255), game.music_button.centerx, game.music_button.centery)

    back_color = (150, 150, 150) if game.back_button.collidepoint(mouse_pos) else (100, 100, 100)
    pygame.draw.rect(game.screen, back_color, game.back_button, border_radius=10)
    draw_text(game, "Kembali", 32, (255, 255, 255), game.back_button.centerx, game.back_button.centery)


def draw_win_screen(game):
    overlay = pygame.Surface((game.screen.get_width(), game.screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    game.screen.blit(overlay, (0, 0))

    draw_text(game, "Selamat! Semua Level Selesai!", 60, (255, 255, 255), game.screen.get_width() / 2, game.screen.get_height() / 4)

    game.restart_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2, 200, 50)
    game.main_menu_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 + 75, 200, 50)

    buttons = [
        (game.restart_button, "Mulai Baru"),
        (game.main_menu_button, "Menu Utama"),
    ]

    mouse_pos = pygame.mouse.get_pos()
    for rect, text in buttons:
        color = (150, 150, 150) if rect.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, color, rect, border_radius=10)
        draw_text(game, text, 32, (255, 255, 255), rect.centerx, rect.centery)


def draw_game_over_screen(game):
    overlay = pygame.Surface((game.screen.get_width(), game.screen.get_height()), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    game.screen.blit(overlay, (0, 0))

    draw_text(game, "Game Over", 60, (255, 255, 255), game.screen.get_width() / 2, game.screen.get_height() / 4)

    game.restart_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2, 200, 50)
    game.main_menu_button = pygame.Rect(game.screen.get_width() / 2 - 100, game.screen.get_height() / 2 + 75, 200, 50)

    buttons = [
        (game.restart_button, "Restart"),
        (game.main_menu_button, "Menu Utama"),
    ]

    mouse_pos = pygame.mouse.get_pos()
    for rect, text in buttons:
        color = (150, 150, 150) if rect.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(game.screen, color, rect, border_radius=10)
        draw_text(game, text, 32, (255, 255, 255), rect.centerx, rect.centery)


def draw_main_menu_new(game, asset_loader, mouse_pos, prev_mouse_pressed):
    """
    Draw Main Menu menggunakan aset gambar dengan desain baru.
    Mengembalikan aksi jika tombol ditekan.
    """
    screen = game.screen
    sw, sh = screen.get_width(), screen.get_height()

    # Background
    screen.fill((0, 0, 0))
    bg = asset_loader.menu_assets['background']
    bg_scaled = pygame.transform.scale(bg, (sw, sh))
    screen.blit(bg_scaled, (0, 0))

    # Button config
    BASE_SCALE = 0.65
    HOVER_SCALE = 0.70
    CLICK_SCALE = 0.60

    def scale(img, factor):
        w, h = img.get_size()
        return pygame.transform.scale(img, (int(w * factor), int(h * factor)))

    mouse_pressed = pygame.mouse.get_pressed()[0]
    
    # Detect click only on button press (not hold)
    mouse_clicked = mouse_pressed and not prev_mouse_pressed
    
    # Store for next frame
    game.prev_mouse_pressed = mouse_pressed

    def draw_button(img, center):
        base_img = scale(img, BASE_SCALE)
        rect = base_img.get_rect(center=center)
        hovered = rect.collidepoint(mouse_pos)

        if hovered and mouse_pressed:
            img_draw = scale(img, CLICK_SCALE)
        elif hovered:
            img_draw = scale(img, HOVER_SCALE)
        else:
            img_draw = base_img

        rect = img_draw.get_rect(center=center)
        screen.blit(img_draw, rect)

        # Click only valid on fresh press (not hold)
        clicked = hovered and mouse_clicked
        return rect, clicked

    # Layout
    cx = sw // 2
    start_y = sh // 2 - 20
    base_btn = scale(asset_loader.menu_assets['btn_lanjutkan'], BASE_SCALE)
    spacing = base_btn.get_height() + 18

    # Draw buttons
    _, click_lanjutkan = draw_button(asset_loader.menu_assets['btn_lanjutkan'], (cx, start_y))
    _, click_mulai = draw_button(asset_loader.menu_assets['btn_mulai_baru'], (cx, start_y + spacing))
    _, click_keluar = draw_button(asset_loader.menu_assets['btn_keluar'], (cx, start_y + spacing * 2))

    # Return action
    if click_lanjutkan:
        return "CONTINUE"
    if click_mulai:
        return "NEW_GAME"
    if click_keluar:
        return "EXIT"

    return None
