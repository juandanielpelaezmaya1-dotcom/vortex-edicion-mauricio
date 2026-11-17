import numpy as np
a=np.fromfile('cache/agudos.raw',np.float32); sr=44100; n=len(a)//sr
db=20*np.log10(np.sqrt((a[:n*sr].reshape(n,sr)**2).mean(1))+1e-9)
b=db>-60; prev=None; ini=0
for i,v in enumerate(list(b)+[None]):
    if v!=prev:
        if prev is not None: print(f"{'ANCHO ' if prev else 'angosto'} {ini//60}:{ini%60:02d} - {i//60}:{i%60:02d}  ({i-ini}s)")
        prev=v; ini=i
