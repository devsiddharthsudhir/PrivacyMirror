from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer

from .text_clean import normalize


@dataclass
class VectorSpace:
    vectorizer: TfidfVectorizer
    X: object  # sparse matrix
    feature_names: List[str]


def build_tfidf(texts: List[str], max_features: int = 6000) -> VectorSpace:
    vec = TfidfVectorizer(
        preprocessor=normalize,
        ngram_range=(1, 2),
        max_features=max_features,
        min_df=2,
        stop_words="english",
    )
    X = vec.fit_transform(texts)
    feature_names = list(vec.get_feature_names_out())
    return VectorSpace(vectorizer=vec, X=X, feature_names=feature_names)
