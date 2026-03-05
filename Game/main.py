import pygame, sys
from map import Map
from player import Player
from building import Building
from npc import NPC

pygame.init()

# Configurações
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
player = Player(x=(MAP_WIDTH // 2 - 1) * TILE_SIZE, y=(MAP_HEIGHT - 7) * TILE_SIZE)
buildings = []
npcs = [NPC(game_map.grid) for _ in range(12)]

# Recursos iniciais
population = 0
food = 100
money = 500
current_building_type = "house"

# Loop principal
while True:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: current_building_type = "house"
            if event.key == pygame.K_2: current_building_type = "farm"
            if event.key == pygame.K_3: current_building_type = "factory"
            if event.key == pygame.K_SPACE:
                b = Building(player.rect.x, player.rect.y, type=current_building_type)
                buildings.append(b)
                if b.type == "house": population += 5; money -= 50
                elif b.type == "farm": food += 20; money -= 30
                elif b.type == "factory": money += 0

    keys = pygame.key.get_pressed()
    player.move(keys, MAP_WIDTH, MAP_HEIGHT)

    for npc in npcs:
        npc.update()

    # desenhar tudo
    screen.fill((0,0,0))
    game_map.draw(screen)
    for building in buildings:
        building.draw(screen)
    for npc in npcs:
        npc.draw(screen)
    player.draw(screen)

    # mostrar recursos
    pop_text = font.render(f"Population: {population}", True, (0,0,0))
    food_text = font.render(f"Food: {food}", True, (0,0,0))
    money_text = font.render(f"Money: {money}", True, (0,0,0))
    screen.blit(pop_text, (10,10))
    screen.blit(food_text, (10,40))
    screen.blit(money_text, (10,70))

    pygame.display.flip()