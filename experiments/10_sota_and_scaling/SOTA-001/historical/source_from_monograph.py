"""Part 1: Quick accuracy comparison (2 epochs, 2000 samples)"""
import torch, torch.nn as nn, torch.nn.functional as F, time, json, gc
from torchvision import datasets, transforms

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

class MLP(nn.Module):
    def __init__(self,i,nc=10):
        super().__init__()
        self.n=nn.Sequential(nn.Flatten(),nn.Linear(i,256),nn.ReLU(),nn.Linear(256,128),nn.ReLU(),nn.Linear(128,nc))
    def forward(self,x):return self.n(x)

tf=transforms.ToTensor()
trd=torch.utils.data.Subset(datasets.FashionMNIST('/tmp/data',True,download=True,transform=tf),range(2000))
ted=torch.utils.data.Subset(datasets.FashionMNIST('/tmp/data',False,download=True,transform=tf),range(500))
tl=torch.utils.data.DataLoader(trd,64,shuffle=True);el=torch.utils.data.DataLoader(ted,64)

R={}
for nm,mf in [("Fractal_SBOHN_v2",lambda:FractalSBOHN(28,1,10,16,4)),
              ("CNN",lambda:CNN(1,10)),("ViT-Tiny",lambda:ViT(28,1,10,64,4,2)),
              ("MLP",lambda:MLP(784,10))]:
    gc.collect();m=mf();np_=sum(p.numel() for p in m.parameters())
    mem=sum(p.nelement()*p.element_size() for p in m.parameters())/1e6
    o=torch.optim.Adam(m.parameters(),1e-3);cr=nn.CrossEntropyLoss()
    m.train()
    t0=time.time()
    for ep in range(3):
        for x,y in tl:o.zero_grad();cr(m(x),y).backward();o.step()
    tt=time.time()-t0
    m.eval();c=t=0
    with torch.no_grad():
        for x,y in el:c+=(m(x).argmax(1)==y).sum().item();t+=y.size(0)
    acc=c/t*100
    R[nm]={"acc":round(acc,1),"params":np_,"mem_mb":round(mem,2),"train_s":round(tt,1)}
    print(f"{nm:22s} | Acc:{acc:5.1f}% | Params:{np_:>7,} | Mem:{mem:.2f}MB | Train:{tt:.1f}s")
    del m;gc.collect()

with open('/tmp/sota_acc.json','w') as f:json.dump(R,f,indent=2)
print("Part 1 done")
