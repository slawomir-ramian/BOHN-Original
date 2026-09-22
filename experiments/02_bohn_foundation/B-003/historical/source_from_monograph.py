import numpy as np

class ReversibleRMIGLayer:
    """
    Reversible permutation-sign RMIG layer.
    
    Operates on vector X in R^64:
    1. Permutes coordinates according to Z3 action
    2. Multiplies each coordinate by weight w_i in {-1, +1}
    
    The layer is exactly reversible: X = inverse(forward(X)).
    """
    
    def __init__(self, n_states=64, n_bits=6, seed=42):
        self.n_states = n_states
        self.n_bits = n_bits
        
        # Compute Z3 permutations
        self.perm = np.array([
            z3_permutation(s, n_bits) for s in range(n_states)
        ])
        
        # Inverse permutation
        self.inv_perm = np.zeros(n_states, dtype=int)
        for i, p in enumerate(self.perm):
            self.inv_perm[p] = i
        
        # Binary weights {-1, +1}
        rng = np.random.RandomState(seed)
        self.weights = rng.choice([-1.0, 1.0], size=n_states)
    
    def forward(self, X):
        """Forward pass: Y = weights * X[perm]"""
        self._input = X.copy()  # Store for backward
        X_permuted = X[..., self.perm]
        Y = self.weights * X_permuted
        return Y
    
    def inverse(self, Y):
        """Exact inverse: X = (weights * Y)[inv_perm]"""
        # Weights are {-1,+1}, so w^{-1} = w
        X_permuted = self.weights * Y
        X = X_permuted[..., self.inv_perm]
        return X
    
    def backward(self, grad_Y):
        """Backward gradient propagation."""
        # dL/dX[perm[i]] = weights[i] * grad_Y[i]
        grad_X_permuted = self.weights * grad_Y
        grad_X = grad_X_permuted[..., self.inv_perm]
        
        # dL/dW[i] = X[perm[i]] * grad_Y[i]
        X_permuted = self._input[..., self.perm]
        grad_W = X_permuted * grad_Y
        
        return grad_X, grad_W
    
    def set_weights(self, new_weights):
        """Set new weights (for training)."""
        self.weights = new_weights.copy()

# Verification
layer = ReversibleRMIGLayer(seed=42)
print("ReversibleRMIGLayer:")
print(f"  Number of states: {layer.n_states}")
print(f"  Weight size:      {layer.weights.shape}")
print(f"  Unique weights:   {np.unique(layer.weights)}")
print(f"  Permutacja [0:5]: {layer.perm[:5]}")
