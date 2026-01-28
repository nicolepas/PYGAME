"""
Gerenciamento de áudio com fallback silencioso para pygame.
Uso: from audio_fallback import AudioManager, load_sound_safe
"""

import time
from pathlib import Path

# Tenta importar e inicializar pygame.mixer
try:
    import pygame
    try:
        pygame.mixer.init()
        PYGAME_MIXER_OK = True
    except Exception as e:
        # mixer não inicializou (ex.: ambiente headless / sem áudio)
        PYGAME_MIXER_OK = False
        print("Aviso: pygame.mixer não pôde inicializar:", e)
except Exception as e:
    pygame = None
    PYGAME_MIXER_OK = False
    # não imprimir muito em produção
    print("Aviso: pygame não disponível:", e)


# --- Fallback silencioso (mira compatibilidade com pygame.mixer.Sound API) ---
class SilentChannel:
    """Canal 'vazio' que aceita stop() e set_volume() sem fazer nada."""
    def __init__(self):
        self._busy = False
    def stop(self):
        self._busy = False
    def set_volume(self, v):
        pass
    def get_busy(self):
        return False

class SilentSound:
    """Objeto que imita pygame.mixer.Sound mas não faz som."""
    def __init__(self, name="<silent>"):
        self._name = name
        self._volume = 1.0
    def play(self, loops=0):
        # Retorna um 'channel' compatível minimamente
        return SilentChannel()
    def stop(self):
        pass
    def set_volume(self, v):
        try:
            self._volume = float(v)
        except Exception:
            pass
    def get_length(self):
        return 0.0
    def __repr__(self):
        return f"<SilentSound {self._name}>"

def load_sound_safe(path_like):
    """
    Tenta carregar um som via pygame.mixer.Sound(path).
    Se falhar (arquivo ausente ou mixer indisponível), retorna SilentSound.
    path_like: str | Path
    """
    path = Path(path_like)
    if not path.exists():
        # arquivo não existe -> fallback silencioso
        # print opcional para debug
        # print(f"Aviso: som não encontrado em {path}, usando SilentSound.")
        return SilentSound(path.name)
    if not PYGAME_MIXER_OK:
        # mixer indisponível -> fallback silencioso
        return SilentSound(path.name)
    try:
        snd = pygame.mixer.Sound(str(path))
        return snd
    except Exception as e:
        # falha ao carregar -> fallback silencioso
        print(f"Aviso: falha ao carregar som {path}: {e}\nUsando SilentSound.")
        return SilentSound(path.name)


# --- Gerenciador prático para áudio de movimento / passos ---
class AudioManager:
    """
    Gerencia sons de movimento de forma segura.
    Parâmetros:
      movement_sound: caminho ou Sound para loop enquanto se move (ou None)
      step_sound: caminho ou Sound para passos (ou None)
      step_cooldown: min segundos entre passos quando usar try_step()
    """
    def __init__(self, movement_sound=None, step_sound=None, step_cooldown=0.12):
        # Carrega com fallback
        self.movement_sound = load_sound_safe(movement_sound) if movement_sound else SilentSound("movement_none")
        self.step_sound = load_sound_safe(step_sound) if step_sound else SilentSound("step_none")
        self.step_cooldown = float(step_cooldown)
        self._last_step_time = 0.0

        # Channel usado para o loop do movimento (quando disponível)
        self._movement_channel = None

    # --- Controle loop while moving ---
    def start_movement(self, volume=0.25):
        """
        Toca o som de movimento em loop (apenas se não estiver tocando).
        Se o resultado for SilentSound, as chamadas são seguras e silenciosas.
        """
        try:
            if PYGAME_MIXER_OK:
                # se já estiver ocupado, não reinicia
                if self._movement_channel is None or not self._movement_channel.get_busy():
                    self._movement_channel = self.movement_sound.play(loops=-1)
                    # se play retornou None (algumas impls), tentamos um channel default
                    if self._movement_channel is None:
                        # tenta setar volume diretamente na Sound
                        try:
                            self.movement_sound.set_volume(volume)
                        except Exception:
                            pass
                    else:
                        try:
                            self._movement_channel.set_volume(volume)
                        except Exception:
                            pass
            else:
                # mixer não disponível -> chamar play em SilentSound (no-op)
                self.movement_sound.play(loops=-1)
        except Exception as e:
            # segurança: nunca propagar erro de áudio
            print("Aviso: erro ao tentar iniciar movimento (silenciado):", e)

    def stop_movement(self):
        """Para o som de movimento (se estiver tocando)."""
        try:
            if self._movement_channel is not None:
                try:
                    self._movement_channel.stop()
                except Exception:
                    pass
                self._movement_channel = None
            # also try to stop sound object
            try:
                self.movement_sound.stop()
            except Exception:
                pass
        except Exception as e:
            print("Aviso: erro ao tentar parar movimento (silenciado):", e)

    # --- Passos com cooldown ---
    def try_step(self):
        """
        Toca um som de 'passo' respeitando cooldown para evitar bips por frame.
        Retorna True se tocou o som, False caso contrário.
        """
        now = time.monotonic()
        if now - self._last_step_time >= self.step_cooldown:
            try:
                self.step_sound.play()
            except Exception:
                # caso de SilentSound ou falha qualquer, ignora
                pass
            self._last_step_time = now
            return True
        return False

    # --- Tocar som único (útil para 'start move' ou outros eventos) ---
    def play_once(self, sound):
        """
        Toca uma instância única de som passado (caminho ou Sound). Seguro.
        """
        snd = load_sound_safe(sound) if isinstance(sound, (str, Path)) else sound
        try:
            snd.play()
        except Exception:
            pass