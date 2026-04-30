import pygame
import random

class AlertaEvento:
    def __init__(self, screen_width, screen_height):
        self.active = False
        self.font_titulo = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_texto = pygame.font.SysFont("Arial", 18)
        self.rect = pygame.Rect(screen_width//4, screen_height//4, 400, 250)
        self.evento_atual = None
        self.btn_ok = pygame.Rect(0, 0, 0, 0)

    def disparar(self, evento):
        self.evento_atual = evento
        self.active = True

    def desenhar(self, surface):
        if not self.active: return

        # Fundo da janela (Estilo papel/pergaminho ou escuro)
        pygame.draw.rect(surface, (50, 40, 30), self.rect)
        pygame.draw.rect(surface, (200, 180, 100), self.rect, 3) # Borda

        # Título
        img_titulo = self.font_titulo.render(self.evento_atual["titulo"], True, (255, 255, 255))
        surface.blit(img_titulo, (self.rect.x + 20, self.rect.y + 20))

        # Mensagem (Quebra de linha simples)
        palavras = self.evento_atual["mensagem"].split(' ')
        linha = ""
        y_offset = 70
        for p in palavras:
            test_line = linha + p + " "
            if self.font_texto.size(test_line)[0] < (self.rect.width - 40):
                linha = test_line
            else:
                img_msg = self.font_texto.render(linha, True, (200, 200, 200))
                surface.blit(img_msg, (self.rect.x + 20, self.rect.y + y_offset))
                y_offset += 25
                linha = p + " "
        img_msg = self.font_texto.render(linha, True, (200, 200, 200))
        surface.blit(img_msg, (self.rect.x + 20, self.rect.y + y_offset))

        # Botão OK
        self.btn_ok = pygame.Rect(self.rect.centerx - 40, self.rect.bottom - 50, 80, 30)
        pygame.draw.rect(surface, (100, 100, 100), self.btn_ok)
        txt_ok = self.font_texto.render("Entendido", True, (255, 255, 255))
        surface.blit(txt_ok, (self.btn_ok.x + 5, self.btn_ok.y + 5))

    def checar_clique(self, pos):
        if self.active and self.btn_ok.collidepoint(pos):
            self.active = False
            return True
        return False

# Lista de eventos possíveis
EVENTOS = [
    {
        "titulo": "Colheita Farta",
        "mensagem": "Nossas fazendas produziram mais este mes! Ganhamos um bonus de comida.",
        "efeito": {"food": 50, "money": 0, "happiness": 5}
    },
    {
        "titulo": "Ajuda Humanitaria",
        "mensagem": "Uma organizacao internacional enviou fundos para nossa ilha.",
        "efeito": {"food": 0, "money": 100, "happiness": 10}
    },
    {
        "titulo": "Praga nas Plantas",
        "mensagem": "Uma praga atingiu nossas plantacoes. Perdemos um pouco de comida.",
        "efeito": {"food": -30, "money": 0, "happiness": -5}
    },
    {
        "titulo": "Tempestade Tropical",
        "mensagem": "Uma tempestade danificou alguns estoques. Perdemos dinheiro e comida.",
        "efeito": {"food": -20, "money": -50, "happiness": -10}
    },
    {
        "titulo": "Crise Politica",
        "mensagem": "Manifestacoes estao ocorrendo na capital. A felicidade do povo diminuiu significativamente.",
        "efeito": {"food": 0, "money": 0, "happiness": -25}
    }
]

def disparar_evento_aleatorio(alerta_sistema):
    evento = random.choice(EVENTOS)
    alerta_sistema.disparar(evento)
    return evento
