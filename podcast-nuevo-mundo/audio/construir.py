"""Podcast Nuevo Mundo: arma la version mejorada a partir del MP3 original (que no se toca).
  python audio/construir.py
Lee audio/intervenciones.json  [{ "desde": s, "quien": "conductor|drogueria|orientadora|estudiantes|..." }]
(en tiempos del ORIGINAL; cada entrada dura hasta la siguiente). Escribe salida/podcast-mejorado.mp3."""
import numpy as np, subprocess, json, wave, os
SR=44100
ORIG='material/Podcast-en-audio.mp3'
LIMPIEZA=("highpass=f=85,afftdn=nr=12:nf=-40:tn=1,"
          "equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3000:t=q:w=1.2:g=2.5,"
          "equalizer=f=10000:t=h:w=3000:g=1.5,deesser=i=0.3,lowpass=f=15000")
PAUSA_MAX=0.50     # pausas mas largas que esto se acortan...
PAUSA_DEJA=0.35    # ...a esto
CAMBIO_HUECO=1.4   # aire entre intervenciones, donde suena la firma
FIRMA={'drogueria':'sfx_drogueria.wav','orientadora':'sfx_orientadora.wav','estudiantes':'sfx_estudiantes.wav','conductor':'sfx_conductor.wav'}
FIRMA_VOL=0.32
SIN_FIRMA=('presentacion',)
CAMA_VOL=0.20      # cama bajo la voz (ya con ducking encima)

def ff(*a): subprocess.run(['ffmpeg','-v','error','-y',*a],check=True)
def leer_raw(p,ch=1): return np.fromfile(p,np.float32).reshape(-1,ch)
def leer_wav(p):
    with wave.open(p) as w: x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768; return x.reshape(-1,w.getnchannels())
def db(x): return 20*np.log10(x+1e-9)

# 1) limpieza
ff('-i',ORIG,'-af',f'pan=mono|c0=0.5*c0+0.5*c1,{LIMPIEZA}','-ar',str(SR),'-f','f32le','cache/voz_limpia.raw')
v=leer_raw('cache/voz_limpia.raw')[:,0].copy()
interv=json.load(open('audio/intervenciones.json'))
bordes_aprox=[i['desde'] for i in interv]

H=int(0.02*SR)
def rms_frames(x):
    n=len(x)//H; return np.sqrt((x[:n*H].reshape(n,H)**2).mean(1))

# 2) mapa de voz/silencio con umbral relativo al piso local (cuadros de 20 ms)
r=db(rms_frames(v)); n=len(r)
piso=np.array([np.percentile(r[max(0,i-150):i+150],12) for i in range(0,n,25)]).repeat(25)[:n]
voz=(r>np.maximum(piso+9,-52))
def morf(m,largo,val):   # quita rachas de `val` mas cortas que `largo` cuadros
    m=m.copy(); i=0
    while i<len(m):
        if m[i]==val:
            j=i
            while j<len(m) and m[j]==val: j+=1
            if j-i<largo and i>0 and j<len(m): m[i:j]=not val
            i=j
        else: i+=1
    return m
voz=morf(voz,6,False); voz=morf(voz,3,True)
silencios=[]; j=0
while j<n:
    e=j
    while e<n and voz[e]==voz[j]: e+=1
    if not voz[j]: silencios.append([j*H,e*H])
    j=e

# 3) cada cambio de intervencion se ajusta al silencio mas largo a +-1,5 s del tiempo aproximado
#    "exacto": true -> no hay pausa (una voz arranca sobre la otra): se corta en el cuadro de menor
#    energia a +-0,15 s del tiempo dado, sin buscar silencio.
for k in range(1,len(interv)):
    if interv[k].get('exacto'):
        c=int(bordes_aprox[k]*SR)//H; w=r[c-7:c+8]; p=(c-7+int(np.argmin(w)))*H
        silencios=[s for s in silencios if not (s[0]<=p<=s[1])]+[[p,p]]
