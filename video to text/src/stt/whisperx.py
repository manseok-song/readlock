"""WhisperX STT 엔진 - 정밀 타임스탬프 및 화자분리"""

import asyncio
from pathlib import Path
from typing import Optional

from src.stt.base import STTEngine, TranscriptionResult, Segment


class WhisperXConfig:
    """WhisperX 설정"""
    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        batch_size: int = 16,
        hf_token: Optional[str] = None,  # Hugging Face token (Pyannote용)
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.batch_size = batch_size
        self.hf_token = hf_token

    @classmethod
    def for_low_vram(cls, vram_gb: int = 4) -> "WhisperXConfig":
        """
        저사양 GPU용 설정 (4-6GB VRAM)

        Args:
            vram_gb: GPU VRAM 크기 (GB)

        Returns:
            최적화된 WhisperXConfig
        """
        if vram_gb <= 4:
            # GTX 1050 Ti, GTX 1650 등
            return cls(
                model_size="small",      # ~2GB VRAM
                compute_type="int8",     # 메모리 절약
                batch_size=4,            # 작은 배치
            )
        elif vram_gb <= 6:
            # GTX 1060, RTX 3050 등
            return cls(
                model_size="medium",     # ~5GB VRAM
                compute_type="int8",
                batch_size=8,
            )
        else:
            # RTX 3060 이상
            return cls(
                model_size="large-v3",
                compute_type="float16",
                batch_size=16,
            )

    @classmethod
    def for_cpu(cls) -> "WhisperXConfig":
        """CPU 전용 설정 (GPU 없을 때)"""
        return cls(
            model_size="small",
            device="cpu",
            compute_type="int8",
            batch_size=2,
        )


