"""전사 품질 점수 계산 모듈

전사 결과의 품질을 다양한 지표로 측정합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.stt.base import TranscriptionResult
    from src.rag.knowledge_builder import KnowledgeBase


@dataclass
class QualityIssue:
    """품질 문제점"""
    type: str           # "speaker", "policy", "confidence", "timestamp"
    severity: str       # "low", "medium", "high"
    description: str
    segment_index: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class QualityScore:
    """품질 점수 결과"""
    total: float                             # 총점 (0.0 ~ 1.0)
    speaker_accuracy: float                  # 화자 정확도
    policy_accuracy: float                   # 정책명 정확도
    avg_confidence: float                    # 평균 신뢰도
    timestamp_quality: float                 # 타임스탬프 품질
    issues: list[QualityIssue] = field(default_factory=list)

    # 상세 통계
    total_segments: int = 0
    matched_speakers: int = 0
    matched_policies: int = 0
    low_confidence_segments: int = 0

    @property
    def grade(self) -> str:
        """품질 등급 (A~F)"""
        if self.total >= 0.95:
            return "A+"
        elif self.total >= 0.90:
            return "A"
        elif self.total >= 0.85:
            return "B+"
        elif self.total >= 0.80:
            return "B"
        elif self.total >= 0.75:
            return "C+"
        elif self.total >= 0.70:
            return "C"
        elif self.total >= 0.60:
            return "D"
        else:
            return "F"

    @property
    def is_acceptable(self) -> bool:
        """허용 가능한 품질 여부 (C 이상)"""
        return self.total >= 0.70

    @property
    def needs_review(self) -> bool:
        """수동 검토 필요 여부"""
        return self.total < 0.85 or len(self.issues) > 5

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "total": round(self.total, 4),
            "grade": self.grade,
            "speaker_accuracy": round(self.speaker_accuracy, 4),
            "policy_accuracy": round(self.policy_accuracy, 4),
            "avg_confidence": round(self.avg_confidence, 4),
            "timestamp_quality": round(self.timestamp_quality, 4),
            "is_acceptable": self.is_acceptable,
            "needs_review": self.needs_review,
            "issues": [
                {
                    "type": i.type,
                    "severity": i.severity,
                    "description": i.description,
                    "segment_index": i.segment_index,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
            "statistics": {
                "total_segments": self.total_segments,
                "matched_speakers": self.matched_speakers,
                "matched_policies": self.matched_policies,
                "low_confidence_segments": self.low_confidence_segments,
            }
        }


class QualityScorer:
    """전사 품질 점수 계산기"""

    # 가중치 설정
    DEFAULT_WEIGHTS = {
        "speaker": 0.35,      # 화자 정확도 가중치
        "policy": 0.25,       # 정책명 정확도 가중치
        "confidence": 0.25,   # 평균 신뢰도 가중치
        "timestamp": 0.15,    # 타임스탬프 품질 가중치
    }

    # 임계값 설정
    LOW_CONFIDENCE_THRESHOLD = 0.7
    TIMESTAMP_GAP_THRESHOLD = 2.0  # 초
    TIMESTAMP_OVERLAP_THRESHOLD = 0.5  # 초

    def __init__(
        self,
        weights: Optional[dict] = None,
        low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD
    ):
        """
        Args:
            weights: 가중치 설정 (speaker, policy, confidence, timestamp)
            low_confidence_threshold: 낮은 신뢰도 임계값
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.low_confidence_threshold = low_confidence_threshold

    def calculate(
        self,
        transcription: "TranscriptionResult",
        knowledge_base: Optional["KnowledgeBase"] = None
    ) -> QualityScore:
        """
        품질 점수 계산

        Args:
            transcription: 전사 결과
            knowledge_base: 선거 지식 베이스 (RAG 데이터)

        Returns:
            QualityScore
        """
        issues = []

        # 1. 화자 정확도 계산
        speaker_accuracy, speaker_issues, matched_speakers = self._calculate_speaker_accuracy(
            transcription, knowledge_base
        )
        issues.extend(speaker_issues)

        # 2. 정책명 정확도 계산
        policy_accuracy, policy_issues, matched_policies = self._calculate_policy_accuracy(
            transcription, knowledge_base
        )
        issues.extend(policy_issues)

        # 3. 평균 신뢰도 계산
        avg_confidence, confidence_issues, low_conf_count = self._calculate_confidence(
            transcription
        )
        issues.extend(confidence_issues)

        # 4. 타임스탬프 품질 계산
        timestamp_quality, timestamp_issues = self._calculate_timestamp_quality(
            transcription
        )
        issues.extend(timestamp_issues)

        # 5. 총점 계산 (가중 평균)
        total = (
            self.weights["speaker"] * speaker_accuracy +
            self.weights["policy"] * policy_accuracy +
            self.weights["confidence"] * avg_confidence +
            self.weights["timestamp"] * timestamp_quality
        )

        return QualityScore(
            total=total,
            speaker_accuracy=speaker_accuracy,
            policy_accuracy=policy_accuracy,
            avg_confidence=avg_confidence,
            timestamp_quality=timestamp_quality,
            issues=issues,
            total_segments=len(transcription.segments),
            matched_speakers=matched_speakers,
            matched_policies=matched_policies,
            low_confidence_segments=low_conf_count,
        )

    def _calculate_speaker_accuracy(
        self,
        transcription: "TranscriptionResult",
        knowledge_base: Optional["KnowledgeBase"]
    ) -> tuple[float, list[QualityIssue], int]:
        """화자 정확도 계산"""
        issues = []
        matched = 0

        if not knowledge_base or not knowledge_base.candidates:
            # RAG 데이터 없으면 기본 점수
            return 0.8, [], 0

        candidate_names = set(knowledge_base.candidate_names)
        speaker_segments = [s for s in transcription.segments if s.speaker]

        if not speaker_segments:
            return 1.0, [], 0  # 화자 정보 없으면 만점

        for i, seg in enumerate(speaker_segments):
            if seg.speaker in candidate_names:
                matched += 1
            else:
                # 유사한 이름이 있는지 확인
                similar = self._find_similar_name(seg.speaker, candidate_names)
                if similar:
                    issues.append(QualityIssue(
                        type="speaker",
                        severity="medium",
                        description=f"화자 '{seg.speaker}'가 '{similar}'과 유사합니다",
                        segment_index=i,
                        suggestion=f"'{similar}'로 수정 권장"
                    ))
                else:
                    issues.append(QualityIssue(
                        type="speaker",
                        severity="high",
                        description=f"알 수 없는 화자: '{seg.speaker}'",
                        segment_index=i,
                    ))

        accuracy = matched / len(speaker_segments) if speaker_segments else 1.0
        return accuracy, issues, matched

    def _calculate_policy_accuracy(
        self,
        transcription: "TranscriptionResult",
        knowledge_base: Optional["KnowledgeBase"]
    ) -> tuple[float, list[QualityIssue], int]:
        """정책명 정확도 계산"""
        issues = []
        matched = 0

        if not knowledge_base or not knowledge_base.policies:
            return 0.8, [], 0  # RAG 데이터 없으면 기본 점수

        policy_names = set(knowledge_base.policy_names)
        full_text = " ".join(seg.text for seg in transcription.segments)

        # 정책명이 텍스트에 포함되어 있는지 확인
        for policy in knowledge_base.policies:
            if policy.name in full_text:
                matched += 1
            else:
                # 유사한 단어가 있는지 확인
                similar = self._find_similar_in_text(policy.name, full_text)
                if similar:
                    issues.append(QualityIssue(
                        type="policy",
                        severity="medium",
                        description=f"정책명 '{policy.name}'이 '{similar}'로 표기됨",
                        suggestion=f"'{policy.name}'으로 수정 권장"
                    ))

        total_policies = len(knowledge_base.policies)
        accuracy = matched / total_policies if total_policies > 0 else 1.0
        return accuracy, issues, matched

    def _calculate_confidence(
        self,
        transcription: "TranscriptionResult"
    ) -> tuple[float, list[QualityIssue], int]:
        """평균 신뢰도 계산"""
        issues = []
        low_confidence_count = 0

        if not transcription.segments:
            return 1.0, [], 0

        confidences = []
        for i, seg in enumerate(transcription.segments):
            conf = seg.confidence if seg.confidence is not None else 0.8
            confidences.append(conf)

            if conf < self.low_confidence_threshold:
                low_confidence_count += 1
                issues.append(QualityIssue(
                    type="confidence",
                    severity="low" if conf >= 0.5 else "medium",
                    description=f"낮은 신뢰도 ({conf:.2f}): '{seg.text[:30]}...'",
                    segment_index=i,
                ))

        avg_confidence = sum(confidences) / len(confidences)
        return avg_confidence, issues, low_confidence_count

    def _calculate_timestamp_quality(
        self,
        transcription: "TranscriptionResult"
    ) -> tuple[float, list[QualityIssue]]:
        """타임스탬프 품질 계산"""
        issues = []

        if len(transcription.segments) < 2:
            return 1.0, []

        problems = 0
        total_checks = len(transcription.segments) - 1

        for i in range(len(transcription.segments) - 1):
            current = transcription.segments[i]
            next_seg = transcription.segments[i + 1]

            # 겹침 확인
            if current.end > next_seg.start + self.TIMESTAMP_OVERLAP_THRESHOLD:
                problems += 1
                issues.append(QualityIssue(
                    type="timestamp",
                    severity="medium",
                    description=f"세그먼트 {i}와 {i+1} 사이 타임스탬프 겹침",
                    segment_index=i,
                ))

            # 큰 간격 확인
            gap = next_seg.start - current.end
            if gap > self.TIMESTAMP_GAP_THRESHOLD:
                # 긴 간격은 문제가 아닐 수 있음 (침묵 구간)
                if gap > 10.0:  # 10초 이상이면 경고
                    issues.append(QualityIssue(
                        type="timestamp",
                        severity="low",
                        description=f"세그먼트 {i}와 {i+1} 사이 {gap:.1f}초 간격",
                        segment_index=i,
                    ))

        quality = 1.0 - (problems / total_checks) if total_checks > 0 else 1.0
        return max(0.0, quality), issues

    def _find_similar_name(self, name: str, candidates: set[str]) -> Optional[str]:
        """유사한 이름 찾기 (간단한 편집 거리 기반)"""
        for candidate in candidates:
            # 첫 글자가 같고 길이가 비슷하면 유사하다고 판단
            if name and candidate:
                if name[0] == candidate[0] and abs(len(name) - len(candidate)) <= 1:
                    return candidate
        return None

    def _find_similar_in_text(self, target: str, text: str) -> Optional[str]:
        """텍스트에서 유사한 단어 찾기"""
        import re

        # 타겟의 핵심 키워드 추출
        keywords = [w for w in target.split() if len(w) > 1]
        if not keywords:
            return None

        # 키워드 중 일부가 텍스트에 있는지 확인
        for keyword in keywords:
            pattern = rf'\b[가-힣]*{keyword[0]}[가-힣]*{keyword[-1]}[가-힣]*\b'
            matches = re.findall(pattern, text)
            for match in matches:
                if match != target and len(match) <= len(target) + 2:
                    return match

        return None


def calculate_quality(
    transcription: "TranscriptionResult",
    knowledge_base: Optional["KnowledgeBase"] = None
) -> QualityScore:
    """품질 점수 계산 헬퍼 함수"""
    scorer = QualityScorer()
    return scorer.calculate(transcription, knowledge_base)
