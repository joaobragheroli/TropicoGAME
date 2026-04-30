import pygame
import sys
import os

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Principal")
clock = pygame.time.Clock()

# ─── Função para assets (ESSENCIAL pro .exe) ────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ─── Paleta ────────────────────────────────────────────────────────────────
GOLD      = (255, 210,  50)
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
MENU_HOV  = (255, 215,   0)
RED_ERR   = (220,  60,  50)

OVERLAY_W = 490

# ─── Fontes ────────────────────────────────────────────────────────────────
font_logo   = pygame.font.SysFont("Impact",  64, bold=True)
font_star   = pygame.font.SysFont("Arial",   22, bold=True)
font_header = pygame.font.SysFont("Georgia", 18, bold=True)
font_small  = pygame.font.SysFont("Arial",   12)
font_body_b = pygame.font.SysFont("Arial",   14, bold=True)
font_err    = pygame.font.SysFont("Arial",   13)
PIXEL_SIZE  = 38
font_menu   = pygame.font.Font(None, PIXEL_SIZE)

# ─── Background ────────────────────────────────────────────────────────────
BG_PATH = resource_path("menu/fundo-menu.png")

try:
    bg_raw = pygame.image.load(BG_PATH)
    bg_img = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))
except Exception as e:
    print(f"[AVISO] fundo-menu nao carregado: {e}")
    bg_img = None

# ─── Estado ────────────────────────────────────────────────────────────────
hovered_item = -1
time_val     = 0.0
error_msg    = ""
error_timer  = 0

MENU_ITEMS   = ["Continuar", "Novo Jogo", "Sair do Jogo"]

PANEL_TOP    = 195
ITEM_START_Y = 245
ITEM_STEP    = 58
LOGO_Y       = (PANEL_TOP - 80) // 2 + 50

# ─── Helpers ───────────────────────────────────────────────────────────────
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

def draw_menu(surf, hovered):
    for i, name in enumerate(MENU_ITEMS):
        y = ITEM_START_Y + i * ITEM_STEP
        col = MENU_HOV if i == hovered else WHITE
        text = font_menu.render(name, True, col)
        x = OVERLAY_W // 2 - text.get_width() // 2
        surf.blit(text, (x, y))

def draw_error(surf, msg):
    if not msg:
        return
    lbl = font_err.render(msg, True, RED_ERR)
    surf.blit(lbl, (20, HEIGHT - 40))

# ─── Lançamento do jogo (CORRIGIDO) ─────────────────────────────────────────
def launch_game():
    global error_msg, error_timer

    try:
        from jogo.main import main  # ajuste se o nome for diferente
        pygame.quit()
        main()
    except Exception as e:
        error_msg = f"Erro ao iniciar: {e}"
        error_timer = 180
        print(f"[ERRO] {e}")

# ─── Loop principal ─────────────────────────────────────────────────────────
running = True
while running:
    dt = clock.tick(60) / 1000.0
    time_val += dt

    mx, my = pygame.mouse.get_pos()

    hovered_item = -1
    for i in range(len(MENU_ITEMS)):
        y = ITEM_START_Y + i * ITEM_STEP
        if OVERLAY_W // 2 - 150 <= mx <= OVERLAY_W // 2 + 150 and y <= my <= y + 40:
            hovered_item = i

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if hovered_item == 1:  # Novo Jogo
                launch_game()
            elif hovered_item == 2:  # Sair
                running = False

    draw_background(screen)
    draw_logo(screen)
    draw_menu(screen, hovered_item)
    draw_error(screen, error_msg)

    pygame.display.flip()

pygame.quit()
sys.exit()