class WhisperXSTT(STTEngine):
    """
    WhisperX 기반 STT 엔진

    특징:
    - 로컬 GPU 기반 전사 (무료)
    - 단어 단위 정밀 타임스탬프 (±0.1초)
    - Pyannote 통합 화자분리
    - 배치 처리로 3배 빠른 속도

    요구사항:
    - GPU (CUDA) 권장
    - whisperx 패키지: pip install whisperx
    - torch: pip install torch
    - Hugging Face 토큰 (화자분리용, 선택)
    """

    def __init__(self, config: Optional[WhisperXConfig] = None):
        self.config = config or WhisperXConfig()
        self._model = None
        self._diarize_model = None
        self._align_model = None
        self._align_metadata = None

    @property
    def name(self) -> str:
        return "whisperx"

    @property
    def supports_diarization(self) -> bool:
        return True

    def _check_dependencies(self) -> tuple[bool, str]:
        """의존성 확인"""
        try:
            import whisperx
            import torch
            return True, ""
        except ImportError as e:
            return False, f"WhisperX 의존성 부족: {e}. 'pip install whisperx torch' 실행 필요"

    def _load_model(self):
        """Whisper 모델 로드"""
        if self._model is not None:
            return

        import whisperx

        self._model = whisperx.load_model(
            self.config.model_size,
            self.config.device,
            compute_type=self.config.compute_type
        )

    def _load_align_model(self, language: str):
        """정렬 모델 로드"""
        if self._align_model is not None:
            return

        import whisperx

        self._align_model, self._align_metadata = whisperx.load_align_model(
            language_code=language,
            device=self.config.device
        )

    def _load_diarize_model(self):
        """화자분리 모델 로드 (Pyannote)"""
        if self._diarize_model is not None:
            return

        import whisperx
        import os

        hf_token = self.config.hf_token or os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError(
                "화자분리를 위해 Hugging Face 토큰이 필요합니다. "
                "HF_TOKEN 환경변수를 설정하거나 config에 hf_token을 전달하세요. "
                "토큰은 https://huggingface.co/settings/tokens 에서 발급받을 수 있습니다."
            )

        self._diarize_model = whisperx.DiarizationPipeline(
            use_auth_token=hf_token,
            device=self.config.device
        )

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
        WhisperX를 사용한 전사

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드
            num_speakers: 화자 수 힌트 (None이면 자동 감지)
            proper_nouns: (미사용) Gemini 전용 옵션
            use_video_mode: (미사용) Gemini 전용 옵션
            original_video_path: (미사용) Gemini 전용 옵션
            remove_fillers: (미사용) Gemini 전용 옵션
            election_debate_mode: (미사용) Gemini 전용 옵션

        Returns:
            TranscriptionResult 객체
        """
        # 동기 작업을 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_path,
            language,
            num_speakers
        )

    def _transcribe_sync(
        self,
        audio_path: str,
        language: str,
        num_speakers: Optional[int],
    ) -> TranscriptionResult:
        """동기 전사 수행"""
        import whisperx

        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        # 의존성 확인
        ok, msg = self._check_dependencies()
        if not ok:
            raise RuntimeError(msg)

        # 1. 모델 로드
        self._load_model()

        # 2. 오디오 로드
        audio = whisperx.load_audio(str(audio_path))

        # 3. 전사 수행
        result = self._model.transcribe(
            audio,
            batch_size=self.config.batch_size,
            language=language
        )

        # 4. 단어 단위 타임스탬프 정렬
        self._load_align_model(language)
        result = whisperx.align(
            result["segments"],
            self._align_model,
            self._align_metadata,
            audio,
            self.config.device,
            return_char_alignments=False
        )

        # 5. 화자 분리 (선택적)
        diarize_segments = None
        if num_speakers is not None or self.config.hf_token:
            try:
                self._load_diarize_model()
                diarize_segments = self._diarize_model(
                    audio,
                    min_speakers=num_speakers,
                    max_speakers=num_speakers
                )
                result = whisperx.assign_word_speakers(diarize_segments, result)
            except Exception as e:
                # 화자분리 실패해도 전사 결과는 반환
                print(f"화자분리 실패 (무시됨): {e}")

        # 6. TranscriptionResult 변환
        segments = []
        detected_speakers = set()

        for seg in result.get("segments", []):
            speaker = seg.get("speaker", None)
            if speaker:
                detected_speakers.add(speaker)
                # SPEAKER_00 -> 화자1 형식으로 변환
                speaker_num = int(speaker.split("_")[1]) + 1
                speaker = f"화자{speaker_num}"

            segments.append(Segment(
                start=float(seg.get("start", 0)),
                end=float(seg.get("end", 0)),
                text=seg.get("text", "").strip(),
                speaker=speaker,
                confidence=seg.get("confidence")
            ))

        # 전체 길이 계산
        total_duration = segments[-1].end if segments else 0.0

        return TranscriptionResult(
            segments=segments,
            language=language,
            duration=total_duration,
            num_speakers=len(detected_speakers) if detected_speakers else 1,
            engine=self.name,
            model=self.config.model_size
        )

    def transcribe_sync(
        self,
        audio_path: str,
        language: str = "ko",
        num_speakers: Optional[int] = None,
    ) -> TranscriptionResult:
        """동기 버전 전사 (직접 호출용)"""
        return self._transcribe_sync(audio_path, language, num_speakers)

    async def health_check(self) -> bool:
        """WhisperX 사용 가능 여부 확인"""
        try:
            import torch
            import whisperx
            # GPU 있으면 True, 없어도 CPU로 실행 가능
            return True
        except ImportError:
            return False

    def get_word_timestamps(
        self,
        audio_path: str,
        language: str = "ko"
    ) -> list[dict]:
        """
        단어 단위 타임스탬프만 추출

        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드

        Returns:
            단어별 타임스탬프 리스트
        """
        import whisperx

        self._load_model()
        self._load_align_model(language)

        audio = whisperx.load_audio(str(audio_path))
        result = self._model.transcribe(audio, batch_size=self.config.batch_size, language=language)
        result = whisperx.align(
            result["segments"],
            self._align_model,
            self._align_metadata,
            audio,
            self.config.device,
            return_char_alignments=False
        )

        words = []
        for seg in result.get("segments", []):
            for word in seg.get("words", []):
                words.append({
                    "word": word.get("word", ""),
                    "start": word.get("start", 0),
                    "end": word.get("end", 0),
                    "confidence": word.get("score", None)
                })

        return words
