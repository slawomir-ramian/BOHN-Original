"""Testowalne kontrakty architektur z listingów 62–64."""
from __future__ import annotations
import torch
import torch.nn as nn
import torch.nn.functional as F


def sinkhorn(log_alpha, n_iters=7):
    for _ in range(n_iters):
        log_alpha=log_alpha-torch.logsumexp(log_alpha,-1,True)
        log_alpha=log_alpha-torch.logsumexp(log_alpha,-2,True)
    return log_alpha.exp()


class PatchEncoder(nn.Module):
    def __init__(self,patch_size=7,n_patches=16,features_per_patch=16,hidden=128):
        super().__init__(); self.patch_size=patch_size; self.n_patches=n_patches
        self.patch_embed=nn.Linear(patch_size*patch_size,features_per_patch)
        self.encoder=nn.Sequential(nn.Linear(n_patches*features_per_patch,hidden),nn.ReLU()); self.hidden=hidden
    def forward(self,x,perm_matrix=None):
        p=F.unfold(x.view(x.shape[0],1,28,28),self.patch_size,stride=self.patch_size).transpose(1,2)
        p=self.patch_embed(p)
        if perm_matrix is not None:p=torch.matmul(perm_matrix.unsqueeze(0),p)
        return self.encoder(p.reshape(p.shape[0],-1))


class DeepPatchEncoder(PatchEncoder):
    def __init__(self,patch_size=7,n_patches=16,features_per_patch=16,hidden=128):
        super().__init__(patch_size,n_patches,features_per_patch,hidden)
        self.encoder=nn.Sequential(nn.Linear(n_patches*features_per_patch,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU())


class PermGenerator(nn.Module):
    def __init__(self,n_patches=16):
        super().__init__(); self.n_patches=n_patches
        self.support_encoder=nn.Sequential(nn.Linear(784,128),nn.ReLU(),nn.Linear(128,64),nn.ReLU())
        self.perm_head=nn.Linear(64,n_patches*n_patches)
    def forward(self,x): return sinkhorn(self.perm_head(self.support_encoder(x).mean(0)).view(self.n_patches,self.n_patches))


class SinkhornLayer(nn.Module):
    def __init__(self,size,tau=.1,iters=7):
        super().__init__(); self.log_alpha=nn.Parameter(torch.randn(size,size)*.01); self.tau=tau; self.iters=iters
    def forward(self,x): return x@sinkhorn(self.log_alpha/self.tau,self.iters)


class FrozenEncoder(nn.Module):
    def __init__(self,input_dim=784,hidden=128,feat_dim=64):
        super().__init__(); self.net=nn.Sequential(nn.Linear(input_dim,hidden),nn.ReLU(),nn.Linear(hidden,feat_dim),nn.ReLU())
    def forward(self,x): return self.net(x)


class Expert(nn.Module):
    def __init__(self,feat_dim=64,n_classes=10):
        super().__init__(); self.perm=SinkhornLayer(feat_dim); self.head=nn.Linear(feat_dim,n_classes)
    def forward(self,x): return self.head(self.perm(x))


class MetaPermGenerator(nn.Module):
    def __init__(self,feat_dim=64,hidden=128):
        super().__init__(); self.feat_dim=feat_dim
        self.task_encoder=nn.Sequential(nn.Linear(feat_dim,hidden),nn.ReLU(),nn.Linear(hidden,hidden),nn.ReLU())
        self.perm_decoder=nn.Linear(hidden,feat_dim*feat_dim)
    def forward(self,x): return self.perm_decoder(self.task_encoder(x.mean(0,keepdim=True))).view(self.feat_dim,self.feat_dim)*.01


class TaskRouter(nn.Module):
    def __init__(self,feat_dim=64,n_experts=4):
        super().__init__(); self.gate=nn.Sequential(nn.Linear(feat_dim,32),nn.ReLU(),nn.Linear(32,n_experts))
    def forward(self,x): return F.softmax(self.gate(x),-1)


def parameter_count(model): return sum(p.numel() for p in model.parameters())
