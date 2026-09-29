
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RMIG-FBOHN / Meta-FBOHN experimental suite.
This single script reproduces the experiments added after BOHN v4:
  - rmig_fbohn_v1
  - noise_robustness
  - test_a_out_of_representation
  - meta_fbohn_v2_orbitwise
  - meta_fbohn_v3_mixing
  - meta_fbohn_v4_symbolic
  - meta_fbohn_v5_library

Dependencies: numpy, pandas, scikit-learn.
Usage examples:
  python bohn_v4_update_rmig_fbohn_suite.py --experiment v1
  python bohn_v4_update_rmig_fbohn_suite.py --experiment v4 --seeds 10
  python bohn_v4_update_rmig_fbohn_suite.py --experiment v5 --seeds 3 --discovery-runs 5 --generations 15
"""
import argparse
import time
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

EPS = 1e-6
N_NODES = 18
ORBIT_SIZE = 3
N_ORBITS = 6
TEST_SIZE = 0.30
ALPHA_LAPLACIAN = 0.70

# ------------------------------------------------------------
# RMIG graph: 18 nodes, six Z3 orbits
# ------------------------------------------------------------
def rmig_orbits():
    return [[3*i, 3*i+1, 3*i+2] for i in range(N_ORBITS)]

ORBITS = rmig_orbits()

def z3_permutation(k=1):
    perm = np.arange(N_NODES)
    for orbit in ORBITS:
        for j, node in enumerate(orbit):
            perm[node] = orbit[(j+k) % ORBIT_SIZE]
    return perm

Z3_PERMS = [z3_permutation(0), z3_permutation(1), z3_permutation(2)]

def build_rmig_edges():
    edges = set()
    # triangles inside orbits
    for orbit in ORBITS:
        a,b,c = orbit
        for u,v in [(a,b),(b,c),(c,a)]:
            edges.add(tuple(sorted((u,v))))
    # radial edges between consecutive orbits
    for i in range(N_ORBITS-1):
        for j in range(ORBIT_SIZE):
            edges.add(tuple(sorted((ORBITS[i][j], ORBITS[i+1][j]))))
    # Z3-equivariant cross-fractal edges
    cross_pairs = [(0,2,1),(1,3,2),(2,4,1),(3,5,2),(0,3,2),(1,4,1),(2,5,2)]
    for i,j,shift in cross_pairs:
        for k in range(ORBIT_SIZE):
            edges.add(tuple(sorted((ORBITS[i][k], ORBITS[j][(k+shift)%ORBIT_SIZE]))))
    return sorted(edges)

EDGES = build_rmig_edges()

def adjacency_matrix(edges):
    A = np.zeros((N_NODES, N_NODES), dtype=float)
    for u,v in edges:
        A[u,v] = A[v,u] = 1.0
    return A

ADJ = adjacency_matrix(EDGES)
DEG = np.diag(ADJ.sum(axis=1))
LAPLACIAN = DEG - ADJ

def check_z3_equivariance():
    for perm in Z3_PERMS:
        P = np.eye(N_NODES)[perm]
        if not np.allclose(P.T @ ADJ @ P, ADJ):
            return False
    return True

def graph_summary():
    return dict(n_nodes=N_NODES, n_edges=len(EDGES), n_orbits=len(ORBITS),
                orbit_size=ORBIT_SIZE, z3_equivariant=check_z3_equivariance(),
                avg_degree=float(ADJ.sum(axis=1).mean()),
                min_degree=int(ADJ.sum(axis=1).min()), max_degree=int(ADJ.sum(axis=1).max()))

# ------------------------------------------------------------
# Data and features
# ------------------------------------------------------------
def generate_signals(n_samples, seed=0):
    rng = np.random.default_rng(seed)
    base = rng.normal(size=(n_samples, N_NODES))
    beta = 0.25
    X = base @ (np.eye(N_NODES) + beta*ADJ)
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + EPS)
    return X

def laplacian_signal(X):
    return X @ LAPLACIAN.T

def orbit_energy(X):
    return np.column_stack([np.sum(X[:,O]**2, axis=1) for O in ORBITS])

def orbit_mean(X):
    return np.column_stack([np.mean(X[:,O], axis=1) for O in ORBITS])

def orbit_abs_dev(X):
    feats=[]
    for O in ORBITS:
        mu = np.mean(X[:,O], axis=1, keepdims=True)
        feats.append(np.mean(np.abs(X[:,O]-mu), axis=1))
    return np.column_stack(feats)

def orbit_laplacian_energy(X):
    LX = laplacian_signal(X)
    return np.column_stack([np.sum(LX[:,O]**2, axis=1) for O in ORBITS])

def orbit_laplacian_mean(X):
    LX = laplacian_signal(X)
    return np.column_stack([np.mean(LX[:,O], axis=1) for O in ORBITS])

def raw_features(X): return X

def bohn_blocks(X):
    return dict(E=orbit_energy(X), M=orbit_mean(X), A=orbit_abs_dev(X))

def fbohn_blocks(X):
    return dict(E=orbit_energy(X), M=orbit_mean(X), A=orbit_abs_dev(X),
                S=orbit_laplacian_energy(X), L=orbit_laplacian_mean(X))

def bohn_features(X):
    b=bohn_blocks(X); return np.concatenate([b['E'], b['M'], b['A']], axis=1)

def fbohn_features(X):
    b=fbohn_blocks(X); return np.concatenate([b['E'], b['M'], b['A'], b['S'], b['L']], axis=1)

def fbohn_feature_names():
    return [f"{block}_{i}" for block in ['E','M','A','S','L'] for i in range(N_ORBITS)]
FBOHN_DIM = 5*N_ORBITS
FBOHN_NAMES = fbohn_feature_names()

def fbohn_poly_control_features(X):
    b=fbohn_blocks(X); E,M,A,S,L = b['E'],b['M'],b['A'],b['S'],b['L']
    feats = [fbohn_features(X), E*S, E*A, A*S, M*L,
             np.sqrt(np.abs(E*S)+EPS), np.sqrt(np.abs(A*S)+EPS),
             np.tanh(E-S), np.tanh(A-L), np.tanh(M+L)]
    return np.concatenate(feats, axis=1)

# ------------------------------------------------------------
# Labels
# ------------------------------------------------------------
def make_fbohn_labels(X, seed=0, alpha=ALPHA_LAPLACIAN, noise=0.1):
    rng = np.random.default_rng(seed)
    E = orbit_energy(X); S = orbit_laplacian_energy(X)
    wE = np.array([1.4,0.0,1.0,0.0,0.8,0.0])
    wS = np.array([0.0,1.2,0.0,0.9,0.0,1.1])
    signal = E@wE + alpha*(S@wS) + 0.20*E[:,0]*S[:,1]/(1+np.abs(E[:,0]))
    signal += noise*rng.normal(size=X.shape[0])
    return (signal > np.median(signal)).astype(int)

def make_out_of_representation_labels(X, seed=0, noise=0.1):
    rng = np.random.default_rng(seed)
    signal = (np.sin(X[:,3]*X[:,8]) + np.cos(X[:,5]*X[:,11])
              + 0.75*X[:,1]*X[:,7]*X[:,14] + 0.50*X[:,2]*X[:,13]
              - 0.35*X[:,4]*X[:,9] + 0.25*X[:,0]*X[:,6]
              - 0.20*X[:,10]*X[:,17])
    signal += noise*rng.normal(size=X.shape[0])
    return (signal > np.median(signal)).astype(int)

# ------------------------------------------------------------
# Classifier utilities
# ------------------------------------------------------------
def make_classifier():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, solver='lbfgs'))

def evaluate_features_split(X_feat, y, seed):
    Xtr, Xte, ytr, yte = train_test_split(X_feat, y, test_size=TEST_SIZE,
                                          random_state=seed, stratify=y)
    model = make_classifier(); model.fit(Xtr, ytr)
    return accuracy_score(yte, model.predict(Xte))

def evaluate_pca_representation(X_feat, y, seed, latent_dim):
    Xtr, Xte, ytr, yte = train_test_split(X_feat, y, test_size=TEST_SIZE,
                                          random_state=seed, stratify=y)
    model = make_pipeline(StandardScaler(), PCA(n_components=latent_dim, random_state=seed),
                          StandardScaler(), LogisticRegression(max_iter=3000, solver='lbfgs'))
    model.fit(Xtr, ytr)
    pca = model.named_steps['pca']
    return accuracy_score(yte, model.predict(Xte)), float(np.sum(pca.explained_variance_ratio_))

# ------------------------------------------------------------
# Meta-FBOHN v1/v2: weighting, included to show invariance under StandardScaler
# ------------------------------------------------------------
def softplus(x): return np.log1p(np.exp(x))

def weighted_fbohn_global(X, theta5):
    w=softplus(np.asarray(theta5)); b=fbohn_blocks(X)
    return np.concatenate([w[0]*b['E'], w[1]*b['M'], w[2]*b['A'], w[3]*b['S'], w[4]*b['L']], axis=1)

def weighted_fbohn_orbitwise(X, theta30):
    return fbohn_features(X) * softplus(np.asarray(theta30)).reshape(1,-1)

def mutate_theta(theta, rng, sigma=0.35): return theta + sigma*rng.normal(size=theta.shape)

def crossover_theta(t1,t2,rng):
    a=rng.uniform(); return a*t1 + (1-a)*t2

def evolve_weighted_meta(X, y, seed, mode='global', pop=70, generations=25, elite=7):
    rng=np.random.default_rng(seed); dim=5 if mode=='global' else FBOHN_DIM
    population=[rng.normal(scale=1.0, size=dim) for _ in range(pop)]
    best=None; hist=[]
    for gen in range(generations):
        scored=[]
        for theta in population:
            F = weighted_fbohn_global(X,theta) if mode=='global' else weighted_fbohn_orbitwise(X,theta)
            scored.append(dict(theta=theta, accuracy=evaluate_features_split(F,y,seed)))
        scored=sorted(scored, key=lambda d:d['accuracy'], reverse=True)
        if best is None or scored[0]['accuracy']>best['accuracy']: best=scored[0]
        hist.append(dict(generation=gen, best_accuracy=scored[0]['accuracy'], global_best_accuracy=best['accuracy'], mean_accuracy=float(np.mean([s['accuracy'] for s in scored]))))
        elites=[s['theta'] for s in scored[:elite]]; new=elites.copy()
        while len(new)<pop:
            if rng.random()<0.6: child=mutate_theta(elites[rng.integers(0,elite)], rng, 0.35)
            else: child=mutate_theta(crossover_theta(elites[rng.integers(0,elite)], elites[rng.integers(0,elite)], rng), rng, 0.20)
            new.append(child)
        population=new
    return best, pd.DataFrame(hist)

# ------------------------------------------------------------
# Meta-FBOHN v3: learned orbit mixing
# ------------------------------------------------------------
def theta_dim_v3(mix_features): return mix_features*FBOHN_DIM + mix_features + mix_features

def unpack_theta_v3(theta, mix_features):
    n_w=mix_features*FBOHN_DIM; n_b=mix_features
    W=theta[:n_w].reshape(mix_features,FBOHN_DIM); b=theta[n_w:n_w+n_b]
    gate=1/(1+np.exp(-theta[n_w+n_b:n_w+n_b+mix_features]))
    return W,b,gate

def meta_fbohn_v3_features(X, theta, mix_features=12, include_base=True):
    F=fbohn_features(X); W,b,gate=unpack_theta_v3(theta,mix_features)
    Z=np.tanh((F@W.T)/np.sqrt(FBOHN_DIM)+b.reshape(1,-1))*gate.reshape(1,-1)
    return np.concatenate([F,Z],axis=1) if include_base else Z

def evolve_mixing_v3(X,y,seed,mix_features=12,pop=80,generations=30,elite=8):
    rng=np.random.default_rng(seed); dim=theta_dim_v3(mix_features)
    population=[rng.normal(scale=0.50,size=dim) for _ in range(pop)]
    best=None; hist=[]
    for gen in range(generations):
        scored=[]
        for theta in population:
            F=meta_fbohn_v3_features(X,theta,mix_features,True)
            scored.append(dict(theta=theta, accuracy=evaluate_features_split(F,y,seed)))
        scored=sorted(scored,key=lambda d:d['accuracy'],reverse=True)
        if best is None or scored[0]['accuracy']>best['accuracy']: best=scored[0]
        hist.append(dict(generation=gen,best_accuracy=scored[0]['accuracy'],global_best_accuracy=best['accuracy'],mean_accuracy=float(np.mean([s['accuracy'] for s in scored]))))
        elites=[s['theta'] for s in scored[:elite]]; new=elites.copy()
        while len(new)<pop:
            if rng.random()<0.6: child=mutate_theta(elites[rng.integers(0,elite)], rng, 0.20)
            else: child=mutate_theta(crossover_theta(elites[rng.integers(0,elite)], elites[rng.integers(0,elite)], rng), rng, 0.12)
            new.append(child)
        population=new
    return best,pd.DataFrame(hist)

# ------------------------------------------------------------
# Meta-FBOHN v4/v5: symbolic operators and library discovery
# ------------------------------------------------------------
OPS=['add','sub','mul','ratio','sqrt_prod','absdiff','tanh_diff','tanh_sum']

def safe_ratio(a,b): return a/(np.abs(b)+EPS)

def symbolic_op(a,b,op):
    if op=='add': return a+b
    if op=='sub': return a-b
    if op=='mul': return a*b
    if op=='ratio': return safe_ratio(a,b)
    if op=='sqrt_prod': return np.sqrt(np.abs(a*b)+EPS)
    if op=='absdiff': return np.abs(a-b)
    if op=='tanh_diff': return np.tanh(a-b)
    if op=='tanh_sum': return np.tanh(a+b)
    raise ValueError(op)

def random_gene(rng): return dict(op=int(rng.integers(0,len(OPS))), i=int(rng.integers(0,FBOHN_DIM)), j=int(rng.integers(0,FBOHN_DIM)))

def random_genome(rng,n_symbolic_features=16): return [random_gene(rng) for _ in range(n_symbolic_features)]

def gene_key(g):
    op=OPS[int(g['op'])]; i=int(g['i']); j=int(g['j'])
    if op in ['add','mul','sqrt_prod']: i,j=sorted([i,j])
    return (op,i,j)

def key_to_gene(k): return dict(op=OPS.index(k[0]), i=int(k[1]), j=int(k[2]))

def gene_to_string(g):
    op=OPS[int(g['op'])]; fi=FBOHN_NAMES[int(g['i'])]; fj=FBOHN_NAMES[int(g['j'])]
    return {'add':f'({fi}+{fj})','sub':f'({fi}-{fj})','mul':f'({fi}*{fj})','ratio':f'({fi}/|{fj}|)',
            'sqrt_prod':f'sqrt(|{fi}*{fj}|)','absdiff':f'|{fi}-{fj}|','tanh_diff':f'tanh({fi}-{fj})','tanh_sum':f'tanh({fi}+{fj})'}[op]

def genome_to_strings(genome): return [gene_to_string(g) for g in genome]

def genome_to_symbolic_features(F, genome):
    cols=[]
    for g in genome:
        z=symbolic_op(F[:,int(g['i'])], F[:,int(g['j'])], OPS[int(g['op'])])
        cols.append(np.clip(z,-20.0,20.0))
    return np.column_stack(cols)

def symbolic_fbohn_features(X, genome, include_base=True):
    F=fbohn_features(X); Z=genome_to_symbolic_features(F,genome)
    return np.concatenate([F,Z],axis=1) if include_base else Z

def mutate_gene(g,rng,p_op=0.25,p_idx=0.45):
    out=dict(g)
    if rng.random()<p_op: out['op']=int(rng.integers(0,len(OPS)))
    if rng.random()<p_idx: out['i']=int(rng.integers(0,FBOHN_DIM))
    if rng.random()<p_idx: out['j']=int(rng.integers(0,FBOHN_DIM))
    return out

def mutate_genome(genome,rng):
    child=[mutate_gene(g,rng) if rng.random()<0.35 else dict(g) for g in genome]
    if rng.random()<0.15: child[int(rng.integers(0,len(child)))] = random_gene(rng)
    return child

def crossover_genome(g1,g2,rng): return [dict(a if rng.random()<0.5 else b) for a,b in zip(g1,g2)]

def operator_counts_from_keys(keys):
    c=Counter(k[0] for k in keys); return {op:int(c.get(op,0)) for op in OPS}

def evolve_symbolic_composer(X,y,seed,pop=80,generations=30,elite=8,n_symbolic_features=16):
    rng=np.random.default_rng(seed); population=[random_genome(rng,n_symbolic_features) for _ in range(pop)]
    best=None; hist=[]
    for gen in range(generations):
        scored=[]
        for genome in population:
            F=symbolic_fbohn_features(X,genome,True)
            scored.append(dict(genome=genome, accuracy=evaluate_features_split(F,y,seed)))
        scored=sorted(scored,key=lambda d:d['accuracy'],reverse=True)
        if best is None or scored[0]['accuracy']>best['accuracy']: best=scored[0]
        hist.append(dict(generation=gen,best_accuracy=scored[0]['accuracy'],global_best_accuracy=best['accuracy'],mean_accuracy=float(np.mean([s['accuracy'] for s in scored]))))
        elites=[s['genome'] for s in scored[:elite]]; new=[list(map(dict,g)) for g in elites]
        while len(new)<pop:
            if rng.random()<0.60: child=mutate_genome(elites[int(rng.integers(0,elite))],rng)
            else: child=mutate_genome(crossover_genome(elites[int(rng.integers(0,elite))],elites[int(rng.integers(0,elite))],rng),rng)
            new.append(child)
        population=new
    return best,pd.DataFrame(hist)

def discover_library_for_dataset(X,y,seed_base,runs=12,library_size=32,pop=80,generations=30,elite=8,n_symbolic_features=16):
    counter=Counter(); weighted=defaultdict(float); run_rows=[]
    for r in range(runs):
        best,hist=evolve_symbolic_composer(X,y,seed_base+10000*r,pop,generations,elite,n_symbolic_features)
        for gene in best['genome']:
            k=gene_key(gene); counter[k]+=1; weighted[k]+=best['accuracy']
        run_rows.append(dict(discovery_run=r, accuracy=best['accuracy'], best_genome=genome_to_strings(best['genome']), operator_counts=operator_counts_from_keys([gene_key(g) for g in best['genome']])))
    keys_sorted=sorted(counter.keys(), key=lambda k:(counter[k],weighted[k]), reverse=True)
    library=keys_sorted[:library_size]
    lib_rows=[dict(symbol=gene_to_string(key_to_gene(k)), key=k, count=int(counter[k]), weighted_score=float(weighted[k]), operator=k[0], feature_i=FBOHN_NAMES[k[1]], feature_j=FBOHN_NAMES[k[2]]) for k in library]
    return library,pd.DataFrame(lib_rows),pd.DataFrame(run_rows)

# ------------------------------------------------------------
# Experiment runners
# ------------------------------------------------------------
def evaluate_standard_reps(X,y,seed):
    reps={'RAW':raw_features(X),'BOHN':bohn_features(X),'FBOHN':fbohn_features(X),'FBOHN-poly-control':fbohn_poly_control_features(X)}
    return [dict(representation=k, feature_dim=v.shape[1], accuracy=evaluate_features_split(v,y,seed)) for k,v in reps.items()]

def run_v1(seed, n_samples=6000, noise=0.10):
    X=generate_signals(n_samples,seed); y=make_fbohn_labels(X,seed+123,noise=noise)
    rows=[]
    for name,F in {'RAW':raw_features(X),'BOHN':bohn_features(X),'FBOHN':fbohn_features(X)}.items():
        rows.append(dict(seed=seed, representation=name, feature_dim=F.shape[1], accuracy=evaluate_features_split(F,y,seed), explained_variance=np.nan))
    for k in [2,4,6,8,12]:
        acc,ev=evaluate_pca_representation(fbohn_features(X),y,seed,k)
        rows.append(dict(seed=seed, representation=f'FBOHN_SRL_{k}', feature_dim=k, accuracy=acc, explained_variance=ev))
    return rows

def run_experiment(args):
    t0=time.perf_counter(); seeds=list(range(args.seeds)); noises=args.noises
    print('Graph summary:'); print(pd.DataFrame([graph_summary()]).to_string(index=False))
    print(f'Experiment={args.experiment}, samples={args.samples}, seeds={seeds}, noises={noises}')
    all_rows=[]; all_libraries=[]; all_discovery=[]
    if args.experiment=='v1':
        for seed in seeds:
            rows=run_v1(seed,args.samples,0.10); all_rows.extend(rows); print(pd.DataFrame(rows).to_string(index=False))
    else:
        for noise in noises:
            print('\n'+'='*30+f' NOISE={noise} '+'='*30)
            for seed in seeds:
                X=generate_signals(args.samples,seed)
                y=make_out_of_representation_labels(X,seed+123,noise=noise) if args.experiment!='noise' else make_fbohn_labels(X,seed+123,noise=noise)
                rows=[]
                for r in evaluate_standard_reps(X,y,seed): rows.append(dict(seed=seed,noise=noise,**r,extra=''))
                if args.experiment in ['v2']:
                    for mode,label in [('global','Meta-FBOHN-v1-global'),('orbitwise','Meta-FBOHN-v2-orbitwise')]:
                        best,_=evolve_weighted_meta(X,y,seed+int(noise*1000)+(111 if mode=='global' else 222),mode,args.population,args.generations,args.elite)
                        F=weighted_fbohn_global(X,best['theta']) if mode=='global' else weighted_fbohn_orbitwise(X,best['theta'])
                        rows.append(dict(seed=seed,noise=noise,representation=label,feature_dim=F.shape[1],accuracy=evaluate_features_split(F,y,seed),extra=str(np.round(softplus(best['theta']),4).tolist())))
                if args.experiment in ['v3']:
                    best,_=evolve_mixing_v3(X,y,seed+int(noise*1000)+333,args.mix_features,args.population,args.generations,args.elite)
                    F=meta_fbohn_v3_features(X,best['theta'],args.mix_features,True)
                    rows.append(dict(seed=seed,noise=noise,representation='Meta-FBOHN-v3-mixing',feature_dim=F.shape[1],accuracy=evaluate_features_split(F,y,seed),extra='theta omitted'))
                if args.experiment in ['v4','v5']:
                    best,_=evolve_symbolic_composer(X,y,seed+int(noise*1000)+444,args.population,args.generations,args.elite,args.n_symbolic)
                    F=symbolic_fbohn_features(X,best['genome'],True)
                    rows.append(dict(seed=seed,noise=noise,representation='Meta-FBOHN-v4-single',feature_dim=F.shape[1],accuracy=evaluate_features_split(F,y,seed),extra=str(genome_to_strings(best['genome']))))
                if args.experiment=='v5':
                    lib,lib_df,disc_df=discover_library_for_dataset(X,y,seed+int(noise*1000)+555,args.discovery_runs,args.library_size,args.population,args.generations,args.elite,args.n_symbolic)
                    F=symbolic_fbohn_features(X,[key_to_gene(k) for k in lib],True)
                    rows.append(dict(seed=seed,noise=noise,representation='Meta-FBOHN-v5-library',feature_dim=F.shape[1],accuracy=evaluate_features_split(F,y,seed),extra=str([gene_to_string(key_to_gene(k)) for k in lib])))
                    lib_df['seed']=seed; lib_df['noise']=noise; all_libraries.append(lib_df)
                    disc_df['seed']=seed; disc_df['noise']=noise; all_discovery.append(disc_df)
                all_rows.extend(rows)
                print(pd.DataFrame(rows)[['seed','noise','representation','accuracy','feature_dim']].to_string(index=False))
    df=pd.DataFrame(all_rows)
    print('\nRAW RESULTS'); print(df.to_string(index=False))
    if 'noise' in df.columns:
        summary=df.groupby(['noise','representation']).agg(acc_mean=('accuracy','mean'), acc_std=('accuracy','std'), feature_dim=('feature_dim','mean')).reset_index().sort_values(['noise','acc_mean'],ascending=[True,False])
    else:
        summary=df.groupby(['representation']).agg(acc_mean=('accuracy','mean'), acc_std=('accuracy','std'), feature_dim=('feature_dim','mean')).reset_index().sort_values('acc_mean',ascending=False)
    print('\nSUMMARY'); print(summary.to_string(index=False))
    if all_libraries:
        lib_df=pd.concat(all_libraries,ignore_index=True)
        global_counts=lib_df.groupby(['symbol','operator','feature_i','feature_j']).agg(total_count=('count','sum'), appearances=('count','count'), mean_weighted_score=('weighted_score','mean')).reset_index().sort_values(['appearances','total_count','mean_weighted_score'],ascending=False)
        ops=lib_df.groupby('operator').agg(total_count=('count','sum'), appearances=('operator','count'), mean_weighted_score=('weighted_score','mean')).reset_index().sort_values('total_count',ascending=False)
        print('\nGLOBAL SYMBOL COUNTS'); print(global_counts.head(80).to_string(index=False))
        print('\nOPERATOR STATS'); print(ops.to_string(index=False))
    print(f'Elapsed time: {time.perf_counter()-t0:.2f} sec')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--experiment', choices=['v1','noise','testA','v2','v3','v4','v5'], default='v4')
    p.add_argument('--samples', type=int, default=6000)
    p.add_argument('--seeds', type=int, default=10)
    p.add_argument('--noises', type=float, nargs='*', default=[0.0,0.1,0.3,0.5])
    p.add_argument('--population', type=int, default=80)
    p.add_argument('--generations', type=int, default=30)
    p.add_argument('--elite', type=int, default=8)
    p.add_argument('--mix-features', type=int, default=12)
    p.add_argument('--n-symbolic', type=int, default=16)
    p.add_argument('--discovery-runs', type=int, default=12)
    p.add_argument('--library-size', type=int, default=32)
    args=p.parse_args()
    run_experiment(args)
