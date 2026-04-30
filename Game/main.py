import pygame, sys, os, math
import pygame, sys, os, math
from map import Map
from building import Building, BuildingSystem, BUILDING_TYPES
from npc import NPC
from boat import Boat
from trees import TreeManager, TREE_POSITIONS
from events import AlertaEvento, disparar_evento_aleatorio
from events import AlertaEvento, disparar_evento_aleatorio
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
# Fonte estilizada da v2
font   = pygame.font.SysFont("segoeui", 26, bold=True)
small_font = pygame.font.SysFont("segoeui", 18, bold=True)
# Fonte estilizada da v2
font   = pygame.font.SysFont("segoeui", 26, bold=True)
small_font = pygame.font.SysFont("segoeui", 18, bold=True)

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
build_sys.set_tree_manager(trees)

# Eventos Customizados
PROD_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(PROD_EVENT, 5000) # Produção a cada 5s

BOAT_SPAWN_EVENT = pygame.USEREVENT + 2
# O primeiro barco aparece após 10 segundos de jogo
pygame.time.set_timer(BOAT_SPAWN_EVENT, 10000, loops=1) 

# Alerta de Eventos
alerta_sistema = AlertaEvento(SCREEN_WIDTH, SCREEN_HEIGHT)
RANDOM_EVENT_TIMER = pygame.USEREVENT + 3
pygame.time.set_timer(RANDOM_EVENT_TIMER, 30000) # Evento aleatório a cada 30s
# Recursos iniciais
population = 12
food       = 50
money      = 150   # suficiente para casa ($50) + fazenda ($80)
has_traded = False
happiness  = 0     # 0-100 calculado a cada tick de produção
event_happiness_modifier = 0  # Modificador temporário de eventos

# ── Game Over ────────────────────────────────────────────────────────────────
game_over       = False
game_over_cause = ""
game_start_time = pygame.time.get_ticks()
GRACE_PERIOD    = 80_000   # 80s de graça no início sem penalidade
UNHAPPY_LIMIT   = 30_000   # 30s abaixo de 50% = game over
unhappy_since   = None     # timestamp quando felicidade caiu abaixo de 50%

