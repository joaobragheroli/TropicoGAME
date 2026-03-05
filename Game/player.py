import pygame

class Player:
    def __init__(self, x=0, y=0, size=32):
        self.rect = pygame.Rect(x, y, size, size)

    def move(self, keys, map_width, map_height):
        # movimento por tile
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.rect.width
        if keys[pygame.K_RIGHT] and self.rect.x < (map_width-1)*self.rect.width:
            self.rect.x += self.rect.width
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= self.rect.height
        if keys[pygame.K_DOWN] and self.rect.y < (map_height-1)*self.rect.height:
            self.rect.y += self.rect.height

    def draw(self, screen):
        # cursor maior e mais visível
        pygame.draw.rect(screen, (255, 255, 0), self.rect, 4)