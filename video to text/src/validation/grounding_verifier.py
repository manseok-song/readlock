"""Google Search Grounding 검증 모듈

Gemini API의 Google Search Grounding 기능을 활용하여
정책명, 고유명사 등의 실제 존재 여부를 검증합니다.
"""

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.stt.base import TranscriptionResult

# 모듈 레벨 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """검증 결과"""
    term: str                           # 검증 대상 용어
    verified: bool                      # 검증 성공 여부
    confidence: float                   # 신뢰도 (0.0 ~ 1.0)
    corrected: Optional[str] = None     # 수정된 용어 (검증 실패 시)
    source: Optional[str] = None        # 출처 URL
    reason: Optional[str] = None        # 검증 결과 이유


@dataclass
class BatchVerificationResult:
    """배치 검증 결과"""
    verified_terms: list[VerificationResult] = field(default_factory=list)
    corrections: dict[str, str] = field(default_factory=dict)  # 원본 -> 수정

    @property
    def accuracy(self) -> float:
        """검증 성공률"""
        if not self.verified_terms:
            return 1.0
        verified = sum(1 for r in self.verified_terms if r.verified)
        return verified / len(self.verified_terms)

    @property
    def needs_correction(self) -> bool:
        """수정 필요 여부"""
        return len(self.corrections) > 0


class GroundingVerifier:
    """Google Search Grounding 검증기"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    @property
    def is_available(self) -> bool:
        """API 사용 가능 여부"""
        return bool(self.api_key)

    def _get_client(self):
        """Gemini 클라이언트 가져오기"""
        if self._client is not None:
            return self._client

        try:
            from google import genai
            from google.genai import types
            self._genai = genai
            self._types = types

            self._client = genai.Client(api_key=self.api_key)
            logger.info("Gemini 클라이언트 초기화 완료")
            return self._client
        except ImportError as e:
            logger.error(f"google-genai 패키지 import 실패: {e}")
            raise RuntimeError(
                "google-genai 패키지가 설치되지 않았습니다. "
                "'pip install google-genai' 실행 필요"
            )
        except Exception as e:
            logger.error(f"Gemini 클라이언트 초기화 실패: {e}")
            raise

    async def verify_term(self, term: str, context: Optional[str] = None) -> VerificationResult:
        """
        단일 용어 검증

        Args:
            term: 검증할 용어 (정책명, 고유명사 등)
            context: 추가 맥락 정보

        Returns:
            VerificationResult
        """
        if not self.is_available:
            # API 없으면 기본 결과 반환
            return VerificationResult(
                term=term,
                verified=True,
                confidence=0.5,
                reason="API 키 없음 - 검증 생략"
            )

        client = self._get_client()

        prompt = f"""다음 용어가 실제로 존재하는 정책명, 제도명, 또는 공식 용어인지 확인하세요.

용어: "{term}"
{f'맥락: {context}' if context else ''}

