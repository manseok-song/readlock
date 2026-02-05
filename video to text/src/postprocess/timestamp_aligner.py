"""타임스탬프 정렬 모듈 - WhisperX 기반 정밀 정렬"""

import asyncio
from pathlib import Path
from typing import Optional

from src.stt.base import TranscriptionResult, Segment


class TimestampAlignerConfig:
    """타임스탬프 정렬 설정"""
    def __init__(
        self,
        device: str = "cuda",
        tolerance_ms: int = 500,
        align_model: str = "WAV2VEC2_ASR_LARGE_LV60K_960H"
    ):
        self.device = device
        self.tolerance_ms = tolerance_ms
        self.align_model = align_model


class TimestampAligner:
    """
    WhisperX 기반 정밀 타임스탬프 정렬기

    용도:
    - Gemini의 대략적인 타임스탬프를 WhisperX로 정밀 정렬
    - 단어 단위 타임스탬프 생성
    - VAD (Voice Activity Detection) 기반 정렬

    작동 원리:
    1. Gemini 전사 텍스트를 입력으로 받음
    2. WhisperX의 정렬 모델로 오디오와 텍스트 매칭
    3. 단어 단위 정밀 타임스탬프 생성
    4. 세그먼트 타임스탬프 보정
    """

    def __init__(self, config: Optional[TimestampAlignerConfig] = None):
        self.config = config or TimestampAlignerConfig()
        self._align_model = None
        self._align_metadata = None

    def _check_dependencies(self) -> tuple[bool, str]:
        """의존성 확인"""
        try:
            import whisperx
            import torch
            return True, ""
        except ImportError as e:
            return False, f"WhisperX 의존성 부족: {e}. 'pip install whisperx torch' 실행 필요"

    def _load_align_model(self, language: str):
        """정렬 모델 로드"""
        if self._align_model is not None:
            return

        import whisperx

        self._align_model, self._align_metadata = whisperx.load_align_model(
            language_code=language,
            device=self.config.device
        )

    async def align(
        self,
        audio_path: str,
        transcription: TranscriptionResult
    ) -> TranscriptionResult:
        """
        타임스탬프 정렬

        Args:
            audio_path: 오디오 파일 경로
            transcription: Gemini 등 다른 엔진의 전사 결과

        Returns:
            정렬된 TranscriptionResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._align_sync,
            audio_path,
            transcription
        )

    def _align_sync(
        self,
        audio_path: str,
        transcription: TranscriptionResult
    ) -> TranscriptionResult:
        """동기 정렬"""
        import whisperx

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        ok, msg = self._check_dependencies()
        if not ok:
            raise RuntimeError(msg)

        # 오디오 로드
        audio = whisperx.load_audio(str(audio_path))

        # 정렬 모델 로드
        self._load_align_model(transcription.language)

        # 세그먼트를 WhisperX 형식으로 변환
        segments_for_align = [
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            }
            for seg in transcription.segments
        ]

        # 정렬 수행
        aligned_result = whisperx.align(
            segments_for_align,
            self._align_model,
            self._align_metadata,
            audio,
            self.config.device,
            return_char_alignments=False
        )

        # 결과 변환
        aligned_segments = []
        original_speakers = {
            (seg.start, seg.end): seg.speaker
            for seg in transcription.segments
        }

        for i, seg in enumerate(aligned_result.get("segments", [])):
            # 원본 화자 정보 매칭 (가장 가까운 원본 세그먼트)
            original_speaker = None
            if i < len(transcription.segments):
                original_speaker = transcription.segments[i].speaker

            aligned_segments.append(Segment(
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                text=seg.get("text", "").strip(),
                speaker=original_speaker,
                confidence=seg.get("confidence")
            ))

        return TranscriptionResult(
            segments=aligned_segments,
            language=transcription.language,
            duration=aligned_segments[-1].end if aligned_segments else 0.0,
            num_speakers=transcription.num_speakers,
            engine=f"{transcription.engine}+whisperx_aligned",
            model=transcription.model
        )

    def get_word_level_alignment(
        self,
        audio_path: str,
        transcription: TranscriptionResult
    ) -> list[dict]:
        """
        단어 단위 타임스탬프 추출

        Args:
            audio_path: 오디오 파일 경로
            transcription: 전사 결과

        Returns:
            단어별 타임스탬프 리스트
        """
        import whisperx

        audio = whisperx.load_audio(str(audio_path))
        self._load_align_model(transcription.language)

        segments_for_align = [
            {"start": seg.start, "end": seg.end, "text": seg.text}
            for seg in transcription.segments
        ]

        aligned = whisperx.align(
            segments_for_align,
            self._align_model,
            self._align_metadata,
            audio,
            self.config.device,
            return_char_alignments=False
        )

        words = []
        for seg in aligned.get("segments", []):
            for word in seg.get("words", []):
                words.append({
                    "word": word.get("word", ""),
                    "start": word.get("start", 0),
                    "end": word.get("end", 0),
                    "confidence": word.get("score")
                })

        return words

    def align_sync(
        self,
        audio_path: str,
        transcription: TranscriptionResult
    ) -> TranscriptionResult:
        """동기 버전 (직접 호출용)"""
        return self._align_sync(audio_path, transcription)

    def calculate_alignment_quality(
        self,
        original: TranscriptionResult,
        aligned: TranscriptionResult
    ) -> dict:
        """
        정렬 품질 계산

        Args:
            original: 원본 전사 결과
            aligned: 정렬된 전사 결과

        Returns:
            품질 지표 딕셔너리
        """
        if len(original.segments) != len(aligned.segments):
            return {"error": "세그먼트 수가 일치하지 않습니다"}

        total_shift = 0
        max_shift = 0
        shifts = []

        for orig, align in zip(original.segments, aligned.segments):
            start_shift = abs(orig.start - align.start)
            end_shift = abs(orig.end - align.end)
            avg_shift = (start_shift + end_shift) / 2

            shifts.append(avg_shift)
            total_shift += avg_shift
            max_shift = max(max_shift, start_shift, end_shift)

        avg_shift = total_shift / len(shifts) if shifts else 0

        return {
            "average_shift_seconds": round(avg_shift, 3),
            "max_shift_seconds": round(max_shift, 3),
            "segments_count": len(shifts),
            "quality": "good" if avg_shift < 0.5 else "moderate" if avg_shift < 1.0 else "poor"
        }
