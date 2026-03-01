def is_anomalous(results, baseline_mean, baseline_std, sensitivity=2.0):
    if not results:
        return True

    threshold = baseline_mean - sensitivity * baseline_std
    return results[0]["similarity"] < threshold