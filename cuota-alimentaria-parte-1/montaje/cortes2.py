import json, wave, struct, math, unicodedata, sys
def norm(s): return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if c.isalnum() and not unicodedata.combining(c))
W={t:json.load(open(f"audio/dtw{t}.json",encoding="utf-8")) for t in ("79","80","81")}
def palabra(t, txt, aprox, cual):
    c=[w for w in W[t] if norm(w["text"])==norm(txt) and abs(w["startMs"]/1000-aprox)<2.5]
    if not c: sys.exit(f"no encuentro '{txt}' cerca de {aprox} en {t}")
    w=min(c,key=lambda w:abs(w["startMs"]/1000-aprox))
    return w["startMs"]/1000 if cual=="ini" else w["endMs"]/1000
def energia(t,a,z):
    w=wave.open(f"audio/{t}.wav");sr=w.getframerate();w.setpos(int(a*sr));raw=w.readframes(int((z-a)*sr))
    x=struct.unpack(f"<{len(raw)//2}h",raw);win=int(0.02*sr);hop=int(0.005*sr);r=[]
    for k in range(0,len(x)-win,hop):
        e=sum(v*v for v in x[k:k+win])/win;r.append((a+(k+win/2)/sr,10*math.log10(e/32768**2+1e-12)))
    return r
def corte_in(t,s):
    r=energia(t,s-0.30,s+0.06); m=min(r,key=lambda p:p[1]); return m
def corte_out(t,e):
    r=energia(t,e-0.06,e+0.30); m=min(r,key=lambda p:p[1]); return m
S=json.load(open("guion.json",encoding="utf-8"))
out={}
for p,L in S.items():
    tot=0;out[p]=[]
    for s in L:
        a=palabra(s["toma"],s["de"][0],s["de"][1],"ini"); z=palabra(s["toma"],s["a"][0],s["a"][1],"fin")
        (ia,da),(oz,dz)=corte_in(s["toma"],a),corte_out(s["toma"],z)
        ia=round(ia-0.02,2); oz=round(oz+0.06,2); tot+=oz-ia
        out[p].append(dict(s,in_s=ia,out_s=oz))
        print(f"{p}-{s['id']:3} {s['toma']} {ia:7.2f} {oz:7.2f} ({oz-ia:5.2f}s) {da:4.0f}/{dz:4.0f} dB  {s['texto'][:60]}")
    print(f"  {p}: {tot:.1f} s")
json.dump(out,open("cortes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
