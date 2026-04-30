import pygame
import random

TILE = 16

# Tiles que são terra (grama ou areia) — NPCs só andam neles
WALKABLE = {1, 2}

class NPC:
    def __init__(self, grid, color=None):
        self.grid = grid
        self.color = color or (
            random.randint(180, 255),
            random.randint(100, 200),
            random.randint(50, 150)
        )
        # Cor da roupa (segunda cor)
        self.shirt = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        # Posição inicial aleatória em tile walkable
        self.tx, self.ty = self._random_walkable()
        self.x = self.tx * TILE
        self.y = self.ty * TILE
        # Destino atual
        self.dest_x = self.x
        self.dest_y = self.y
        # Velocidade de movimento suave (pixels por frame)
        self.speed = random.choice([1, 1, 2])
        # Timer para escolher novo destino
        self.wait = random.randint(30, 120)
        # Direção para animação
        self.facing = "down"
        self.anim_frame = 0
        self.anim_timer = 0
        # Estado social
        self.has_home  = False
        self.has_job   = False
        self.happiness = 50   # 0-100

    def _random_walkable(self):
        tiles = []
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile in WALKABLE:
                    tiles.append((x, y))
        return random.choice(tiles)

    def _pick_destination(self):
        # Escolhe tile adjacente walkable aleatório
        directions = [(-1,0),(1,0),(0,-1),(0,1)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = self.tx + dx, self.ty + dy
            if 0 <= ny < len(self.grid) and 0 <= nx < len(self.grid[0]):
                if self.grid[ny][nx] in WALKABLE:
                    self.tx, self.ty = nx, ny
                    self.dest_x = nx * TILE
                    self.dest_y = ny * TILE
                    # Atualizar direção
                    if dx == 1:  self.facing = "right"
                    if dx == -1: self.facing = "left"
                    if dy == 1:  self.facing = "down"
                    if dy == -1: self.facing = "up"
                    return
        # Se nenhum adjacente disponível, fica parado
        self.wait = random.randint(30, 90)

    def update(self):
        # Mover suavemente em direção ao destino
        moved = False
        if self.x < self.dest_x:
            self.x = min(self.x + self.speed, self.dest_x); moved = True
        elif self.x > self.dest_x:
            self.x = max(self.x - self.speed, self.dest_x); moved = True
        if self.y < self.dest_y:
            self.y = min(self.y + self.speed, self.dest_y); moved = True
        elif self.y > self.dest_y:
            self.y = max(self.y - self.speed, self.dest_y); moved = True

        # Animação de caminhada
        if moved:
            self.anim_timer += 1
            if self.anim_timer >= 10:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % 2
        else:
            self.anim_frame = 0

        # Chegou ao destino — esperar ou escolher novo
        if self.x == self.dest_x and self.y == self.dest_y:
            self.wait -= 1
            if self.wait <= 0:
                self._pick_destination()
                self.wait = random.randint(40, 100)

    def update_social(self, food_ratio, modifier=0):
        """Recalcula a felicidade individual com base em moradia, emprego e comida."""
        score = 0
        if self.has_home: score += 50
        if self.has_job:  score += 15
        score += int(min(1.0, food_ratio) * 35)
        score += modifier
        self.happiness = max(0, min(100, score))

    def draw(self, screen):
        px = self.x
        py = self.y
        # Offset de caminhada (balanço)
        bob = self.anim_frame * 1 if self.anim_frame else 0

        # Sombra
        pygame.draw.ellipse(screen, (0, 0, 0, 80),
            (px + 3, py + 13 + bob, 10, 4))

        # Pernas (animadas)
        if self.anim_frame == 0:
            pygame.draw.rect(screen, (40, 40, 120), (px+4, py+10+bob, 3, 5))
            pygame.draw.rect(screen, (40, 40, 120), (px+9, py+10+bob, 3, 5))
        else:
            pygame.draw.rect(screen, (40, 40, 120), (px+4, py+12+bob, 3, 4))
            pygame.draw.rect(screen, (40, 40, 120), (px+9, py+9+bob,  3, 4))

        # Corpo / camisa
        pygame.draw.rect(screen, self.shirt, (px+3, py+6+bob, 10, 6))

        # Braços
        arm_offset = 2 if self.anim_frame == 0 else -1
        pygame.draw.rect(screen, self.color, (px+1,  py+6+bob+arm_offset, 2, 4))
        pygame.draw.rect(screen, self.color, (px+13, py+6+bob-arm_offset, 2, 4))

        # Cabeça
        pygame.draw.circle(screen, self.color, (px+8, py+4+bob), 4)

        # Olhos (dependendo da direção)
        if self.facing in ("down", "right", "left"):
            pygame.draw.circle(screen, (0,0,0), (px+6, py+4+bob), 1)
            pygame.draw.circle(screen, (0,0,0), (px+10, py+4+bob), 1)

        # Chapéu
        pygame.draw.rect(screen, (80, 40, 10), (px+4, py+1+bob, 8, 2))
        pygame.draw.rect(screen, (80, 40, 10), (px+5, py-1+bob, 6, 3))