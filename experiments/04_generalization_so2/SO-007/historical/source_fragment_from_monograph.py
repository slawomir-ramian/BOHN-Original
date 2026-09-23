def so2_sbohn_features(X, K=4, N_theta=500):
    """Moments M_1..M_K of the asymmetry profile for each 2D block."""
    n_samples = X.shape[0]
    n_blocks = X.shape[1] // 2
    features = np.zeros((n_samples, n_blocks * K))
    thetas = np.linspace(0, 2*np.pi, N_theta, endpoint=False)
    for i in range(n_samples):
        for b in range(n_blocks):
            xb = X[i, 2*b:2*b+2]
            A_vals = np.array([norm(xb - rotation_matrix(th) @ xb) 
                               for th in thetas])
            for k in range(1, K+1):
                features[i, b*K + (k-1)] = np.mean(A_vals**k)
    return features
