import json
c=json.load(open("cortes.json",encoding="utf-8"))
def get(p,i): return next(s for s in c[p] if s["id"]==i)
get("p2","a")["in_s"]=6.20
a2=get("p2","a2"); b=get("p2","b"); a2["out_s"]=b["out_s"]; a2["texto"]=a2["texto"]+" "+b["texto"]; c["p2"].remove(b)
get("p2","e")["in_s"]=87.50
get("p1","h")["out_s"]=82.32
get("p1","c")["in_s"]=18.04
get("p2","h")["in_s"]=351.50
get("p2","h2")["in_s"]=363.56
get("p2","e2")["in_s"]=102.58
c["p1"]=[s for s in c["p1"] if s["id"]!="h"]
c["p2"]=[s for s in c["p2"] if s["id"]!="e2"]
X={"p1":dict(a=45,b=48,b2=48,c=48,d=35,f=48,e=52,g=48,h2=48,i=48,k=48,j=48),
   "p2":dict(a=38,a2=50,c=48,d=47,d2=47,e=47,f=47,f2=47,g=38,h=38,h2=38)}
for p in c:
    t=0
    for s in c[p]: s["x"]=X[p][s["id"]]; t+=s["out_s"]-s["in_s"]
    print(p,len(c[p]),"tramos",round(t,1),"s ->",round(t/1.1,1),"s a 1,1x")
json.dump(c,open("cortes-final.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)

# --- 2.a pasada (2026-11-27), verificada transcribiendo cada punto de entrada con whisper ---
# (corre sobre montaje/cortes.json; ver el bloque de abajo)
# p1-a in 203.56 (sin "es que") · p1-d in 86.46 (sin la cola de "alimentaria")
# p2-d in 61.56 (sin "que") · p2-d2 out 72.60 (entero "el 50 por ciento")
