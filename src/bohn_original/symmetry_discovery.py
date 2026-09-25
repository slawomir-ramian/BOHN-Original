"""Małe narzędzia kontrolne Etapu 06; pełny bieg wykonuje kod historyczny."""
import numpy as np
def images(X): return np.asarray(X).reshape(-1,8,8)
def flat(X): return np.asarray(X).reshape(len(X),-1)
def flip_horizontal(X): return flat(images(X)[:,:,::-1])
def rotate_180(X): return flat(np.rot90(images(X),2,axes=(1,2)))
def random_permutation(X,seed): return np.asarray(X)[:,np.random.default_rng(seed).permutation(X.shape[1])]
def asymmetry(X,Y): return np.abs(np.asarray(X)-np.asarray(Y))
def sum_asymmetry(X,Y):
    X,Y=np.asarray(X),np.asarray(Y)
    return np.concatenate([X+Y,np.abs(X-Y)],axis=1)
