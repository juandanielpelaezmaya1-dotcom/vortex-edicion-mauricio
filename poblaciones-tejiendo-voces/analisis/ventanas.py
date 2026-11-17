# Hoja de las ventanas candidatas: inicio, medio y fin de cada una (fila = 6 ventanas).
import subprocess, sys, os
V = [l.split() for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]
os.makedirs("cache/ventanas", exist_ok=True)
fs = []
for i, (f, a, b) in enumerate(V):
    a, b = float(a), float(b)
    for j, t in enumerate([a + 0.05, (a + b) / 2, b - 0.1]):
        o = f"cache/ventanas/{i:02d}_{j}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f"material/cine/{f}.mp4", "-frames:v", "1", "-vf", "scale=120:-2,pad=iw+4:ih+4:2:2:red", o], stdin=subprocess.DEVNULL)
        fs.append(o)
open("cache/ventanas/l.txt", "w").write("\n".join(f"file '{os.path.abspath(x)}'" for x in fs))
rows = (len(fs) + 17) // 18
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "cache/ventanas/l.txt", "-vf", f"tile=18x{rows}", "-frames:v", "1", sys.argv[2]])
