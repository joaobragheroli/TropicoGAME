import pygame
import random

# Posicoes fixas das arvores (tile x, tile y) — apenas em tiles de grama (tipo 1)
# Espalhadas pelo mapa evitando a baia central e bordas de areia
TREE_POSITIONS = [
    # Regiao noroeste
    (6,  6), (9,  5), (7,  9), (5, 12), (8, 14),
    (6, 17), (9, 19), (7, 22), (5, 16), (10, 11),
    # Regiao norte/centro
    (15, 4), (19, 5), (22, 4), (17, 8), (21, 9),
    (24, 6), (27, 5), (29, 8), (26, 11),(20, 13),
    # Regiao nordeste
    (33, 6), (36, 8), (38, 5), (40, 9), (35, 12),
    (37, 15),(39, 18),(41, 14),(36, 20),(38, 22),
    # Regiao leste
    (40, 25),(42, 28),(41, 21),(39, 24),
    # Regiao sudeste
    (33, 28),(35, 30),(37, 27),(36, 32),
    # Regiao sudoeste
    (8, 28), (6, 30), (9, 32), (7, 26),
    (10, 29),(5, 27),
    # Centro da ilha
    (18, 15),(22, 17),(25, 14),(20, 19),
    (16, 20),(23, 22),(27, 18),(14, 16),
    (30, 15),(28, 21),(15, 24),(32, 24),
]

TILE = 16

def _draw_palm(surface, px, py, variant, shadow_surf):
    """Desenha uma palmeira tropical pixel art."""
    # Sombra eliptica no chao
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50),
        (px - 6, py + 18, 20, 6))

    # Tronco (marrom, ligeiramente inclinado conforme variant)
    lean = [-1, 0, 1][variant % 3]
    trunk_color  = (120, 80, 40)
    trunk_dark   = (90,  58, 28)
    # 4 segmentos do tronco
    for i in range(4):
        tx = px + 4 + lean * i // 2
        ty = py + 18 - i * 5
        pygame.draw.rect(surface, trunk_color, (tx, ty, 4, 5))
        pygame.draw.rect(surface, trunk_dark,  (tx + 3, ty, 1, 5))

    # Copa: folhas em leque (5 folhas)
    top_x = px + 4 + lean * 2
    top_y = py

    leaf_colors = [
        (34, 139, 34),   # verde medio
        (50, 160, 50),   # verde claro
        (22, 110, 22),   # verde escuro
    ]
    lc  = leaf_colors[variant % 3]
    lc2 = leaf_colors[(variant + 1) % 3]

    # Folhas: (dx_end, dy_end, largura)
    leaves = [
        (-12, -6,  3),   # esquerda baixo
        (-8,  -14, 3),   # esquerda cima
        (0,   -16, 4),   # topo
        (8,   -14, 3),   # direita cima
        (12,  -6,  3),   # direita baixo
    ]
    for i, (dx, dy, w) in enumerate(leaves):
        ex = top_x + dx
        ey = top_y + dy
        color = lc if i % 2 == 0 else lc2
        # Linha grossa simulando folha
        pygame.draw.line(surface, color, (top_x, top_y), (ex, ey), w)
        # Ponta mais clara
        pygame.draw.circle(surface, lc2, (ex, ey), 2)

    # Coquinhos (2-3 bolinhas marrom-amareladas embaixo da copa)
    if variant % 2 == 0:
        nut_color = (180, 120, 40)
        pygame.draw.circle(surface, nut_color, (top_x - 2, top_y + 4), 3)
        pygame.draw.circle(surface, nut_color, (top_x + 4, top_y + 3), 3)


def _draw_tropical(surface, px, py, variant, shadow_surf):
    """Arvore tropical frondosa (mais larga)."""
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 45),
        (px - 8, py + 20, 24, 7))

    # Tronco curto e grosso
    trunk_color = (100, 65, 30)
    pygame.draw.rect(surface, trunk_color, (px + 5, py + 14, 5, 8))

    # Copa em 3 camadas sobrepostas (efeito de profundidade)
    layers = [
        (px + 7,  py + 13, 14, 10, (22, 100, 22)),   # base (mais escura)
        (px + 4,  py + 8,  18, 10, (34, 130, 34)),   # meio
        (px + 6,  py + 2,  14,  9, (55, 160, 55)),   # topo (mais clara)
    ]
    for (cx, cy, w, h, color) in layers:
        pygame.draw.ellipse(surface, color, (cx, cy, w, h))
        # Highlight
        pygame.draw.ellipse(surface, (
            min(color[0]+30, 255),
            min(color[1]+30, 255),
            min(color[2]+20, 255)
        ), (cx + 2, cy + 1, w - 6, h - 4))


class TreeManager:
    def __init__(self, grid, tile_size=TILE):
        self.tile_size = tile_size
        self.trees = []

        # Filtra posicoes validas (apenas tiles de grama = tipo 1)
        for (tx, ty) in TREE_POSITIONS:
            if 0 <= ty < len(grid) and 0 <= tx < len(grid[0]):
                if grid[ty][tx] == 1:
                    variant = (tx * 3 + ty * 7) % 6
                    self.trees.append((tx, ty, variant))

        # Surface de sombras (pre-renderizada)
        sw = len(grid[0]) * tile_size
        sh = len(grid)    * tile_size
        self.shadow_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self.shadow_surf.fill((0, 0, 0, 0))

        # Surface das arvores (pre-renderizada)
        self.tree_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        self.tree_surf.fill((0, 0, 0, 0))

        self._render_all()

    def _render_all(self):
        for (tx, ty, variant) in self.trees:
            px = tx * self.tile_size - 4
            py = ty * self.tile_size - 16
            if variant < 3:
                _draw_palm(self.tree_surf, px, py, variant, self.shadow_surf)
            else:
                _draw_tropical(self.tree_surf, px, py, variant % 3, self.shadow_surf)

    def draw(self, screen):
        screen.blit(self.shadow_surf, (0, 0))
        screen.blit(self.tree_surf,   (0, 0))
