"""전사 파이프라인 - 전체 워크플로우 오케스트레이션 (Phase 2 하이브리드)"""

import asyncio
import shutil
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from src.audio.extractor import AudioExtractor, ExtractionConfig
from src.audio.analyzer import AudioAnalyzer, AudioMetadata
from src.stt.base import STTEngine, TranscriptionResult
from src.stt.gemini import GeminiSTT, GeminiConfig
from src.output.srt import SRTGenerator, SRTConfig, VTTGenerator
from src.output.json_export import JSONExporter, JSONExportConfig


class OutputFormat(str, Enum):
    """출력 포맷"""
    SRT = "srt"
    VTT = "vtt"
    JSON = "json"
    TXT = "txt"


class PipelineMode(str, Enum):
    """파이프라인 모드"""
    FAST = "fast"           # Gemini만 사용 (빠르지만 타임스탬프 부정확)
    ACCURATE = "accurate"   # WhisperX만 사용 (정확하지만 GPU 필요)
    HYBRID = "hybrid"       # Gemini + WhisperX 정렬 (권장)
    FULL = "full"          # 하이브리드 + LLM 교정 (최고 품질)


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    # 오디오 설정
    audio_format: str = "wav"
    audio_sample_rate: int = 16000
    audio_channels: int = 1

    # 파이프라인 모드
    mode: PipelineMode = PipelineMode.FAST

    # STT 설정
    stt_engine: str = "gemini"  # "gemini" 또는 "whisperx"
    gemini_model: str = "gemini-3-flash-preview"  # 기본: Gemini 3 Flash (백업: gemini-3-pro)
    language: str = "ko"
    num_speakers: Optional[int] = None
    proper_nouns: Optional[list[str]] = None  # 후보자 이름/정책명 힌트
    use_video_mode: bool = False  # 영상 모드 (자동 감지)
    remove_fillers: bool = False  # 필러 제거 (비활성화)
    election_debate_mode: bool = True  # 선거 토론회 모드 (기본 활성화)

    # Phase 2 옵션
    enable_timestamp_alignment: bool = False  # WhisperX 타임스탬프 정렬
    enable_llm_correction: bool = False       # Claude LLM 교정
    enable_pyannote_diarization: bool = False # Pyannote 화자분리

    # 출력 설정
    output_formats: list[OutputFormat] = field(
        default_factory=lambda: [OutputFormat.SRT]
    )
    include_speaker_labels: bool = True

    # 기타
    temp_dir: Optional[str] = None
    cleanup_temp: bool = True
    device: str = "cuda"  # WhisperX용
    vram_gb: Optional[int] = None  # GPU VRAM (GB) - 자동 모델 선택용


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    transcription: Optional[TranscriptionResult] = None
    output_files: dict[str, Path] = field(default_factory=dict)
    audio_metadata: Optional[AudioMetadata] = None
    error: Optional[str] = None
    processing_info: dict = field(default_factory=dict)


