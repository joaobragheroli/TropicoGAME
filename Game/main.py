import pygame, sys
from map import Map
from building import Building, BuildingSystem
from npc import NPC
from boat import Boat
from trees import TreeManager, TREE_POSITIONS

pygame.init()

# Configuracoes
TILE_SIZE    = 16
MAP_WIDTH    = 46
MAP_HEIGHT   = 36
SCREEN_WIDTH  = MAP_WIDTH  * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

# --- FULL SCREEN ---
# Usamos SCALED para que o Pygame estique a imagem para preencher o monitor mantendo o aspecto
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Ilha Tropico Simplificada")
clock  = pygame.time.Clock()
font   = pygame.font.SysFont(None, 24)

# Objetos do jogo
game_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, tile_size=TILE_SIZE)
trees    = TreeManager(game_map.grid, tile_size=TILE_SIZE)
buildings = []
npcs     = [NPC(game_map.grid) for _ in range(12)]
boat     = Boat(tile_size=TILE_SIZE)

# Sistema de construção
build_sys = BuildingSystem(game_map.grid, tile_size=TILE_SIZE)
build_sys.register_trees(TREE_POSITIONS)

# Eventos Customizados
PROD_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(PROD_EVENT, 5000) # Produção a cada 5s

BOAT_SPAWN_EVENT = pygame.USEREVENT + 2
# O primeiro barco aparece após 10 segundos de jogo
pygame.time.set_timer(BOAT_SPAWN_EVENT, 10000, loops=1) 

# Recursos iniciais
population = 12
food       = 50
money      = 500
has_traded = False

# ── Loop principal ─────────────────────────────────────────────────────────────
while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # Tecla ESC para sair do Fullscreen rapidamente
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not build_sys.selected:
                pygame.quit()
                sys.exit()

        # Gatilho de novo navio
        if event.type == BOAT_SPAWN_EVENT:
            boat.state = "sailing"
            has_traded = False

        # Produção Passiva
        if event.type == PROD_EVENT:
            farm_count = sum(1 for b in buildings if b.btype == "farm")
            food += farm_count * 8
            # Consumo da população
            food = max(0, food - (population // 3))

        # Sistema de construção
        built = build_sys.handle_event(event, buildings, money)
        if built:
            dm, dp, df = build_sys.flush_effects()
            money      += dm
            population += dp
            food       += df

    # LÓGICA DE EXPORTAÇÃO E PARTIDA
    if boat.is_docked and not has_traded:
        if food > 25:
            export = food - 25
            money += export * 4
            food = 25
            has_traded = True
            
            # Comanda a saída do navio
            boat.leave()
            
            # Agenda o próximo navio para daqui a 45 segundos
            pygame.time.set_timer(BOAT_SPAWN_EVENT, 45000, loops=1)

    # Atualizações
    for npc in npcs:
        npc.update()
    boat.update()

    # Desenho
    screen.fill((0, 0, 0))
    game_map.draw(screen)
    trees.draw(screen)
    boat.draw(screen)
    for b in buildings:
        b.draw(screen)
    for npc in npcs:
        npc.draw(screen)

    build_sys.draw_preview(screen)

    # HUD
    pop_t   = font.render(f"Pop: {population}", True, (255, 255, 255))
    food_t  = font.render(f"Comida: {food}",     True, (150, 255, 150))
    money_t = font.render(f"Tesouro: ${money}",  True, (255, 255, 0))
    screen.blit(pop_t,   (15, 15))
    screen.blit(food_t,  (15, 40))
    screen.blit(money_t, (15, 65))

    build_sys.draw_hud(screen, font, money)
    pygame.display.flip()