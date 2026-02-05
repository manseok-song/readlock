"""한국어 음성학적 매칭 모듈

전사된 텍스트와 정답 후보 목록을 비교하여 가장 유사한 항목을 찾습니다.
자모 분리, 초성 유사도, Levenshtein 거리를 조합하여 매칭합니다.
"""

from dataclasses import dataclass
from typing import Optional

try:
    import jamo
    JAMO_AVAILABLE = True
except ImportError:
    JAMO_AVAILABLE = False


@dataclass
class MatchResult:
    """매칭 결과"""
    matched: str
    confidence: float
    original: str
    method: str  # "exact", "phonetic", "fuzzy"


class KoreanPhoneticMatcher:
    """한국어 발음 유사도 매칭"""

    # 초성 목록 (ㄱ~ㅎ)
    CHOSUNG = [
        'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ',
        'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
    ]

    # 중성 목록
    JUNGSUNG = [
        'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ',
        'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
    ]

    # 종성 목록 (빈 문자열 포함)
    JONGSUNG = [
        '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ',
        'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ',
        'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
    ]

    # 유사 발음 그룹 (혼동되기 쉬운 자음/모음)
    SIMILAR_CONSONANTS = {
        'ㄱ': ['ㄱ', 'ㅋ', 'ㄲ'],
        'ㄲ': ['ㄱ', 'ㅋ', 'ㄲ'],
        'ㅋ': ['ㄱ', 'ㅋ', 'ㄲ'],
        'ㄷ': ['ㄷ', 'ㅌ', 'ㄸ'],
        'ㄸ': ['ㄷ', 'ㅌ', 'ㄸ'],
        'ㅌ': ['ㄷ', 'ㅌ', 'ㄸ'],
        'ㅂ': ['ㅂ', 'ㅍ', 'ㅃ'],
        'ㅃ': ['ㅂ', 'ㅍ', 'ㅃ'],
        'ㅍ': ['ㅂ', 'ㅍ', 'ㅃ'],
        'ㅅ': ['ㅅ', 'ㅆ'],
        'ㅆ': ['ㅅ', 'ㅆ'],
        'ㅈ': ['ㅈ', 'ㅊ', 'ㅉ'],
        'ㅉ': ['ㅈ', 'ㅊ', 'ㅉ'],
        'ㅊ': ['ㅈ', 'ㅊ', 'ㅉ'],
        'ㄴ': ['ㄴ', 'ㄹ'],
        'ㄹ': ['ㄴ', 'ㄹ'],
    }

    SIMILAR_VOWELS = {
        'ㅏ': ['ㅏ', 'ㅓ'],
        'ㅓ': ['ㅏ', 'ㅓ'],
        'ㅗ': ['ㅗ', 'ㅜ'],
        'ㅜ': ['ㅗ', 'ㅜ'],
        'ㅐ': ['ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'],
        'ㅔ': ['ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'],
        'ㅒ': ['ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'],
        'ㅖ': ['ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'],
    }

    def __init__(
        self,
        exact_weight: float = 0.4,
        chosung_weight: float = 0.3,
        jamo_weight: float = 0.3,
        min_confidence: float = 0.6
    ):
        """
        Args:
            exact_weight: 정확 일치 가중치
            chosung_weight: 초성 유사도 가중치
            jamo_weight: 자모 유사도 가중치
            min_confidence: 최소 신뢰도 임계값
        """
        self.exact_weight = exact_weight
        self.chosung_weight = chosung_weight
        self.jamo_weight = jamo_weight
        self.min_confidence = min_confidence

    def decompose_korean(self, char: str) -> tuple[str, str, str]:
        """한글 한 글자를 초성, 중성, 종성으로 분리"""
        if not self._is_korean_char(char):
            return (char, '', '')

        code = ord(char) - 0xAC00
        cho = code // 588
        jung = (code % 588) // 28
        jong = code % 28

        return (
            self.CHOSUNG[cho],
            self.JUNGSUNG[jung],
            self.JONGSUNG[jong]
        )

    def _is_korean_char(self, char: str) -> bool:
        """한글 문자인지 확인"""
        return len(char) == 1 and 0xAC00 <= ord(char) <= 0xD7A3

    def get_chosung(self, text: str) -> str:
        """문자열에서 초성만 추출"""
        result = []
        for char in text:
            if self._is_korean_char(char):
                cho, _, _ = self.decompose_korean(char)
                result.append(cho)
            elif char.isalpha():
                result.append(char.upper())
        return ''.join(result)

    def get_jamo(self, text: str) -> str:
        """문자열을 자모로 분리"""
        if JAMO_AVAILABLE:
            return jamo.h2j(text)

        # jamo 라이브러리 없을 때 수동 분리
        result = []
        for char in text:
            if self._is_korean_char(char):
                cho, jung, jong = self.decompose_korean(char)
                result.extend([cho, jung])
                if jong:
                    result.append(jong)
            else:
                result.append(char)
        return ''.join(result)

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Levenshtein 편집 거리 계산"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def phonetic_similarity(self, s1: str, s2: str) -> float:
        """음성학적 유사도 계산 (0.0 ~ 1.0)"""
        jamo1 = self.get_jamo(s1)
        jamo2 = self.get_jamo(s2)

        if not jamo1 or not jamo2:
            return 0.0

        # 기본 Levenshtein 유사도
        max_len = max(len(jamo1), len(jamo2))
        distance = self.levenshtein_distance(jamo1, jamo2)
        base_similarity = 1.0 - (distance / max_len)

        # 유사 발음 보정
        bonus = self._calculate_phonetic_bonus(s1, s2)

        return min(1.0, base_similarity + bonus)

    def _calculate_phonetic_bonus(self, s1: str, s2: str) -> float:
        """유사 발음에 대한 보너스 점수 계산"""
        bonus = 0.0
        min_len = min(len(s1), len(s2))

        for i in range(min_len):
            if not (self._is_korean_char(s1[i]) and self._is_korean_char(s2[i])):
                continue

            cho1, jung1, jong1 = self.decompose_korean(s1[i])
            cho2, jung2, jong2 = self.decompose_korean(s2[i])

            # 초성 유사도 보너스
            if cho1 != cho2 and cho1 in self.SIMILAR_CONSONANTS:
                if cho2 in self.SIMILAR_CONSONANTS.get(cho1, []):
                    bonus += 0.02

            # 중성 유사도 보너스
            if jung1 != jung2 and jung1 in self.SIMILAR_VOWELS:
                if jung2 in self.SIMILAR_VOWELS.get(jung1, []):
                    bonus += 0.02

        return bonus

    def chosung_similarity(self, s1: str, s2: str) -> float:
        """초성 유사도 계산"""
        cho1 = self.get_chosung(s1)
        cho2 = self.get_chosung(s2)

        if not cho1 or not cho2:
            return 0.0

        max_len = max(len(cho1), len(cho2))
        distance = self.levenshtein_distance(cho1, cho2)

        return 1.0 - (distance / max_len)

    def calculate_similarity(self, text: str, candidate: str) -> float:
        """종합 유사도 계산"""
        # 정확 일치
        if text == candidate:
            return 1.0

        # 대소문자 무시 일치
        if text.lower() == candidate.lower():
            return 0.98

        # 공백 제거 후 일치
        if text.replace(' ', '') == candidate.replace(' ', ''):
            return 0.95

        # 초성 유사도
        chosung_sim = self.chosung_similarity(text, candidate)

        # 자모 유사도
        jamo_sim = self.phonetic_similarity(text, candidate)

        # 가중 평균
        exact_score = 1.0 if text == candidate else 0.0
        total = (
            self.exact_weight * exact_score +
            self.chosung_weight * chosung_sim +
            self.jamo_weight * jamo_sim
        )

        return total

    def match(
        self,
        text: str,
        candidates: list[str],
        threshold: Optional[float] = None
    ) -> Optional[MatchResult]:
        """
        텍스트와 가장 유사한 후보 매칭

        Args:
            text: 전사된 텍스트
            candidates: 정답 후보 목록
            threshold: 최소 신뢰도 (None이면 self.min_confidence 사용)

        Returns:
            MatchResult 또는 None (매칭 실패 시)
        """
        if not text or not candidates:
            return None

        threshold = threshold if threshold is not None else self.min_confidence

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            score = self.calculate_similarity(text, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match is None or best_score < threshold:
            return None

        # 매칭 방법 결정
        if text == best_match:
            method = "exact"
        elif best_score >= 0.9:
            method = "phonetic"
        else:
            method = "fuzzy"

        return MatchResult(
            matched=best_match,
            confidence=best_score,
            original=text,
            method=method
        )

    def find_and_replace(
        self,
        text: str,
        candidates: list[str],
        threshold: Optional[float] = None
    ) -> tuple[str, list[MatchResult]]:
        """
        텍스트 내 모든 후보 단어를 찾아 교체

        Args:
            text: 원본 텍스트
            candidates: 교체 대상 후보 목록
            threshold: 최소 신뢰도

        Returns:
            (교체된 텍스트, 매칭 결과 목록)
        """
        matches = []
        result_text = text

        for candidate in candidates:
            # 단어 단위로 분할하여 검사
            words = result_text.split()
            new_words = []

            for word in words:
                # 구두점 분리
                prefix = ''
                suffix = ''
                core = word

                while core and not core[0].isalnum() and not self._is_korean_char(core[0]):
                    prefix += core[0]
                    core = core[1:]

                while core and not core[-1].isalnum() and not self._is_korean_char(core[-1]):
                    suffix = core[-1] + suffix
                    core = core[:-1]

                if not core:
                    new_words.append(word)
                    continue

                # 매칭 시도
                match = self.match(core, [candidate], threshold)
                if match and match.confidence >= (threshold or self.min_confidence):
                    new_words.append(prefix + match.matched + suffix)
                    matches.append(match)
                else:
                    new_words.append(word)

            result_text = ' '.join(new_words)

        return result_text, matches


# 싱글톤 인스턴스
_matcher: Optional[KoreanPhoneticMatcher] = None


def get_phonetic_matcher() -> KoreanPhoneticMatcher:
    """음성학적 매처 싱글톤 인스턴스 반환"""
    global _matcher
    if _matcher is None:
        _matcher = KoreanPhoneticMatcher()
    return _matcher
