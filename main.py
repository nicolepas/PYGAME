"""
main.py - ECO  

"""

import pygame
import sys
import math
import time
import random
from enum import Enum
from pathlib import Path

# Integração com fallback de áudio
from audio_fallback import AudioManager, load_sound_safe, PYGAME_MIXER_OK

#configuração
LARGURA, ALTURA = 900, 640   # tamanho da janela do jogo
FPS = 60                     # taxa de quadros por segundo (velocidade do jogo)

# Diretórios principais para guardar imagens e sons
DIR_ASSETS = Path("assets")          # pasta raiz dos assets
DIR_IMG = DIR_ASSETS / "imagens"     # subpasta para imagens
DIR_SOM = DIR_ASSETS / "sons"        # subpasta para sons


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


# ESTADOS 

# Estados principais do jogo
class EstadoJogo(Enum):
    MENU = 1       # tela inicial/menu
    JOGANDO = 2    # jogo em andamento
    FIM = 3        # tela de fim de jogo

# Estados de comportamento dos inimigos
class EstadoInimigo(Enum):
    PATRULHA = 1    # andando normalmente
    INVESTIGAR = 2  # procurando jogador após alerta
    PERSEGUIR = 3   # perseguindo diretamente o jogador


# funções

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

# Carrega som usando o fallback seguro (load_sound_safe) — sempre retorna algo seguro (Sound ou SilentSound)
def carregar_som(nome):
    for p in _possible_sound_paths(nome):
        try:
            # load_sound_safe aceita Path e fará fallback se o arquivo não existir ou mixer estiver off
            return load_sound_safe(p)
        except Exception:
            pass
    # caso nenhum caminho funcione, tenta carregar um path padrão (vai produzir SilentSound)
    return load_sound_safe(DIR_SOM / nome)


# partículas
class Particula:
    def __init__(self, x, y):
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
        # só desenha se ainda estiver "viva"
        if self.idade >= self.vida:
            return

        # transparência proporcional ao tempo de vida
        alpha = int(255 * (1 - (self.idade / self.vida)))

        # cria superfície temporária para desenhar a partícula
        s = pygame.Surface((int(self.tamanho*2), int(self.tamanho*2)), flags=pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.cor, alpha), (int(self.tamanho), int(self.tamanho)), int(self.tamanho))

        # desenha na tela na posição correta
        tela.blit(s, (int(self.x - self.tamanho), int(self.y - self.tamanho)))


class Jogador:
    def __init__(self, x, y, imagem):
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
    def __init__(self, x, y, imagem, pontos_patrulha=None):
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

