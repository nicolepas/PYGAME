import time
from pathlib import Path

# tenta importar pygame.mixer (pode falhar em headless)
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

# Silent fallback simples
class SilentChannel:
    def stop(self): pass
    def set_volume(self, v): pass
    def get_busy(self): return False

class SilentSound:
    def _init_(self, name="<silent>"):
        self._name = name
    def play(self, loops=0):
        return SilentChannel()
    def stop(self): pass
    def set_volume(self, v): pass
    def get_length(self): return 0.0
    def _repr_(self): return f"<SilentSound {self._name}>"

def load_sound_safe(path_like):
    """Tenta carregar um som via pygame; se falhar, retorna SilentSound"""
    p = Path(path_like)
    if not p.exists() or not PYGAME_MIXER_OK:
        return SilentSound(p.name)
    try:
        return pygame.mixer.Sound(str(p))
    except Exception:
        return SilentSound(p.name)


# AudioManager simples com try_step() 
class AudioManager:
    def _init_(self, movement_sound=None, step_sound=None, step_cooldown=0.32):
        self.movement_sound = load_sound_safe(movement_sound) if movement_sound else SilentSound("movement")
        self.step_sound = load_sound_safe(step_sound) if step_sound else SilentSound("step")
        self.step_cooldown = float(step_cooldown)
        self._last_step = 0.0
        self._movement_channel = None


    def start_movement(self, volume=0.25):
        try:
            ch = self.movement_sound.play(loops=-1)
            if ch is not None:
                try: ch.set_volume(volume)
                except Exception: pass
            else:
                try: self.movement_sound.set_volume(volume)
                except Exception: pass
            self._movement_channel = ch
        except Exception:
            pass
    def stop_movement(self):
        try:
            if self._movement_channel:
                try: self._movement_channel.stop()
                except Exception: pass
            try: self.movement_sound.stop()
            except Exception: pass
            self._movement_channel = None
        except Exception:
            pass

    def try_step(self):
        now = time.monotonic()
        if now - self._last_step >= self.step_cooldown:
            try:
                self.step_sound.play()
            except Exception:
                pass
            self._last_step = now
            return True
        return False