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
        "capacity": 4,          # NPCs que pode abrigar
        "workers":  0,          # trabalhadores necessários
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
        "capacity": 0,
        "workers":  2,
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
        "capacity": 0,
        "workers":  4,
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
        self.active    = True   # True se tem trabalhadores suficientes

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

<<<<<<< HEAD
        # Sombra (v2 style)
        shadow_rect = pygame.Rect(r.x + 4, r.y + 4, r.width, r.height)
        shadow_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 70)) 
=======
        # Draw Shadow
        shadow_rect = pygame.Rect(r.x + 6, r.y + 6, r.width, r.height)
        shadow_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80)) # Semi-transparent black
>>>>>>> 6abfd031e5d739d894922fa5497baee308fa11a5
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

    PANEL_HEIGHT = 72

    def __init__(self, grid, tile_size=16):
        self.grid             = grid
        self.tile_size        = tile_size
        self.selected         = None
        self.demolish_mode    = False
        self._pending         = []
        self._pending_refunds = []   # list of (dm, dp, df)
        self.tree_tiles       = set()
        self.occupied         = set()
        self._buttons         = []
        self._blocked_msg     = ""
        self._blocked_timer   = 0
        self._tree_manager    = None

    def register_trees(self, tree_positions):
        self.tree_tiles = set(tree_positions)

    def set_tree_manager(self, tree_manager):
        self._tree_manager = tree_manager

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

    def handle_event(self, event, buildings, money, free_workers=999):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected = None
                self.demolish_mode = False
            # [D] toggles demolish mode
            if event.key in (pygame.K_d, pygame.K_DELETE):
                self.demolish_mode = not self.demolish_mode
                self.selected = None
            shortcuts = {pygame.K_1: "house", pygame.K_2: "farm", pygame.K_3: "factory"}
            if event.key in shortcuts:
                t = shortcuts[event.key]
                self.selected = None if self.selected == t else t
                self.demolish_mode = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # HUD buttons (always checked first)
            for btn in self._buttons:
                if btn["rect"].collidepoint(mx, my):
                    t = btn["type"]
                    if t == "demolish":
                        self.demolish_mode = not self.demolish_mode
                        self.selected = None
                    else:
                        self.selected = None if self.selected == t else t
                        self.demolish_mode = False
                    return False

            # Demolish mode: remove building or tree
            if self.demolish_mode:
                tile_x = mx // self.tile_size
                tile_y = my // self.tile_size
                for b in list(buildings):
                    if (tile_x, tile_y) in set(b.occupied_tiles()):
                        info = BUILDING_TYPES[b.btype]
                        self._pending_refunds.append(
                            (info["cost"] // 2, -info["pop"], -info["food"]))
                        for tile in b.occupied_tiles():
                            self.occupied.discard(tile)
                        buildings.remove(b)
                        return True
                if (tile_x, tile_y) in self.tree_tiles:
                    self.tree_tiles.discard((tile_x, tile_y))
                    if self._tree_manager:
                        self._tree_manager.remove_tree(tile_x, tile_y)
                return False

            # Build mode
            if self.selected:
                info    = BUILDING_TYPES[self.selected]
                size    = info["size"]
                cost    = info["cost"]
                needed  = info["workers"]
                tile_x  = mx // self.tile_size
                tile_y  = my // self.tile_size
                if money < cost:
                    self._blocked_msg   = "Dinheiro insuficiente!"
                    self._blocked_timer = 180
                    return False
                if needed > 0 and free_workers < needed:
                    self._blocked_msg   = f"Precisa de {needed} trabalhador(es) livre(s)!"
                    self._blocked_timer = 180
                    return False
                if self._can_place(tile_x, tile_y, size):
                    b = Building(tile_x, tile_y, self.selected, self.tile_size)
                    buildings.append(b)
                    for tile in b.occupied_tiles():
                        self.occupied.add(tile)
                    self._pending.append(info)
                    self._blocked_msg = ""
                    return True
        return False

    def flush_effects(self):
        dm = dp = df = 0
        for info in self._pending:
            dm -= info["cost"]
            dp += info["pop"]
            df += info["food"]
        for (rdm, rdp, rdf) in self._pending_refunds:
            dm += rdm
            dp += rdp
            df += rdf
        self._pending.clear()
        self._pending_refunds.clear()
        return dm, dp, df

    def draw_preview(self, screen):
        mx, my = pygame.mouse.get_pos()
        tile_x = mx // self.tile_size
        tile_y = my // self.tile_size

        if self.demolish_mode:
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            surf.fill((255, 60, 60, 140))
            screen.blit(surf, (tile_x * self.tile_size, tile_y * self.tile_size))
            return

        if not self.selected:
            return
        info   = BUILDING_TYPES[self.selected]
        size   = info["size"]
        valid  = self._can_place(tile_x, tile_y, size)
        color  = (0, 255, 0, 100) if valid else (255, 0, 0, 100)
        surf   = pygame.Surface((size * self.tile_size, size * self.tile_size), pygame.SRCALPHA)
        surf.fill(color)
        screen.blit(surf, (tile_x * self.tile_size, tile_y * self.tile_size))
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

        # Painel de fundo
        panel = pygame.Surface((sw, ph), pygame.SRCALPHA)
        panel.fill((12, 12, 20, 220))
        screen.blit(panel, (0, sh - ph))
        pygame.draw.line(screen, (60, 60, 100), (0, sh - ph), (sw, sh - ph), 1)

        self._buttons.clear()
        sf   = pygame.font.SysFont(None, 18)   # small font
        tf   = pygame.font.SysFont(None, 22)   # title font
        btn_w = 142
        gap   = 8
        btn_h = ph - 10

        for i, (btype, info) in enumerate(BUILDING_TYPES.items()):
            bx   = gap + i * (btn_w + gap)
            by   = sh - ph + 5
            rect = pygame.Rect(bx, by, btn_w, btn_h)
            sel        = self.selected == btype
            affordable = money >= info["cost"]

            if sel:
                bg, border = (55, 44, 8), (255, 210, 40)
            elif not affordable:
                bg, border = (28, 28, 34), (70, 70, 85)
            else:
                bg, border = (18, 44, 22), (55, 155, 75)

            pygame.draw.rect(screen, bg,     rect, border_radius=6)
            pygame.draw.rect(screen, border, rect, 2, border_radius=6)

            # Ícone colorido
            icon = pygame.Rect(bx + 5, by + 6, 13, 13)
            pygame.draw.rect(screen, info["color"], icon, border_radius=2)
            pygame.draw.rect(screen, info["roof"],  icon, 1,  border_radius=2)

            # Nome
            nc = (255, 210, 40) if sel else (230, 230, 230)
            screen.blit(tf.render(info["label"], True, nc), (bx + 22, by + 5))

            # Shortcut
            sk = sf.render(f"[{i+1}]", True, (110, 110, 140))
            screen.blit(sk, (rect.right - sk.get_width() - 5, by + 6))

            # Custo
            cc = (255, 195, 45) if affordable else (150, 90, 90)
            screen.blit(sf.render(f"${info['cost']}", True, cc), (bx + 5, by + 22))

            # Trabalhadores / moradores
            if info["workers"] > 0:
                screen.blit(sf.render(f"{info['workers']} trabalhadores",
                    True, (120, 205, 120)), (bx + 5, by + 36))
            elif info["capacity"] > 0:
                screen.blit(sf.render(f"{info['capacity']} moradores",
                    True, (120, 155, 255)), (bx + 5, by + 36))

            # Produção
            if info["food"] > 0:
                screen.blit(sf.render(f"+{info['food']} comida/tick",
                    True, (90, 195, 90)), (bx + 5, by + 50))
            elif info["income"] > 0:
                screen.blit(sf.render(f"+${info['income']}/tick",
                    True, (215, 175, 45)), (bx + 5, by + 50))
            elif info["pop"] > 0:
                screen.blit(sf.render(f"+{info['pop']} populacao",
                    True, (175, 150, 255)), (bx + 5, by + 50))

            self._buttons.append({"rect": rect, "type": btype})

        # Botão Demolir
        demo_x    = gap + len(BUILDING_TYPES) * (btn_w + gap)
        demo_rect = pygame.Rect(demo_x, sh - ph + 5, 100, btn_h)
        if self.demolish_mode:
            dbg, dborder = (75, 18, 18), (255, 75, 75)
        else:
            dbg, dborder = (38, 18, 18), (170, 55, 55)
        pygame.draw.rect(screen, dbg,     demo_rect, border_radius=6)
        pygame.draw.rect(screen, dborder, demo_rect, 2, border_radius=6)
        dtitle = tf.render("Demolir", True,
            (255, 95, 95) if self.demolish_mode else (195, 75, 75))
        screen.blit(dtitle,
            (demo_rect.centerx - dtitle.get_width() // 2, demo_rect.y + 8))
        dhint = sf.render("[D]", True, (140, 70, 70))
        screen.blit(dhint,
            (demo_rect.centerx - dhint.get_width() // 2, demo_rect.y + 36))
        dinfo = sf.render("50% reembolso", True, (120, 60, 60))
        screen.blit(dinfo,
            (demo_rect.centerx - dinfo.get_width() // 2, demo_rect.y + 50))
        self._buttons.append({"rect": demo_rect, "type": "demolish"})

        # Mensagens de status
        if self.demolish_mode:
            msg = sf.render(
                "DEMOLIR: clique em edificio ou arvore  |  ESC cancela",
                True, (255, 120, 120))
            screen.blit(msg, (sw // 2 - msg.get_width() // 2, sh - ph - 18))
        elif self.selected:
            msg = sf.render("ESC / clique no botao para cancelar",
                True, (180, 180, 210))
            screen.blit(msg, (sw - msg.get_width() - 10, sh - ph - 18))

        # Mensagem de bloqueio
        if self._blocked_timer > 0:
            self._blocked_timer -= 1
            warn = tf.render(self._blocked_msg, True, (255, 80, 80))
            screen.blit(warn, (sw // 2 - warn.get_width() // 2, sh - ph - 40))
