import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

def z3_permutation_index(i):
    bits = format(i, "06b")
    new_bits = bits[2:4] + bits[4:6] + bits[0:2]
    return int(new_bits, 2)

perm = np.array([z3_permutation_index(i) for i in range(64)])

def apply_g(X):
    return X[:, perm]

N = 5000
X = np.random.randn(N, 64)
gX = apply_g(X)
sym = (X + gX)[:, 3]
asym = (X - gX)[:, 7]
y = ((sym + asym) > 0).astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42)

base_model = MLPClassifier(hidden_layer_sizes=(64,),
                           max_iter=500, random_state=42)
base_model.fit(X_train, y_train)
base_acc = accuracy_score(y_test, base_model.predict(X_test))
print("Baseline accuracy:", base_acc)

gX_all = apply_g(X)
sigma = X + gX_all
delta = X - gX_all
X_doublet = np.concatenate([sigma, delta], axis=1)

Xd_train, Xd_test, y_train, y_test = train_test_split(
    X_doublet, y, test_size=0.3, random_state=42)
doublet_model = MLPClassifier(hidden_layer_sizes=(64,),
                              max_iter=500, random_state=42)
doublet_model.fit(Xd_train, y_train)
doublet_acc = accuracy_score(y_test, doublet_model.predict(Xd_test))
print("Doublet accuracy:", doublet_acc)
print("Gain:", doublet_acc - base_acc)
