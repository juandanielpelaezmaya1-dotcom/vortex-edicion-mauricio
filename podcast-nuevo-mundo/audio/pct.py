import numpy as np,sys
x=np.fromfile(sys.argv[1],np.float32); w=4410; n=len(x)//w
db=20*np.log10(np.sqrt((x[:n*w].reshape(n,w)**2).mean(1))+1e-9)
print(sys.argv[1][-12:], 'piso p10 %.1f  voz p80 %.1f  -> SNR %.1f dB'%(np.percentile(db,10),np.percentile(db,80),np.percentile(db,80)-np.percentile(db,10)))
