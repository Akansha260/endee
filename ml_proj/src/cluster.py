def cluster_results(results, eps=0.002):
    """
    Lightweight similarity-based clustering.
    Groups results whose similarity scores are very close.
    """

    clusters = []

    for r in results:
        placed = False

        for cluster in clusters:
            if abs(cluster[0]["similarity"] - r["similarity"]) < eps:
                cluster.append(r)
                placed = True
                break

        if not placed:
            clusters.append([r])

    return clusters
