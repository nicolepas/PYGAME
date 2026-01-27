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