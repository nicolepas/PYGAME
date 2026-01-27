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

