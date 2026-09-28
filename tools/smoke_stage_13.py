#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))


def main():
    p=argparse.ArgumentParser(); p.add_argument("--only",required=True); a=p.parse_args()
    import torch
    from bohn_original.integrated_system import PatchEncoder,DeepPatchEncoder,PermGenerator,FrozenEncoder,Expert,MetaPermGenerator,TaskRouter,parameter_count
    with torch.no_grad():
        x=torch.randn(3,1,28,28); patch=PatchEncoder(); deep=DeepPatchEncoder(); perm=PermGenerator()(torch.randn(5,784))
        frozen=FrozenEncoder(); feat=frozen(torch.randn(3,784)); expert=Expert(); meta=MetaPermGenerator(); router=TaskRouter()
        payload={"id":a.only,"patch_shape":list(patch(x).shape),"deep_shape":list(deep(x).shape),"perm_shape":list(perm.shape),
                 "expert_shape":list(expert(feat).shape),"meta_shape":list(meta(feat).shape),"router_shape":list(router(feat).shape),
                 "params":{"PatchEncoder":parameter_count(patch),"DeepPatchEncoder":parameter_count(deep),"FrozenEncoder":parameter_count(frozen),
                           "Expert":parameter_count(expert),"MetaPermGenerator":parameter_count(meta),"TaskRouter":parameter_count(router)}}
    print(json.dumps(payload,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
