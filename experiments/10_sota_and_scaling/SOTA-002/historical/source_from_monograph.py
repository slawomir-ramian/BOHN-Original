"""Part 2: Inference Scaling Benchmark"""
import torch, torch.nn as nn, torch.nn.functional as F, time, json, gc, math


class SinkhornOp(nn.Module):
    def __init__(self, np_, fd, nh=4):
        super().__init__()
        self.nh=nh;self.np=np_;self.hd=fd//nh
        self.la=nn.Parameter(torch.randn(nh,np_,np_)*0.01)
        self.qn=nn.Linear(fd,nh*np_);self.op=nn.Linear(fd,fd)
    def forward(self, x):
        B=x.shape[0];q=self.qn(x.mean(1)).view(B,self.nh,self.np,1)
        la=self.la.unsqueeze(0)+q
        for _ in range(4):la=la-torch.logsumexp(la,-1,True);la=la-torch.logsumexp(la,-2,True)
        P=torch.exp(la);xh=x.view(B,self.np,self.nh,self.hd).permute(0,2,1,3)
        return self.op(torch.abs(xh-torch.matmul(P,xh)).permute(0,2,1,3).reshape(B,self.np,-1))

class FractalSBOHN(nn.Module):
    def __init__(self, ims=28,ch=1,nc=10,fd=16,nh=4):
        super().__init__()
        self.ps=max(4,ims//4);self.np=(ims//self.ps)**2;self.fd=fd
        self.pe=nn.Sequential(nn.Linear(ch*self.ps*self.ps,64),nn.ReLU(),nn.Linear(64,fd))
        self.lvs=nn.ModuleList();self.pls=nn.ModuleList();n=self.np
        for _ in range(3):
            if n<4:break
            self.lvs.append(SinkhornOp(n,fd,nh));nn_=max(n//2,2)
            self.pls.append(nn.Linear(n*fd,nn_*fd));n=nn_
        self.fn=n;self.cls=nn.Sequential(nn.Linear(n*fd,64),nn.ReLU(),nn.Linear(64,nc))
    def forward(self, x):
        B=x.shape[0]
        p=x.unfold(2,self.ps,self.ps).unfold(3,self.ps,self.ps).permute(0,2,3,1,4,5).contiguous().view(B,self.np,-1)
        h=self.pe(p)
        for l,pl in zip(self.lvs,self.pls):h=pl(l(h).reshape(B,-1)).view(B,-1,self.fd)
        return self.cls(h.reshape(B,-1))

class CNN(nn.Module):
    def __init__(self,ch=1,nc=10):
        super().__init__()
        self.f=nn.Sequential(nn.Conv2d(ch,16,3,1,1),nn.ReLU(),nn.Conv2d(16,32,3,2,1),nn.ReLU(),
                             nn.Conv2d(32,64,3,2,1),nn.ReLU(),nn.AdaptiveAvgPool2d(1))
        self.fc=nn.Linear(64,nc)
    def forward(self,x):return self.fc(self.f(x).flatten(1))

class ViT(nn.Module):
    def __init__(self,ims=28,ch=1,nc=10,d=64,nh=4,nl=2):
        super().__init__()
        self.ps=max(4,ims//4);self.np=(ims//self.ps)**2
        self.pe=nn.Linear(ch*self.ps*self.ps,d)
        self.pos=nn.Parameter(torch.randn(1,self.np+1,d)*0.02)
        self.ct=nn.Parameter(torch.randn(1,1,d)*0.02)
        self.tf=nn.TransformerEncoder(nn.TransformerEncoderLayer(d,nh,128,0.1,batch_first=True),nl)
        self.h=nn.Linear(d,nc)
    def forward(self, x):
        B=x.shape[0]
        p=x.unfold(2,self.ps,self.ps).unfold(3,self.ps,self.ps).permute(0,2,3,1,4,5).contiguous().view(B,self.np,-1)
        h=torch.cat([self.ct.expand(B,-1,-1),self.pe(p)],1)
        h=h+self.pos[:,:h.size(1),:];return self.h(self.tf(h)[:,0])


resolutions = [28, 56, 112, 224, 448]
results = {}

for nm, make_m in [
    ("Fractal_SBOHN_v2", lambda r: FractalSBOHN(r,1,10,16,4)),
    ("CNN", lambda r: CNN(1,10)),
    ("ViT-Tiny", lambda r: ViT(r,1,10,64,4,2)),
]:
    results[nm] = {"times":{},"params":{},"mem":{},"patches":{}}
    for res in resolutions:
        gc.collect()
        m = make_m(res)
        np_ = sum(p.numel() for p in m.parameters())
        mem = sum(p.nelement()*p.element_size() for p in m.parameters())/1e6
        n_patches = getattr(m, 'np', 0)

        x = torch.randn(1,1,res,res)
        with torch.no_grad(): _ = m(x)  # warmup
        ts = []
        for _ in range(3):
            t0=time.time()
            with torch.no_grad(): _ = m(x)
            ts.append((time.time()-t0)*1000)
        avg = sum(ts)/len(ts)

        results[nm]["times"][str(res)] = round(avg, 2)
        results[nm]["params"][str(res)] = np_
        results[nm]["mem"][str(res)] = round(mem, 3)
        results[nm]["patches"][str(res)] = n_patches

# Scaling analysis
for nm in results:
    times = results[nm]["times"]
    valid = [(int(r), t) for r,t in times.items() if t > 0]
    r1, t1 = valid[0]; r2, t2 = valid[-1]
    pixel_ratio = (r2*r2) / (r1*r1)
    time_ratio = t2 / t1
    exp = math.log(time_ratio) / math.log(pixel_ratio)

    # Extrapolate to 4K
    pixels_4k = 2160 * 3840
    t_4k = t2 * (pixels_4k / (r2*r2)) ** exp

    results[nm]["scaling_exp"] = round(exp, 3)
    results[nm]["est_4k_ms"] = round(t_4k, 1)

    print(f"{nm}: scaling_exp={exp:.3f}, estimated_4K={t_4k:.0f}ms")

with open('/tmp/sota_scaling.json','w') as f:json.dump(results,f,indent=2)
print("Part 2 done")
