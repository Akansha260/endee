import pandas as pd

def load_hdfs_data(trace_path, limit=5000):
    data = pd.read_csv(trace_path)
    return data.head(limit)