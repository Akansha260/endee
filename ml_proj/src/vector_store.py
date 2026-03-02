from endee import Endee
import uuid


class VectorStore:
    def __init__(self, index_name="logs_index", dimension=384):
        self.client = Endee()
        self.index_name = index_name

        try:
            self.index = self.client.get_index(index_name)
        except Exception:
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                space_type="cosine",
                precision="float16"
            )
            self.index = self.client.get_index(index_name)

    # 🔹 Single query
    def query(self, vector, top_k=5):
        response = self.index.query(
            vector=vector.tolist(),
            top_k=top_k
        )
        return response

    # 🔹 Single upsert (insert/update)
    def insert(self, vector, metadata):
        data = [{
            "id": str(uuid.uuid4()),
            "vector": vector.tolist(),
            "meta": metadata or {}
        }]
        self.index.upsert(data)

    # 🔹 Batch query
    def query_batch(self, vectors, top_k=5):
        results = []
        for vec in vectors:
            res = self.query(vec, top_k=top_k)
            results.append(res)
        return results

    # 🔹 Batch insert
    def insert_batch(self, vectors, metadata_batch):
        for vec, metadata in zip(vectors, metadata_batch):
            self.insert(vec, metadata)