import pygame
import sys
import os
from utils import resource_path
from main import run_game

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Principal - Tropico Island")
clock = pygame.time.Clock()

# ─── Paleta ───────────────────────────────────────────────────────────────────
GOLD      = (255, 210,  50)
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
MENU_HOV  = (255, 215,   0)
RED_ERR   = (220,  60,  50)

OVERLAY_W = 490

# ─── Fontes ───────────────────────────────────────────────────────────────────
font_logo   = pygame.font.SysFont("Impact",  64, bold=True)
font_star   = pygame.font.SysFont("Arial",   22, bold=True)
font_header = pygame.font.SysFont("Georgia", 18, bold=True)
font_small  = pygame.font.SysFont("Arial",   12)
font_body_b = pygame.font.SysFont("Arial",   14, bold=True)
font_err    = pygame.font.SysFont("Arial",   13)
PIXEL_SIZE  = 38
font_menu   = pygame.font.Font(None, PIXEL_SIZE)

# ─── Background ───────────────────────────────────────────────────────────────
BG_PATH = resource_path("assets/fundo-menu.png")
try:
    bg_raw = pygame.image.load(BG_PATH)
    bg_img = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))
except Exception as e:
    print(f"[AVISO] fundo-menu nao carregado: {e}")
    bg_img = None

# ─── Estado ──────────────────────────────────────────────────────────────────
hovered_item = -1
time_val     = 0.0
error_msg    = ""
error_timer  = 0

MENU_ITEMS   = ["Continuar", "Novo Jogo", "Tutorial", "Sair do Jogo"]

PANEL_TOP    = 195
ITEM_START_Y = 245
ITEM_STEP    = 58
LOGO_Y       = (PANEL_TOP - 80) // 2 + 50

# ─── Helpers ─────────────────────────────────────────────────────────────────
def draw_gradient_rect(surf, rect, top_col, bot_col):
    x, y, w, h = rect
    for i in range(h):
        t = i / max(h - 1, 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * t)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * t)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * t)
        pygame.draw.line(surf, (r, g, b), (x, y + i), (x + w, y + i))

def draw_background(surf):
    if bg_img:
        surf.blit(bg_img, (0, 0))
    else:
        draw_gradient_rect(surf, (0, 0, WIDTH, HEIGHT), (80, 140, 180), (30, 80, 120))
    ov = pygame.Surface((OVERLAY_W, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 10, 35, 102))
    surf.blit(ov, (0, 0))

def draw_logo(surf):
    logo_surf   = font_logo.render("TROPICO", True, WHITE)
    shadow_surf = font_logo.render("TROPICO", True, BLACK)
    logo_x = (OVERLAY_W - logo_surf.get_width()) // 2
    surf.blit(shadow_surf, (logo_x + 2, LOGO_Y + 2))
    surf.blit(logo_surf,   (logo_x,     LOGO_Y))
    line_y = LOGO_Y + logo_surf.get_height() + 8
    margin = 30
    pygame.draw.line(surf, GOLD, (margin, line_y), (OVERLAY_W - margin, line_y), 2)

def draw_menu(surf, hovered):
    hdr_w, hdr_h = 330, 36
    hdr_x    = (OVERLAY_W - hdr_w) // 2
    hdr_rect = pygame.Rect(hdr_x, PANEL_TOP, hdr_w, hdr_h)
    s = pygame.Surface((hdr_w, hdr_h), pygame.SRCALPHA)
    s.fill((0, 25, 70, 200))
    surf.blit(s, hdr_rect.topleft)
    pygame.draw.rect(surf, GOLD, hdr_rect, 2, border_radius=4)
    
    hdr = font_header.render("Menu Principal", True, WHITE)
    surf.blit(hdr, (hdr_rect.centerx - hdr.get_width() // 2, PANEL_TOP + 9))

    for i, name in enumerate(MENU_ITEMS):
        y = ITEM_START_Y + i * ITEM_STEP
        is_hov = (i == hovered)
        if is_hov:
            bg = pygame.Surface((hdr_w, 48), pygame.SRCALPHA)
            bg.fill((255, 200, 0, 60))
            surf.blit(bg, (hdr_x, y - 5))
            pygame.draw.line(surf, GOLD, (hdr_x, y + 40), (hdr_x + hdr_w, y + 40), 1)
        
        col    = MENU_HOV if is_hov else WHITE
        shadow = font_menu.render(name, True, BLACK)
        text   = font_menu.render(name, True, col)
        cx     = OVERLAY_W // 2
        sx     = cx - text.get_width() // 2
        surf.blit(shadow, (sx + 2, y + 2))
        surf.blit(text,   (sx,     y))

def draw_error(surf, msg):
    if not msg:
        return
    lbl = font_err.render(msg, True, WHITE)
    bg = pygame.Surface((lbl.get_width() + 20, 26), pygame.SRCALPHA)
    bg.fill((180, 30, 30, 210))
    x = OVERLAY_W // 2 - bg.get_width() // 2
    y = HEIGHT - 60
    surf.blit(bg, (x, y))
    surf.blit(lbl, (x + 10, y + 5))

def launch_tutorial():
    global screen, error_msg, error_timer
    print("Launching tutorial...")
    try:
        from tutorial.tutorial_view import run_tutorial
        run_tutorial(screen, WIDTH, HEIGHT)
        # Ao voltar, precisamos resetar o titulo e modo de video da janela
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Menu Principal - Tropico Island")
    except Exception as e:
        print(f"Error launching tutorial: {e}")
        error_msg = f"Erro no tutorial: {e}"
        error_timer = 180

def launch_game():
    print("Launching game...")
    try:
        run_game()
        print("Returned from game.")
        # Ao voltar do jogo, precisamos resetar o modo de vídeo do menu
        global screen
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Menu Principal - Tropico Island")
    except Exception as e:
        print(f"Error launching game: {e}")
        global error_msg, error_timer
        error_msg = f"Erro ao iniciar: {e}"
        error_timer = 180

# ─── Loop ─────────────────────────────────────────────────────────────────────
running = True
while running:
    dt = clock.tick(60) / 1000.0
    time_val += dt
    if error_timer > 0:
        error_timer -= 1
    else:
        error_msg = ""

    mx, my = pygame.mouse.get_pos()
    hdr_x = (OVERLAY_W - 330) // 2

    hovered_item = -1
    for i in range(len(MENU_ITEMS)):
        y = ITEM_START_Y + i * ITEM_STEP
        if hdr_x <= mx <= hdr_x + 330 and y - 5 <= my <= y + 46:
            hovered_item = i
            break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print(f"Click at {event.pos}, hovered_item: {hovered_item}")
            if hovered_item in (0, 1): # Continuar ou Novo Jogo
                launch_game()
            elif hovered_item == 2:    # Tutorial
                launch_tutorial()
            elif hovered_item == 3:    # Sair
                running = False

    draw_background(screen)
    draw_logo(screen)
    draw_menu(screen, hovered_item)
    draw_error(screen, error_msg)

    pygame.display.flip()

pygame.quit()
sys.exit()