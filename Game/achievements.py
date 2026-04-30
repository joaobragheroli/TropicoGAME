import pygame
import math

class AchievementSystem:
    """Sistema de Nível e Conquistas (estilo Clash of Clans)"""

    def __init__(self):
        # Level system
        self.level = 1
        self.max_level = 100
        self.xp = 0
        self.xp_needed = self.calculate_xp_needed(self.level)
        
        # UI Setup
        pygame.font.init()
        self.font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.title_font = pygame.font.SysFont("segoeui", 28, bold=True)
        self.star_font = pygame.font.SysFont("segoeui", 32, bold=True)
        
        # Achievements tracking
        self.unlocked = set()
        self.last_population = 0
        self.last_money = 0
        self.last_food = 0
        
        # Animação de Level Up
        self.level_up_timer = 0
        
        # Títulos de Rank
        self.ranks = [
            (1, "Novato"),
            (5, "Governador"),
            (10, "Prefeito"),
            (20, "Ministro"),
            (35, "Ditador"),
            (50, "El Presidente"),
            (75, "Imperador"),
            (100, "Deus de Tropico")
        ]

        # Definições simples para bônus de XP
        self.achievements = {
            "Primeira Casa": lambda p, m, f: p >= 15,
            "Vilarejo": lambda p, m, f: p >= 30,
            "Comerciante": lambda p, m, f: m >= 1000,
            "Fazendeiro": lambda p, m, f: f >= 200,
            "Capitalista": lambda p, m, f: m >= 5000,
        }

    def get_rank_name(self):
        current_rank = "Visitante"
        for lvl, name in self.ranks:
            if self.level >= lvl:
                current_rank = name
            else:
                break
        return current_rank

    def calculate_xp_needed(self, level):
        if level >= self.max_level:
            return 9999999
        return int(100 * (level ** 1.5))

    def add_xp(self, amount):
        if self.level >= self.max_level:
            return
            
        self.xp += amount
        while self.xp >= self.xp_needed and self.level < self.max_level:
            self.xp -= self.xp_needed
            self.level += 1
            self.level_up_timer = 120 # 2 segundos de animação a 60fps
            self.xp_needed = self.calculate_xp_needed(self.level)

    def update(self, population, money, food):
        self.last_population = population
        self.last_money = money
        self.last_food = food
        self._check_achievements()
        if self.level_up_timer > 0:
            self.level_up_timer -= 1

    def _check_achievements(self):
        for name, condition in self.achievements.items():
            if name not in self.unlocked and condition(
                self.last_population, self.last_money, self.last_food
            ):
                self.unlocked.add(name)
                self.add_xp(500)

    def draw(self, screen, cycle=0.0):
        ticks = pygame.time.get_ticks()
        sw, sh = screen.get_size()

        # Configurações do Painel
        PANEL_W = 240
        PANEL_X = 16
        BAR_H   = 12          
        DAY_H   = 4           
        BADGE_R = 20          
        PAD     = 15
        GAP     = 10
        STICK   = 4           

        PANEL_H = PAD + BADGE_R*2 + GAP + BAR_H + STICK + DAY_H + PAD + 20
        panel_y = (sh - PANEL_H) // 2

        # ── Glass Card com Glow Neon ──────────────────────────────────────────
        # Glow externo sutil
        glow_color = (0, 150, 255, 40)
        if self.level_up_timer > 0:
            # Glow dourado intenso no level up
            glow_color = (255, 215, 0, 100 + int(50 * math.sin(ticks * 0.02)))
            
        pygame.draw.rect(screen, glow_color, (PANEL_X-4, panel_y-4, PANEL_W+8, PANEL_H+8), border_radius=18)
        
        card = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        # Fundo gradiente/escuro
        pygame.draw.rect(card, (15, 20, 35, 230), card.get_rect(), border_radius=16)
        # Borda brilhante
        pygame.draw.rect(card, (255, 255, 255, 40), card.get_rect(), 1, border_radius=16)
        screen.blit(card, (PANEL_X, panel_y))

        # ── Badge de Nível (Estilizado) ──────────────────────────────────────
        bx = PANEL_X + PAD + BADGE_R          
        by = panel_y + PAD + BADGE_R                      

        # Aura de nível
        aura_pulse = int(40 + 20 * math.sin(ticks * 0.005))
        aura_surf = pygame.Surface((BADGE_R*3, BADGE_R*3), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (0, 100, 255, aura_pulse), (BADGE_R*1.5, BADGE_R*1.5), BADGE_R*1.2)
        screen.blit(aura_surf, (bx - BADGE_R*1.5, by - BADGE_R*1.5))

        # Círculos concêntricos
        pygame.draw.circle(screen, (30, 30, 50), (bx, by), BADGE_R)
        pygame.draw.circle(screen, (0, 180, 255), (bx, by), BADGE_R, 2)
        
        lvl_txt = self.star_font.render(str(self.level), True, (255, 255, 255))
        screen.blit(lvl_txt, (bx - lvl_txt.get_width()//2, by - lvl_txt.get_height()//2 - 2))

        # ── Títulos e Rank ────────────────────────────────────────────────────
        rank_name = self.get_rank_name()
        title_y = by - BADGE_R + 2
        
        rank_label = self.font.render(rank_name.upper(), True, (255, 215, 0))
        screen.blit(rank_label, (bx + BADGE_R + 12, title_y))
        
        lvl_label = self.font.render(f"Nível {self.level}", True, (150, 180, 255))
        screen.blit(lvl_label, (bx + BADGE_R + 12, title_y + 22))

        # ── Barra de XP (Gradiente e Animação) ────────────────────────────────
        cy = by + BADGE_R + GAP + 10
        bar_x = PANEL_X + PAD
        bar_w = PANEL_W - PAD * 2

        # Fundo da barra
        pygame.draw.rect(screen, (20, 25, 45), (bar_x, cy, bar_w, BAR_H), border_radius=6)
        
        fill_pct = min(1.0, self.xp / self.xp_needed) if self.level < self.max_level else 1.0
        fill_w   = max(0, int((bar_w - 4) * fill_pct))
        
        if fill_w > 4:
            # Cor principal (Cyan para Azul)
            pygame.draw.rect(screen, (0, 120, 255), (bar_x+2, cy+2, fill_w, BAR_H-4), border_radius=4)
            # Brilho superior
            pygame.draw.rect(screen, (100, 200, 255, 100), (bar_x+2, cy+2, fill_w, (BAR_H-4)//2), border_radius=4)
        
        xp_txt = f"XP {int(self.xp)} / {self.xp_needed}" if self.level < self.max_level else "NÍVEL MÁXIMO"
        xp_surf = self.font.render(xp_txt, True, (200, 220, 255))
        # Fonte menor para o XP
        xp_surf = pygame.transform.scale(xp_surf, (int(xp_surf.get_width()*0.7), int(xp_surf.get_height()*0.7)))
        screen.blit(xp_surf, (bar_x + bar_w//2 - xp_surf.get_width()//2, cy + BAR_H + 4))

        # ── Ciclo de Tempo (Barra Neon) ───────────────────────────────────────
        cy += BAR_H + 20
        pygame.draw.rect(screen, (10, 15, 30), (bar_x, cy, bar_w, DAY_H), border_radius=2)
        
        # Cores vibrantes para o tempo
        t = cycle
        if t < 0.25:   bar_col = (255, 255, 100) # Dia (Amarelo)
        elif t < 0.5:  bar_col = (255, 100, 0)   # Tarde (Laranja)
        elif t < 0.75: bar_col = (80, 80, 255)   # Noite (Azul)
        else:          bar_col = (255, 100, 200) # Amanhecer (Rosa)

        time_fill = max(0, int((bar_w) * cycle))
        if time_fill > 0:
            pygame.draw.rect(screen, bar_col, (bar_x, cy, time_fill, DAY_H), border_radius=2)
            # Partícula na ponta do tempo
            pygame.draw.circle(screen, (255, 255, 255), (bar_x + time_fill, cy + DAY_H//2), 3)

        # ── Mensagem de LEVEL UP ──────────────────────────────────────────────
        if self.level_up_timer > 0:
            alpha = min(255, self.level_up_timer * 5)
            lu_surf = self.title_font.render("LEVEL UP!", True, (255, 215, 0))
            lu_surf.set_alpha(alpha)
            # Centraliza na tela
            screen.blit(lu_surf, (sw//2 - lu_surf.get_width()//2, sh//2 - 100 - (120 - self.level_up_timer)))

