# rival_ai.py - Inteligência Artificial do Rival
import random
from building import BUILDING_TYPES, Building


class RivalAI:
    """Jogador rival controlado pela IA que compete com o player."""

    def __init__(self, build_sys_grid, tile_size=16):
        self.grid       = build_sys_grid
        self.tile_size  = tile_size
        self.money      = 500
        self.food       = 50
        self.timer      = 0
        self.occupied   = set()   # tiles ocupados pelo rival
        self.think_interval = 220  # ~3.7 segundos a 60fps

    # ──────────────────────────────────────────────────────────────
    #  LÓGICA DE DECISÃO
    # ──────────────────────────────────────────────────────────────

    def think(self, player_stats, buildings):
        """Chamado a cada frame. Retorna dict com ação ou None."""
        self.timer += 1
        if self.timer < self.think_interval:
            return None
        self.timer = 0

        # ── 1. ANALISAR O ESTADO DO JOGO ──────────────────────────
        player_farms     = sum(1 for b in buildings if b.btype == "farm"    and b.owner == "player")
        rival_farms      = sum(1 for b in buildings if b.btype == "farm"    and b.owner == "rival")
        player_houses    = sum(1 for b in buildings if b.btype == "house"   and b.owner == "player")
        rival_houses     = sum(1 for b in buildings if b.btype == "house"   and b.owner == "rival")
        player_factories = sum(1 for b in buildings if b.btype == "factory" and b.owner == "player")
        rival_factories  = sum(1 for b in buildings if b.btype == "factory" and b.owner == "rival")

        # ── 2. DECIDIR AÇÃO ───────────────────────────────────────
        # Prioridade 1: Se o player tem mais fazendas, iguala
        if rival_farms < player_farms and self.money >= BUILDING_TYPES["farm"]["cost"]:
            return self.try_build("farm", buildings)

        # Prioridade 2: Se player tem mais casas, compite por moradia
        if rival_houses < player_houses and self.money >= BUILDING_TYPES["house"]["cost"]:
            return self.try_build("house", buildings)

        # Prioridade 3: Com dinheiro sobrando, constrói casa para atrair NPCs
        if self.money > 300 and self.money >= BUILDING_TYPES["house"]["cost"]:
            return self.try_build("house", buildings)

        # Prioridade 4: Constrói fazenda se precisar de comida
        if self.food < 30 and self.money >= BUILDING_TYPES["farm"]["cost"]:
            return self.try_build("farm", buildings)

        # Prioridade 5: Fábrica se tiver bastante dinheiro
        if self.money > 500 and self.money >= BUILDING_TYPES["factory"]["cost"]:
            if rival_factories < player_factories + 1:
                return self.try_build("factory", buildings)

        return None

    def update_economy(self, buildings):
        """Chamado a cada evento PROD_EVENT para atualizar economia do rival."""
        for b in buildings:
            if b.owner != "rival":
                continue
            if b.btype == "farm":
                self.food += 6
            elif b.btype == "factory":
                self.money += 15

        # Consumo: rival tem ~8 NPCs virtuais
        self.food = max(0, self.food - 3)

        # Rival recebe renda base pequena (sem fazendas = mais lento)
        self.money += 12

    # ──────────────────────────────────────────────────────────────
    #  CONSTRUÇÃO
    # ──────────────────────────────────────────────────────────────

    def try_build(self, btype, buildings):
        """Tenta encontrar um tile livre para construir. Retorna ação ou None."""
        info  = BUILDING_TYPES[btype]
        size  = info["size"]
        cost  = info["cost"]

        if self.money < cost:
            return None

        # Pega todos os tiles ocupados (player + rival)
        all_occupied = set()
        for b in buildings:
            all_occupied.update(b.occupied_tiles())
        all_occupied.update(self.occupied)

        # Posições candidatas aleatórias no mapa
        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0
        candidates = []
        for ty in range(rows - size):
            for tx in range(cols - size):
                if self._can_place(tx, ty, size, all_occupied):
                    candidates.append((tx, ty))

        if not candidates:
            return None

        tx, ty = random.choice(candidates)
        return {"x": tx, "y": ty, "type": btype, "cost": cost}

    def _can_place(self, tile_x, tile_y, size, all_occupied):
        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0
        for dy in range(size):
            for dx in range(size):
                tx, ty = tile_x + dx, tile_y + dy
                if not (0 <= ty < rows and 0 <= tx < cols):
                    return False
                if self.grid[ty][tx] == 0:
                    return False
                if (tx, ty) in all_occupied:
                    return False
        return True

    def register_building(self, building):
        """Registra tiles ocupados por um novo prédio do rival."""
        for tile in building.occupied_tiles():
            self.occupied.add(tile)
