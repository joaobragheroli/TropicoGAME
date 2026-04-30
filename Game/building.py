# Sistema de Construção - TropicoGAME
import pygame

# Definição dos tipos de construção disponíveis
BUILDING_TYPES = {
    "house": {
        "label":    "Casa",
        "color":    (160, 82,  45),
        "roof":     (200, 50,  50),
        "cost":     50,
        "size":     2,          # em tiles (2x2)
        "pop":      +5,
        "food":     -2,
        "income":   0,
    },
    "farm": {
        "label":    "Fazenda",
        "color":    (34,  139, 34),
        "roof":     (139, 90,  43),
        "cost":     80,
        "size":     2,
        "pop":      0,
        "food":     +10,
        "income":   0,
    },
    "factory": {
        "label":    "Fabrica",
        "color":    (105, 105, 105),
        "roof":     (80,  80,  80),
        "cost":     150,
        "size":     3,          # 3x3
        "pop":      0,
        "food":     0,
        "income":   +20,
    },
}


class Building:
    """Representa um prédio já construído no mapa."""

    def __init__(self, tile_x, tile_y, btype, tile_size=16):
        self.tile_x    = tile_x
        self.tile_y    = tile_y
        self.btype     = btype
        self.tile_size = tile_size
        info           = BUILDING_TYPES[btype]
        self.size      = info["size"]
        px             = tile_x * tile_size
        py             = tile_y * tile_size
        self.rect      = pygame.Rect(px, py, self.size * tile_size, self.size * tile_size)

    def occupied_tiles(self):
        """Retorna lista de (tx, ty) que este prédio ocupa."""
        tiles = []
        for dy in range(self.size):
            for dx in range(self.size):
                tiles.append((self.tile_x + dx, self.tile_y + dy))
        return tiles

    def draw(self, screen):
        info   = BUILDING_TYPES[self.btype]
        color  = info["color"]
        roof_c = info["roof"]
        r      = self.rect

        # Draw Shadow
        shadow_rect = pygame.Rect(r.x + 6, r.y + 6, r.width, r.height)
        shadow_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80)) # Semi-transparent black
        screen.blit(shadow_surf, shadow_rect.topleft)

        # Paredes
        pygame.draw.rect(screen, color, r)

        # Borda escura
        dark = tuple(max(0, c - 60) for c in color)
        pygame.draw.rect(screen, dark, r, 2)

        # Telhado triangular (house e farm)
        if self.btype in ("house", "farm"):
            apex   = (r.centerx, r.top + 2)
            left   = (r.left,    r.top + r.height // 3)
            right_ = (r.right,   r.top + r.height // 3)
            pygame.draw.polygon(screen, roof_c, [apex, left, right_])

        # Chamine (fabrica)
        if self.btype == "factory":
            cw, ch = 4, 8
            cx = r.left + r.width // 4
            cy = r.top  - ch
            pygame.draw.rect(screen, (60, 60, 60), (cx, cy, cw, ch))

        # Janelinha central
        w_size = max(4, r.width // 4)
        w_rect = pygame.Rect(
            r.centerx - w_size // 2,
            r.centery  - w_size // 2,
            w_size, w_size
        )
        pygame.draw.rect(screen, (173, 216, 230), w_rect)
        pygame.draw.rect(screen, dark, w_rect, 1)


class BuildingSystem:
    """
    Centraliza toda a lógica de construção.

    Uso em main.py:
      bs = BuildingSystem(game_map.grid, tile_size=TILE_SIZE)
      bs.register_trees(tree_positions)
      # no loop:
      built = bs.handle_event(event, buildings, money)
      dm, dp, df = bs.flush_effects()
      bs.draw_preview(screen)
      bs.draw_hud(screen, font, money)
    """

    PANEL_HEIGHT = 50

    def __init__(self, grid, tile_size=16):
        self.grid      = grid
        self.tile_size = tile_size
        self.selected  = None
        self._pending  = []
        self.tree_tiles = set()
        self.occupied   = set()
        self._buttons   = []

    def register_trees(self, tree_positions):
        self.tree_tiles = set(tree_positions)

    def _can_place(self, tile_x, tile_y, size):
        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0
        for dy in range(size):
            for dx in range(size):
                tx, ty = tile_x + dx, tile_y + dy
                if not (0 <= ty < rows and 0 <= tx < cols):
                    return False
                if self.grid[ty][tx] == 0:
                    return False
                if (tx, ty) in self.tree_tiles:
                    return False
                if (tx, ty) in self.occupied:
                    return False
        return True

    def handle_event(self, event, buildings, money):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected = None
            shortcuts = {pygame.K_1: "house", pygame.K_2: "farm", pygame.K_3: "factory"}
            if event.key in shortcuts:
                t = shortcuts[event.key]
                self.selected = None if self.selected == t else t

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for btn in self._buttons:
                if btn["rect"].collidepoint(mx, my):
                    t = btn["type"]
                    self.selected = None if self.selected == t else t
                    return False
            if self.selected:
                info   = BUILDING_TYPES[self.selected]
                size   = info["size"]
                cost   = info["cost"]
                tile_x = mx // self.tile_size
                tile_y = my // self.tile_size
                if money < cost:
                    return False
                if self._can_place(tile_x, tile_y, size):
                    b = Building(tile_x, tile_y, self.selected, self.tile_size)
                    buildings.append(b)
                    for tile in b.occupied_tiles():
                        self.occupied.add(tile)
                    self._pending.append(info)
                    return True
        return False

    def flush_effects(self):
        dm = dp = df = 0
        for info in self._pending:
            dm -= info["cost"]
            dp += info["pop"]
            df += info["food"]
        self._pending.clear()
        return dm, dp, df

    def draw_preview(self, screen):
        if not self.selected:
            return
        mx, my = pygame.mouse.get_pos()
        info   = BUILDING_TYPES[self.selected]
        size   = info["size"]
        tile_x = mx // self.tile_size
        tile_y = my // self.tile_size
        valid  = self._can_place(tile_x, tile_y, size)
        color  = (0, 255, 0, 100) if valid else (255, 0, 0, 100)
        surf   = pygame.Surface((size * self.tile_size, size * self.tile_size), pygame.SRCALPHA)
        surf.fill(color)
        screen.blit(surf, (tile_x * self.tile_size, tile_y * self.tile_size))
        # Grade auxiliar
        for dx in range(size + 1):
            x = tile_x * self.tile_size + dx * self.tile_size
            pygame.draw.line(screen, (255, 255, 255),
                             (x, tile_y * self.tile_size),
                             (x, (tile_y + size) * self.tile_size), 1)
        for dy in range(size + 1):
            y = tile_y * self.tile_size + dy * self.tile_size
            pygame.draw.line(screen, (255, 255, 255),
                             (tile_x * self.tile_size, y),
                             ((tile_x + size) * self.tile_size, y), 1)

    def draw_hud(self, screen, font, money):
        sw, sh = screen.get_size()
        ph     = self.PANEL_HEIGHT
        panel  = pygame.Surface((sw, ph), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 180))
        screen.blit(panel, (0, sh - ph))

        self._buttons.clear()
        btn_w = 110
        gap   = 10
        small_font = pygame.font.SysFont(None, 18)

        for i, (btype, info) in enumerate(BUILDING_TYPES.items()):
            bx   = gap + i * (btn_w + gap)
            by   = sh - ph + 6
            rect = pygame.Rect(bx, by, btn_w, ph - 12)
            selected   = self.selected == btype
            can_afford = money >= info["cost"]
            if selected:
                bg = (255, 220, 50)
            elif not can_afford:
                bg = (60, 60, 60)
            else:
                bg = (70, 120, 70)
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=4)
            label = font.render(f"{info['label']}  ${info['cost']}", True,
                                (0, 0, 0) if selected else (230, 230, 230))
            screen.blit(label, (rect.x + 4, rect.y + 4))
            hint = small_font.render(f"[{i+1}]", True, (180, 180, 180))
            screen.blit(hint, (rect.x + 4, rect.y + rect.height - 14))
            self._buttons.append({"rect": rect, "type": btype})

        if self.selected:
            cancel_font = pygame.font.SysFont(None, 20)
            msg = cancel_font.render("ESC / clique no botao para cancelar", True, (200, 200, 200))
            screen.blit(msg, (sw - msg.get_width() - 10, sh - ph + 16))
