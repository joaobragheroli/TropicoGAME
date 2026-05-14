import pygame, sys, os, math
from utils import resource_path
from map import Map
from building import Building, BuildingSystem, BUILDING_TYPES
from npc import NPC
from boat import Boat
from trees import TreeManager, TREE_POSITIONS
from events import AlertaEvento, disparar_evento_aleatorio
from rival_ai import RivalAI

def run_game():
    pygame.init()

    # Configuracoes
    TILE_SIZE    = 16
    MAP_WIDTH    = 46
    MAP_HEIGHT   = 36
    SCREEN_WIDTH  = MAP_WIDTH  * TILE_SIZE
    SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

    # --- FULL SCREEN ---
    pygame.display.quit()
    pygame.display.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Ilha Tropico Simplificada")
    clock  = pygame.time.Clock()
    
    font   = pygame.font.SysFont("segoeui", 26, bold=True)
    small_font = pygame.font.SysFont("segoeui", 18, bold=True)

    # Objetos do jogo
    game_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, tile_size=TILE_SIZE)
    trees    = TreeManager(game_map.grid, tile_size=TILE_SIZE)
    buildings = []
    npcs     = [NPC(game_map.grid) for _ in range(12)]
    boat     = Boat(tile_size=TILE_SIZE)

    # Sistema de construção
    build_sys = BuildingSystem(game_map.grid, tile_size=TILE_SIZE)
    build_sys.register_trees(TREE_POSITIONS)
    build_sys.set_tree_manager(trees)

    # Rival
    rival = RivalAI(game_map.grid, tile_size=TILE_SIZE)
    rival_score   = 0
    player_score  = 0

    # Eventos Customizados
    PROD_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(PROD_EVENT, 1000) 

    BOAT_SPAWN_EVENT = pygame.USEREVENT + 2
    # Barco não usa mais timer inicial, controlado pelo ciclo do dia

    # Alerta de Eventos
    alerta_sistema = AlertaEvento(SCREEN_WIDTH, SCREEN_HEIGHT)
    RANDOM_EVENT_TIMER = pygame.USEREVENT + 3
    pygame.time.set_timer(RANDOM_EVENT_TIMER, 30000) 

    # Recursos iniciais
    population = 12
    food       = 50.0
    money      = 150.0   
    has_traded = False
    happiness  = 0     
    event_happiness_modifier = 0  
    boat_dock_time = 0 # Para auto-partida

    # Game Over logic
    game_over       = False
    game_over_cause = ""
    game_start_time = pygame.time.get_ticks()
    UNHAPPY_LIMIT   = 30_000   
    unhappy_since   = None     

    # Sistema de Dia e Noite
    game_time = 6.0
    day_count = 1
    boat_has_spawned_today = False

    # Loop principal
    while True:
        dt = clock.tick(60) / 1000.0

        # Atualizar tempo do jogo
        if 6.0 <= game_time < 18.0:
            # Dia = 45 segundos reais para 12 horas do jogo
            game_time += (12.0 / 45.0) * dt
            is_night = False
        else:
            # Noite = 15 segundos reais para 12 horas do jogo
            game_time += (12.0 / 15.0) * dt
            is_night = True
            
        if game_time >= 24.0:
            game_time -= 24.0
            day_count += 1
            boat_has_spawned_today = False
            
        if day_count >= 2 and game_time >= 6.0 and not boat_has_spawned_today:
            pygame.event.post(pygame.event.Event(BOAT_SPAWN_EVENT))
            boat_has_spawned_today = True

        for npc in npcs:
            npc.is_night = is_night

        if game_over:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return 
                    if ev.key == pygame.K_r:
                        run_game() 
                        return
            screen.fill((0, 0, 0))
            game_map.draw(screen)
            draw_game_over(screen, font, game_over_cause, happiness, population,
                           pygame.time.get_ticks() - game_start_time)
            pygame.display.flip()
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not build_sys.selected and not build_sys.demolish_mode:
                    return 

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                _dbg = pygame.Rect(SCREEN_WIDTH - 115, 10, 105, 28)
                if _dbg.collidepoint(event.pos):
                    game_over       = True
                    game_over_cause = "Forçado pelo desenvolvedor"

                _dbg_ev = pygame.Rect(SCREEN_WIDTH - 115, 45, 105, 28)
                if _dbg_ev.collidepoint(event.pos):
                    ev = disparar_evento_aleatorio(alerta_sistema)
                    money += ev["efeito"]["money"]
                    food += ev["efeito"]["food"]
                    event_happiness_modifier += ev["efeito"]["happiness"]
                
                _dbg_skip = pygame.Rect(SCREEN_WIDTH - 115, 80, 105, 28)
                if _dbg_skip.collidepoint(event.pos):
                    game_time = 6.0
                    day_count += 1
                    boat_has_spawned_today = False
                    
                alerta_sistema.checar_clique(event.pos)
                
            if event.type == RANDOM_EVENT_TIMER:
                if day_count % 2 == 0:
                    ev = disparar_evento_aleatorio(alerta_sistema)
                    money += ev["efeito"]["money"]
                    food += ev["efeito"]["food"]
                    event_happiness_modifier += ev["efeito"]["happiness"]

            if event.type == BOAT_SPAWN_EVENT:
                boat.reset_position() # Garante que volta pro fundo da tela
                boat.state = "sailing"
                has_traded = False

            if event.type == PROD_EVENT:
                assign_housing_and_jobs(npcs, buildings)

                for b in buildings:
                    if b.btype == "farm" and b.active:
                        food += 8.0 / 5.0
                    if b.btype == "factory" and b.active:
                        money += 20.0 / 5.0

                food = max(0.0, food - (population / 15.0))

                total    = len(npcs)
                housed   = sum(1 for n in npcs if n.has_home)
                employed = sum(1 for n in npcs if n.has_job)
                food_ratio      = min(1.0, food / max(1, population * 2))
                housing_score   = (housed   / total) if total > 0 else 0.0
                job_score       = (employed / total) if total > 0 else 0.0
                
                happiness = int(housing_score * 50 + job_score * 15 + food_ratio * 35) + event_happiness_modifier
                happiness = max(0, min(100, happiness))

                for npc in npcs:
                    npc.update_social(food_ratio, event_happiness_modifier)

                if event_happiness_modifier > 0:
                    event_happiness_modifier -= 2
                elif event_happiness_modifier < 0:
                    event_happiness_modifier += 2

                rival.update_economy(buildings)

                p_houses    = sum(1 for b in buildings if b.btype == "house"   and b.owner == "player")
                p_factories = sum(1 for b in buildings if b.btype == "factory" and b.owner == "player")
                r_houses    = sum(1 for b in buildings if b.btype == "house"   and b.owner == "rival")
                r_factories = sum(1 for b in buildings if b.btype == "factory" and b.owner == "rival")
                player_score = int(food * 0.5 + p_houses * 5 * 0.5 + p_factories * 3)
                rival_score  = int(rival.food * 0.5 + r_houses * 5 * 0.5 + r_factories * 3)

                _now = pygame.time.get_ticks()
                if day_count >= 3:
                    if happiness < 50:
                        if unhappy_since is None:
                            unhappy_since = _now
                        elif _now - unhappy_since >= UNHAPPY_LIMIT:
                            game_over       = True
                            game_over_cause = "O povo ficou infeliz por tempo demais!"
                    else:
                        unhappy_since = None

            free_workers = sum(1 for n in npcs if not n.has_job)
            
            built = False
            if not alerta_sistema.active:
                built = build_sys.handle_event(event, buildings, money, free_workers)
                
            if built:
                dm, dp, df = build_sys.flush_effects()
                money      += dm
                population += dp
                food       += df
                
                # Sincroniza NPCs visuais com a população
                if dp > 0:
                    for _ in range(dp):
                        npcs.append(NPC(game_map.grid))
                elif dp < 0:
                    for _ in range(min(len(npcs), -dp)):
                        npcs.pop()

        if boat.is_docked:
            if not has_traded:
                if food > 25:
                    export = food - 25
                    money += export * 4
                    food = 25
                    has_traded = True
                    boat.leave()
                    pygame.time.set_timer(BOAT_SPAWN_EVENT, 45000, loops=1)
                else:
                    # Auto-partida após 30 segundos se não tiver comida
                    boat_dock_time += 1
                    if boat_dock_time > 60 * 30:
                        boat.leave()
                        pygame.time.set_timer(BOAT_SPAWN_EVENT, 45000, loops=1)
                        has_traded = True # Impede de tentar vender enquanto sai
            else:
                boat_dock_time = 0
        else:
            boat_dock_time = 0

        for npc in npcs:
            npc.update()
        boat.update()

        rival_action = rival.think(
            player_stats={"food": food, "money": money},
            buildings=buildings
        )
        if rival_action:
            new_b = Building(
                rival_action["x"], rival_action["y"],
                rival_action["type"],
                tile_size=TILE_SIZE,
                owner="rival"
            )
            buildings.append(new_b)
            rival.register_building(new_b)
            rival.money -= rival_action["cost"]

        screen.fill((0, 0, 0))
        game_map.draw(screen)
        trees.draw(screen)
        boat.draw(screen)
        for b in buildings:
            b.draw(screen)
        for npc in npcs:
            npc.draw(screen)

        # Ciclo Dia/Noite Visual
        # Escurece gradualmente à noite (18h às 6h)
        if is_night:
            if game_time >= 18.0:
                # 18.0 até 24.0
                progress = (game_time - 18.0) / 6.0
            else:
                # 0.0 até 6.0
                progress = (game_time + 6.0) / 12.0
            
            # Curva de escurecimento (máximo no meio da noite)
            darkness = math.sin(progress * math.pi)
            if darkness > 0:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                alpha = int(darkness * 160) 
                overlay.fill((10, 10, 40, alpha)) 
                screen.blit(overlay, (0, 0))

        build_sys.draw_preview(screen)

        # HUD
        hud_w, hud_h = 240, 135
        hud_panel = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_panel, (15, 15, 25, 200), hud_panel.get_rect(), border_radius=12)
        pygame.draw.rect(hud_panel, (255, 215, 0, 150), hud_panel.get_rect(), 2, border_radius=12)
        screen.blit(hud_panel, (10, 10))

        hud_texts = [
            (f"👥 Pop: {population}", (255, 255, 255)),
            (f"🍞 Comida: {int(food)}", (150, 255, 150)),
            (f"💰 Tesouro: ${int(money)}", (255, 215, 0))
        ]
        
        for i, (txt, color) in enumerate(hud_texts):
            sh_t = font.render(txt, True, (0, 0, 0))
            screen.blit(sh_t, (22, 22 + i * 32))
            s_t = font.render(txt, True, color)
            screen.blit(s_t, (20, 20 + i * 32))

        happy_label = small_font.render(f"Felicidade: {happiness}%", True, (220, 220, 220))
        screen.blit(happy_label, (20, 110))


        bar_x, bar_y, bar_w, bar_h = 20, 128, 220, 8
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
        fill_w = max(0, int(bar_w * happiness / 100))
        if happiness < 35:
            bar_color = (210,  55,  55)
        elif happiness < 65:
            bar_color = (220, 180,  40)
        else:
            bar_color = ( 60, 200,  90)
        if fill_w > 0:
            rad_h = min(4, fill_w // 2, bar_h // 2)
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=rad_h)
        pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

        total_npc  = len(npcs)
        housed_cnt = sum(1 for n in npcs if n.has_home)
        alert_y    = 145 
        alert_font = pygame.font.SysFont("segoeui", 18, bold=True)
        if housed_cnt < total_npc:
            sem_casa = alert_font.render(f"! {total_npc - housed_cnt} sem abrigo", True, (255, 100, 100))
            screen.blit(sem_casa, (15, alert_y))
            alert_y += 16
        if food == 0:
            sem_comida = alert_font.render("! Sem comida", True, (255, 60, 60))
            screen.blit(sem_comida, (15, alert_y))
            alert_y += 16

        draw_rivalry_bar(screen, small_font, player_score, rival_score, SCREEN_WIDTH)
        build_sys.draw_hud(screen, font, money)
        alerta_sistema.desenhar(screen)

        # Botões de Debug (Canto Superior Direito)
        _df = pygame.font.SysFont(None, 18)
        
        # Botão Force Game Over
        _dbg_rect = pygame.Rect(SCREEN_WIDTH - 115, 10, 105, 28)
        pygame.draw.rect(screen, (80, 15, 15), _dbg_rect, border_radius=4)
        pygame.draw.rect(screen, (180, 45, 45), _dbg_rect, 1, border_radius=4)
        _dbg_t = _df.render("[DEV] FORCE GO", True, (220, 80, 80))
        screen.blit(_dbg_t, (_dbg_rect.centerx - _dbg_t.get_width() // 2, _dbg_rect.centery - _dbg_t.get_height() // 2))

        # Botão Force Evento
        _dbg_ev_rect = pygame.Rect(SCREEN_WIDTH - 115, 45, 105, 28)
        pygame.draw.rect(screen, (15, 40, 80), _dbg_ev_rect, border_radius=4)
        pygame.draw.rect(screen, (45, 120, 180), _dbg_ev_rect, 1, border_radius=4)
        _dbg_ev_t = _df.render("[DEV] EVENTO", True, (80, 180, 220))
        screen.blit(_dbg_ev_t, (_dbg_ev_rect.centerx - _dbg_ev_t.get_width() // 2, _dbg_ev_rect.centery - _dbg_ev_t.get_height() // 2))

        # Botão Skip Dia
        # _dbg_skip_rect = pygame.Rect(SCREEN_WIDTH - 115, 80, 105, 28)
        # pygame.draw.rect(screen, (40, 80, 15), _dbg_skip_rect, border_radius=4)
        # pygame.draw.rect(screen, (120, 180, 45), _dbg_skip_rect, 1, border_radius=4)
        # _dbg_skip_t = _df.render("[DEV] SKIP DIA", True, (180, 220, 80))
        # screen.blit(_dbg_skip_t, (_dbg_skip_rect.centerx - _dbg_skip_t.get_width() // 2, _dbg_skip_rect.centery - _dbg_skip_t.get_height() // 2))

        # Adicionar Dia e Hora (Abaixo dos botões de debug)
        time_hours = int(game_time)
        clock_str = f"Dia {day_count} - {time_hours:02d}h"
        clock_label = small_font.render(clock_str, True, (200, 220, 255))
        screen.blit(clock_label, (SCREEN_WIDTH - clock_label.get_width() - 10, 115))
        
        pygame.display.flip()

# As funções auxiliares (draw_rivalry_bar, assign_housing_and_jobs, draw_game_over) permanecem iguais.
def draw_rivalry_bar(screen, font, player_score, rival_score, screen_width):
    bar_w  = 280
    bar_h  = 18
    bar_x  = screen_width // 2 - bar_w // 2
    bar_y  = 8
    panel = pygame.Surface((bar_w + 80, bar_h + 24), pygame.SRCALPHA)
    panel.fill((10, 10, 20, 200))
    screen.blit(panel, (bar_x - 40, bar_y - 4))
    total = max(1, player_score + rival_score)
    p_frac = player_score / total
    r_frac = rival_score  / total
    p_w = max(0, int(bar_w * p_frac) - 2)
    if p_w > 0:
        rad_p = min(3, p_w // 2, bar_h // 2)
        pygame.draw.rect(screen, (50, 120, 230), (bar_x, bar_y, p_w, bar_h), border_radius=rad_p)
    r_w = max(0, int(bar_w * r_frac) - 2)
    if r_w > 0:
        rad_r = min(3, r_w // 2, bar_h // 2)
        rx = bar_x + bar_w - r_w
        pygame.draw.rect(screen, (210, 45, 45), (rx, bar_y, r_w, bar_h), border_radius=rad_r)
    pygame.draw.rect(screen, (150, 150, 180), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)
    lbl_p = font.render("👑 Tu", True, (100, 160, 255))
    lbl_r = font.render("Rival 🔴", True, (255, 100, 100))
    screen.blit(lbl_p, (bar_x - 38, bar_y + 1))
    screen.blit(lbl_r, (bar_x + bar_w + 4, bar_y + 1))

def assign_housing_and_jobs(npcs, buildings):
    for npc in npcs:
        npc.has_home = False
        npc.home_x   = None
        npc.home_y   = None
        npc.has_job  = False
    npc_idx = 0
    for b in buildings:
        cap = BUILDING_TYPES[b.btype].get("capacity", 0)
        for _ in range(cap):
            if npc_idx < len(npcs):
                npcs[npc_idx].has_home = True
                npcs[npc_idx].home_x = b.rect.x
                npcs[npc_idx].home_y = b.rect.y
                npc_idx += 1
    job_idx = 0
    for b in buildings:
        needed = BUILDING_TYPES[b.btype]["workers"]
        if needed == 0:
            b.active = True
            continue
        assigned = 0
        for _ in range(needed):
            if job_idx < len(npcs):
                npcs[job_idx].has_job = True
                job_idx += 1
                assigned += 1
        b.active = (assigned >= needed)

def draw_game_over(screen, font, cause, happiness, population, elapsed_ms):
    sw, sh = screen.get_size()
    overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))
    big_f = pygame.font.SysFont(None, 90)
    mid_f = pygame.font.SysFont(None, 34)
    
    go_t = big_f.render("GAME OVER", True, (220, 45, 45))
    screen.blit(go_t, (sw // 2 - go_t.get_width() // 2, sh // 2 - 80))
    
    cause_t = mid_f.render(cause, True, (200, 200, 200))
    screen.blit(cause_t, (sw // 2 - cause_t.get_width() // 2, sh // 2 + 10))

if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()