# ── Funções auxiliares ────────────────────────────────────────────────────────────────────
def assign_housing_and_jobs(npcs, buildings):
    """Atribui moradia e emprego aos NPCs com base nos edifícios existentes."""
    for npc in npcs:
        npc.has_home = False
        npc.has_job  = False

    # Moradia: preenche casas em ordem
    npc_idx = 0
    for b in buildings:
        cap = BUILDING_TYPES[b.btype]["capacity"]
        for _ in range(cap):
            if npc_idx < len(npcs):
                npcs[npc_idx].has_home = True
                npc_idx += 1

    # Emprego: preenche fazendas e fábricas em ordem
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

    big_f   = pygame.font.SysFont(None, 90)
    mid_f   = pygame.font.SysFont(None, 34)
    small_f = pygame.font.SysFont(None, 24)

    pw, ph = 520, 290
    px, py = sw // 2 - pw // 2, sh // 2 - ph // 2
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((18, 8, 8, 240))
    screen.blit(panel, (px, py))
    pygame.draw.rect(screen, (180, 35, 35), (px, py, pw, ph), 2, border_radius=10)
    pygame.draw.rect(screen, (100, 20, 20), (px+2, py+2, pw-4, ph-4), 1, border_radius=9)

    go_t = big_f.render("GAME OVER", True, (220, 45, 45))
    screen.blit(go_t, (sw // 2 - go_t.get_width() // 2, py + 18))

    pygame.draw.line(screen, (120, 30, 30), (px + 20, py + 100), (px + pw - 20, py + 100), 1)

    cause_t = mid_f.render(cause, True, (210, 170, 170))
    screen.blit(cause_t, (sw // 2 - cause_t.get_width() // 2, py + 110))

    mins = elapsed_ms // 60000
    secs = (elapsed_ms % 60000) // 1000
    stats = [
        f"Tempo jogado: {mins}m {secs}s",
        f"Felicidade final: {happiness}%",
        f"Populacao: {population}",
    ]
    for j, s in enumerate(stats):
        st = small_f.render(s, True, (170, 145, 145))
        screen.blit(st, (sw // 2 - st.get_width() // 2, py + 148 + j * 22))

    pygame.draw.line(screen, (100, 30, 30), (px + 20, py + 248), (px + pw - 20, py + 248), 1)
    inst = small_f.render("R  -  Reiniciar       ESC  -  Sair", True, (140, 130, 160))
    screen.blit(inst, (sw // 2 - inst.get_width() // 2, py + 258))


# ── Loop principal ─────────────────────────────────────────────────────────────
while True:
    clock.tick(60)

    # ── Tela de Game Over ──────────────────────────────────────────────────────
    if game_over:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if ev.key == pygame.K_r:
                    os.execl(sys.executable, sys.executable, *sys.argv)
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
        
        # Tecla ESC para sair do Fullscreen rapidamente
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not build_sys.selected and not build_sys.demolish_mode:
                pygame.quit()
                sys.exit()

        # Botão de debug Force Game Over
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            _dbg = pygame.Rect(SCREEN_WIDTH - 115, 10, 105, 28)
            if _dbg.collidepoint(event.pos):
                game_over       = True
                game_over_cause = "Forçado pelo desenvolvedor"

        # Botão de debug Force Evento
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            _dbg_ev = pygame.Rect(SCREEN_WIDTH - 115, 45, 105, 28)
            if _dbg_ev.collidepoint(event.pos):
                ev = disparar_evento_aleatorio(alerta_sistema)
                money += ev["efeito"]["money"]
                food += ev["efeito"]["food"]
                event_happiness_modifier += ev["efeito"]["happiness"]
                achievements.add_xp(100) # Bônus por lidar com evento!
            
            # Checar clique no alerta
            alerta_sistema.checar_clique(event.pos)

        # Evento Aleatório
        if event.type == RANDOM_EVENT_TIMER:
            ev = disparar_evento_aleatorio(alerta_sistema)
            money += ev["efeito"]["money"]
            food += ev["efeito"]["food"]
            event_happiness_modifier += ev["efeito"]["happiness"]

        # Gatilho de novo navio
        if event.type == BOAT_SPAWN_EVENT:
            boat.state = "sailing"
            has_traded = False

        # Produção Passiva
        if event.type == PROD_EVENT:
            assign_housing_and_jobs(npcs, buildings)

            # Produção só em edifícios ativos (com trabalhadores)
            for b in buildings:
                if b.btype == "farm" and b.active:
                    food += 8
                if b.btype == "factory" and b.active:
                    money += 20

            # Consumo da população
            food = max(0, food - (population // 3))

            # Felicidade global
            total    = len(npcs)
            housed   = sum(1 for n in npcs if n.has_home)
            employed = sum(1 for n in npcs if n.has_job)
            food_ratio      = min(1.0, food / max(1, population * 2))
            housing_score   = (housed   / total) if total > 0 else 0.0
            job_score       = (employed / total) if total > 0 else 0.0
            
            # Nova fórmula: 50% abrigo, 35% comida, 15% trabalho
            happiness = int(housing_score * 50 + job_score * 15 + food_ratio * 35) + event_happiness_modifier
            happiness = max(0, min(100, happiness))

            for npc in npcs:
                npc.update_social(food_ratio, event_happiness_modifier)

            # Decaimento do modificador de evento (volta a 0 gradualmente)
            if event_happiness_modifier > 0:
                event_happiness_modifier -= 2
            elif event_happiness_modifier < 0:
                event_happiness_modifier += 2

            # ── Rastrear infelicidade prolongada ─────────────────────────────
            _now = pygame.time.get_ticks()
            _in_grace = (_now - game_start_time) < GRACE_PERIOD
            if not _in_grace:
                if happiness < 50:
                    if unhappy_since is None:
                        unhappy_since = _now
                    elif _now - unhappy_since >= UNHAPPY_LIMIT:
                        game_over       = True
                        game_over_cause = "O povo ficou infeliz por tempo demais!"
                else:
                    unhappy_since = None

        # Sistema de construção
        # Trabalhadores livres = NPCs sem emprego (baseado na última atribuição)
        free_workers = sum(1 for n in npcs if not n.has_job)
        
        # Só permite construção se não houver alerta ativo
        built = False
        if not alerta_sistema.active:
            built = build_sys.handle_event(event, buildings, money, free_workers)
            
        if built:
            dm, dp, df = build_sys.flush_effects()
            money      += dm
            population += dp
            food       += df
            achievements.add_xp(abs(dm)) # XP proporcional ao custo da construção

    # LÓGICA DE EXPORTAÇÃO E PARTIDA
    if boat.is_docked and not has_traded:
        if food > 25:
            export = food - 25
            money += export * 4
            food = 25
            has_traded = True
            achievements.add_xp(export * 3) # XP por exportação
            
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

    # ── Ciclo Dia/Noite (v2) ──────────────────────────────────────────────────
    time_ms = pygame.time.get_ticks()
    # Ciclo de 60 segundos
    cycle = (time_ms % 60000) / 60000.0
    # Senoide para suavidade (Noite no meio do ciclo)
    darkness = max(0, math.sin(cycle * math.pi * 2 - math.pi/2)) 
    if darkness > 0:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = int(darkness * 140) # Máximo 140 para não ficar 100% preto
        overlay.fill((10, 10, 40, alpha)) # Tom azul escuro
        screen.blit(overlay, (0, 0))

    build_sys.draw_preview(screen)

    # ── HUD ───────────────────────────────────────────
    # Painel estilizado da v2
    hud_w, hud_h = 240, 135
    hud_panel = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
    pygame.draw.rect(hud_panel, (15, 15, 25, 200), hud_panel.get_rect(), border_radius=12)
    pygame.draw.rect(hud_panel, (255, 215, 0, 150), hud_panel.get_rect(), 2, border_radius=12)
    screen.blit(hud_panel, (10, 10))



    # Textos com Sombra e Emojis
    hud_texts = [
        (f"👥 Pop: {population}", (255, 255, 255)),
        (f"🍞 Comida: {food}", (150, 255, 150)),
        (f"💰 Tesouro: ${money}", (255, 215, 0))
    ]
    
    for i, (txt, color) in enumerate(hud_texts):
        # Sombra
        sh_t = font.render(txt, True, (0, 0, 0))
        screen.blit(sh_t, (22, 22 + i * 32))
        # Principal
        s_t = font.render(txt, True, color)
        screen.blit(s_t, (20, 20 + i * 32))

    # Barra de felicidade integrada ao novo HUD
    happy_label = small_font.render(f"Felicidade: {happiness}%", True, (220, 220, 220))
    screen.blit(happy_label, (20, 110))
    bar_x, bar_y, bar_w, bar_h = 20, 128, 220, 8
    # ... (Barra será desenhada abaixo)
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
    fill_w = max(0, int(bar_w * happiness / 100))
    if happiness < 35:
        bar_color = (210,  55,  55)
    elif happiness < 65:
        bar_color = (220, 180,  40)
    else:
        bar_color = ( 60, 200,  90)
    if fill_w > 0:
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
    pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=4)

    # Alertas de moradia / comida (Abaixo do HUD)
    total_npc  = len(npcs)
    housed_cnt = sum(1 for n in npcs if n.has_home)
    alert_y    = 145 # Abaixo do painel HUD
    alert_font = pygame.font.SysFont("segoeui", 18, bold=True)
    if housed_cnt < total_npc:
        sem_casa = alert_font.render(
            f"! {total_npc - housed_cnt} sem abrigo  (construa casas!)",
            True, (255, 100, 100))
        screen.blit(sem_casa, (15, alert_y))
        alert_y += 16
    if food == 0:
        sem_comida = alert_font.render("! Sem comida  (povo faminto!)", True, (255, 60, 60))
        screen.blit(sem_comida, (15, alert_y))
        alert_y += 16

    # Aviso de graça / perigo de game over
    _now_hud = pygame.time.get_ticks()
    _grace_rem = GRACE_PERIOD - (_now_hud - game_start_time)
    if _grace_rem > 0:
        gr_s = _grace_rem // 1000 + 1
        grace_t = alert_font.render(f"Tempo de graca: {gr_s}s", True, (100, 200, 255))
        screen.blit(grace_t, (15, alert_y))
    elif unhappy_since is not None and happiness < 50:
        _danger = max(0, UNHAPPY_LIMIT - (_now_hud - unhappy_since))
        dr_s = _danger // 1000 + 1
        danger_t = alert_font.render(
            f"! PERIGO: game over em {dr_s}s se nao melhorar!",
            True, (255, 50, 50))
        screen.blit(danger_t, (15, alert_y))

    # Botão de debug Force Game Over (remover depois)
    _df = pygame.font.SysFont(None, 19)
    _dbg_rect = pygame.Rect(SCREEN_WIDTH - 115, 10, 105, 28)
    pygame.draw.rect(screen, (80, 15, 15), _dbg_rect, border_radius=4)
    pygame.draw.rect(screen, (180, 45, 45), _dbg_rect, 1, border_radius=4)
    _dbg_t = _df.render("[DEV] FORCE GO", True, (220, 80, 80))
    screen.blit(_dbg_t, (_dbg_rect.centerx - _dbg_t.get_width() // 2,
                          _dbg_rect.centery - _dbg_t.get_height() // 2))

    # Botão de debug Force Evento
    _dbg_ev_rect = pygame.Rect(SCREEN_WIDTH - 115, 45, 105, 28)
    pygame.draw.rect(screen, (15, 40, 80), _dbg_ev_rect, border_radius=4)
    pygame.draw.rect(screen, (45, 120, 180), _dbg_ev_rect, 1, border_radius=4)
    _dbg_ev_t = _df.render("[DEV] EVENTO", True, (80, 180, 220))
    screen.blit(_dbg_ev_t, (_dbg_ev_rect.centerx - _dbg_ev_t.get_width() // 2,
                             _dbg_ev_rect.centery - _dbg_ev_t.get_height() // 2))

    achievements.draw(screen, cycle)
    build_sys.draw_hud(screen, font, money)

    # Desenha o alerta por cima de tudo
    alerta_sistema.desenhar(screen)
    
    pygame.display.flip()