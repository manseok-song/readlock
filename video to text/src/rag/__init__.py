"""RAG (Retrieval-Augmented Generation) 시스템

선거 토론회 영상 전사의 정확도를 높이기 위한 RAG 시스템.
후보자 이름, 정책명 등의 고유명사를 정확하게 인식하고 교정합니다.
"""

from src.rag.phonetic_matcher import KoreanPhoneticMatcher
from src.rag.knowledge_builder import (
    KnowledgeBase,
    Candidate,
    Policy,
    ElectionKnowledgeBuilder,
)
from src.rag.web_searcher import ElectionWebSearcher

__all__ = [
    "KoreanPhoneticMatcher",
    "KnowledgeBase",
    "Candidate",
    "Policy",
    "ElectionKnowledgeBuilder",
    "ElectionWebSearcher",
]
