import numpy as np, wave, sys
w=wave.open('cache/voz16k.wav'); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
win=1600; n=len(x)//win; e=x[:n*win].reshape(n,win); db=20*np.log10(np.sqrt((e**2).mean(1))+1e-9)
print('percentiles dB', [round(float(np.percentile(db,p)),1) for p in (5,10,20,30,50,70,90)])
# por minuto: nivel mediano de voz (p80) y piso (p10)
for m in range(0,n,600):
    s=db[m:m+600]; print(f"{m/600:4.0f} min  piso {np.percentile(s,10):6.1f}  voz {np.percentile(s,80):6.1f}")
