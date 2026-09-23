import numpy as np
from numpy.linalg import norm

def rotation_matrix(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])

test_points = [
    np.array([1.0, 0.0]),
    np.array([3.0, 4.0]),
    np.array([0.5, -2.0]),
    np.array([7.0, 7.0]),
]

N_samples = [100, 1000, 10000, 100000]

for x in test_points:
    for N in N_samples:
        thetas = np.linspace(0, 2*np.pi, N, endpoint=False)
        S = np.zeros(2)
        for th in thetas:
            S += rotation_matrix(th) @ x
        S /= N
        # ||S|| ~ 1e-15 for every N and x
