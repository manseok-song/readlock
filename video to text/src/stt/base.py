"""STT 엔진 추상 인터페이스"""

from abc import ABC, abstractmethod
from datetime import timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SpeakerLabel(str, Enum):
    """화자 레이블"""
    SPEAKER_1 = "화자1"
    SPEAKER_2 = "화자2"
    SPEAKER_3 = "화자3"
    SPEAKER_4 = "화자4"
    SPEAKER_5 = "화자5"
    SPEAKER_6 = "화자6"
    SPEAKER_7 = "화자7"
    SPEAKER_8 = "화자8"
    SPEAKER_9 = "화자9"
    SPEAKER_10 = "화자10"
    UNKNOWN = "알 수 없음"

    @classmethod
    def from_index(cls, index: int) -> "SpeakerLabel":
        """인덱스로부터 화자 레이블 생성"""
        labels = [
            cls.SPEAKER_1, cls.SPEAKER_2, cls.SPEAKER_3, cls.SPEAKER_4,
            cls.SPEAKER_5, cls.SPEAKER_6, cls.SPEAKER_7, cls.SPEAKER_8,
            cls.SPEAKER_9, cls.SPEAKER_10
        ]
        if 0 <= index < len(labels):
            return labels[index]
        return cls.UNKNOWN


class Segment(BaseModel):
    """전사 세그먼트"""
    start: float = Field(description="시작 시간 (초)")
    end: float = Field(description="종료 시간 (초)")
    text: str = Field(description="전사된 텍스트")
    speaker: Optional[str] = Field(default=None, description="화자 레이블")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="신뢰도 (0-1)")

    @property
    def duration(self) -> float:
        """세그먼트 길이 (초)"""
        return self.end - self.start

    @property
    def start_timedelta(self) -> timedelta:
        """시작 시간 timedelta"""
        return timedelta(seconds=self.start)

    @property
    def end_timedelta(self) -> timedelta:
        """종료 시간 timedelta"""
        return timedelta(seconds=self.end)

    def format_timestamp(self, time_seconds: float, format_type: str = "srt") -> str:
        """
        타임스탬프 포맷팅

        Args:
            time_seconds: 시간 (초)
            format_type: 포맷 타입 (srt, vtt)

        Returns:
            포맷된 타임스탬프 문자열
        """
        td = timedelta(seconds=time_seconds)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((td.total_seconds() - total_seconds) * 1000)

        if format_type == "srt":
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        else:  # vtt
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


class TranscriptionResult(BaseModel):
    """전사 결과"""
    segments: list[Segment] = Field(default_factory=list)
    language: str = Field(default="ko")
    duration: float = Field(default=0.0, description="전체 길이 (초)")
    num_speakers: int = Field(default=1, description="감지된 화자 수")
    engine: str = Field(default="unknown", description="사용된 STT 엔진")
    model: Optional[str] = Field(default=None, description="사용된 모델명")

    @property
    def full_text(self) -> str:
        """전체 텍스트 (화자 레이블 포함)"""
        lines = []
        for seg in self.segments:
            if seg.speaker:
                lines.append(f"[{seg.speaker}] {seg.text}")
            else:
                lines.append(seg.text)
        return "\n".join(lines)

    @property
    def speakers(self) -> list[str]:
        """고유 화자 목록"""
        return list(set(seg.speaker for seg in self.segments if seg.speaker))

    def get_speaker_segments(self, speaker: str) -> list[Segment]:
        """특정 화자의 세그먼트만 추출"""
        return [seg for seg in self.segments if seg.speaker == speaker]

    def merge_consecutive_segments(self, max_gap: float = 0.5) -> "TranscriptionResult":
        """
        연속된 동일 화자 세그먼트 병합

        Args:
            max_gap: 병합할 최대 간격 (초)

        Returns:
            병합된 TranscriptionResult
        """
        if not self.segments:
            return self

        merged = []
        current = self.segments[0].model_copy()

        for seg in self.segments[1:]:
            # 같은 화자이고 간격이 max_gap 이하면 병합
            if (seg.speaker == current.speaker and
                    seg.start - current.end <= max_gap):
                current.end = seg.end
                current.text = f"{current.text} {seg.text}"
            else:
                merged.append(current)
                current = seg.model_copy()

        merged.append(current)

        return TranscriptionResult(
            segments=merged,
            language=self.language,
            duration=self.duration,
            num_speakers=self.num_speakers,
            engine=self.engine,
            model=self.model
        )


class STTEngine(ABC):
    """STT 엔진 추상 클래스"""

    @property
    @abstractmethod
    def name(self) -> str:
        """엔진 이름"""
        pass

    @property
    @abstractmethod
    def supports_diarization(self) -> bool:
        """화자 분리 지원 여부"""
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio_path: str,
        language: str = "ko",
        num_speakers: Optional[int] = None,
        proper_nouns: Optional[list[str]] = None,
        use_video_mode: bool = False,
        original_video_path: Optional[str] = None,
        remove_fillers: bool = False,
        election_debate_mode: bool = False,
    ) -> TranscriptionResult:
        """
        오디오/영상 파일 전사

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드
            num_speakers: 화자 수 힌트 (None이면 자동 감지)
            proper_nouns: 고유명사/인명 힌트 리스트 (예: ["황금석", "삼성전자"])
            use_video_mode: 영상 모드 (화면 텍스트를 참고하여 전사 보정)
            original_video_path: 원본 영상 파일 경로 (영상 모드일 때 사용)
            remove_fillers: 필러/더듬거림 제거 여부
            election_debate_mode: 선거 토론회 모드 (사회자/후보명 구분)

        Returns:
            TranscriptionResult 객체
        """
        pass

    async def health_check(self) -> bool:
        """엔진 상태 확인"""
        return True
