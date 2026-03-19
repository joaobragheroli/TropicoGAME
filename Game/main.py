import pygame, sys
from map import Map
from building import Building
from npc import NPC
from boat import Boat
from trees import TreeManager

pygame.init()

# Configuracoes
TILE_SIZE = 16
MAP_WIDTH = 46
MAP_HEIGHT = 36
SCREEN_WIDTH = MAP_WIDTH * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ilha Tropico Simplificada")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 30)

# Objetos
game_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, tile_size=TILE_SIZE)
trees = TreeManager(game_map.grid, tile_size=TILE_SIZE)
buildings = []
npcs = [NPC(game_map.grid) for _ in range(12)]
boat = Boat(tile_size=TILE_SIZE)

# Recursos iniciais
population = 0
food = 100
money = 500

# Loop principal
while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    for npc in npcs:
        npc.update()
    boat.update()

    # Desenhar tudo
    screen.fill((0, 0, 0))
    game_map.draw(screen)
    trees.draw(screen)        # arvores ficam sobre o mapa mas abaixo dos NPCs
    boat.draw(screen)
    for building in buildings:
        building.draw(screen)
    for npc in npcs:
        npc.draw(screen)

    # Mostrar recursos
    pop_text   = font.render(f"Population: {population}", True, (0, 0, 0))
    food_text  = font.render(f"Food: {food}",             True, (0, 0, 0))
    money_text = font.render(f"Money: {money}",           True, (0, 0, 0))
    screen.blit(pop_text,   (10, 10))
    screen.blit(food_text,  (10, 40))
    screen.blit(money_text, (10, 70))

    pygame.display.flip()