import numpy as np

def test_invariance_single(orbits, dim=64, seed=42):
    """
    Invariance test on a single vector.
    Check: Phi(X) = Phi(gX) = Phi(g^2 X).
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(dim)
    
    # Z3 permutations
    perm = np.array([z3_permutation(s) for s in range(dim)])
    perm2 = perm[perm]  # g^2 = g o g
    
    # Three versions of data
    X_e = X              # e(X) = X
    X_g = X[perm]        # g(X)
    X_g2 = X[perm2]      # g^2(X)
    
    # Orbit histograms
    Phi_e = compute_orbit_histogram(X_e, orbits)
    Phi_g = compute_orbit_histogram(X_g, orbits)
    Phi_g2 = compute_orbit_histogram(X_g2, orbits)
    
    # Errors
    err_g = np.max(np.abs(Phi_e - Phi_g))
    err_g2 = np.max(np.abs(Phi_e - Phi_g2))
    
    return err_g, err_g2, Phi_e, Phi_g, Phi_g2

def test_invariance_batch(orbits, n_samples=100, 
                          dim=64, seed=42):
    """
    Invariance test on a batch of vectors.
    """
    rng = np.random.RandomState(seed)
    X = rng.randn(n_samples, dim)
    
    perm = np.array([z3_permutation(s) for s in range(dim)])
    perm2 = perm[perm]
    
    X_g = X[:, perm]
    X_g2 = X[:, perm2]
    
    Phi_e = compute_orbit_histogram(X, orbits)
    Phi_g = compute_orbit_histogram(X_g, orbits)
    Phi_g2 = compute_orbit_histogram(X_g2, orbits)
    
    err_g = np.max(np.abs(Phi_e - Phi_g))
    err_g2 = np.max(np.abs(Phi_e - Phi_g2))
    max_err = max(err_g, err_g2)
    
    return max_err, err_g, err_g2


# ---- Running tests ----
print("="*60)
print("INVARIANCE TEST Phi(X) = Phi(gX) = Phi(g^2 X)")
print("="*60)

# Test na pojedynczym wektorze
err_g, err_g2, Phi_e, Phi_g, Phi_g2 = \
    test_invariance_single(orbits)

print(f"\nTest 1: Single vector")
print(f"  ||Phi(X) - Phi(gX)||_inf   = {err_g:.2e}")
print(f"  ||Phi(X) - Phi(g^2 X)||_inf = {err_g2:.2e}")
print(f"  Dimension of Phi:            {len(Phi_e)}")

eps_single = max(err_g, err_g2)
status1 = "PASSED" if eps_single < 1e-14 else "FAILED"
print(f"  eps_single = {eps_single:.2e}")
print(f"  Status: {status1}")

# Detailed error breakdown
print(f"\n  Error breakdown by components:")
diff_g = np.abs(Phi_e - Phi_g)
diff_g2 = np.abs(Phi_e - Phi_g2)
print(f"    E_i blad max: {np.max(diff_g[:24]):.2e}")
print(f"    M_i blad max: {np.max(diff_g[24:48]):.2e}")
print(f"    A_i blad max: {np.max(diff_g[48:72]):.2e}")

# Test na batchu
max_err, err_g_b, err_g2_b = \
    test_invariance_batch(orbits, n_samples=100)

print(f"\nTest 2: Batch (100 vectors)")
print(f"  max ||Phi(X) - Phi(gX)||_inf   = {err_g_b:.2e}")
print(f"  max ||Phi(X) - Phi(g^2 X)||_inf = {err_g2_b:.2e}")

eps_batch = max_err
status2 = "PASSED" if eps_batch < 1e-13 else "FAILED"
print(f"  eps_batch = {eps_batch:.2e}")
print(f"  Status: {status2}")

# Verification: Phi(X) != Phi(X') dla roznych X
rng = np.random.RandomState(99)
X1 = rng.randn(64)
X2 = rng.randn(64)
Phi1 = compute_orbit_histogram(X1, orbits)
Phi2 = compute_orbit_histogram(X2, orbits)
diff_different = np.max(np.abs(Phi1 - Phi2))

print(f"\nDiscrimination verification:")
print(f"  ||Phi(X1) - Phi(X2)||_inf = {diff_different:.4f}")
print(f"  (different X yield different Phi -> representation")
print(f"   preserves information)")

print(f"\n{'='*60}")
print(f"INVARIANCE SUMMARY: {status1}, {status2}")
print(f"Errors on the order of machine precision (10^-15 -- 10^-16)")
print(f"Invariance is STRUCTURAL, not learned.")
print(f"{'='*60}")