class TranscriptionPipeline:
    """전사 파이프라인 (Phase 2 하이브리드 지원)"""

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        self.config = config or PipelineConfig()
        self.progress_callback = progress_callback

        # 컴포넌트 초기화
        self._extractor: Optional[AudioExtractor] = None
        self._analyzer: Optional[AudioAnalyzer] = None
        self._stt_engine: Optional[STTEngine] = None
        self._timestamp_aligner = None
        self._llm_corrector = None
        self._speaker_diarizer = None
        self._temp_dir: Optional[Path] = None

        # 모드에 따른 설정 자동 적용
        self._apply_mode_settings()

    def _apply_mode_settings(self):
        """모드에 따른 설정 자동 적용"""
        if self.config.mode == PipelineMode.FAST:
            self.config.stt_engine = "gemini"
            self.config.enable_timestamp_alignment = False
            self.config.enable_llm_correction = False

        elif self.config.mode == PipelineMode.ACCURATE:
            self.config.stt_engine = "whisperx"
            self.config.enable_timestamp_alignment = False
            self.config.enable_llm_correction = False

        elif self.config.mode == PipelineMode.HYBRID:
            self.config.stt_engine = "gemini"
            self.config.enable_timestamp_alignment = True
            self.config.enable_llm_correction = False

        elif self.config.mode == PipelineMode.FULL:
            self.config.stt_engine = "gemini"
            self.config.enable_timestamp_alignment = True
            self.config.enable_llm_correction = True

    def _report_progress(self, stage: str, progress: float) -> None:
        if self.progress_callback:
            self.progress_callback(stage, progress)

    def _get_extractor(self) -> AudioExtractor:
        if self._extractor is None:
            self._extractor = AudioExtractor(ExtractionConfig(
                format=self.config.audio_format,
                sample_rate=self.config.audio_sample_rate,
                channels=self.config.audio_channels
            ))
        return self._extractor

    def _get_analyzer(self) -> AudioAnalyzer:
        if self._analyzer is None:
            self._analyzer = AudioAnalyzer()
        return self._analyzer

    def _get_stt_engine(self) -> STTEngine:
        if self._stt_engine is None:
            if self.config.stt_engine == "gemini":
                # 모델별 설정
                gemini_config = GeminiConfig(model=self.config.gemini_model)

                # Gemini 3 Flash는 thinking_level과 temperature 설정 필요
                if "gemini-3" in self.config.gemini_model:
                    gemini_config.thinking_level = "medium"
                    gemini_config.media_resolution = "low"
                    gemini_config.temperature = 1.0
                else:
                    # Gemini 2.5 Pro는 기존 설정 유지
                    gemini_config.temperature = 0.1

                print(f"[Pipeline] Gemini 모델: {self.config.gemini_model}")
                self._stt_engine = GeminiSTT(gemini_config)
            elif self.config.stt_engine == "whisperx":
                from src.stt.whisperx import WhisperXSTT, WhisperXConfig
                # VRAM에 따른 자동 설정
                if self.config.vram_gb and self.config.vram_gb <= 6:
                    whisperx_config = WhisperXConfig.for_low_vram(self.config.vram_gb)
                elif self.config.device == "cpu":
                    whisperx_config = WhisperXConfig.for_cpu()
                else:
                    whisperx_config = WhisperXConfig(device=self.config.device)
                self._stt_engine = WhisperXSTT(whisperx_config)
            else:
                raise ValueError(f"지원하지 않는 STT 엔진: {self.config.stt_engine}")
        return self._stt_engine

    def _get_timestamp_aligner(self):
        if self._timestamp_aligner is None:
            from src.postprocess.timestamp_aligner import TimestampAligner, TimestampAlignerConfig
            self._timestamp_aligner = TimestampAligner(TimestampAlignerConfig(
                device=self.config.device
            ))
        return self._timestamp_aligner

    def _get_llm_corrector(self):
        if self._llm_corrector is None:
            from src.postprocess.llm_corrector import LLMCorrector
            self._llm_corrector = LLMCorrector()
        return self._llm_corrector

    def _get_speaker_diarizer(self):
        if self._speaker_diarizer is None:
            from src.diarization.speaker import SpeakerDiarizer, SpeakerDiarizerConfig
            self._speaker_diarizer = SpeakerDiarizer(SpeakerDiarizerConfig(
                device=self.config.device
            ))
        return self._speaker_diarizer

    def _get_temp_dir(self) -> Path:
        if self._temp_dir is None:
            if self.config.temp_dir:
                self._temp_dir = Path(self.config.temp_dir)
                self._temp_dir.mkdir(parents=True, exist_ok=True)
            else:
                self._temp_dir = Path(tempfile.mkdtemp(prefix="vtt_pipeline_"))
        return self._temp_dir

    def _cleanup(self) -> None:
        if self.config.cleanup_temp and self._temp_dir and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    async def run(
        self,
        input_path: str | Path,
        output_dir: Optional[str | Path] = None,
    ) -> PipelineResult:
        """
        파이프라인 실행

        Args:
            input_path: 입력 파일 경로
            output_dir: 출력 디렉토리

        Returns:
            PipelineResult 객체
        """
        input_path = Path(input_path)
        if not input_path.exists():
            return PipelineResult(
                success=False,
                error=f"입력 파일을 찾을 수 없습니다: {input_path}"
            )

        # 🎬 파일 확장자 기반 영상/오디오 자동 감지
        VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.flv'}
        AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma'}
        file_ext = input_path.suffix.lower()

        if file_ext in VIDEO_EXTENSIONS:
            # 영상 파일 → 영상 모드 자동 활성화
            if not self.config.use_video_mode:
                print(f"[Pipeline] 🎬 영상 파일 감지 ({file_ext}) → 영상 모드 자동 활성화")
                self.config.use_video_mode = True
        elif file_ext in AUDIO_EXTENSIONS:
            # 오디오 파일 → 영상 모드 비활성화
            if self.config.use_video_mode:
                print(f"[Pipeline] 🎵 오디오 파일 감지 ({file_ext}) → 영상 모드 자동 비활성화")
                self.config.use_video_mode = False
        else:
            print(f"[Pipeline] ⚠️ 알 수 없는 확장자 ({file_ext}) → 기존 설정 유지")

        output_dir = Path(output_dir) if output_dir else input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = input_path.stem

        processing_info = {
            "mode": self.config.mode.value,
            "stt_engine": self.config.stt_engine,
            "steps_completed": []
        }

        try:
            # 1. 오디오 분석
            self._report_progress("분석", 0.05)
            analyzer = self._get_analyzer()
            metadata = analyzer.analyze(input_path)
            processing_info["steps_completed"].append("audio_analysis")

            # 2. 오디오 추출
            self._report_progress("오디오 추출", 0.1)
            extractor = self._get_extractor()
            temp_dir = self._get_temp_dir()
            audio_path = temp_dir / f"audio.{self.config.audio_format}"
            extractor.extract(input_path, audio_path)
            processing_info["steps_completed"].append("audio_extraction")

            # 3. 전사 (STT)
            self._report_progress("전사", 0.3)
            stt_engine = self._get_stt_engine()
            transcription = await stt_engine.transcribe(
                str(audio_path),
                language=self.config.language,
                num_speakers=self.config.num_speakers,
                proper_nouns=self.config.proper_nouns,
                use_video_mode=self.config.use_video_mode,
                original_video_path=str(input_path),  # 원본 영상 경로 전달
                remove_fillers=self.config.remove_fillers,  # 필러 제거 옵션
                election_debate_mode=self.config.election_debate_mode  # 선거 토론회 모드
            )
            processing_info["steps_completed"].append(f"stt_{self.config.stt_engine}")
            if self.config.use_video_mode:
                processing_info["steps_completed"].append("video_mode_enabled")
            if self.config.remove_fillers:
                processing_info["steps_completed"].append("filler_removal_enabled")
            if self.config.election_debate_mode:
                processing_info["steps_completed"].append("election_debate_mode_enabled")

            # 4. Pyannote 화자분리 (선택적, Gemini 화자분리 대체)
            if self.config.enable_pyannote_diarization:
                self._report_progress("화자 분리 (Pyannote)", 0.5)
                try:
                    diarizer = self._get_speaker_diarizer()
                    diarization = await diarizer.diarize(
                        str(audio_path),
                        self.config.num_speakers
                    )
                    transcription = diarizer.align_speakers(transcription, diarization)
                    processing_info["steps_completed"].append("pyannote_diarization")
                except Exception as e:
                    processing_info["pyannote_error"] = str(e)

            # 5. 타임스탬프 정렬 (Phase 2)
            if self.config.enable_timestamp_alignment:
                self._report_progress("타임스탬프 정렬", 0.6)
                try:
                    aligner = self._get_timestamp_aligner()
                    transcription = await aligner.align(str(audio_path), transcription)
                    processing_info["steps_completed"].append("timestamp_alignment")
                except Exception as e:
                    processing_info["alignment_error"] = str(e)

            # 6. LLM 교정 (Phase 2)
            if self.config.enable_llm_correction:
                self._report_progress("LLM 교정", 0.75)
                try:
                    corrector = self._get_llm_corrector()
                    # 고유명사 힌트를 context_hint로 전달
                    context_hint = None
                    if self.config.proper_nouns:
                        context_hint = f"등장 인물/용어: {', '.join(self.config.proper_nouns)}"
                    transcription = await corrector.correct(transcription, context_hint=context_hint)
                    processing_info["steps_completed"].append("llm_correction")
                except Exception as e:
                    processing_info["correction_error"] = str(e)

            # 7. 세그먼트 병합
            self._report_progress("후처리", 0.85)
            transcription = transcription.merge_consecutive_segments()
            processing_info["steps_completed"].append("merge_segments")

            # 8. 출력 파일 생성
            self._report_progress("출력 생성", 0.9)
            output_files = {}

            for fmt in self.config.output_formats:
                output_path = output_dir / f"{base_name}.{fmt.value}"

                if fmt == OutputFormat.SRT:
                    generator = SRTGenerator(SRTConfig(
                        include_speaker=self.config.include_speaker_labels
                    ))
                    generator.save(transcription, output_path)

                elif fmt == OutputFormat.VTT:
                    generator = VTTGenerator(SRTConfig(
                        include_speaker=self.config.include_speaker_labels
                    ))
                    generator.save(transcription, output_path)

                elif fmt == OutputFormat.JSON:
                    exporter = JSONExporter(JSONExportConfig())
                    exporter.save(transcription, output_path, str(input_path))

                elif fmt == OutputFormat.TXT:
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(transcription.full_text)

                output_files[fmt.value] = output_path

            self._report_progress("완료", 1.0)

            return PipelineResult(
                success=True,
                transcription=transcription,
                output_files=output_files,
                audio_metadata=metadata,
                processing_info=processing_info
            )

        except Exception as e:
            return PipelineResult(
                success=False,
                error=str(e),
                processing_info=processing_info
            )

        finally:
            self._cleanup()

    def run_sync(
        self,
        input_path: str | Path,
        output_dir: Optional[str | Path] = None,
    ) -> PipelineResult:
        """동기 실행 래퍼"""
        return asyncio.run(self.run(input_path, output_dir))