silencios.sort()
cambios={}
for k in range(1,len(interv)):
    t=bordes_aprox[k]*SR; mejor=None
    if interv[k].get('exacto'):
        c=int(t)//H; w=r[c-7:c+8]; p=(c-7+int(np.argmin(w)))*H
        cambios[silencios.index([p,p])]=k; continue
    for s_i,(a,b) in enumerate(silencios):
        d=0 if a<=t<=b else min(abs(a-t),abs(b-t))
        if d<=1.5*SR and (mejor is None or (b-a)-d*0.3>mejor[0]): mejor=((b-a)-d*0.3,s_i)
    if mejor is None:   # sin silencio cerca: se crea uno de 0 s en el punto
        silencios.append([int(t),int(t)]); silencios.sort(); 
        cambios={ (s if s<silencios.index([int(t),int(t)]) else s+1):kk for s,kk in cambios.items()}
        cambios[silencios.index([int(t),int(t)])]=k
    else: cambios[mejor[1]]=k
bordes=[0]+[0]*(len(interv)-1)+[len(v)]
for s_i,k in cambios.items(): bordes[k]=(silencios[s_i][0]+silencios[s_i][1])//2
for k in range(1,len(interv)):
    interv[k]['desde_ajustado']=round(bordes[k]/SR,2)

# 4) nivel por intervencion: RMS de los cuadros con voz -> -20 dBFS (rampa de 80 ms en el silencio)
gan=np.ones(len(v),np.float32)
for k in range(len(interv)):
    a,b=bordes[k],bordes[k+1]; seg=v[a:b]
    if b-a<H*10: continue
    rr=db(rms_frames(seg)); act=rr[rr>np.percentile(rr,90)-18]
    g=float(np.clip(10**((-20-db(np.sqrt(np.mean(10**(act/10)))))/20),0.25,6))
    gan[a:b]=g; interv[k]['ganancia_db']=round(float(db(g)),1)
R=int(0.08*SR); ker=np.ones(R)/R; gan=np.convolve(gan,ker,'same')
v=v*gan

# 5) nueva linea de tiempo: todo verbatim salvo pausas largas (se acortan) y cambios (aire fijo)
salida=[]; pos=0; marcas=[(0,0)]; cur=0; X=int(0.03*SR)
def pegar(x): 
    global pos; salida.append(x.astype(np.float32)); pos+=len(x)
def cruzar(a_fin,b_ini):   # une v[..a_fin] con v[b_ini..] con fundido cruzado de 30 ms
    global cur
    pegar(v[cur:a_fin-X]); fo=np.linspace(1,0,X)
    pegar(v[a_fin-X:a_fin]*fo+v[b_ini:b_ini+X]*(1-fo)); cur=b_ini+X
