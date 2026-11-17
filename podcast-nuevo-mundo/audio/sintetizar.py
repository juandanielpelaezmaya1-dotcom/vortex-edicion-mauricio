"""Musica y efectos ORIGINALES sintetizados (sin licencias de terceros).
Uso: python audio/sintetizar.py <duracion_cama_s>
Salidas en cache/: cama.wav (cama educativa en bucle), sfx_drogueria.wav, sfx_orientadora.wav,
sfx_estudiantes.wav, sfx_conductor.wav, intro.wav (cortina de entrada), cierre.wav."""
import numpy as np, wave, sys
SR=44100
def guardar(nombre,x):
    x=np.asarray(x,np.float32)
    if x.ndim==1: x=np.stack([x,x],1)
    pk=np.abs(x).max(); x=x/pk*0.89 if pk>0 else x
    with wave.open('cache/'+nombre,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x*32767).astype(np.int16).tobytes())
def hz(m): return 440*2**((m-69)/12)
def env(n,a,d,s,r,sl=0.6):
    a,d,r=int(a*SR),int(d*SR),int(r*SR); s=max(n-a-d-r,0)
    e=np.concatenate([np.linspace(0,1,a,False),np.linspace(1,sl,d,False),np.full(s,sl),np.linspace(sl,0,r)])
    return np.pad(e,(0,max(0,n-len(e))))[:n]
def t(n): return np.arange(n)/SR
def campana(f,dur,brillo=1.0):
    n=int(dur*SR); tt=t(n); x=np.zeros(n)
    for k,(r,g,dec) in enumerate([(1,1,1.6),(2.76,.45*brillo,3.5),(5.4,.25*brillo,6),(8.9,.12*brillo,9)]):
        x+=g*np.sin(2*np.pi*f*r*tt)*np.exp(-dec*tt/dur*2)
    return x*np.minimum(1,tt/0.003)
def marimba(f,dur):
    n=int(dur*SR); tt=t(n)
    return (np.sin(2*np.pi*f*tt)+.35*np.sin(2*np.pi*f*4*tt)*np.exp(-tt*25))*np.exp(-tt*7)*np.minimum(1,tt/0.002)
def pluck(f,dur):  # Karplus-Strong suave
    n=int(dur*SR); p=int(SR/f); buf=np.random.uniform(-1,1,p); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%p]; buf[i%p]=0.5*(buf[i%p]+buf[(i+1)%p])*0.996
    return out
def pad(fs,dur):
    n=int(dur*SR); tt=t(n); x=np.zeros(n)
    for f in fs:
        for det in (-0.12,0,0.12):
            fr=f*2**(det/12); x+=np.sin(2*np.pi*fr*tt+np.random.rand()*6)+.3*np.sin(2*np.pi*2*fr*tt)
    return x*env(n,1.2,.5,0,1.5,1)/len(fs)
def lp(x,a=0.15):  # pasabajos de un polo
    y=np.empty_like(x); acc=0.0
    for i,v in enumerate(x): acc+=a*(v-acc); y[i]=acc
    return y
def mezclar(dst,src,i,g=1.0):
    j=min(len(dst),i+len(src)); dst[i:j]+=g*src[:j-i]

