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