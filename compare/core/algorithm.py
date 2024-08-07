from __future__ import annotations
from typing import List, Dict, Union, Optional

import numpy as np
import spacy

from scipy.spatial.distance import cosine
from sklearn.feature_extraction.text import TfidfVectorizer
from Levenshtein import distance as levenshtein_distance

from ..model import (
    Responses,
    Response,
    SIMILARITY_THRESHOLD,
    TextEmbedding,
    TextPair,
    SimilarityScore,
    ResultScore
)

import sys

try:
    nlp = spacy.load("en_core_web_sm")
except:
    spacy.cli.download("en_core_web_sm")
    print("Successfully downloaded spaCy model, please restart your program.")
    sys.exit(1)

def embed_text(text: str) -> np.ndarray:
    doc = nlp(text)
    return np.array([token.vector for token in doc if token.has_vector])

def advanced_similarity(text1: str, text2: str) -> float:
    vec1: np.ndarray = embed_text(text1)
    vec2: np.ndarray = embed_text(text2)

    if vec1.size == 0 or vec2.size == 0:
        return 0.0  # Handle cases where the embeddings are empty

    _, _, v1 = np.linalg.svd(vec1, full_matrices=False)
    _, _, v2 = np.linalg.svd(vec2, full_matrices=False)

    cos_sim = np.dot(v1[0], v2[0]) / (np.linalg.norm(v1[0]) * np.linalg.norm(v2[0]))
    return cos_sim

class TextComparer:
    def __init__(self, texts: List[str]):
        self.texts: List[str] = texts
        self.vectorizer: TfidfVectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 5))
        self.embeddings: List[np.ndarray] = self._calculate_embeddings()

    def _calculate_embeddings(self) -> List[np.ndarray]:
        return self.vectorizer.fit_transform(self.texts).toarray()

    def compare_texts(self, input_text: str, advanced: Optional[bool] = False) -> Dict[str, Union[str, float, List[str]]]:
        input_embedding = self.vectorizer.transform([input_text]).toarray()[0]
        
        similarities = [
            (text, self._combined_similarity(input_text, text, input_embedding, text_embedding, advanced))
            for text, text_embedding in zip(self.texts, self.embeddings)
        ]
        
        similarities.sort(key=lambda x: x[1], reverse=True)

        closest, score = similarities[0]
        similar = [text for text, sim_score in similarities[1:] if sim_score >= SIMILARITY_THRESHOLD]

        return ResultScore(
            closest=closest,
            score=score,
            similar=similar
        )

    def _combined_similarity(self, input_text: str, text: str, input_embedding: np.ndarray, text_embedding: np.ndarray, advanced: bool) -> float:
        tfidf_cosine_sim = 1 - cosine(input_embedding, text_embedding)
        
        if advanced:
            embedding_sim = advanced_similarity(input_text, text)
        else:
            embedding_sim = tfidf_cosine_sim
        
        lev_distance = levenshtein_distance(input_text, text)
        lev_similarity = 1 - (lev_distance / max(len(input_text), len(text)))
        
        combined_score = 0.7 * embedding_sim + 0.3 * lev_similarity
        return combined_score


__all__ = [
    "embed_text",
    "advanced_similarity",
    "TextComparer"
]