for s_i,(a,b) in enumerate(silencios):
    dur=(b-a)/SR
    rol=lambda k: 'conductor' if interv[k]['quien'] in ('conductor','presentacion') else interv[k]['quien']
    if s_i in cambios and rol(cambios[s_i])!=rol(cambios[s_i]-1):
        cola=min(int(0.18*SR),(b-a)//2); pegar(v[cur:a+cola]*1)
        fl=min(len(salida[-1]),int(.12*SR)); salida[-1][len(salida[-1])-fl:]*=np.linspace(1,0,fl)
        pegar(np.zeros(int((CAMBIO_HUECO-0.36)*SR)))
        ini=max(b-cola,a+cola); x=v[ini:b].copy(); 
        if len(x): x[:min(len(x),int(.1*SR))]*=np.linspace(0,1,min(len(x),int(.1*SR)))
        marcas.append((cambios[s_i],pos)); pegar(x); cur=b
    elif dur>PAUSA_MAX and a-cur>X*2:
        m=int(PAUSA_DEJA/2*SR); cruzar(a+m,b-m)
pegar(v[cur:])
voz_out=np.concatenate(salida)
voz_out.astype(np.float32).tofile('cache/voz_editada.raw')

# 5) compresion + loudnorm de la voz sola a -16 LUFS (dos pasadas)
comp='acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=3,alimiter=limit=0.89:level=false'
p=subprocess.run(['ffmpeg','-hide_banner','-f','f32le','-ar',str(SR),'-ac','1','-i','cache/voz_editada.raw','-af',comp+',loudnorm=I=-16:TP=-1.5:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
m=json.loads(p[p.rindex('{'):p.rindex('}')+1])
ln=f"loudnorm=I=-16:TP=-1.5:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
ff('-f','f32le','-ar',str(SR),'-ac','1','-i','cache/voz_editada.raw','-af',f'{comp},{ln}','-ar',str(SR),'-f','f32le','cache/voz_final.raw')
vf=leer_raw('cache/voz_final.raw')[:,0]

# 6) mezcla: cortina de entrada, voz, cama con ducking, firmas, cierre
intro=leer_wav('cache/intro.wav'); cierre=leer_wav('cache/cierre.wav'); cama_full=leer_wav('cache/cama.wav')
ENTRA=int(6.0*SR)                     # la voz entra a los 6 s, sobre la cola de la cortina
tot=ENTRA+len(vf)+int(1.0*SR)+len(cierre)
mix=np.zeros((tot,2),np.float32)
mix[:len(intro)]+=intro*0.55
voz_st=np.zeros(tot,np.float32); voz_st[ENTRA:ENTRA+len(vf)]=vf
# envolvente de la voz para ducking (ataque 30 ms, suelta 600 ms)
e=np.abs(voz_st); env=np.zeros_like(e); acc=0.0
blk=441; nb=len(e)//blk; eb=e[:nb*blk].reshape(nb,blk).max(1); envb=np.zeros(nb)
for i2 in range(nb):
    x=eb[i2]; acc = acc+(x-acc)*(0.5 if x>acc else 0.015); envb[i2]=acc
envb=np.repeat(envb,blk); envb=np.pad(envb,(0,tot-len(envb)),'edge')
duck=np.clip(1-np.clip((db(envb)+45)/20,0,1)*0.6,0.4,1)   # con voz la cama baja ~8 dB mas
cama=np.zeros((tot,2),np.float32)
a0=int(4.5*SR); b0=ENTRA+len(vf)+int(1.0*SR)
L=min(b0-a0,len(cama_full)); cama[a0:a0+L]=cama_full[:L]
fade=int(1.5*SR); cama[a0:a0+fade]*=np.linspace(0,1,fade)[:,None]; cama[a0+L-fade:a0+L]*=np.linspace(1,0,fade)[:,None]
mix+=cama*(CAMA_VOL*duck)[:,None]
mix+=voz_st[:,None]
for k,p_ in marcas:
    if k==0: continue
    f=FIRMA.get(interv[k]['quien'])
    if k>0 and interv[k-1]['quien'] in ('presentacion',) and interv[k]['quien']=='conductor': f=None
    if not f: continue
    s=leer_wav('cache/'+f); st=max(0,ENTRA+p_-int((CAMBIO_HUECO-0.36+0.08)*SR))
    mix[st:st+len(s)]+=s[:tot-st]*FIRMA_VOL
mix[b0:b0+len(cierre)]+=cierre[:tot-b0]*0.5
hablando=envb>10**(-30/20); camaL=(cama[:,0]*CAMA_VOL*duck)
print('cama bajo la voz: %.1f dB por debajo de la voz; cama en los huecos: %.1f dBFS'%(
    db(np.sqrt(np.mean(voz_st[hablando]**2)))-db(np.sqrt(np.mean(camaL[hablando]**2))),
    db(np.sqrt(np.mean(camaL[(~hablando)&(cama[:,0]!=0)]**2)))))
mix.astype(np.float32).tofile('cache/mezcla.raw')
os.makedirs('salida',exist_ok=True)
# la voz mono va igual en los dos canales: eso suma 3 dB a la medicion. Se baja para quedar en -16 LUFS
ff('-f','f32le','-ar',str(SR),'-ac','2','-i','cache/mezcla.raw','-af','volume=-3dB,alimiter=limit=0.84:level=false',
   '-c:a','libmp3lame','-b:a','192k','-metadata','title=Podcast Nuevo Mundo','salida/podcast-mejorado.mp3')
json.dump({'intervenciones':interv,'marcas_salida_s':[(k,round((ENTRA+p_)/SR,2)) for k,p_ in marcas],
           'duracion_original_s':round(len(v)/SR,1),'duracion_final_s':round(tot/SR,1)},
          open('cache/informe.json','w'),indent=1,ensure_ascii=False)
print('original %.1f s -> final %.1f s'%(len(v)/SR,tot/SR))
