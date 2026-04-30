import pygame
import math

class AchievementSystem:
    """Professional Level and Achievement System (Clash of Clans style)"""

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
        
        # Simple achievement definitions for bonus XP
        self.achievements = {
            "Primeira Casa": lambda p, m, f: p >= 15,
            "Vilarejo": lambda p, m, f: p >= 30,
            "Comerciante": lambda p, m, f: m >= 1000,
            "Fazendeiro": lambda p, m, f: f >= 200,
            "Capitalista": lambda p, m, f: m >= 5000,
        }

    def calculate_xp_needed(self, level):
        if level >= self.max_level:
            return 9999999
        # Scales: L1=100, L2=282, L3=519, L10=3162...
        return int(100 * (level ** 1.5))

    def add_xp(self, amount):
        if self.level >= self.max_level:
            return
            
        self.xp += amount
        while self.xp >= self.xp_needed and self.level < self.max_level:
            self.xp -= self.xp_needed
            self.level += 1
            self.xp_needed = self.calculate_xp_needed(self.level)

    def update(self, population, money, food):
        self.last_population = population
        self.last_money = money
        self.last_food = food
        
        self._check_achievements()

    def _check_achievements(self):
        for name, condition in self.achievements.items():
            if name not in self.unlocked and condition(
                self.last_population, self.last_money, self.last_food
            ):
                self.unlocked.add(name)
                self.add_xp(500) # Give a big XP bonus for achievements!

    def draw(self, screen, cycle=0.0):
        ticks = pygame.time.get_ticks()
        _, screen_h = screen.get_size()

        # ── compact layout ────────────────────────────────────────────
        PANEL_W = 220
        PANEL_X = 16
        BAR_H   = 10          # XP bar height
        DAY_H   = 6           # day/night bar height (thinner, glued below)
        BADGE_R = 16          # small level circle
        PAD     = 10
        GAP     = 8
        STICK   = 3           # gap between the two stacked bars

        PANEL_H = PAD + BADGE_R*2 + GAP + BAR_H + STICK + DAY_H + PAD
        panel_y = (screen_h - PANEL_H) // 2

        # ── glass card ────────────────────────────────────────────────
        card = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        pygame.draw.rect(card, (10, 14, 24, 200), card.get_rect(), border_radius=14)
        pygame.draw.rect(card, (255, 255, 255, 30), card.get_rect(), 1, border_radius=14)
        screen.blit(card, (PANEL_X, panel_y))

        cx = PANEL_X + PANEL_W // 2
        cy = panel_y + PAD

        # ── ① LEVEL BADGE (small, left-aligned) ──────────────────────
        bx = PANEL_X + PAD + BADGE_R          # badge center x
        by = cy + BADGE_R                      # badge center y

        # pulsating glow
        pulse = int(30 + 20 * math.sin(ticks * 0.003))
        g = pygame.Surface((BADGE_R*2+14, BADGE_R*2+14), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 200, 50, pulse), (BADGE_R+7, BADGE_R+7), BADGE_R+7)
        screen.blit(g, (bx - BADGE_R - 7, by - BADGE_R - 7))

        pygame.draw.circle(screen, (200, 155, 10), (bx, by), BADGE_R)
        pygame.draw.circle(screen, (255, 215, 50), (bx, by), BADGE_R - 1)
        pygame.draw.circle(screen, (18,  75, 175), (bx, by), BADGE_R - 5)

        lvl_s = self.font.render(str(self.level), True, (255, 255, 255))
        screen.blit(lvl_s, (bx - lvl_s.get_width()//2, by - lvl_s.get_height()//2))

        # level label to the right of badge
        lbl = self.font.render(f"Nível  {self.level} / {self.max_level}", True, (180, 205, 255))
        screen.blit(lbl, (bx + BADGE_R + 6, by - lbl.get_height()//2))

        cy = by + BADGE_R + GAP

        bar_x = PANEL_X + PAD
        bar_w = PANEL_W - PAD * 2

        # ── ② XP BAR ─────────────────────────────────────────────────
        pygame.draw.rect(screen, (25, 30, 50), (bar_x, cy, bar_w, BAR_H), border_radius=5)
        fill_pct = min(1.0, self.xp / self.xp_needed) if self.level < self.max_level else 1.0
        fill_w   = max(0, int((bar_w - 4) * fill_pct))
        if fill_w > 0:
            pygame.draw.rect(screen, (0, 145, 255), (bar_x+2, cy+2, fill_w, BAR_H-4), border_radius=4)
            # gloss
            pygame.draw.rect(screen, (160, 230, 255, 80), (bar_x+2, cy+2, fill_w, (BAR_H-4)//2), border_radius=4)
        xp_lbl = self.font.render(
            f"XP  {int(self.xp)}/{self.xp_needed}" if self.level < self.max_level else "XP  MAX",
            True, (140, 180, 255))
        screen.blit(xp_lbl, (bar_x + bar_w//2 - xp_lbl.get_width()//2, cy - xp_lbl.get_height() - 2))

        cy += BAR_H + STICK

        # ── ③ DAY / NIGHT BAR (thinner, glued right below XP) ────────
        pygame.draw.rect(screen, (20, 22, 40), (bar_x, cy, bar_w, DAY_H), border_radius=3)

        # color shifts: gold (day) → orange (sunset) → indigo (night) → pink (dawn)
        t = cycle
        if t < 0.25:
            bar_col = (255, 220, 60)
        elif t < 0.5:
            r2 = int(255 - (t - 0.25) * 4 * 60)
            bar_col = (max(100, r2), 80, 40)
        elif t < 0.75:
            bar_col = (60, 70, 180)
        else:
            bar_col = (200, 120, 180)

        day_fill = max(0, int((bar_w - 2) * cycle))
        if day_fill > 0:
            pygame.draw.rect(screen, bar_col, (bar_x+1, cy+1, day_fill, DAY_H-2), border_radius=3)
            pygame.draw.rect(screen, (255,255,255,50), (bar_x+1, cy+1, day_fill, (DAY_H-2)//2), border_radius=3)

''