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

