import random

def inject_anomaly(sequence: str) -> str:
    """
    Inject strong synthetic anomaly.
    Strategies:
    - Replace entire sequence with unrelated failure text
    - Inject error phrases
    - Reverse sequence
    """

    strategy = random.choice(["replace", "inject_error", "reverse"])

    if strategy == "replace":
        return "Disk failure corrupted block replication node crash timeout"

    elif strategy == "inject_error":
        return sequence + " CRITICAL ERROR SEGMENTATION FAULT MEMORY CORRUPTION"

    elif strategy == "reverse":
        tokens = sequence.split()
        tokens.reverse()
        return " ".join(tokens)