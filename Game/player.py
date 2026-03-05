import pygame
import os

TILE = 16

class Player:
    def __init__(self, x=0, y=0):
        BASE_DIR = os.path.dirname(__file__)
        ASSETS_DIR = os.path.join(BASE_DIR, "assets")
        img = pygame.image.load(os.path.join(ASSETS_DIR, "navio1.png")).convert_alpha()

        self.boat_w = TILE * 2
        self.boat_h = TILE * 6
        self.sprite = pygame.transform.scale(img, (self.boat_w, self.boat_h))
        self.rect = pygame.Rect(x, y, self.boat_w, self.boat_h)

    def move(self, keys, map_width, map_height):
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= TILE
        if keys[pygame.K_RIGHT] and self.rect.right < map_width * TILE:
            self.rect.x += TILE
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= TILE
        if keys[pygame.K_DOWN] and self.rect.bottom < map_height * TILE:
            self.rect.y += TILE

    def draw(self, screen):
        screen.blit(self.sprite, (self.rect.x, self.rect.y))