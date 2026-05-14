import pygame
import sys
import os

# Adiciona o diretório principal ao sys.path para importar modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from map import Map
from building import Building, BuildingSystem, BUILDING_TYPES
from npc import NPC
from boat import Boat
from trees import TreeManager, TREE_POSITIONS

class TutorialModal:
    """Uma caixa de diálogo para guiar o jogador durante o tutorial."""
    def __init__(self, title, text_lines, buttons=None):
        self.title = title
        self.text_lines = text_lines
        self.buttons = buttons or []  # Ex: [{"text": "OK", "color": (r,g,b), "id": "btn1"}]
        self.active = True
        self.result = None
        self.btn_rects = []

    def draw(self, screen, font_title, font_text):
        sw, sh = screen.get_size()
        
        # Fundo escurecido
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        # Caixa do modal
        mw, mh = 640, max(300, 150 + len(self.text_lines)*30 + 80)
        mx, my = sw//2 - mw//2, sh//2 - mh//2
        rect = pygame.Rect(mx, my, mw, mh)
        
        pygame.draw.rect(screen, (30, 40, 60), rect, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=15)

        # Título
        t_surf = font_title.render(self.title, True, (255, 215, 0))
        screen.blit(t_surf, (mx + mw//2 - t_surf.get_width()//2, my + 20))

        # Textos
        ty = my + 80
        for line in self.text_lines:
            ln_surf = font_text.render(line, True, (240, 240, 240))
            screen.blit(ln_surf, (mx + mw//2 - ln_surf.get_width()//2, ty))
            ty += 35

        # Botões
        if self.buttons:
            bw = 160
            bh = 45
            total_w = len(self.buttons) * bw + (len(self.buttons)-1) * 20
            bx_start = mx + mw//2 - total_w//2
            by = my + mh - 70
            
            self.btn_rects = []
            for i, btn in enumerate(self.buttons):
                br = pygame.Rect(bx_start + i*(bw+20), by, bw, bh)
                self.btn_rects.append((br, btn))
                pygame.draw.rect(screen, btn.get("color", (100, 100, 100)), br, border_radius=8)
                pygame.draw.rect(screen, (255, 255, 255), br, 2, border_radius=8)
                
                b_surf = font_text.render(btn["text"], True, (255,255,255))
                screen.blit(b_surf, (br.centerx - b_surf.get_width()//2, br.centery - b_surf.get_height()//2))

    def handle_click(self, pos):
        if not self.active or not self.buttons:
            return False
        for br, btn in self.btn_rects:
            if br.collidepoint(pos):
                self.result = btn["id"]
                self.active = False
                return True
        return True # Se clicou fora do botão mas o modal tá ativo, consome o clique pra não construir sem querer

def run_tutorial(screen_arg, width_arg, height_arg):
    """
    Roda a tela de tutorial.
    Separado do resto do código para evitar conflitos de merge.
    """
    # Guardamos os dados originais para restaurar quando fechar o tutorial
    orig_building_types = BUILDING_TYPES.copy()

    # Adicionamos o "Porto" dinamicamente apenas para o tutorial
    if "port" not in BUILDING_TYPES:
        BUILDING_TYPES["port"] = {
            "label":    "Porto",
            "color":    (80, 80, 200),
            "roof":     (50, 50, 150),
            "cost":     0,
            "size":     3,
            "pop":      0,
            "food":     0,
            "income":   0,
            "capacity": 0,
            "workers":  0,
        }

    # Configurações do Mapa
    TILE_SIZE = 16
    MAP_WIDTH = 46
    MAP_HEIGHT = 36
    SCREEN_WIDTH  = MAP_WIDTH  * TILE_SIZE
    SCREEN_HEIGHT = MAP_HEIGHT * TILE_SIZE

    # Reconfigura o vídeo para ficar igual ao jogo principal (escala inteira fullscreen)
    pygame.display.quit()
    pygame.display.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Tutorial - Tropico Island")
    clock = pygame.time.Clock()
    
    # Fontes
    font_title = pygame.font.SysFont("segoeui", 34, bold=True)
    font_text = pygame.font.SysFont("segoeui", 22)
    font_hud = pygame.font.SysFont("segoeui", 26, bold=True)

    # Objetos do Jogo
    game_map = Map(width=MAP_WIDTH, height=MAP_HEIGHT, tile_size=TILE_SIZE)
    trees = TreeManager(game_map.grid, tile_size=TILE_SIZE)
    buildings = []
    npcs = []
    
    boat = Boat(tile_size=TILE_SIZE)
    boat.state = "hidden" # Fica escondido no começo

    build_sys = BuildingSystem(game_map.grid, tile_size=TILE_SIZE)
    build_sys.register_trees(TREE_POSITIONS)
    build_sys.set_tree_manager(trees)

    # Recursos (Infinitos no Tutorial)
    money = 99999
    food = 99999
    population = 0

    # Máquina de Estados
    state = "STATE_INTRO"
    state_timer = 0
    modal = None

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        # ─── LÓGICA DE ESTADOS ────────────────────────────────────────────────
        if state == "STATE_INTRO":
            if state_timer == 0:
                boat.reset_position()
                boat.state = "sailing"
            state_timer += 1
            if boat.is_docked:
                # O barco chegou, criamos o explorador!
                explorador = NPC(game_map.grid)
                explorador.x = boat.x # Sai de perto do barco
                explorador.y = boat.y
                npcs.append(explorador)
                population += 1
                boat.leave()
                state = "STATE_PORT_MODAL"
                
        elif state == "STATE_PORT_MODAL":
            if not modal:
                modal = TutorialModal(
                    "O Explorador Chegou!",
                    [
                        "Um bravo explorador desembarcou na sua ilha.",
                        "Para começar sua colônia e receber mais navios,",
                        "você deve construir um Porto de Comércio.",
                        "Escolha o tipo de alimento principal do seu porto:"
                    ],
                    [
                        {"text": "Peixes (Azul)", "color": (50, 100, 200), "id": "peixe"},
                        {"text": "Frutas (Laranja)", "color": (200, 100, 50), "id": "frutas"},
                        {"text": "Milho (Amarelo)", "color": (200, 200, 50), "id": "milho"}
                    ]
                )
            elif not modal.active:
                # Aplicamos a cor escolhida ao porto
                choice = modal.result
                if choice == "peixe":
                    BUILDING_TYPES["port"]["color"] = (50, 100, 200)
                    BUILDING_TYPES["port"]["roof"] = (30, 80, 180)
                elif choice == "frutas":
                    BUILDING_TYPES["port"]["color"] = (200, 100, 50)
                    BUILDING_TYPES["port"]["roof"] = (180, 80, 30)
                elif choice == "milho":
                    BUILDING_TYPES["port"]["color"] = (200, 200, 50)
                    BUILDING_TYPES["port"]["roof"] = (180, 180, 30)
                
                modal = None
                state = "STATE_BUILD_PORT"
                
        elif state == "STATE_BUILD_PORT":
            # Aguarda até que o jogador construa o porto
            has_port = any(b.btype == "port" for b in buildings)
            if has_port:
                state = "STATE_COLONISTS"
                state_timer = 0
                build_sys.selected = None # Deseleciona
                
        elif state == "STATE_COLONISTS":
            if state_timer == 0:
                boat.reset_position()
                boat.state = "sailing"
            state_timer += 1
            if boat.is_docked:
                # Chegam mais 4 pessoas
                for _ in range(4):
                    npcs.append(NPC(game_map.grid))
                population += 4
                boat.leave()
                
                modal = TutorialModal(
                    "Novos Colonos!",
                    [
                        "O porto atraiu novos colonos para a ilha!",
                        "Porém, eles não têm onde dormir...",
                        "Selecione 'Casa' [1] e construa pelo menos 2 casas",
                        "para abrigar sua nova população."
                    ],
                    [{"text": "Entendido!", "color": (50, 150, 50), "id": "ok"}]
                )
                state = "STATE_BUILD_HOUSES"
                
        elif state == "STATE_BUILD_HOUSES":
            if modal and not modal.active:
                modal = None
            
            if not modal:
                houses = sum(1 for b in buildings if b.btype == "house")
                if houses >= 2:
                    state = "STATE_FARM_MODAL"
                    
        elif state == "STATE_FARM_MODAL":
            if not modal:
                modal = TutorialModal(
                    "Eles estão com fome!",
                    [
                        "Excelente! Suas casas estão prontas.",
                        "Mas a população precisa comer para trabalhar.",
                        "Construa uma FAZENDA [2] para produzir alimento.",
                        "Não se preocupe com o dinheiro no tutorial!"
                    ],
                    [{"text": "Construir Fazenda", "color": (50, 150, 50), "id": "ok"}]
                )
            elif not modal.active:
                modal = None
                state = "STATE_BUILD_FARM"
                
        elif state == "STATE_BUILD_FARM":
            has_farm = any(b.btype == "farm" for b in buildings)
            if has_farm:
                state = "STATE_FINAL_MODAL"
                
        elif state == "STATE_FINAL_MODAL":
            if not modal:
                modal = TutorialModal(
                    "Tutorial Concluído!",
                    [
                        "Perfeito! A Fazenda produzirá comida constantemente.",
                        "Quando o navio retornar, o excesso de comida",
                        "será automaticamente vendido no seu Porto,",
                        "gerando dinheiro para você expandir sua cidade.",
                        "",
                        "Você está pronto. Boa sorte, El Presidente!"
                    ],
                    [{"text": "Finalizar e Voltar", "color": (150, 50, 50), "id": "end"}]
                )
            elif not modal.active:
                running = False


        # ─── EVENTOS ──────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False # sair do tutorial
            
            # O Modal intercepta os cliques se estiver ativo
            if modal and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if modal.handle_click(event.pos):
                    continue
                    
            if not modal:
                built = build_sys.handle_event(event, buildings, money, free_workers=99)
                if built:
                    dm, dp, df = build_sys.flush_effects()
                    # Ignoramos dinheiro para o tutorial (recursos infinitos)
                    population += dp
                    if dp > 0:
                        for _ in range(dp):
                            npcs.append(NPC(game_map.grid))

        # ─── ATUALIZAÇÕES ─────────────────────────────────────────────────────
        boat.update()
        for npc in npcs:
            npc.update()

        # ─── DESENHAR ─────────────────────────────────────────────────────────
        screen.fill((0, 0, 0))
        game_map.draw(screen)
        trees.draw(screen)
        boat.draw(screen)
        
        for b in buildings:
            b.draw(screen)
            
        for npc in npcs:
            npc.draw(screen)
            
        # Filtro de HUD para o jogador focar no objetivo
        if not modal:
            if state == "STATE_BUILD_PORT":
                # Mostra apenas o porto no menu
                bkp = BUILDING_TYPES.copy()
                BUILDING_TYPES.clear()
                BUILDING_TYPES["port"] = bkp["port"]
                build_sys.draw_preview(screen)
                build_sys.draw_hud(screen, font_text, money)
                BUILDING_TYPES.update(bkp)
            elif state in ["STATE_BUILD_HOUSES", "STATE_FARM_MODAL", "STATE_BUILD_FARM"]:
                # Esconde o porto, mostra os outros edifícios
                bkp = BUILDING_TYPES.copy()
                if "port" in BUILDING_TYPES:
                    del BUILDING_TYPES["port"]
                build_sys.draw_preview(screen)
                build_sys.draw_hud(screen, font_text, money)
                BUILDING_TYPES.clear()
                BUILDING_TYPES.update(bkp)

        # Informações na tela
        hud_panel = pygame.Surface((200, 100), pygame.SRCALPHA)
        hud_panel.fill((15, 15, 25, 200))
        screen.blit(hud_panel, (10, 10))
        screen.blit(font_hud.render(f"População: {population}", True, (255,255,255)), (20, 20))
        screen.blit(font_hud.render(f"Modo Tutorial", True, (255,215,0)), (20, 60))

        if modal:
            modal.draw(screen, font_title, font_text)

        pygame.display.flip()

    # Ao sair do tutorial, restaura o dicionário original
    BUILDING_TYPES.clear()
    BUILDING_TYPES.update(orig_building_types)
