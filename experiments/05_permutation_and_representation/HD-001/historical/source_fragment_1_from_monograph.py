def sbohn_z3_features(X, perm_g):
    gX = X[:, perm_g]
    g2X = gX[:, perm_g]
    S3 = X + gX + g2X
    A1 = np.abs(X - gX)
    A2 = np.abs(X - g2X)
    return np.concatenate([S3, A1, A2], axis=1)
