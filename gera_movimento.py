"""
Gera um som contínuo e suave para movimento (loop-friendly).
Cria: assets/sons/movimento.wav
"""

import math
import struct
import wave
from pathlib import Path

# CONFIGURAÇÃO 
OUT_DIR = Path("assets/sons")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "movimento.wav"

FREQ = 220.0        # frequência baixa (grave suave)
DURACAO = 1.0       # 1 segundo (ideal para loop)
VOLUME = 0.18       # bem baixo (não cansativo)
SAMPLE_RATE = 44100
