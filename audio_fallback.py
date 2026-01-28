# audio_fallback.py
import time
from pathlib import Path

# Tenta importar pygame e inicializar o mixer.
# Em ambientes headless ou sem suporte a áudio, isso pode falhar — lidamos com isso.
try:
    import pygame
    try:
        pygame.mixer.init()
        PYGAME_MIXER_OK = True
    except Exception:
        PYGAME_MIXER_OK = False
except Exception:
    pygame = None
    PYGAME_MIXER_OK = False

# --- Fallbacks silenciosos ---------------------------------------------------

class SilentChannel:
    """Objeto que simula um Channel do pygame (apenas os métodos que usamos)."""
    def stop(self):
        return None

    def set_volume(self, v):
        return None

    def get_busy(self):
        return False

class SilentSound:
    """
    Representa um 'som' silencioso quando não é possível carregar o arquivo real.
    A assinatura aceita um nome para fins de debug (opcional).
    """
    def __init__(self, nome="<silent>"):
        self._nome = nome

    def play(self, loops=0):
        """
        Simula pygame.Sound.play().
        Retorna um objeto tipo Channel (aqui SilentChannel).
        """
        return SilentChannel()

    def stop(self):
        return None

    def set_volume(self, v):
        return None

    def get_length(self):
        return 0.0

    def __repr__(self):
        return f"<SilentSound {self._nome}>"

# --- Função utilitária para carregar sons com segurança ---------------------

def load_sound_safe(path_like):
    """
    Tenta carregar um som via pygame.mixer.Sound.
    Se não for possível por qualquer motivo (arquivo ausente, mixer inválido, erro),
    retorna uma instância de SilentSound (fallback silencioso).
    - path_like pode ser None, str, ou Path.
    """
    # aceita None (quando o chamador explicitamente passa None)
    if path_like is None:
        return SilentSound("<none>")

    p = Path(path_like)

    # Se o arquivo não existe ou o mixer não está disponível, devolve SilentSound
    if (not p.exists()) or (not PYGAME_MIXER_OK):
        return SilentSound(p.name if p.name else "<missing>")

    try:
        snd = pygame.mixer.Sound(str(p))
        return snd
    except Exception:
        # Qualquer erro ao carregar -> fallback silencioso
        return SilentSound(p.name if p.name else "<error>")

# --- Gerenciador simples de áudio (movimento + passos) ----------------------

class AudioManager:
    """
    AudioManager simplificado.
    - movement_sound e step_sound podem ser path-like (Path/str) ou objetos já carregados.
    - try_step() respeita um cooldown interno para evitar muitos 'bips' por frame.
    """
    def __init__(self, movement_sound=None, step_sound=None, step_cooldown=0.32):
        # Se o chamador passou paths (Path/str), load_sound_safe cuidará do fallback.
        if movement_sound is None:
            self.movement_sound = SilentSound("movement")
        else:
            # se já for um objeto tipo Sound, mantemos; se for path, load_sound_safe lida
            try:
                # detecta se é um path/str/Path-like
                if isinstance(movement_sound, (str, Path)):
                    self.movement_sound = load_sound_safe(movement_sound)
                else:
                    # presume-se que é um objeto compatível com pygame.Sound
                    self.movement_sound = movement_sound
            except Exception:
                self.movement_sound = SilentSound("movement")

        if step_sound is None:
            self.step_sound = SilentSound("step")
        else:
            try:
                if isinstance(step_sound, (str, Path)):
                    self.step_sound = load_sound_safe(step_sound)
                else:
                    self.step_sound = step_sound
            except Exception:
                self.step_sound = SilentSound("step")

        self.step_cooldown = float(step_cooldown)
        self._last_step = 0.0
        self._movement_channel = None

    def start_movement(self, volume=0.25):
        """
        Tenta tocar o som de movimento em loop.
        Se o objeto real for compatível com pygame, play retornará um Channel; caso contrário,
        usamos o fallback silencioso sem erro.
        """
        try:
            ch = None
            try:
                ch = self.movement_sound.play(loops=-1)
            except Exception:
                ch = None

            if ch is not None:
                try:
                    ch.set_volume(volume)
                except Exception:
                    pass
            else:
                # Se play não retornou canal, tenta ajustar o próprio objeto (alguns objetos suportam set_volume)
                try:
                    self.movement_sound.set_volume(volume)
                except Exception:
                    pass

            self._movement_channel = ch
        except Exception:
            # nunca deixar uma falha de áudio quebrar o jogo
            pass

    def stop_movement(self):
        """Para o som de movimento (se houver)."""
        try:
            if self._movement_channel:
                try:
                    self._movement_channel.stop()
                except Exception:
                    pass
            try:
                self.movement_sound.stop()
            except Exception:
                pass
            self._movement_channel = None
        except Exception:
            pass

    def try_step(self):
        """
        Tenta tocar som de passo com cooldown.
        Retorna True se o som foi acionado (ou o cooldown resetou), False caso contrário.
        """
        now = time.monotonic()
        if now - self._last_step >= self.step_cooldown:
            try:
                # play() no SilentSound funciona (retorna SilentChannel) e não causa erro
                self.step_sound.play()
            except Exception:
                pass
            self._last_step = now
            return True
        return False
