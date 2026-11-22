"""Banda oscura suave para leer los subtitulos sobre el apoyo de papeles claros (80,9-85,65 s).
Centrada en y=56 % (la altura de esas frases), negro con alfa maximo 0,55 y bordes gaussianos."""
import os
import numpy as np
from PIL import Image

W, H = 1080, 1920
y = np.arange(H)[:, None] / H
x = np.arange(W)[None, :] / W
a = 0.55 * np.exp(-((y - 0.56) / 0.075) ** 2) * (0.75 + 0.25 * np.exp(-((x - 0.5) / 0.45) ** 2))
img = np.zeros((H, W, 4), np.uint8)
img[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
salida = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "material", "banda-apoyo.png")
Image.fromarray(img, "RGBA").save(salida)
print("listo:", salida)
