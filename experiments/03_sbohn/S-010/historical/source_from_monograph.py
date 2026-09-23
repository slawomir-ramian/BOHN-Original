import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


class SBOHNFeatureExtractor:
    """
    Symmetry-Breaking BOHN feature extractor for Z3.

    Phi_Z3(X) = [S3, A1, A2]

    S3 = X + gX + g2X
    A1 = |X - gX|
    A2 = |X - g2X|
    """

    def __init__(self, n_bits=6):
        self.n_bits = n_bits
        self.n_states = 2 ** n_bits

        if self.n_states != 64:
            raise ValueError(
                "This reference version assumes n_bits=6 and n_states=64."
            )

        self.perm_g = self._build_z3_permutation()
        self.perm_g2 = self.perm_g[self.perm_g]

    def _z3_permutation_index(self, i):
        bits = format(i, f"0{self.n_bits}b")
        new_bits = bits[2:4] + bits[4:6] + bits[0:2]
        return int(new_bits, 2)

    def _build_z3_permutation(self):
        return np.array([
            self._z3_permutation_index(i)
            for i in range(self.n_states)
        ])

    def transform(self, X):
        X = np.asarray(X)

        if X.ndim != 2:
            raise ValueError("X must have shape (n_samples, 64).")

        if X.shape[1] != self.n_states:
            raise ValueError(f"X must have {self.n_states} features.")

        gX = X[:, self.perm_g]
        g2X = X[:, self.perm_g2]

        S3 = X + gX + g2X
        A1 = np.abs(X - gX)
        A2 = np.abs(X - g2X)

        return np.concatenate([S3, A1, A2], axis=1)


class SBOHNLR:
    """
    SBOHN-LR model:

        x -> Phi_Z3(x) -> Logistic Regression
    """

    def __init__(self, random_state=42, max_iter=5000):
        self.extractor = SBOHNFeatureExtractor()
        self.classifier = LogisticRegression(
            max_iter=max_iter,
            solver="liblinear",
            random_state=random_state
        )

    def fit(self, X, y):
        Phi = self.extractor.transform(X)
        self.classifier.fit(Phi, y)
        return self

    def predict(self, X):
        Phi = self.extractor.transform(X)
        return self.classifier.predict(Phi)

    def score(self, X, y):
        return accuracy_score(y, self.predict(X))
