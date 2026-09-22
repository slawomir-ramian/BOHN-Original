import numpy as np

def test_reversibility(layer, n_tests=100, dim=64):
    """Test 1: Reversibility X = inverse(forward(X))"""
    max_error = 0.0
    for _ in range(n_tests):
        X = np.random.randn(dim)
        Y = layer.forward(X)
        X_rec = layer.inverse(Y)
        error = np.max(np.abs(X - X_rec))
        max_error = max(max_error, error)
    return max_error

def test_gradient_input(layer, dim=64, eps=1e-5):
    """Test 2: Input gradient (finite differences)"""
    X = np.random.randn(dim)
    
    # Compute analytical gradient
    Y = layer.forward(X)
    grad_Y = np.random.randn(dim)  # random upstream gradient
    grad_X_analytic, _ = layer.backward(grad_Y)
    
    # Compute numerical gradient
    grad_X_numeric = np.zeros(dim)
    for i in range(dim):
        X_plus = X.copy()
        X_plus[i] += eps
        Y_plus = layer.forward(X_plus)
        
        X_minus = X.copy()
        X_minus[i] -= eps
        Y_minus = layer.forward(X_minus)
        
        grad_X_numeric[i] = np.sum(
            grad_Y * (Y_plus - Y_minus) / (2 * eps)
        )
    
    error = np.max(np.abs(grad_X_analytic - grad_X_numeric))
    return error, grad_X_analytic, grad_X_numeric

def test_gradient_weights(layer, dim=64, eps=1e-5):
    """Test 3: Weight gradient (finite differences)"""
    X = np.random.randn(dim)
    
    # Compute analytical gradient
    Y = layer.forward(X)
    grad_Y = np.random.randn(dim)
    _, grad_W_analytic = layer.backward(grad_Y)
    
    # Compute numerical gradient
    grad_W_numeric = np.zeros(dim)
    original_weights = layer.weights.copy()
    
    for i in range(dim):
        w_plus = original_weights.copy()
        w_plus[i] += eps
        layer.set_weights(w_plus)
        Y_plus = layer.forward(X)
        
        w_minus = original_weights.copy()
        w_minus[i] -= eps
        layer.set_weights(w_minus)
        Y_minus = layer.forward(X)
        
        grad_W_numeric[i] = np.sum(
            grad_Y * (Y_plus - Y_minus) / (2 * eps)
        )
    
    layer.set_weights(original_weights)  # Restore weights
    error = np.max(np.abs(grad_W_analytic - grad_W_numeric))
    return error, grad_W_analytic, grad_W_numeric


# ---- Running tests ----
np.random.seed(42)
layer = ReversibleRMIGLayer(seed=42)

print("="*60)
print("REVERSIBLE LAYER CORRECTNESS TESTS")
print("="*60)

# Test 1: Odwracalnosc
eps_rec = test_reversibility(layer)
status1 = "PASSED" if eps_rec == 0.0 else "FAILED"
print(f"\nTest 1: Reversibility")
print(f"  eps_rec = max|X - X_rec| = {eps_rec}")
print(f"  Status: {status1}")

# Test 2: Gradient po wejsciu
eps_grad_X, gX_a, gX_n = test_gradient_input(layer)
status2 = "PASSED" if eps_grad_X < 1e-6 else "FAILED"
print(f"\nTest 2: Input gradient X")
print(f"  eps_grad_X = {eps_grad_X:.2e}")
print(f"  Analytical gradient norm: {np.linalg.norm(gX_a):.6f}")
print(f"  Numerical gradient norm:  {np.linalg.norm(gX_n):.6f}")
print(f"  Status: {status2}")

# Test 3: Gradient po wagach
eps_grad_W, gW_a, gW_n = test_gradient_weights(layer)
status3 = "PASSED" if eps_grad_W < 1e-6 else "FAILED"
print(f"\nTest 3: Weight gradient W")
print(f"  eps_grad_W = {eps_grad_W:.2e}")
print(f"  Analytical gradient norm: {np.linalg.norm(gW_a):.6f}")
print(f"  Numerical gradient norm:  {np.linalg.norm(gW_n):.6f}")
print(f"  Status: {status3}")

print(f"\n{'='*60}")
print(f"SUMMARY: {status1}, {status2}, {status3}")
print(f"{'='*60}")
