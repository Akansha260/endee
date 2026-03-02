import numpy as np


def compute_threshold(similarities, method="percentile", value=5):
    """
    method:
        - "percentile": value = percentile (e.g., 5)
        - "std": value = number of std deviations
    """
    if method == "percentile":
        return np.percentile(similarities, value)

    elif method == "std":
        mean = np.mean(similarities)
        std = np.std(similarities)
        return mean - value * std

    else:
        raise ValueError("Unsupported threshold method")


def is_anomalous(similarity, threshold):
    return similarity < threshold