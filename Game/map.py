import pygame
import os

class Map:
    def __init__(self, width=46, height=36, tile_size=16):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.generate_island()

        BASE_DIR = os.path.dirname(__file__)
        ASSETS_DIR = os.path.join(BASE_DIR, "assets")

        self.sprites = {
            0: pygame.image.load(os.path.join(ASSETS_DIR, "mar1.jpeg")),
            1: pygame.image.load(os.path.join(ASSETS_DIR, "grama.png")),
            2: pygame.image.load(os.path.join(ASSETS_DIR, "areia.jpg"))
        }

    def generate_island(self):
        # 0 = água/mar
        # 1 = grama (centro da ilha)
        # 2 = borda da ilha (areia/transição)

        # Mapa baseado na imagem: ilha em forma de semicírculo/ferradura
        # Grid 46x36 tiles. A ilha ocupa a maior parte, com baía central na parte inferior.

        # Definindo as linhas da ilha (coluna_inicio, coluna_fim) para cada linha y
        # Formato: (x_start, x_end) para a ilha naquela linha, ou None para mar puro
        # Baía inferior: colunas 16-22 ficam como mar nas linhas 26-33
        # Canal central: coluna 23-25 ficam como mar nas linhas 22-27

        island_rows = {
            # y: [(x_start, x_end), ...]  — pode ter múltiplos segmentos por linha
            2:  [(18, 26), (28, 34)],                   # pequenas ilhas no topo
            3:  [(10, 36)],
            4:  [(8, 38)],
            5:  [(6, 40)],
            6:  [(5, 41)],
            7:  [(4, 42)],
            8:  [(3, 43)],
            9:  [(3, 43)],
            10: [(2, 44)],
            11: [(2, 44)],
            12: [(2, 44)],
            13: [(2, 44)],
            14: [(2, 44)],
            15: [(2, 44)],
            16: [(2, 44)],
            17: [(2, 44)],
            18: [(2, 44)],
            19: [(2, 44)],
            20: [(2, 44)],
            21: [(2, 44)],
            22: [(2, 44)],
            23: [(2, 23), (25, 44)],   # canal estreito no centro (col 23-24)
            24: [(2, 23), (25, 44)],
            25: [(2, 44)],
            26: [(2, 15), (26, 44)],   # baía central começa
            27: [(2, 15), (26, 44)],
            28: [(2, 14), (27, 44)],
            29: [(2, 13), (28, 44)],
            30: [(2, 12), (28, 44)],
            31: [(3, 11), (29, 43)],
            32: [(4, 10), (30, 42)],
            33: [(5, 9),  (31, 41)],
            34: [(32, 38)],
        }

        # Pequenas ilhas externas (isoladas)
        small_islands = [
            (7, 2), (8, 2),    # top left small island
            (30, 1), (31, 1),  # top right small island
            (38, 3),           # far right small
            (3, 12),           # left side tiny
            (12, 22), (13, 22),# left inner lake
            (27, 22), (28, 22),# right inner spot
            (30, 34),          # bottom small island
        ]

        # Preencher o grid base com água
        for y in range(self.height):
            for x in range(self.width):
                self.grid[y][x] = 0

        # Preencher a ilha
        for y, segments in island_rows.items():
            if y < self.height:
                for (x_start, x_end) in segments:
                    for x in range(x_start, min(x_end, self.width)):
                        self.grid[y][x] = 1

        # Pequenas ilhas externas
        for (x, y) in small_islands:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = 1

        # Aplicar borda (tile 2) onde terra encontra água
        border = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                if self.grid[ny][nx] == 0:
                                    border.add((y, x))

        for (y, x) in border:
            self.grid[y][x] = 2

        # Lagos/água internos (pequenas poças dentro da ilha)
        internal_water = [
            (8, 14), (8, 15),         # lago esquerdo
            (23, 22),                  # lago central pequeno
            (22, 26),                  # lago direito interno
        ]
        for (x, y) in internal_water:
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = 0

    def draw(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                screen.blit(self.sprites[tile], (x * self.tile_size, y * self.tile_size))