웹 검색을 통해 확인하고, 다음 형식으로 답변하세요:
1. 존재 여부: [예/아니오]
2. 신뢰도: [0.0-1.0]
3. 수정 제안 (잘못된 경우): [올바른 용어 또는 "해당 없음"]
4. 출처: [URL 또는 "확인 불가"]
5. 이유: [간단한 설명]"""

        try:
            logger.debug(f"용어 검증 시작: '{term}'")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=self._types.GenerateContentConfig(
                    tools=[self._types.Tool(google_search=self._types.GoogleSearch())],
                    temperature=0.1,
                )
            )

            result = self._parse_verification_response(term, response.text)
            logger.info(f"용어 검증 완료: '{term}' -> verified={result.verified}, confidence={result.confidence:.2f}")
            return result

        except Exception as e:
            logger.error(f"용어 검증 실패 '{term}': {e}", exc_info=True)
            return VerificationResult(
                term=term,
                verified=True,
                confidence=0.5,
                reason=f"검증 오류: {str(e)}"
            )

    def _parse_verification_response(self, term: str, response: str) -> VerificationResult:
        """검증 응답 파싱"""
        lines = response.strip().split("\n")

        verified = True
        confidence = 0.7
        corrected = None
        source = None
        reason = None

        for line in lines:
            line_lower = line.lower()

            if "존재 여부" in line or "existence" in line_lower:
                verified = "예" in line or "yes" in line_lower
            elif "신뢰도" in line or "confidence" in line_lower:
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    confidence = float(match.group(1))
                    if confidence > 1:
                        confidence = confidence / 100  # 백분율 처리
            elif "수정" in line or "correction" in line_lower:
                if "해당 없음" not in line and "없음" not in line and "none" not in line_lower:
                    corrected = line.split(":")[-1].strip().strip('"\'')
            elif "출처" in line or "source" in line_lower:
                url_match = re.search(r'https?://[^\s]+', line)
                if url_match:
                    source = url_match.group(0)
            elif "이유" in line or "reason" in line_lower:
                reason = line.split(":")[-1].strip()

        return VerificationResult(
            term=term,
            verified=verified,
            confidence=confidence,
            corrected=corrected if not verified else None,
            source=source,
            reason=reason
        )

    async def verify_batch(
        self,
        terms: list[str],
        context: Optional[str] = None
    ) -> BatchVerificationResult:
        """
        여러 용어 일괄 검증

        Args:
            terms: 검증할 용어 목록
            context: 추가 맥락 정보

        Returns:
            BatchVerificationResult
        """
        logger.info(f"배치 검증 시작: {len(terms)}개 용어")
        results = []
        corrections = {}

        for i, term in enumerate(terms):
            try:
                result = await self.verify_term(term, context)
                results.append(result)

                if not result.verified and result.corrected:
                    corrections[term] = result.corrected
                    logger.info(f"수정 필요: '{term}' -> '{result.corrected}'")

            except Exception as e:
                logger.error(f"배치 검증 중 오류 (용어 {i+1}/{len(terms)}): {e}")
                results.append(VerificationResult(
                    term=term,
                    verified=True,
                    confidence=0.5,
                    reason=f"검증 실패: {str(e)}"
                ))

        logger.info(f"배치 검증 완료: 정확도 {len([r for r in results if r.verified])}/{len(results)}")
        return BatchVerificationResult(
            verified_terms=results,
            corrections=corrections
        )

    async def verify_transcription(
        self,
        transcription: "TranscriptionResult",
        policy_names: Optional[list[str]] = None
    ) -> BatchVerificationResult:
        """
        전사 결과 내 정책명 검증

        Args:
            transcription: 전사 결과
            policy_names: 검증할 정책명 목록 (없으면 자동 추출)

        Returns:
            BatchVerificationResult
        """
        logger.info("전사 결과 정책명 검증 시작")

        if policy_names is None:
            policy_names = self._extract_policy_names(transcription)
            logger.info(f"자동 추출된 정책명 후보: {len(policy_names)}개")

        if not policy_names:
            logger.info("검증할 정책명 없음")
            return BatchVerificationResult()

        # 전체 텍스트를 맥락으로 사용
        full_text = " ".join(seg.text for seg in transcription.segments[:5])
        context = f"선거 토론회 전사 내용: {full_text[:500]}"

        result = await self.verify_batch(policy_names, context)
        logger.info(f"전사 검증 완료: 정확도 {result.accuracy:.1%}, 수정 필요 {len(result.corrections)}개")
        return result

    def _extract_policy_names(self, transcription: "TranscriptionResult") -> list[str]:
        """전사 결과에서 정책명 후보 추출"""
        full_text = " ".join(seg.text for seg in transcription.segments)

        # 정책명 패턴 (따옴표, 괄호 등)
        patterns = [
            r"['\"]([^'\"]{5,30})['\"]",          # 따옴표
            r"「([^」]{5,30})」",                  # 낫표
            r"정책[:\s]*([가-힣\s]{5,30})",        # "정책" 뒤
            r"([가-힣]+\s*(정책|제도|사업|지원))",  # ~정책, ~제도
        ]

        candidates = set()
        for pattern in patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and len(match) >= 4:
                    candidates.add(match.strip())

        return list(candidates)[:20]  # 최대 20개


def apply_corrections(text: str, corrections: dict[str, str]) -> str:
    """텍스트에 수정 사항 적용"""
    result = text
    for original, corrected in corrections.items():
        result = result.replace(original, corrected)
    return result


async def verify_and_correct(
    transcription: "TranscriptionResult",
    policy_names: Optional[list[str]] = None
) -> tuple["TranscriptionResult", BatchVerificationResult]:
    """
    전사 결과 검증 및 수정

    Args:
        transcription: 전사 결과
        policy_names: 검증할 정책명 목록

    Returns:
        (수정된 전사 결과, 검증 결과)
    """
    from src.stt.base import TranscriptionResult, Segment

    verifier = GroundingVerifier()
    result = await verifier.verify_transcription(transcription, policy_names)

    if not result.needs_correction:
        return transcription, result

    # 수정 적용
    corrected_segments = []
    for seg in transcription.segments:
        corrected_text = apply_corrections(seg.text, result.corrections)
        corrected_segments.append(Segment(
            start=seg.start,
            end=seg.end,
            text=corrected_text,
            speaker=seg.speaker,
            confidence=seg.confidence
        ))

    corrected_transcription = TranscriptionResult(
        segments=corrected_segments,
        language=transcription.language,
        duration=transcription.duration,
        num_speakers=transcription.num_speakers,
        engine=f"{transcription.engine}+grounding_verified",
        model=transcription.model
    )

    return corrected_transcription, result
