"""화자 분리 통합 모듈 - Pyannote 기반"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from src.stt.base import TranscriptionResult, Segment


class DiarizationSegment(BaseModel):
    """화자 분리 세그먼트"""
    start: float
    end: float
    speaker: str


class DiarizationResult(BaseModel):
    """화자 분리 결과"""
    segments: list[DiarizationSegment]
    num_speakers: int


class SpeakerDiarizerConfig(BaseModel):
    """화자 분리 설정"""
    device: str = "cuda"
    hf_token: Optional[str] = None
    min_speakers: Optional[int] = None
    max_speakers: Optional[int] = None


class SpeakerDiarizer:
    """
    Pyannote 기반 화자 분리기

    특징:
    - 최신 Pyannote 3.1 모델 사용
    - 중첩 발화 처리 지원
    - 화자 임베딩 기반 정확한 구분

    요구사항:
    - pyannote.audio 패키지
    - Hugging Face 토큰 (모델 다운로드용)
    """

    def __init__(self, config: Optional[SpeakerDiarizerConfig] = None):
        self.config = config or SpeakerDiarizerConfig()
        self._pipeline = None

    def _get_hf_token(self) -> str:
        """Hugging Face 토큰 가져오기"""
        token = self.config.hf_token or os.getenv("HF_TOKEN")
        if not token:
            raise ValueError(
                "Hugging Face 토큰이 필요합니다. "
                "HF_TOKEN 환경변수를 설정하거나 config에 hf_token을 전달하세요. "
                "토큰 발급: https://huggingface.co/settings/tokens"
            )
        return token

    def _load_pipeline(self):
        """Pyannote 파이프라인 로드"""
        if self._pipeline is not None:
            return

        try:
            from pyannote.audio import Pipeline
            import torch
        except ImportError:
            raise RuntimeError(
                "pyannote.audio가 설치되지 않았습니다. "
                "'pip install pyannote.audio' 실행 필요"
            )

        token = self._get_hf_token()

        self._pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=token
        )

        # GPU 사용 설정
        if self.config.device == "cuda":
            import torch
            if torch.cuda.is_available():
                self._pipeline.to(torch.device("cuda"))

    async def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """
        화자 분리 수행

        Args:
            audio_path: 오디오 파일 경로
            num_speakers: 화자 수 힌트 (None이면 자동 감지)

        Returns:
            DiarizationResult 객체
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._diarize_sync,
            audio_path,
            num_speakers
        )

    def _diarize_sync(
        self,
        audio_path: str,
        num_speakers: Optional[int]
    ) -> DiarizationResult:
        """동기 화자 분리"""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        self._load_pipeline()

        # 파이프라인 실행 옵션
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        elif self.config.min_speakers or self.config.max_speakers:
            if self.config.min_speakers:
                kwargs["min_speakers"] = self.config.min_speakers
            if self.config.max_speakers:
                kwargs["max_speakers"] = self.config.max_speakers

        # 화자 분리 실행
        diarization = self._pipeline(str(audio_path), **kwargs)

        # 결과 변환
        segments = []
        speakers = set()

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            # SPEAKER_00 -> 화자1 형식 변환
            speaker_num = int(speaker.split("_")[1]) + 1
            speaker_label = f"화자{speaker_num}"

            segments.append(DiarizationSegment(
                start=turn.start,
                end=turn.end,
                speaker=speaker_label
            ))

        return DiarizationResult(
            segments=segments,
            num_speakers=len(speakers)
        )

    def align_speakers(
        self,
        transcription: TranscriptionResult,
        diarization: DiarizationResult,
        tolerance: float = 0.5
    ) -> TranscriptionResult:
        """
        전사 결과와 화자 분리 결과 정렬

        Args:
            transcription: 전사 결과
            diarization: 화자 분리 결과
            tolerance: 시간 허용 오차 (초)

        Returns:
            화자 정보가 업데이트된 TranscriptionResult
        """
        aligned_segments = []

        for seg in transcription.segments:
            # 세그먼트 중간점 계산
            seg_mid = (seg.start + seg.end) / 2

            # 가장 적합한 화자 찾기
            best_speaker = None
            best_overlap = 0

            for dia_seg in diarization.segments:
                # 겹치는 구간 계산
                overlap_start = max(seg.start, dia_seg.start)
                overlap_end = min(seg.end, dia_seg.end)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = dia_seg.speaker

            aligned_segments.append(Segment(
                start=seg.start,
                end=seg.end,
                text=seg.text,
                speaker=best_speaker or seg.speaker,
                confidence=seg.confidence
            ))

        return TranscriptionResult(
            segments=aligned_segments,
            language=transcription.language,
            duration=transcription.duration,
            num_speakers=diarization.num_speakers,
            engine=transcription.engine,
            model=transcription.model
        )

    def diarize_sync(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """동기 버전 (직접 호출용)"""
        return self._diarize_sync(audio_path, num_speakers)
