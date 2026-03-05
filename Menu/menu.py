import pygame
import sys
import os

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menu Principal")
clock = pygame.time.Clock()

GOLD      = (255, 210,  50)
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
MENU_HOV  = (255, 215,   0)

font_logo   = pygame.font.SysFont("Impact",  64, bold=True)
font_star   = pygame.font.SysFont("Arial",   22, bold=True)
font_header = pygame.font.SysFont("Georgia", 18, bold=True)
font_menu   = pygame.font.SysFont("Georgia", 28, bold=True)
font_body_b = pygame.font.SysFont("Arial",   14, bold=True)
font_small  = pygame.font.SysFont("Arial",   12)

BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fundo-menu.jpeg")
try:
    bg_raw = pygame.image.load(BG_PATH)
    bg_img = pygame.transform.smoothscale(bg_raw, (WIDTH, HEIGHT))
    print("Imagem de fundo carregada com sucesso.")
except Exception as e:
    print(f"[AVISO] Nao foi possivel carregar '{BG_PATH}': {e}")
    bg_img = None

hovered_item = -1
time_val     = 0.0

MENU_ITEMS = ["Continuar", "Novo Jogo", "Sair do Jogo"]

OVERLAY_W = 490  # largura do painel escuro esquerdo

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
    ov.fill((0, 10, 35, 168))
    surf.blit(ov, (0, 0))

def draw_logo(surf):
    logo_surf   = font_logo.render("TROPICO", True, WHITE)
    shadow_surf = font_logo.render("TROPICO", True, BLACK)
    logo_x = (OVERLAY_W - logo_surf.get_width()) // 2
    surf.blit(shadow_surf, (logo_x + 2, 52))
    surf.blit(logo_surf,   (logo_x,     50))
    # linha e pontos centralizados
    margin = 30
    pygame.draw.line(surf, GOLD, (margin, 122), (OVERLAY_W - margin, 122), 2)
    dot_area = OVERLAY_W - margin * 2
    for i in range(5):
        dx = margin + int(dot_area * (i + 1) / 6)
        pygame.draw.circle(surf, GOLD, (dx, 130), 3)

def draw_menu(surf, hovered):
    hdr_w, hdr_h = 330, 36
    hdr_x = (OVERLAY_W - hdr_w) // 2
    hdr_rect = pygame.Rect(hdr_x, 150, hdr_w, hdr_h)
    s = pygame.Surface((hdr_w, hdr_h), pygame.SRCALPHA)
    s.fill((0, 25, 70, 200))
    surf.blit(s, hdr_rect.topleft)
    pygame.draw.rect(surf, GOLD, hdr_rect, 2, border_radius=4)
    surf.blit(font_star.render("*", True, GOLD), (hdr_x + 8,          153))
    surf.blit(font_star.render("*", True, GOLD), (hdr_x + hdr_w - 24, 153))
    hdr = font_header.render("Menu Principal", True, WHITE)
    surf.blit(hdr, (hdr_rect.centerx - hdr.get_width() // 2, 159))

    for i, name in enumerate(MENU_ITEMS):
        y = 205 + i * 56
        is_hov = (i == hovered)
        if is_hov:
            bg = pygame.Surface((hdr_w, 46), pygame.SRCALPHA)
            bg.fill((255, 200, 0, 55))
            surf.blit(bg, (hdr_x, y - 4))
            pygame.draw.line(surf, GOLD, (hdr_x, y + 39), (hdr_x + hdr_w, y + 39), 1)
            arrow = font_menu.render(">", True, GOLD)
            surf.blit(arrow, (hdr_x - 20, y))
        col = MENU_HOV if is_hov else WHITE
        shadow = font_menu.render(name, True, BLACK)
        text   = font_menu.render(name, True, col)
        cx = OVERLAY_W // 2
        sx = cx - text.get_width() // 2
        surf.blit(shadow, (sx + 2, y + 2))
        surf.blit(text,   (sx,     y))

def draw_social(surf):
    icons = [("f", (59, 89, 152)), ("t", (29, 161, 242)),
             ("Y", (200, 0, 0)),   ("T", (100, 65, 165))]
    sx = 28
    for ch, col in icons:
        r = pygame.Rect(sx, HEIGHT - 48, 34, 34)
        pygame.draw.rect(surf, col, r, border_radius=6)
        lbl = font_body_b.render(ch, True, WHITE)
        surf.blit(lbl, (r.centerx - lbl.get_width() // 2,
                        r.centery - lbl.get_height() // 2))
        sx += 44
    surf.blit(font_small.render("V.1", True, (220, 220, 220)), (WIDTH - 55, HEIGHT - 22))

running = True
while running:
    dt = clock.tick(60) / 1000.0
    time_val += dt
    mx, my = pygame.mouse.get_pos()

    hovered_item = -1
    for i in range(len(MENU_ITEMS)):
        y = 205 + i * 56
        hdr_x = (OVERLAY_W - 330) // 2
        if hdr_x - 20 <= mx <= hdr_x + 330 and y - 4 <= my <= y + 42:
            hovered_item = i
            break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hovered_item == len(MENU_ITEMS) - 1:  # Sair do Jogo
                running = False

    draw_background(screen)
    draw_logo(screen)
    draw_menu(screen, hovered_item)
    draw_social(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()