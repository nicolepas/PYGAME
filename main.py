import pygame
import sys
import math
import time
import random
from enum import Enum
from pathlib import Path

# Integração com fallback de áudio
from audio_fallback import AudioManager, load_sound_safe, PYGAME_MIXER_OK

# CONFIGURAÇÃO
LARGURA, ALTURA = 900, 640   # tamanho da janela do jogo
FPS = 60                     # taxa de quadros por segundo (velocidade do jogo)

# Diretórios principais para guardar imagens e sons
DIR_ASSETS = Path("assets")          # pasta raiz dos assets
DIR_IMG = DIR_ASSETS / "imagens"     # subpasta para imagens
DIR_SOM = DIR_ASSETS / "sons"        # subpasta para sons


# AJUSTES DE JOGO

# velocidade de movimento do jogador 
VEL_JOGADOR = 180            

# Configuração do "ping" (radar/eco)
PING_INTERVALO = 0.9           # tempo entre pings
PING_RAIO = 200                # alcance do ping
PING_DURACAO = 1.1             # quanto tempo o ping fica visível
MAX_PINGS_ATRAIR = 4           # máximo de pings que podem atrair inimigos

# Velocidade dos inimigos
VEL_INIMIGO = 70               # velocidade normal
VEL_INIMIGO_ALERTA = 120       # velocidade quando estão em alerta
DIST_SEPARACAO_INIMIGO = 48    # distância mínima entre inimigos
FORCA_SEPARACAO_INIMIGO = 40   # força que os afasta quando muito próximos

# Partículas (efeitos visuais)
QTD_PARTICULAS = 14            # quantidade de partículas geradas
VIDA_PARTICULA = 0.6           # tempo de vida de cada partícula (segundos)

# Vida e invulnerabilidade do jogador
VIDA_INICIAL = 3               # quantidade inicial de vidas
INVULNERABILIDADE_INICIAL = 1.8  # tempo de invulnerabilidade ao iniciar
COOLDOWN_DANO = 1.4              # tempo de invulnerabilidade após levar dano


# Estados principais do jogo
class EstadoJogo(Enum):
    MENU = 1       # tela inicial/menu
    JOGANDO = 2    # jogo em andamento
    FIM = 3        # tela de fim de jogo

# Estados de comportamento dos inimigos
class EstadoInimigo(Enum):
    PATRULHA = 1    # andando normalmente
    INVESTIGAR = 2  # procurando jogador após alerta - flash de luz
    PERSEGUIR = 3   # perseguindo diretamente o jogador após ele aparecer com o ping


# Procura possíveis caminhos para imagens, considerando traduções de nomes
def _possible_image_paths(nome):
    traducoes = {
        "jogador.png": "player.png",
        "inimigo.png": "enemy.png",
        "fundo.png": "bg.png",
        "item.png": "item.png",
    }
    nomes = [nome]
    if nome in traducoes:
        nomes.append(traducoes[nome])
    paths = []
    for n in nomes:
        paths.append(DIR_IMG / n)                 # pasta 'assets/imagens'
        paths.append(DIR_ASSETS / "images" / n)   # pasta alternativa 'assets/images'
    return paths


# Procura possíveis caminhos para sons, também com traduções
def _possible_sound_paths(nome):
    traducoes = {
        "ambiente.wav": "ambient.wav",
        "perigo.wav": "danger.wav",
        "passo.wav": "footstep.wav",
        "ping.wav": "ping.wav",
        "ping2.wav": "ping2.wav",
    }
    nomes = [nome]
    if nome in traducoes:
        nomes.append(traducoes[nome])
    paths = []
    for n in nomes:
        paths.append(DIR_SOM / n)                 # pasta 'assets/sons'
        paths.append(DIR_ASSETS / "sounds" / n)   # pasta alternativa 'assets/sounds'
    return paths

# Carrega imagem, se não encontrar cria um quadrado vermelho como fallback
def carregar_imagem(nome, fallback_rect=None):
    for p in _possible_image_paths(nome):
        try:
            if p.exists():
                img = pygame.image.load(str(p)).convert_alpha()
                return img
        except Exception:
            pass
    w, h = fallback_rect if fallback_rect else (48,48)
    s = pygame.Surface((w,h), pygame.SRCALPHA)
    s.fill((180, 80, 80, 255))
    return s



# Carrega som usando o fallback seguro (load_sound_safe) — sempre retorna Sound ou SilentSound
def carregar_som(nome):
    for p in _possible_sound_paths(nome):
        try:
            # load_sound_safe aceita Path e fará fallback se o arquivo não existir ou houver erro
            return load_sound_safe(p)
        except Exception:
            pass
    # caso nenhum caminho funcione, tenta carregar um path padrão (SilentSound)
    return load_sound_safe(DIR_SOM / nome)


# PARTÍCULAS 

class Particula:
    def _init_(self, x, y):
        # posição inicial com pequena variação aleatória
        self.x = x + random.uniform(-6,6)
        self.y = y + random.uniform(-6,6)

        # direção e velocidade aleatória
        angulo = random.uniform(0, math.pi*2)
        velocidade = random.uniform(80, 220)
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade

        # tempo de vida da partícula (com variação)
        self.vida = random.uniform(VIDA_PARTICULA*0.6, VIDA_PARTICULA*1.1)
        self.idade = 0.0

        # tamanho e cor da partícula
        self.tamanho = random.uniform(2.0, 5.0)
        self.cor = (255, 215, 100)  # amarelo dourado

    def atualizar(self, dt):
        # aumenta idade da partícula
        self.idade += dt
        if self.idade < self.vida:
            # desaceleração gradual
            self.vx *= (1.0 - 3.0*dt)
            self.vy *= (1.0 - 3.0*dt)

            # gravidade puxando para baixo
            self.vy += 140 * dt

            # atualiza posição
            self.x += self.vx * dt
            self.y += self.vy * dt

    def desenhar(self, tela):
        if self.idade >= self.vida:
            return

        alpha = int(255 * (1 - self.idade / self.vida))
        alpha = max(0, alpha)

        superficie = pygame.Surface((self.tamanho*2, self.tamanho*2), pygame.SRCALPHA)
        pygame.draw.circle(
            superficie,
            (*self.cor[:3], alpha),
            (self.tamanho, self.tamanho),
            self.tamanho
        )

        tela.blit(
            superficie,
            (self.x - self.tamanho, self.y - self.tamanho)
        )

