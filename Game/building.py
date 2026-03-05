# Base para futuras construções na ilha
import pygame

class Building:
    def __init__(self, x, y, size=32, type="house"):
        self.rect = pygame.Rect(x, y, size, size)
        self.type = type

    def draw(self, screen):
        colors = {
            "house": (150, 75, 0),
            "farm": (0, 200, 0),
            "factory": (100, 100, 100)
        }
        pygame.draw.rect(screen, colors.get(self.type, (255, 255, 255)), self.rect)