# jogo
class JogoEco:
    def __init__(self):
        pygame.init()
        # evita exception se já inicializado/ambiente sem áudio
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("ECO DE LUZ")
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

    def reiniciar_jogo(self):
        self.jogador = Jogador(LARGURA//2, ALTURA//2, self.img_jogador)
        self.itens_max = 8           # máximo de itens no mapa ao mesmo tempo
        self.tempo_proximo_respawn = time.time() + 6.0   # primeiro respawn em 6s
        self.respawn_interval = 6.0  # respawn a cada 6s

        def spawn_seguro(x, y):
            min_dist = 160
            if math.hypot(x - self.jogador.x, y - self.jogador.y) < min_dist:
                angle = random.uniform(0, math.pi*2)
                x = self.jogador.x + math.cos(angle) * min_dist
                y = self.jogador.y + math.sin(angle) * min_dist
                x = max(40, min(LARGURA-40, x))
                y = max(40, min(ALTURA-40, y))
            return x, y

        e1x, e1y = spawn_seguro(100, 120)
        e2x, e2y = spawn_seguro(LARGURA-140, ALTURA-180)
        e3x, e3y = spawn_seguro(480, 340)

        e1 = Inimigo(e1x, e1y, self.img_inimigo, pontos_patrulha=[(e1x,e1y),(e1x+140,e1y-40),(e1x+140,e1y+40)])
        e2 = Inimigo(e2x, e2y, self.img_inimigo, pontos_patrulha=[(e2x,e2y),(e2x-140,e2y-40),(e2x-80,e2y+40)])
        e3 = Inimigo(e3x, e3y, self.img_inimigo, pontos_patrulha=[(e3x-60,e3y),(e3x+60,e3y)])
        self.inimigos = [e1, e2, e3]

        self.itens = [{"pos": (200, 150), "coletado": False},{"pos": (600, 420), "coletado": False}]
        self.pings = []
        self.tempo_inicio = time.time()
        self.pontuacao = 0
        self.vida_jogador = VIDA_INICIAL
        self.ultimo_tempo_passo = 0.0
        self.tempo_inicial_invicivel = time.time()
        self.tempo_ultimo_dano = -999  # timestamp do último dano global (redundante com jogador.ultimo_dano)

    def rodar(self):
        while True:
            dt = self.relogio.tick(FPS) / 1000.0
            self.tratar_eventos()
            if self.estado == EstadoJogo.JOGANDO:
                self.atualizar(dt)
            self.desenhar()

    def tratar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                # tenta parar áudio com segurança
                try:
                    if self.canal_ambiente:
                        self.canal_ambiente.stop()
                except Exception:
                    pass
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if self.estado == EstadoJogo.MENU:
                    if evento.key == pygame.K_RETURN:
                        self.reiniciar_jogo()
                        self.estado = EstadoJogo.JOGANDO
                    elif evento.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif self.estado == EstadoJogo.JOGANDO:
                    if evento.key == pygame.K_ESCAPE:
                        self.estado = EstadoJogo.MENU
                    elif evento.key == pygame.K_SPACE:
                        agora = time.time()
                        if self.jogador.pode_ping(agora):
                            qtd_pings = self.jogador.fazer_ping(agora)
                            self.pings.append((self.jogador.x, self.jogador.y, agora))
                            # tocar ping (seguro mesmo sem mixer)
                            try:
                                self.snd_ping.play()
                            except Exception:
                                pass
                            for inimigo in self.inimigos:
                                dist = math.hypot(inimigo.x - self.jogador.x, inimigo.y - self.jogador.y)
                                if dist <= PING_RAIO + 60:
                                    inimigo.ao_ser_revelado((self.jogador.x, self.jogador.y))
                                    inimigo.revelado_ate = agora + PING_DURACAO
                            if qtd_pings >= MAX_PINGS_ATRAIR:
                                for inimigo in self.inimigos:
                                    inimigo.estado = EstadoInimigo.PERSEGUIR
                elif self.estado == EstadoJogo.FIM:
                    if evento.key == pygame.K_RETURN:
                        self.reiniciar_jogo()
                        # tocar ambiente novamente com segurança
                        if self.canal_ambiente:
                            try:
                                self.canal_ambiente.play(self.snd_ambiente, loops=-1)
                                self.canal_ambiente.set_volume(0.45)
                            except Exception:
                                try:
                                    self.snd_ambiente.play(loops=-1)
                                except Exception:
                                    pass
                        else:
                            try:
                                self.snd_ambiente.play(loops=-1)
                            except Exception:
                                pass
                        self.estado = EstadoJogo.JOGANDO
                    elif evento.key == pygame.K_ESCAPE:
                        if self.canal_ambiente:
                            try:
                                self.canal_ambiente.fadeout(400)
                            except Exception:
                                try:
                                    self.snd_ambiente.stop()
                                except Exception:
                                    pass
                        self.estado = EstadoJogo.MENU

    def atualizar(self, dt):
        teclas = pygame.key.get_pressed()
        self.jogador.atualizar(dt, teclas)
        now = time.time()

        # passos: usa AudioManager.try_step() (cooldown interno) para evitar bips por frame
        # --- ÁUDIO: loop enquanto se move ---
        if self.jogador.movendo and not self._audio_movendo:
            # começou a se mover
            self.audio.start_movement(volume=0.22)
            self._audio_movendo = True

        elif not self.jogador.movendo and self._audio_movendo:
            # parou de se mover
            self.audio.stop_movement()
            self._audio_movendo = False


        self.pings = [(x,y,t) for (x,y,t) in self.pings if now - t <= PING_DURACAO]

        attracted = self.jogador.qtd_pings_recentes >= MAX_PINGS_ATRAIR

        for inimigo in self.inimigos:
            inimigo.atualizar(dt, (self.jogador.x, self.jogador.y), self.inimigos, attracted)

        invencivel_spawn = (now - self.tempo_inicial_invicivel) < INVULNERABILIDADE_INICIAL

        # colisões: usar jogador.pode_levar_dano para respeitar cooldown e invencibilidade
        for inimigo in self.inimigos:
            if inimigo.vivo:
                if math.hypot(inimigo.x - self.jogador.x, inimigo.y - self.jogador.y) < 36:
                    if self.jogador.pode_levar_dano(now, invencivel_spawn):
                        # dano efetivo
                        self.vida_jogador -= 1
                        self.jogador.registrar_dano(now)
                        self.tempo_ultimo_dano = now
                        # empurra inimigo para longe para evitar hits múltiplos
                        ang = math.atan2(inimigo.y - self.jogador.y, inimigo.x - self.jogador.x)
                        inimigo.x += math.cos(ang) * 60
                        inimigo.y += math.sin(ang) * 60
                        inimigo.estado = EstadoInimigo.PATRULHA
                        # tocar som de perigo de forma segura
                        try:
                            self.snd_perigo.play()
                        except Exception:
                            pass
                        if self.vida_jogador <= 0:
                            if self.canal_ambiente and self.canal_ambiente.get_busy():
                                try:
                                    self.canal_ambiente.fadeout(800)
                                except Exception:
                                    try:
                                        self.snd_ambiente.stop()
                                    except Exception:
                                        pass
                            self.estado = EstadoJogo.FIM
                    else:
                        # se não pode levar dano (invencível), empurra inimigo levemente e não causa dano
                        ang = math.atan2(inimigo.y - self.jogador.y, inimigo.x - self.jogador.x)
                        inimigo.x += math.cos(ang) * 30
                        inimigo.y += math.sin(ang) * 30

        # coleta de itens (apenas se revelados por ping)
        for item in self.itens:
            if not item["coletado"]:
                if self.is_revealed(item["pos"], now):
                    ix, iy = item["pos"]
                    if math.hypot(ix - self.jogador.x, iy - self.jogador.y) < 28:
                        item["coletado"] = True
                        self.pontuacao += 1
                        for _ in range(QTD_PARTICULAS):
                            self.particulas.append(Particula(ix, iy))
        # respawn: se houver menos itens não-coletados que o máximo e já passou do tempo, adiciona um
        nao_coletados = [it for it in self.itens if not it["coletado"]]
        if len(nao_coletados) < self.itens_max and time.time() >= self.tempo_proximo_respawn:
            # tenta spawnar 1 novo item em posição segura (reusa lógica do gerar_itens_aleatorios)
            def tentar_spawn_um():
                for _ in range(40):
                    x = random.randint(40, LARGURA - 40)
                    y = random.randint(40, ALTURA - 40)
                    if math.hypot(x - self.jogador.x, y - self.jogador.y) < 140:
                        continue
                    ok = True
                    for inim in self.inimigos:
                        if math.hypot(x - inim.x, y - inim.y) < 100:
                            ok = False
                            break
                    if not ok:
                        continue
                    if any(math.hypot(x - it["pos"][0], y - it["pos"][1]) < 60 for it in self.itens if not it["coletado"]):
                        continue
                    return {"pos": (x, y), "coletado": False}
                return None
            novo = tentar_spawn_um()
            if novo:
                self.itens.append(novo)
            self.tempo_proximo_respawn = time.time() + self.respawn_interval
        for p in self.particulas:
            p.atualizar(dt)
        self.particulas = [p for p in self.particulas if p.idade < p.vida]

    def is_revealed(self, pos, agora):
        px, py = pos
        for (x,y,t) in self.pings:
            if math.hypot(px - x, py - y) <= PING_RAIO:
                return True
        return False

    def desenhar(self):
        if self.estado == EstadoJogo.MENU:
            self.desenhar_menu()
        elif self.estado == EstadoJogo.JOGANDO:
            self.desenhar_jogo()
        elif self.estado == EstadoJogo.FIM:
            self.desenhar_fim()
        pygame.display.flip()

    def desenhar_menu(self):
        self.tela.fill((8,8,18))
        fonte_titulo = pygame.font.SysFont("arial", 64)
        titulo = fonte_titulo.render("ECO DE LUZ", True, (220,220,255))
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA//2, 90)))

        fonte_h = pygame.font.SysFont("arial", 20)
        linhas = [
            "Objetivo: Explore emitindo ecos (clarões) para revelar itens e inimigos.",
            "Itens revelados têm um brilho e uma seta aponta para o item mais próximo.",
            "",
            "Controles:",
            "  - Mover: WASD ou setas",
            "  - Ping / Clarão/ Eco: ESPAÇO",
            "  - Iniciar jogo: ENTER",
            "  - Sair: ESC no menu",
            "",
            "Vida: começa com 3 vidas. ",
            
            "Após levar dano há um curto tempo sem levar dano, para evitar perdas rápidas.",
        ]
        y = 170
        for linha in linhas:
            txt = fonte_h.render(linha, True, (210,210,230))
            self.tela.blit(txt, (80, y))
            y += 26

        fonte_footer = pygame.font.SysFont("arial", 18)
        rodape = fonte_footer.render("Pressione ENTER para começar  —  ESPAÇO para emitir eco durante o jogo", True, (200,200,220))
        self.tela.blit(rodape, rodape.get_rect(center=(LARGURA//2, ALTURA - 40)))

    def desenhar_particulas(self):
        for p in self.particulas:
            p.desenhar(self.tela)

    def _desenhar_seta_para(self, alvo_pos):
        # desenha uma seta na borda apontando para alvo_pos (x,y)
        ax, ay = alvo_pos
        cx, cy = self.jogador.x, self.jogador.y
        dx = ax - cx
        dy = ay - cy
        ang = math.atan2(dy, dx)
        # ponto na borda (um pouco dentro)
        margin = 18
        ex = cx + math.cos(ang) * 1000  # estende
        ey = cy + math.sin(ang) * 1000
        # intersecta com retângulo da tela: find t where point at edge
        # simpler: project from center and clamp to screen rect
        px = cx + math.cos(ang) * 420
        py = cy + math.sin(ang) * 320
        # clamp into screen bounds
        px = max(margin, min(LARGURA - margin, px))
        py = max(margin, min(ALTURA - margin, py))
        # desenha triângulo apontando em ang
        size = 14
        p1 = (px + math.cos(ang) * size, py + math.sin(ang) * size)
        p2 = (px + math.cos(ang + 2.2) * size, py + math.sin(ang + 2.2) * size)
        p3 = (px + math.cos(ang - 2.2) * size, py + math.sin(ang - 2.2) * size)
        pygame.draw.polygon(self.tela, (255,200,80), [p1,p2,p3])
        # label "ITEM"
        fonte = pygame.font.SysFont("arial", 16)
        lbl = fonte.render("ITEM", True, (255,200,80))
        self.tela.blit(lbl, (px+10, py-10))

    def desenhar_jogo(self):
        self.tela.fill((0,0,0))
        try:
            self.tela.blit(pygame.transform.scale(self.img_fundo, (LARGURA, ALTURA)), (0,0))
        except Exception:
            pass

        now = time.time()

        # desenhar itens: se revelados, mostrar halo + label; se fora da tela, seta aponta para o mais próximo revelado
        itens_revelados = []
        for item in self.itens:
            if item["coletado"]:
                continue
            ix, iy = item["pos"]
            revelado = self.is_revealed((ix, iy), now)
            if revelado:
                itens_revelados.append(item)
                # halo pulsante
                pulse = 1.0 + 0.25 * math.sin(time.time() * 7.0)
                r = int(18 * pulse)
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                alpha = int(160 * (0.6 + 0.4 * (1 - ( (now - max(t for (x,y,t) in self.pings if True) - now) ) ))) if self.pings else 140
                pygame.draw.circle(s, (255,215,100,140), (r, r), r)
                self.tela.blit(s, (int(ix - r), int(iy - r)))
                # ícone do item
                try:
                    self.tela.blit(self.img_item, self.img_item.get_rect(center=(int(ix), int(iy))))
                except Exception:
                    pygame.draw.rect(self.tela, (200,180,20), (int(ix-12), int(iy-12), 24, 24))
                # rótulo
                fonte = pygame.font.SysFont("arial", 14)
                lbl = fonte.render("ITEM", True, (255,215,100))
                self.tela.blit(lbl, (int(ix - lbl.get_width()//2), int(iy - 26)))
            else:
                # se não revelado, não desenha
                pass

        # desenhar inimigos: visíveis por ping posicional ou por revelado_ate
        for inimigo in self.inimigos:
            pos_revelada = self.is_revealed((inimigo.x, inimigo.y), now)
            marcado = (inimigo.revelado_ate and now <= inimigo.revelado_ate)
            if pos_revelada or marcado:
                inimigo.desenhar(self.tela, now)

        # desenhar jogador (usa estado global 'jogo' para acessar invencibilidade)
        self.jogador.desenhar(self.tela, now)

        # desenhar pings visuais
        for (x,y,t) in self.pings:
            age = now - t
            frac = age / PING_DURACAO
            if frac < 1.0:
                radius = int(PING_RAIO * (1 - frac*0.35))
                alpha = int(200 * (1 - frac))
                s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (180,220,255,alpha), (radius, radius), radius, width=3)
                self.tela.blit(s, (x-radius, y-radius))
                cp = pygame.Surface((48,48), pygame.SRCALPHA)
                pygame.draw.circle(cp, (180,220,255,int(200*(1-frac))), (24,24), int(14*(1-frac)), width=2)
                self.tela.blit(cp, (x-24, y-24))

        # overlay escura com furos
        self.overlay_escuro.fill((0,0,0,220))
        for (x,y,t) in self.pings:
            age = now - t
            frac = age / PING_DURACAO
            if frac < 1.0:
                radius = int(PING_RAIO * (1 - frac*0.25))
                pygame.draw.circle(self.overlay_escuro, (0,0,0,0), (int(x), int(y)), radius)
        pygame.draw.circle(self.overlay_escuro, (0,0,0,0), (int(self.jogador.x), int(self.jogador.y)), 28)
        self.tela.blit(self.overlay_escuro, (0,0))

        # partículas por cima
        self.desenhar_particulas()

        # HUD
        fonte = pygame.font.SysFont("arial", 20)
        txt = fonte.render(f"Pontuação: {self.pontuacao}   Vida: {self.vida_jogador}", True, (240,240,240))
        self.tela.blit(txt, (12, 10))

        ping_pronto = (time.time() - self.jogador.ultimo_ping) >= PING_INTERVALO
        cooldown_frac = min(1.0, max(0.0, (time.time() - self.jogador.ultimo_ping) / PING_INTERVALO))
        barra_w = 140; barra_h = 12
        bx = 12; by = 36
        pygame.draw.rect(self.tela, (60,60,60), (bx, by, barra_w, barra_h))
        inner_w = int(barra_w * cooldown_frac)
        pygame.draw.rect(self.tela, (120,200,255), (bx, by, inner_w, barra_h))
        label = fonte.render("PING (ESPAÇO) - pronto" if ping_pronto else "PING (ESPAÇO) - recarregando", True, (220,220,220))
        self.tela.blit(label, (bx + barra_w + 8, by - 2))

        # aviso invulnerabilidade spawn ou pós-dano
        now = time.time()
        invencivel_spawn = (now - self.tempo_inicial_invicivel) < INVULNERABILIDADE_INICIAL
        pós_dano = (now - self.jogador.ultimo_dano) < COOLDOWN_DANO
        if invencivel_spawn:
            segundos_rest = INVULNERABILIDADE_INICIAL - (now - self.tempo_inicial_invicivel)
            aviso = fonte.render(f"INVULNERÁVEL {segundos_rest:.1f}s (spawn seguro)", True, (255, 205, 80))
            self.tela.blit(aviso, (12, 64))
        elif pós_dano:
            segundos_rest = COOLDOWN_DANO - (now - self.jogador.ultimo_dano)
            aviso = fonte.render(f"INVULNERÁVEL (após dano) {segundos_rest:.1f}s", True, (255, 140, 80))
            self.tela.blit(aviso, (12, 64))

        # seta indicando o item revelado mais próximo (quando há pings ativos)
        # encontrar itens revelados e não coletados
        if self.pings:
            itens_visiveis = [it for it in self.itens if (not it["coletado"]) and self.is_revealed(it["pos"], now)]
            if itens_visiveis:
                # escolher o item não-coletado mais próximo ao jogador
                nearest = min(itens_visiveis, key=lambda it: math.hypot(it["pos"][0]-self.jogador.x, it["pos"][1]-self.jogador.y))
                self._desenhar_seta_para(nearest["pos"])

 
    def desenhar_fim(self):
        # função robusta e defensiva — evita que exceções fechem o jogo
        try:
            # --- garantir inicialização de estado usado ---
            if not getattr(self, "_fim_started", False):
                self._fim_started = True
                self._fim_start_time = time.time()
                self._confetes = []
                cores = [(255,90,90),(255,200,70),(120,220,140),(120,180,255),(200,120,255)]
                for i in range(60):
                    x = random.uniform(0, LARGURA)
                    y = random.uniform(-80, -10)
                    vx = random.uniform(-60, 60)
                    vy = random.uniform(80, 240)
                    rot = random.uniform(0, math.pi*2)
                    vrot = random.uniform(-4, 4)
                    cor = random.choice(cores)
                    size = random.uniform(6, 14)
                    self._confetes.append({"x": x, "y": y, "vx": vx, "vy": vy, "rot": rot, "vrot": vrot, "col": cor, "size": size, "t": 0.0})

                self._burst = []
                for i in range(3):
                    cx = random.uniform(LARGURA*0.25, LARGURA*0.75)
                    cy = random.uniform(ALTURA*0.25, ALTURA*0.45)
                    for k in range(18):
                        ang = random.uniform(0, math.pi*2)
                        s = random.uniform(80, 260)
                        self._burst.append({"x": cx, "y": cy, "vx": math.cos(ang)*s, "vy": math.sin(ang)*s, "life": random.uniform(0.6,1.3), "age": 0.0, "col": random.choice(cores)})

                self._display_score = 0
                self._score_anim_len = 1.6
                self._float_bits = []

            # tempo e dt seguros
            now = time.time()
            last = getattr(self, "_fim_last_time", now)
            dt = min(1/30.0, max(0.0, now - last))
            self._fim_last_time = now

            # atualizar confetes (simples física)
            for c in self._confetes:
                c["t"] += dt
                c["vy"] += 320 * dt
                c["x"] += c["vx"] * dt
                c["y"] += c["vy"] * dt
                c["rot"] += c["vrot"] * dt
                if c["y"] > ALTURA + 40:
                    c["y"] = random.uniform(-60, -10)
                    c["x"] = random.uniform(0, LARGURA)
                    c["vy"] = random.uniform(80, 180)
                    c["vx"] = random.uniform(-60, 60)

            # atualizar burst
            novos_burst = []
            for b in getattr(self, "_burst", []):
                b["age"] += dt
                b["x"] += b["vx"] * dt
                b["y"] += b["vy"] * dt
                b["vx"] *= (1.0 - 2.0*dt)
                b["vy"] *= (1.0 - 2.0*dt)
                if b["age"] < b.get("life", 0.5):
                    novos_burst.append(b)
            self._burst = novos_burst

            # --- desenhar fundo animado ---
            try:
                self.tela.fill((8,6,18))
            except Exception:
                raise

            grad = pygame.Surface((LARGURA, ALTURA), flags=pygame.SRCALPHA)
            pulse = 1.0 + 0.08 * math.sin((now - getattr(self, "_fim_start_time", now)) * 2.6)
            grd_r = int(max(LARGURA, ALTURA) * (0.6 * max(0.01, pulse)))
            pygame.draw.circle(grad, (30,30,80,160), (LARGURA//2, int(ALTURA*0.38)), grd_r)
            pygame.draw.circle(grad, (40,18,30,120), (LARGURA//2, int(ALTURA*0.75)), int(grd_r*0.6))
            self.tela.blit(grad, (0,0))

            # desenhar confetes
            for c in self._confetes:
                w = max(2, int(c["size"]*1.6))
                h = max(2, int(c["size"]*0.9))
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(surf, c["col"], (0,0,w,h))
                try:
                    rs = pygame.transform.rotate(surf, math.degrees(c["rot"]))
                    self.tela.blit(rs, (int(c["x"]-rs.get_width()/2), int(c["y"]-rs.get_height()/2)))
                except Exception:
                    pygame.draw.circle(self.tela, c["col"], (int(max(0,min(LARGURA,c["x"]))), int(max(0,min(ALTURA,c["y"])))), 2)

            # desenhar bursts
            for b in self._burst:
                alpha = int(255 * max(0.0, 1.0 - (b["age"]/b.get("life",1.0))))
                s = pygame.Surface((6,6), pygame.SRCALPHA)
                s.fill((*b["col"], alpha))
                self.tela.blit(s, (int(b["x"])-3, int(b["y"])-3))

            # título principal
            elapsed = now - getattr(self, "_fim_start_time", now)
            pop_scale = 1.0 + 0.12 * math.exp(-elapsed*2.5) * math.cos(elapsed*8.0)
            fonte_t = pygame.font.SysFont("arial", max(12, int(64 * pop_scale)), bold=True)
            titulo = fonte_t.render("FIM DE JOGO", True, (255,220,220))
            tit_rect = titulo.get_rect(center=(LARGURA//2, int(ALTURA*0.18)))
            sh = fonte_t.render("FIM DE JOGO", True, (40,20,30))
            self.tela.blit(sh, (tit_rect.x+6, tit_rect.y+6))
            self.tela.blit(titulo, tit_rect)

            # pontuação contada com easing
            target = int(getattr(self, "pontuacao", 0))
            t = min(1.0, elapsed / getattr(self, "_score_anim_len", 1.6))
            ease = t * t * (3 - 2 * t)
            cur = getattr(self, "_display_score", 0)
            new = int(cur + (target - cur) * (0.06 + 0.9 * ease))
            self._display_score = max(0, new)
            fonte_score = pygame.font.SysFont("arial", 40, bold=True)
            score_txt = fonte_score.render(f"PONTUAÇÃO: {self._display_score}", True, (255,245,200))
            self.tela.blit(score_txt, score_txt.get_rect(center=(LARGURA//2, int(ALTURA*0.32))))

            # selo brilhante
            shine = 1.0 + 0.15 * math.sin((now - getattr(self, "_fim_start_time", now)) * 4.0)
            selo_s = max(80, int(140 * shine))
            selo = pygame.Surface((selo_s, selo_s), pygame.SRCALPHA)
            pygame.draw.circle(selo, (255,240,200,140), (selo_s//2, selo_s//2), selo_s//2)
            pygame.draw.circle(selo, (255,200,70,200), (selo_s//2, selo_s//2), selo_s//2 - 8, width=6)
            try:
                self.tela.blit(selo, (int(LARGURA*0.12), int(ALTURA*0.22)))
            except Exception:
                pass

            # ---- REMOVIDO: tempo/estatísticas (solicitado) ----
            # (antes aqui era desenhado "Tempo: Xm Ys  ·  Itens: N" — removido conforme pedido)

            # botão RECOMEÇAR (ENTER)
            btn_w, btn_h = 360, 52
            bx = LARGURA//2 - btn_w//2
            by = int(ALTURA*0.55)
            btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
            pygame.draw.rect(btn_surf, (255,130,80), (0,0,btn_w,btn_h), border_radius=12)
            txtb = pygame.font.SysFont("arial", 20, bold=True).render("PRESS ENTER — RECOMEÇAR", True, (30,20,10))
            btn_surf.blit(txtb, txtb.get_rect(center=(btn_w//2, btn_h//2)))
            glow = pygame.Surface((btn_w+18, btn_h+18), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255,160,90,90), (0,0,btn_w+18,btn_h+18), border_radius=14)
            self.tela.blit(glow, (bx-9, by-9))
            self.tela.blit(btn_surf, (bx, by))

            # --- AUMENTEI A CAIXA DO MENU (ESC) AQUI ---
            # botão MENU (ESC) grande e proeminente
            btn2_w, btn2_h = 340, 64   # aumentado
            bx2 = LARGURA//2 - btn2_w//2
            by2 = by + btn_h + 20
            # fundo com leve gradiente/retângulo arredondado
            btn2_surf = pygame.Surface((btn2_w, btn2_h), pygame.SRCALPHA)
            pygame.draw.rect(btn2_surf, (70,70,110), (0,0,btn2_w,btn2_h), border_radius=14)
            # uma borda sutil
            pygame.draw.rect(btn2_surf, (110,110,150), (2,2,btn2_w-4,btn2_h-4), width=2, border_radius=12)
            # texto maior e centralizado
            t2font = pygame.font.SysFont("arial", 20, bold=True)
            t2 = t2font.render("ESC — VOLTAR AO MENU", True, (240,240,240))
            btn2_surf.blit(t2, ( (btn2_w - t2.get_width())//2, (btn2_h - t2.get_height())//2 ))
            # glow e blit
            glow2 = pygame.Surface((btn2_w+18, btn2_h+18), pygame.SRCALPHA)
            pygame.draw.rect(glow2, (100,100,150,70), (0,0,btn2_w+18,btn2_h+18), border_radius=16)
            self.tela.blit(glow2, (bx2-9, by2-9))
            self.tela.blit(btn2_surf, (bx2, by2))

            # dica sutil abaixo do menu
            dica = pygame.font.SysFont("arial", 14).render("Dica: Explore áreas escuras — alguns itens estão escondidos!", True, (200,200,210))
            self.tela.blit(dica, (LARGURA//2 - dica.get_width()//2, by2 + btn2_h + 12))

            # floating bits decorativos
            if len(self._float_bits) < 8 and random.random() < 0.08:
                self._float_bits.append({"x": random.uniform(LARGURA*0.78, LARGURA*0.94), "y": random.uniform(ALTURA*0.25, ALTURA*0.6), "vy": random.uniform(-8, -30), "alpha": 255, "t": 0})
            nb = []
            for b in self._float_bits:
                b["t"] += dt
                b["y"] += b["vy"] * dt
                b["alpha"] = max(0, b["alpha"] - 80 * dt)
                if b["alpha"] > 6:
                    nb.append(b)
            self._float_bits = nb
            for b in self._float_bits:
                s = pygame.Surface((8,8), pygame.SRCALPHA)
                s.fill((255,230,150,int(b["alpha"])))
                self.tela.blit(s, (int(b["x"]), int(b["y"])))

            # partículas leves sobre selo
            for i in range(6):
                rx = LARGURA*0.12 + random.uniform(-18,18)
                ry = ALTURA*0.22 + random.uniform(-18,18)
                pygame.draw.circle(self.tela, (255,255,200,80), (int(rx), int(ry)), random.randint(1,3))

            # efeito final de texto quando a contagem terminou
            if elapsed > getattr(self, "_score_anim_len", 1.6) + 0.2:
                pulse2 = 1.0 + 0.08 * math.sin((now - getattr(self, "_fim_start_time", now)) * 6.0)
                finale = pygame.font.SysFont("arial", 20, bold=True).render("MUITO BEM! Pressione ENTER para tentar novamente.", True, (255,240,220))
                rectf = finale.get_rect(center=(LARGURA//2, int(ALTURA*0.48)))
                glow2 = pygame.Surface((rectf.width+40, rectf.height+18), pygame.SRCALPHA)
                pygame.draw.rect(glow2, (255,230,120,80), (0,0,rectf.width+40, rectf.height+18), border_radius=8)
                self.tela.blit(glow2, (rectf.x-20, rectf.y-8))
                self.tela.blit(finale, rectf)

        except Exception as e:
            # Se ocorrer qualquer exceção aqui, desenha fallback simples e imprime erro no console (rode pelo terminal para ver traceback)
            try:
                self.tela.fill((0,0,0))
                fonte = pygame.font.SysFont("arial", 36, bold=True)
                err = fonte.render("FIM DE JOGO", True, (240,240,240))
                self.tela.blit(err, err.get_rect(center=(LARGURA//2, ALTURA//2 - 20)))
                fonte2 = pygame.font.SysFont("arial", 18)
                msg = fonte2.render("Ocorreu um erro ao desenhar a tela final. Veja o terminal.", True, (220,180,180))
                self.tela.blit(msg, msg.get_rect(center=(LARGURA//2, ALTURA//2 + 20)))
            except Exception:
                pass
            import traceback
            traceback.print_exc()
# Expor variável global para o método Jogador.desenhar que usamos (pequeno atalho)
jogo = None

if __name__ == "__main__":
    jogo = JogoEco()
    jogo.rodar()
