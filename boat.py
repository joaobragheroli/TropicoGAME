import pygame
import os
from utils import resource_path

TILE_SIZE = 16

BAY_CENTER_X = 20   # coluna tile do centro da baia
STOP_TILE_Y  = 30   # linha tile onde o barco para (meio da agua da baia)

class Boat:
    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size

        clean_path = resource_path(os.path.join("assets", "navio1_clean.png"))
        orig_path  = resource_path(os.path.join("assets", "navio1.png"))
        img_path   = clean_path if os.path.exists(clean_path) else orig_path
        raw = pygame.image.load(img_path).convert_alpha()

        # Escalar para ~3 tiles de largura
        self.boat_w = tile_size * 3
        self.boat_h = int(raw.get_height() * (self.boat_w / raw.get_width()))
        self.image  = pygame.transform.scale(raw, (self.boat_w, self.boat_h))

        # Posicao inicial fora da tela (sul)
        self.screen_h = 36 * tile_size
        self.reset_position()

        # Destino: meio da agua da baia
        self.target_y = float(STOP_TILE_Y * tile_size - self.boat_h // 2)

        # Velocidade
        self.speed     = 5.0
        self.min_speed = 1.0

        # Balanco quando atracado
        self.bob_offset = 0.0
        self.bob_dir    = 1
        self.bob_speed  = 0.15
        self.bob_max    = 2.5

        # Partículas
        self.wake_particles = []
        self.wake_timer = 0
        self.splash_particles = []
        self.splash_done = False

        # Sombra
        self.shadow_surf = pygame.Surface((self.boat_w, self.boat_h), pygame.SRCALPHA)
        dark = self.image.copy()
        dark.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
        self.shadow_surf.blit(dark, (0, 0))

    def reset_position(self):
        """Prepara o barco para uma nova vinda do sul"""
        self.x = float(BAY_CENTER_X * self.tile_size - self.boat_w // 2)
        self.y = float(self.screen_h + 100)
        self.state = "waiting" # Fica em espera até o timer do main disparar
        self.splash_done = False

    def leave(self):
        """Ativa a partida do navio"""
        if self.state == "docked":
            self.state = "leaving"

    def update(self):
        if self.state == "sailing":
            dist = self.y - self.target_y
            if dist > 80:
                cur_speed = self.speed
            elif dist > 0:
                cur_speed = max(self.min_speed, self.speed * (dist / 80))
            else:
                cur_speed = 0

            self.y -= cur_speed

            self.wake_timer += 1
            if self.wake_timer >= 8 and cur_speed > 0.5:
                self.wake_timer = 0
                cx = self.x + self.boat_w // 2
                cy = self.y + self.boat_h
                self._add_wake(cx, cy)

            if self.y <= self.target_y:
                self.y = self.target_y
                self.state = "docking"
                self._create_splash()

        elif self.state == "docking":
            self._update_splash()
            if len(self.splash_particles) == 0 and not self.splash_done:
                self.splash_done = True
                self.state = "docked"

        elif self.state == "docked":
            self.bob_offset += self.bob_speed * self.bob_dir
            if abs(self.bob_offset) >= self.bob_max:
                self.bob_dir *= -1

        elif self.state == "leaving":
            self.y += self.speed # Move de volta para o sul
            # Se sumir da tela, entra em espera
            if self.y > self.screen_h + 150:
                self.state = "waiting"

        # Atualizar partículas de rastro
        for p in self.wake_particles[:]:
            p["life"] -= 1
            p["r"] += 0.3
            if p["life"] <= 0:
                self.wake_particles.remove(p)

        self._update_splash()

    def _add_wake(self, cx, cy):
        import random
        for i in range(2):
            self.wake_particles.append({
                "x": cx + ([-1, 1][i % 2]) * (self.boat_w // 3),
                "y": cy,
                "r": 2,
                "max_r": 10 + i * 4,
                "life": 30,
                "max_life": 30,
            })

    def _create_splash(self):
        import random, math
        cx = self.x + self.boat_w // 2
        cy = self.y + self.boat_h * 0.3
        for i in range(18):
            angle = random.uniform(0, math.pi)
            speed = random.uniform(1.5, 4.0)
            self.splash_particles.append({
                "x": float(cx),
                "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": -abs(math.sin(angle) * speed),
                "life": random.randint(20, 40),
                "size": random.randint(2, 5),
            })

    def _update_splash(self):
        for p in self.splash_particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.2
            p["life"] -= 1
            if p["life"] <= 0:
                self.splash_particles.remove(p)

    def draw(self, screen):
        if self.state == "waiting":
            return

        draw_y = self.y + self.bob_offset
        # Rastro
        for p in self.wake_particles:
            alpha = int(180 * (p["life"] / p["max_life"]))
            surf = pygame.Surface((int(p["r"] * 2 + 2), int(p["r"] + 2)), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (150, 200, 255, alpha), (0, 0, int(p["r"] * 2), int(p["r"])))
            screen.blit(surf, (int(p["x"] - p["r"]), int(p["y"])))

        screen.blit(self.shadow_surf, (int(self.x) + 4, int(draw_y) + 4))
        screen.blit(self.image, (int(self.x), int(draw_y)))

        # Splash
        for p in self.splash_particles:
            alpha = int(220 * max(0, p["life"] / 40))
            r = max(1, p["size"])
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 230, 255, alpha), (r, r), r)
            screen.blit(surf, (int(p["x"]) - r, int(p["y"]) - r))

    @property
    def is_docked(self):
        return self.state == "docked"