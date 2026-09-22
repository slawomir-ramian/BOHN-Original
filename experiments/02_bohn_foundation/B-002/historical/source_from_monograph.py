import numpy as np

def compute_orbit_histogram(X, orbits):
    """
    Compute the orbit histogram Phi(X) in R^72.
    
    Parameters:
        X: data vector, shape (64,) or (batch, 64)
        orbits: list of orbits (list of lists of indices)
    
    Returns:
        Phi: orbit histogram, shape (72,) or (batch, 72)
    """
    single = (X.ndim == 1)
    if single:
        X = X[np.newaxis, :]  # (1, 64)
    
    batch_size = X.shape[0]
    n_orbits = len(orbits)
    
    # Three observables per orbit -> 3 * 24 = 72
    E = np.zeros((batch_size, n_orbits))  # Energy
    M = np.zeros((batch_size, n_orbits))  # Mean
    A = np.zeros((batch_size, n_orbits))  # Mean |X|
    
    for i, orbit in enumerate(orbits):
        orbit_idx = np.array(orbit)
        X_orbit = X[:, orbit_idx]  # (batch, |O_i|)
        
        # Energy: sum of squares
        E[:, i] = np.sum(X_orbit**2, axis=1)
        
        # Mean amplitude
        M[:, i] = np.mean(X_orbit, axis=1)
        
        # Mean absolute amplitude
        A[:, i] = np.mean(np.abs(X_orbit), axis=1)
    
    # Concatenate into a single vector
    Phi = np.concatenate([E, M, A], axis=1)  # (batch, 72)
    
    if single:
        return Phi[0]
    return Phi

# --- Demonstration ---
np.random.seed(42)
X_demo = np.random.randn(64)

Phi = compute_orbit_histogram(X_demo, orbits)

print("="*60)
print("ORBIT HISTOGRAM - DEMONSTRATION")
print("="*60)
print(f"Input dimension X:    {X_demo.shape[0]}")
print(f"Dimension of Phi(X):  {Phi.shape[0]}")
print(f"Number of orbits:     {len(orbits)}")
print()
print("First 5 orbits - observables:")
print(f"{'Orbita':<8} {'|O_i|':<6} {'E_i':<10} {'M_i':<10} {'A_i':<10}")
print("-"*44)
for i in range(5):
    E_i = Phi[i]
    M_i = Phi[len(orbits) + i]
    A_i = Phi[2*len(orbits) + i]
    print(f"  O_{i+1:<4} {len(orbits[i]):<6} "
          f"{E_i:<10.4f} {M_i:<10.4f} {A_i:<10.4f}")
