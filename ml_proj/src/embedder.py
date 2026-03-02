from sentence_transformers import SentenceTransformer

class LogEmbedder:
    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def encode(self, text):
        return self.model.encode(text)

    def encode_batch(self, texts):
        return self.model.encode(texts)