def create_pipeline(
    mode: str = "fast",
    language: str = "ko",
    num_speakers: Optional[int] = None,
    output_formats: Optional[list[str]] = None,
    include_speaker_labels: bool = True,
    device: str = "cuda",
) -> TranscriptionPipeline:
    """
    파이프라인 팩토리 함수

    Args:
        mode: 파이프라인 모드 ("fast", "accurate", "hybrid", "full")
        language: 언어 코드
        num_speakers: 화자 수 힌트
        output_formats: 출력 포맷 리스트 (["srt", "json"])
        include_speaker_labels: 화자 레이블 포함 여부
        device: 연산 장치 ("cuda" 또는 "cpu")

    Returns:
        설정된 TranscriptionPipeline
    """
    # 모드 파싱
    try:
        pipeline_mode = PipelineMode(mode.lower())
    except ValueError:
        pipeline_mode = PipelineMode.FAST

    # 출력 포맷 파싱
    formats = []
    if output_formats:
        for fmt in output_formats:
            try:
                formats.append(OutputFormat(fmt.lower()))
            except ValueError:
                pass
    if not formats:
        formats = [OutputFormat.SRT]

    config = PipelineConfig(
        mode=pipeline_mode,
        language=language,
        num_speakers=num_speakers,
        output_formats=formats,
        include_speaker_labels=include_speaker_labels,
        device=device
    )

    return TranscriptionPipeline(config)


# 편의 함수들
def create_fast_pipeline(**kwargs) -> TranscriptionPipeline:
    """빠른 파이프라인 (Gemini만)"""
    return create_pipeline(mode="fast", **kwargs)


def create_accurate_pipeline(**kwargs) -> TranscriptionPipeline:
    """정확한 파이프라인 (WhisperX)"""
    return create_pipeline(mode="accurate", **kwargs)


def create_hybrid_pipeline(**kwargs) -> TranscriptionPipeline:
    """하이브리드 파이프라인 (Gemini + WhisperX 정렬)"""
    return create_pipeline(mode="hybrid", **kwargs)


def create_full_pipeline(**kwargs) -> TranscriptionPipeline:
    """전체 파이프라인 (하이브리드 + LLM 교정)"""
    return create_pipeline(mode="full", **kwargs)
