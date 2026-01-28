"""
Gera um som contínuo e suave para movimento (loop-friendly).
Cria: assets/sons/movimento.wav
"""

import math
import struct
import wave
from pathlib import Path

# -------- CONFIGURAÇÃO --------
OUT_DIR = Path("assets/sons")
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FILE = OUT_DIR / "movimento.wav"

FREQ = 220.0        # frequência baixa (grave suave)
DURACAO = 1.0       # 1 segundo (ideal para loop)
VOLUME = 0.18       # bem baixo (não cansativo)
SAMPLE_RATE = 44100

# -------- GERAÇÃO --------
n_samples = int(SAMPLE_RATE * DURACAO)
amp = int(32767 * VOLUME)

frames = bytearray()

for i in range(n_samples):
    t = i / SAMPLE_RATE

    # onda senoidal + leve modulação (fica mais orgânico)
    mod = 1.0 + 0.08 * math.sin(2 * math.pi * 2.0 * t)
    sample = amp * math.sin(2 * math.pi * FREQ * t) * mod

    frames += struct.pack("<h", int(sample))

with wave.open(str(OUT_FILE), "wb") as wav:
    wav.setnchannels(1)       # mono
    wav.setsampwidth(2)       # 16-bit
    wav.setframerate(SAMPLE_RATE)
    wav.writeframes(frames)

print("✅ movimento.wav gerado em:", OUT_FILE.resolve())
print("➡️ Use este som em loop enquanto o jogador se move.")
