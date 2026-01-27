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

# ENTIDADES
class Jogador:
    def _init_(self, x, y, imagem):
        # posição inicial e sprite
        self.x = x; self.y = y
        self.imagem = imagem
        self.rect = self.imagem.get_rect(center=(x,y))

        # controle de ping (radar)
        self.ultimo_ping = -999
        self.historico_pings = []

        # estado de movimento
        self.movendo = False

        # controle de dano
        self.ultimo_dano = -999  # timestamp do último dano recebido


    def atualizar(self, dt, teclas):
        dx = dy = 0
        # movimentação com WASD ou setas
        if teclas[pygame.K_w] or teclas[pygame.K_UP]: dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]: dy += 1
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]: dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]: dx += 1

        # define se está se movendo
        self.movendo = bool(dx or dy)

        # aplica movimento normalizado
        if dx or dy:
            norm = math.hypot(dx, dy)
            self.x += (dx / norm) * VEL_JOGADOR * dt
            self.y += (dy / norm) * VEL_JOGADOR * dt

        # limites da tela
        self.x = max(16, min(LARGURA - 16, self.x))
        self.y = max(16, min(ALTURA - 16, self.y))
        self.rect.center = (int(self.x), int(self.y))

    def pode_ping(self, agora):
        return (agora - self.ultimo_ping) >= PING_INTERVALO
    def fazer_ping(self, agora):
        self.ultimo_ping = agora
        self.historico_pings.append(agora)
        # mantém apenas pings recentes (últimos 5s)
        self.historico_pings = [t for t in self.historico_pings if agora - t <= 5.0]
        return len(self.historico_pings)
    @property
    def qtd_pings_recentes(self):
        return len(self.historico_pings)

    def pode_levar_dano(self, agora, invencivel_global):
        # não pode levar dano se ainda em invulnerabilidade global (spawn) ou cooldown pós-dano
        if invencivel_global:
            return False
        return (agora - self.ultimo_dano) >= COOLDOWN_DANO
    
    def registrar_dano(self, agora):
        self.ultimo_dano = agora

    def desenhar(self, tela, agora):
        # piscamento visual se invencível (piscando)
        invencivel = (now := time.time()) - jogo.tempo_inicial_invicivel < INVULNERABILIDADE_INICIAL
        pos_dano = (now - self.ultimo_dano) < COOLDOWN_DANO
        alpha = 255
        if invencivel or pos_dano:
            # piscar baseado em seno
            t = math.sin(time.time() * 20.0)
            alpha = 180 if t > 0.3 else 60

        # aplica transparência
        surf = pygame.Surface(self.imagem.get_size(), pygame.SRCALPHA)
        surf.blit(self.imagem, (0,0))
        arr = pygame.Surface(self.imagem.get_size(), pygame.SRCALPHA)
        arr.fill((255,255,255,alpha))
        surf.blit(arr, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        tela.blit(surf, surf.get_rect(center=(int(self.x), int(self.y))))

class Inimigo:
    def _init_(self, x, y, imagem, pontos_patrulha=None):
        self.x = x; self.y = y
        self.imagem = imagem
        self.rect = imagem.get_rect(center=(x,y))
        self.estado = EstadoInimigo.PATRULHA
        self.pontos_patrulha = pontos_patrulha or [(x,y)]
        self.idx_alvo = 0
        self.pos_alerta = None
        self.timer_alerta = 0.0
        self.velocidade = VEL_INIMIGO
        self.vivo = True
        self.revelado_ate = 0.0

    def atualizar(self, dt, pos_jogador, inimigos, atraido=False):
        if not self.vivo: return
        px, py = pos_jogador

        # mudança de estado
        if atraido:
            self.estado = EstadoInimigo.PERSEGUIR
        else:
            if self.estado == EstadoInimigo.PERSEGUIR:
                self.estado = EstadoInimigo.INVESTIGAR
                self.pos_alerta = (px, py)
                self.timer_alerta = 2.4

        # separação entre inimigos (evita sobreposição)
        sep_fx = sep_fy = 0.0
        for outro in inimigos:
            if outro is self or not outro.vivo: continue
            dx = self.x - outro.x
            dy = self.y - outro.y
            dist = math.hypot(dx, dy)
            if dist > 0 and dist < DIST_SEPARACAO_INIMIGO:
                empurrar = (DIST_SEPARACAO_INIMIGO - dist) / DIST_SEPARACAO_INIMIGO
                nx = dx / dist
                ny = dy / dist
                sep_fx += nx * empurrar * FORCA_SEPARACAO_INIMIGO
                sep_fy += ny * empurrar * FORCA_SEPARACAO_INIMIGO

            # comportamento por estado
            if self.estado == EstadoInimigo.PATRULHA:
                tx, ty = self.pontos_patrulha[self.idx_alvo]
                self.mover_para(tx, ty, dt, self.velocidade)
                if math.hypot(self.x - tx, self.y - ty) < 8:
                    self.idx_alvo = (self.idx_alvo + 1) % len(self.pontos_patrulha)
            elif self.estado == EstadoInimigo.INVESTIGAR:
                if self.pos_alerta:
                    tx, ty = self.pos_alerta
                    self.mover_para(tx, ty, dt, VEL_INIMIGO_ALERTA)
                    if math.hypot(self.x - tx, self.y - ty) < 10:
                        self.timer_alerta -= dt
                        if self.timer_alerta <= 0:
                            self.estado = EstadoInimigo.PATRULHA
                            self.pos_alerta = None
            elif self.estado == EstadoInimigo.PERSEGUIR:
                self.mover_para(px, py, dt, VEL_INIMIGO_ALERTA)

            # aplica separação
            self.x += sep_fx * dt
            self.y += sep_fy * dt

            # limites da tela
            self.x = max(8, min(LARGURA-8, self.x))
            self.y = max(8, min(ALTURA-8, self.y))
            self.rect.center = (int(self.x), int(self.y))
    def mover_para(self, tx, ty, dt, speed):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            nx = dx / dist
            ny = dy / dist
            self.x += nx * speed * dt
            self.y += ny * speed * dt

    def ao_ser_revelado(self, pos_revelacao):
        self.estado = EstadoInimigo.INVESTIGAR
        self.pos_alerta = pos_revelacao
        self.timer_alerta = 2.6

    def desenhar(self, tela, agora):
        revelado = (self.revelado_ate and agora <= self.revelado_ate)
        if revelado:
            pulse = 1.0 + 0.25 * math.sin(time.time() * 10.0)
            r = int((max(self.imagem.get_width(), self.imagem.get_height())//2 + 8) * pulse)
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            alpha = int(160 * (1 - ((self.revelado_ate - agora) / PING_DURACAO)))
            pygame.draw.circle(s, (180,220,255, max(60, alpha)), (r, r), r, width=3)
            tela.blit(s, (int(self.x - r), int(self.y - r)))
        tela.blit(self.imagem, self.imagem.get_rect(center=(int(self.x), int(self.y))))


# JOGO 

class JogoEco:
    def _init_(self):
        pygame.init()
        # evita exception se já inicializado/ambiente sem áudio
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("ECO - aprimorado (PT-BR)")
        self.relogio = pygame.time.Clock()
        self.estado = EstadoJogo.MENU

        self.img_jogador = carregar_imagem("jogador.png", (48,48))
        self.img_inimigo = carregar_imagem("inimigo.png", (48,48))
        self.img_fundo = carregar_imagem("fundo.png", (LARGURA, ALTURA))
        self.img_item = carregar_imagem("item.png", (24,24))

        # Carrega sons via fallback seguro (retorna Sound ou SilentSound)
        self.snd_ping = carregar_som("ping.wav")  # tentar ping.wav; carregar_som já aplica fallback
        # self.snd_ping2 = carregar_som("ping2.wav")  # se quiser alternativa
        self.snd_ambiente = carregar_som("ambiente.wav")
        self.snd_perigo = carregar_som("perigo.wav")
        self.snd_passo = carregar_som("passo.wav")

        # Cria canais apenas se o mixer estiver disponível; caso contrário, deixamos None
        if PYGAME_MIXER_OK:
            try:
                self.canal_ambiente = pygame.mixer.Channel(0)
                self.canal_sfx = pygame.mixer.Channel(1)
            except Exception:
                self.canal_ambiente = None
                self.canal_sfx = None
        else:
            self.canal_ambiente = None
            self.canal_sfx = None

        # Toca ambiente se possível (com canal quando disponível)
        if self.snd_ambiente:
            if self.canal_ambiente:
                try:
                    self.canal_ambiente.play(self.snd_ambiente, loops=-1)
                    self.canal_ambiente.set_volume(0.45)
                except Exception:
                    # fallback: usar play direto no objeto (SilentSound ou Sound)
                    try:
                        self.snd_ambiente.play(loops=-1)
                    except Exception:
                        pass
            else:
                try:
                    self.snd_ambiente.play(loops=-1)
                except Exception:
                    pass

        # AudioManager: não usamos som de movimento em loop (passamos None), mas habilitamos som de passo com cooldown
        # step_cooldown definido para 0.32s para replicar seu timing anterior
        # --- ÁUDIO DE MOVIMENTO (loop contínuo, sem bips) ---
        self.audio = AudioManager(
            movement_sound=DIR_SOM / "movimento.wav",  # som contínuo
            step_sound=None                            # nenhum som de passo
        )

        # flag interna para detectar início/fim do movimento
        self._audio_movendo = False


        self.particulas = []
        self.reiniciar_jogo()
        self.overlay_escuro = pygame.Surface((LARGURA, ALTURA), flags=pygame.SRCALPHA)

