def explain(similarity, mean, std):
    threshold = mean - 2 * std

    deviation = mean - similarity

    if similarity < threshold:
        return (
            f"Similarity {round(similarity,5)} is below statistical threshold "
            f"{round(threshold,5)} indicating abnormal behavioral pattern."
        )
    else:
        return (
            f"Similarity {round(similarity,5)} lies within expected operational "
            f"variance range."
        )