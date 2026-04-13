# core/semantic_memory.py
import math

class SemanticMemory:
    def __init__(self):
        self.vectors = {}  # title -> vector

    def add(self, title, vector):
        self.vectors[title] = vector

    def cosine(self, a, b):
        dot = sum(x*y for x,y in zip(a,b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return dot / (na * nb + 1e-9)

    def most_similar(self, vector, threshold=0.82):
        best = None
        best_score = 0

        for title, vec in self.vectors.items():
            score = self.cosine(vector, vec)
            if score > best_score:
                best = title
                best_score = score

        if best_score >= threshold:
            return best

        return None