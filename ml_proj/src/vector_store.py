from endee import Endee

class VectorStore:
    def __init__(self, index_name="logs_index", dimension=384):
        self.client = Endee()
        self.index_name = index_name

        try:
            self.index = self.client.get_index(index_name)
        except Exception:
            # If index doesn't exist → create it
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                space_type="cosine",
                precision="float16"
            )
            self.index = self.client.get_index(index_name)

    def upsert(self, vec_id, vector, metadata=None):
        data = [{
            "id": vec_id,
            "vector": vector,
            "meta": metadata or {}
        }]
        self.index.upsert(data)

    def query(self, vector, top_k=3):
        return self.index.query(vector=vector, top_k=top_k)