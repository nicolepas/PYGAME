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

