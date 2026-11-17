import numpy as np,re
x=np.fromfile('cache/mono44.raw',np.float32); SR=44100
def ts(s): h,m,r=s.split(':'); return int(h)*3600+int(m)*60+float(r)
for l in open('cache/segmentos.txt',encoding='utf-8'):
    m=re.match(r'\[(\S+) --> (\S+)\]\s+(.*)',l); a,b=ts(m[1]),ts(m[2]); s=x[int(a*SR):int(b*SR)]
    if len(s)<SR: continue
    N=4096; fr=np.lib.stride_tricks.sliding_window_view(s,N)[::2048]*np.hanning(N)
    P=(np.abs(np.fft.rfft(fr))**2); e=P.sum(1); P=P[e>np.percentile(e,50)].mean(0); f=np.fft.rfftfreq(N,1/SR)
    hb=10*np.log10(P[f>12500].sum()/P.sum()); cen=(P*f).sum()/P.sum(); lo=10*np.log10(P[f<300].sum()/P.sum())
    rms=20*np.log10(np.sqrt((s**2).mean()))
    # tono: autocorrelacion en cuadros con voz
    print(f"{m[1][3:8]} agudos{hb:6.1f} cent{cen:6.0f} graves{lo:6.1f} nivel{rms:6.1f} | {m[3][:60]}")
