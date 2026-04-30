import pygame, sys, math
from map import Map
from building import Building, BuildingSystem
from npc import NPC
from boat import Boat
from trees import TreeManager, TREE_POSITIONS
from achievements import AchievementSystem

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
font   = pygame.font.SysFont("segoeui", 26, bold=True)

# Objetos do jogo
game_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, tile_size=TILE_SIZE)
trees    = TreeManager(game_map.grid, tile_size=TILE_SIZE)
buildings = []
npcs     = [NPC(game_map.grid) for _ in range(12)]
boat     = Boat(tile_size=TILE_SIZE)
achievements = AchievementSystem()

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
            achievements.add_xp(abs(dm)) # Add XP based on construction cost!

    # LÓGICA DE EXPORTAÇÃO E PARTIDA
    if boat.is_docked and not has_traded:
        if food > 25:
            export = food - 25
            money += export * 4
            food = 25
            has_traded = True
            achievements.add_xp(export * 2) # Add XP for trading!
            
            # Comanda a saída do navio
            boat.leave()
            
            # Agenda o próximo navio para daqui a 45 segundos
            pygame.time.set_timer(BOAT_SPAWN_EVENT, 45000, loops=1)

    # Atualizações
    for npc in npcs:
        npc.update()
    boat.update()
    achievements.update(population, money, food)

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

    # Day / Night Cycle Overlay
    time_ms = pygame.time.get_ticks()
    # 1 minuto = 60000 ms. So cycle = time_ms % 60000 / 60000.0
    cycle = (time_ms % 60000) / 60000.0
    # Use sine wave for smooth transition. Peak night at cycle=0.5
    darkness = max(0, math.sin(cycle * math.pi * 2 - math.pi/2)) 
    if darkness > 0:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = int(darkness * 140) # Max darkness alpha is 140 (not pitch black)
        overlay.fill((10, 10, 40, alpha)) # Deep purple/blue night tint
        screen.blit(overlay, (0, 0))



    # HUD - Fundo do HUD
    hud_panel = pygame.Surface((220, 110), pygame.SRCALPHA)
    pygame.draw.rect(hud_panel, (20, 20, 30, 200), hud_panel.get_rect(), border_radius=10)
    pygame.draw.rect(hud_panel, (200, 180, 50, 255), hud_panel.get_rect(), 2, border_radius=10)
    screen.blit(hud_panel, (10, 10))

    # Textos com sombra
    texts = [
        (f"👥 Pop: {population}", (255, 255, 255)),
        (f"🍞 Comida: {food}", (150, 255, 150)),
        (f"💰 Tesouro: ${money}", (255, 215, 0))
    ]
    
    for i, (txt, color) in enumerate(texts):
        # Sombra
        shadow = font.render(txt, True, (0, 0, 0))
        screen.blit(shadow, (22, 22 + i * 30))
        # Texto principal
        surf = font.render(txt, True, color)
        screen.blit(surf, (20, 20 + i * 30))

    achievements.draw(screen, cycle)

    build_sys.draw_hud(screen, font, money)
    pygame.display.flip()