# ---------- cama: C mayor, 84 BPM, I-V-vi-IV, 4 compases por acorde ----------
BPM=84; beat=60/BPM; bar=4*beat
acordes=[[60,64,67,71],[55,59,62,67],[57,60,64,69],[53,57,60,65]]   # Cmaj7 G Am F(add)
bajo=[36,43,45,41]
arpe=[[72,76,79,76],[71,74,79,74],[72,76,81,76],[72,77,81,77]]
ciclo=len(acordes)*2*bar   # 2 compases por acorde -> ciclo de 8 compases
nC=int(ciclo*SR); L=np.zeros(nC); R=np.zeros(nC)
for k,(ac,b,ar) in enumerate(zip(acordes,bajo,arpe)):
    i0=int(k*2*bar*SR)
    p=pad([hz(m) for m in ac],2*bar+1.5); mezclar(L,p,i0,.28); mezclar(R,p,i0,.28)
    bb=np.sin(2*np.pi*hz(b)*t(int(2*bar*SR)))*env(int(2*bar*SR),.05,.4,0,.4,.7)
    mezclar(L,bb,i0,.30); mezclar(R,bb,i0,.30)
    for s in range(16):  # corcheas
        nota=ar[s%4]+(12 if s%8==6 else 0)
        pl=pluck(hz(nota),1.2)*(0.9 if s%2==0 else 0.6)
        pan=0.35+0.3*((s%4)/3)
        mezclar(L,pl,i0+int(s*beat/2*SR),.16*(1-pan)*2); mezclar(R,pl,i0+int(s*beat/2*SR),.16*pan*2)
    for s in range(8):   # golpe suave tipo shaker + bombo leve
        sh=np.random.randn(int(.06*SR))*np.exp(-t(int(.06*SR))*60)
        sh=sh-lp(sh,.3)
        mezclar(L,sh,i0+int((s+.5)*beat*SR),.05); mezclar(R,sh,i0+int((s+.5)*beat*SR),.06)
        if s%2==0:
            kk=np.sin(2*np.pi*(55+60*np.exp(-t(int(.25*SR))*30))*t(int(.25*SR)))*np.exp(-t(int(.25*SR))*14)
            mezclar(L,kk,i0+int(s*beat*SR),.22); mezclar(R,kk,i0+int(s*beat*SR),.22)
cic=np.stack([L,R],1)
dur=float(sys.argv[1]) if len(sys.argv)>1 else 900
reps=int(np.ceil(dur/ciclo))+1
cama=np.tile(cic,(reps,1))[:int(dur*SR)]
# cola del pad que cruza el borde del ciclo: ya va dentro por el tile (suave)
cama[-int(4*SR):]*=np.linspace(1,0,int(4*SR))[:,None]
guardar('cama.wav',cama)

# ---------- cortina de entrada (8 compases con arranque) y cierre ----------
intro=np.tile(cic,(1,1))[:int(4*bar*SR)].copy()
sw=np.random.randn(int(1.5*SR)); sw=lp(sw,.05)*np.linspace(0,1,len(sw))**2
intro[:int(1.5*SR)]*=np.linspace(0,1,int(1.5*SR))[:,None]
intro[-int(2*SR):]*=np.linspace(1,0,int(2*SR))[:,None]
guardar('intro.wav',intro)
cierre=cic[:int(4*bar*SR)].copy()
fin=np.stack([pad([hz(m) for m in [48,60,64,67,72]],5),]*2,1)
cierre=np.concatenate([cierre,np.zeros((len(fin),2))]); cierre[-len(fin):]+=fin*.6
mezclar(cierre[:,0],campana(hz(84),3),len(cierre)-len(fin),.25); mezclar(cierre[:,1],campana(hz(84),3),len(cierre)-len(fin),.25)
cierre[-int(3*SR):]*=np.linspace(1,0,int(3*SR))[:,None]
guardar('cierre.wav',cierre)

# ---------- firmas de cada voz ----------
# Drogueria: campanita de puerta de tienda (dos notas, ding-dong brillante)
d=np.zeros(int(1.6*SR)); mezclar(d,campana(hz(88),1.4,1.3),0,1); mezclar(d,campana(hz(84),1.4,1.3),int(.22*SR),.9)
guardar('sfx_drogueria.wav',d)
# Orientadora: marimba calida, tres notas que suben (acogedor, "te escucho")
o=np.zeros(int(1.4*SR))
for k,m in enumerate([67,71,74]): mezclar(o,marimba(hz(m),1.1),int(k*.12*SR),1-.1*k)
guardar('sfx_orientadora.wav',o)
# Estudiantes: "pop" juguetón + glissando corto hacia arriba (energia juvenil)
n=int(.6*SR); tt=t(n); f=600+900*tt/.6
g=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*6)*.6
pop=np.sin(2*np.pi*(300+500*np.exp(-tt*40))*tt)*np.exp(-tt*30)
e=np.zeros(int(.9*SR)); mezclar(e,pop,0,1); mezclar(e,g,int(.05*SR),.7)
mezclar(e,marimba(hz(84),.6),int(.3*SR),.5)
guardar('sfx_estudiantes.wav',e)
# Conductor/a: barrido suave (transicion neutra)
n=int(1.2*SR); sw=np.random.randn(n); sw=lp(sw,.08); sw*=np.sin(np.pi*np.arange(n)/n)**2
guardar('sfx_conductor.wav',sw)
print('listo', ciclo, 's por ciclo')
