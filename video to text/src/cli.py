"""CLI 엔트리포인트 - Typer 기반 명령줄 인터페이스 (Phase 2)"""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .audio.analyzer import AudioAnalyzer
from .pipeline import (
    TranscriptionPipeline, PipelineConfig, PipelineMode, OutputFormat,
    create_pipeline, create_fast_pipeline, create_hybrid_pipeline, create_full_pipeline
)
from .input.youtube import YouTubeDownloader, download_youtube

app = typer.Typer(
    name="vtt",
    help="한국어 토론 화자 분리 및 자막 자동화 시스템 (Phase 2)",
    add_completion=False
)
# Windows 콘솔 UTF-8 호환성
console = Console(force_terminal=True, legacy_windows=False)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"video-to-text v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="버전 정보 출력"
    )
) -> None:
    """한국어 토론 화자 분리 및 자막 자동화 시스템"""
    pass


@app.command()
def transcribe(
    input_source: str = typer.Argument(
        ...,
        help="입력 파일 경로 또는 YouTube URL"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="출력 파일/디렉토리 경로"
    ),
    format: str = typer.Option(
        "srt",
        "--format", "-f",
        help="출력 포맷 (srt, vtt, json, txt - 쉼표로 복수 지정)"
    ),
    speakers: Optional[int] = typer.Option(
        None,
        "--speakers", "-s",
        help="화자 수 힌트 (미지정시 자동 감지)"
    ),
    language: str = typer.Option(
        "ko",
        "--language", "-l",
        help="언어 코드"
    ),
    mode: str = typer.Option(
        "fast",
        "--mode", "-m",
        help="파이프라인 모드 (fast/accurate/hybrid/full)"
    ),
    engine: str = typer.Option(
        "gemini",
        "--engine", "-e",
        help="STT 엔진 (gemini/whisperx)"
    ),
    device: str = typer.Option(
        "cuda",
        "--device", "-d",
        help="연산 장치 (cuda/cpu)"
    ),
    vram: Optional[int] = typer.Option(
        None,
        "--vram",
        help="GPU VRAM 크기 (GB). 지정시 자동으로 최적 모델 선택 (예: --vram 4)"
    ),
    align: bool = typer.Option(
        False,
        "--align",
        help="WhisperX 타임스탬프 정렬 활성화"
    ),
    correct: bool = typer.Option(
        False,
        "--correct",
        help="LLM 교정 활성화 (ANTHROPIC_API_KEY 필요)"
    ),
    no_speaker_labels: bool = typer.Option(
        False,
        "--no-speaker-labels",
        help="화자 레이블 제외"
    ),
) -> None:
    """
    영상/오디오 파일 또는 YouTube URL을 전사하여 자막 파일 생성

    모드 설명:
      fast     - Gemini만 (빠름, 타임스탬프 ±2초)
      accurate - WhisperX만 (정확, GPU 필요, API 키 불필요)
      hybrid   - Gemini + WhisperX 정렬 (권장)
      full     - 하이브리드 + LLM 교정 (최고 품질)

    예시:
        vtt transcribe video.mp4
        vtt transcribe video.mp4 -m hybrid -f srt,json
        vtt transcribe "https://youtube.com/watch?v=xxx" -m accurate
    """
    # YouTube URL 처리
    youtube_info = None
    temp_audio = None

    if YouTubeDownloader.is_youtube_url(input_source):
        console.print(Panel.fit(
            "[bold blue]YouTube 영상 다운로드 중...[/bold blue]",
            border_style="blue"
        ))
        try:
            downloader = YouTubeDownloader()
            info = downloader.get_video_info(input_source)
            console.print(f"  제목: {info.title}")
            console.print(f"  채널: {info.channel}")
            console.print(f"  길이: {info.duration / 60:.1f}분")

            # 임시 디렉토리에 다운로드
            temp_dir = Path(tempfile.mkdtemp(prefix="vtt_youtube_"))
            audio_path, youtube_info = downloader.download_audio_for_transcription(
                input_source, temp_dir
            )
            input_file = audio_path
            temp_audio = audio_path
            console.print("[green]다운로드 완료[/green]\n")
        except Exception as e:
            console.print(f"[red]YouTube 다운로드 실패: {e}[/red]")
            raise typer.Exit(1)
    else:
        input_file = Path(input_source)
        if not input_file.exists():
            console.print(f"[red]파일을 찾을 수 없습니다: {input_file}[/red]")
            raise typer.Exit(1)

    # 출력 포맷 파싱
    formats = []
    for fmt in format.split(","):
        fmt = fmt.strip().lower()
        try:
            formats.append(OutputFormat(fmt))
        except ValueError:
            console.print(f"[yellow]경고: 지원하지 않는 포맷 '{fmt}' 무시[/yellow]")

    if not formats:
        formats = [OutputFormat.SRT]

    # 출력 경로 결정
    if output:
        if output.is_dir() or not output.suffix:
            output_dir = output
        else:
            output_dir = output.parent
    elif youtube_info:
        # YouTube 영상은 현재 디렉토리에 출력
        output_dir = Path.cwd()
    else:
        output_dir = input_file.parent

    # 파이프라인 설정
    try:
        pipeline_mode = PipelineMode(mode.lower())
    except ValueError:
        pipeline_mode = PipelineMode.FAST

    # VRAM 자동 감지 (미지정시)
    detected_vram = None
    if vram is None and device == "cuda":
        try:
            import torch
            if torch.cuda.is_available():
                detected_vram = int(torch.cuda.get_device_properties(0).total_memory / (1024**3))
        except ImportError:
            pass

    config = PipelineConfig(
        mode=pipeline_mode,
        stt_engine=engine,
        language=language,
        num_speakers=speakers,
        output_formats=formats,
        include_speaker_labels=not no_speaker_labels,
        device=device,
        vram_gb=vram or detected_vram,  # VRAM 설정 추가
        enable_timestamp_alignment=align or pipeline_mode in [PipelineMode.HYBRID, PipelineMode.FULL],
        enable_llm_correction=correct or pipeline_mode == PipelineMode.FULL
    )

    # 모드 정보 표시
    console.print(Panel.fit(
        f"[bold]모드:[/bold] {pipeline_mode.value}\n"
        f"[bold]엔진:[/bold] {config.stt_engine}\n"
        f"[bold]타임스탬프 정렬:[/bold] {'✓' if config.enable_timestamp_alignment else '✗'}\n"
        f"[bold]LLM 교정:[/bold] {'✓' if config.enable_llm_correction else '✗'}",
        title="파이프라인 설정",
        border_style="blue"
    ))

    # 진행 상황 표시
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("준비 중...", total=100)

        def update_progress(stage: str, pct: float) -> None:
            progress.update(task, completed=int(pct * 100), description=stage)

        pipeline = TranscriptionPipeline(config, progress_callback=update_progress)
        result = asyncio.run(pipeline.run(input_file, output_dir))

    # 결과 출력
    if result.success:
        console.print()
        console.print(Panel.fit(
            "[green]✓ 전사 완료[/green]",
            border_style="green"
        ))

        # 결과 테이블
        table = Table(title="전사 결과")
        table.add_column("항목", style="cyan")
        table.add_column("값", style="white")

        # YouTube 정보 표시
        if youtube_info:
            table.add_row("소스", "YouTube")
            table.add_row("제목", youtube_info.title[:40] + "..." if len(youtube_info.title) > 40 else youtube_info.title)

        if result.transcription:
            table.add_row("감지된 화자 수", str(result.transcription.num_speakers))
            table.add_row("세그먼트 수", str(len(result.transcription.segments)))
            table.add_row("언어", result.transcription.language)
            table.add_row("엔진", result.transcription.engine)

        if result.audio_metadata:
            table.add_row("원본 길이", result.audio_metadata.duration_formatted)

        # 처리 정보
        if result.processing_info:
            steps = result.processing_info.get("steps_completed", [])
            table.add_row("처리 단계", ", ".join(steps))

        console.print(table)

        # 출력 파일 목록
        console.print("\n[bold]생성된 파일:[/bold]")
        for fmt, path in result.output_files.items():
            console.print(f"  • {fmt}: {path}")

    else:
        console.print()
        console.print(Panel.fit(
            f"[red]✗ 전사 실패[/red]\n{result.error}",
            border_style="red"
        ))
        if result.processing_info:
            console.print(f"완료된 단계: {result.processing_info.get('steps_completed', [])}")
        raise typer.Exit(1)

    # YouTube 임시 파일 정리
    if temp_audio and temp_audio.exists():
        import shutil
        shutil.rmtree(temp_audio.parent, ignore_errors=True)


@app.command()
def analyze(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        help="분석할 파일 경로"
    ),
) -> None:
    """
    오디오/비디오 파일 메타데이터 분석

    예시:
        vtt analyze video.mp4
    """
    analyzer = AudioAnalyzer()

    try:
        metadata = analyzer.analyze(input_file)
        quality = analyzer.get_audio_quality_score(metadata)
        estimate = analyzer.estimate_processing_time(metadata)

        # 메타데이터 테이블
        table = Table(title=f"파일 분석: {input_file.name}")
        table.add_column("항목", style="cyan")
        table.add_column("값", style="white")

        table.add_row("길이", metadata.duration_formatted)
        table.add_row("샘플레이트", f"{metadata.sample_rate:,} Hz")
        table.add_row("채널 수", str(metadata.channels))
        table.add_row("채널 타입", estimate["channel_type"])
        if metadata.codec:
            table.add_row("코덱", metadata.codec)
        if metadata.bit_rate:
            table.add_row("비트레이트", f"{metadata.bit_rate // 1000} kbps")
        table.add_row("파일 크기", f"{metadata.file_size / (1024*1024):.2f} MB")

        console.print(table)

        # 품질 점수
        quality_color = "green" if quality["score"] >= 80 else "yellow" if quality["score"] >= 50 else "red"
        console.print(f"\n[bold]품질 점수:[/bold] [{quality_color}]{quality['score']}/100[/{quality_color}] ({quality['quality_level']})")

        if quality["issues"]:
            console.print("\n[yellow]주의사항:[/yellow]")
            for issue in quality["issues"]:
                console.print(f"  • {issue}")

        if quality["recommendations"]:
            console.print("\n[blue]권장사항:[/blue]")
            for rec in quality["recommendations"]:
                console.print(f"  • {rec}")

        # 비용 추정
        console.print("\n[bold]예상 처리 비용:[/bold]")
        console.print(f"  • Gemini Flash: ${estimate['estimated_cost_gemini_flash']:.4f}")
        console.print(f"  • Gemini Pro: ${estimate['estimated_cost_gemini_pro']:.4f}")
        console.print(f"  • 권장 엔진: {estimate['recommended_engine']}")

    except Exception as e:
        console.print(f"[red]분석 실패: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def engines() -> None:
    """
    사용 가능한 STT 엔진 및 모드 목록

    예시:
        vtt engines
    """
    # 엔진 테이블
    engine_table = Table(title="지원 STT 엔진")
    engine_table.add_column("엔진", style="cyan")
    engine_table.add_column("모델", style="white")
    engine_table.add_column("화자분리", style="green")
    engine_table.add_column("타임스탬프", style="yellow")
    engine_table.add_column("요구사항", style="blue")

    engine_table.add_row(
        "gemini",
        "gemini-2.5-pro",
        "✓ (내장)",
        "±2초",
        "GEMINI_API_KEY"
    )
    engine_table.add_row(
        "whisperx",
        "large-v3",
        "✓ (Pyannote)",
        "±0.1초",
        "GPU (CUDA), HF_TOKEN"
    )

    console.print(engine_table)

    # 모드 테이블
    console.print()
    mode_table = Table(title="파이프라인 모드")
    mode_table.add_column("모드", style="cyan")
    mode_table.add_column("설명", style="white")
    mode_table.add_column("엔진", style="green")
    mode_table.add_column("추가 처리", style="yellow")

    mode_table.add_row(
        "fast",
        "빠른 전사 (기본)",
        "Gemini",
        "-"
    )
    mode_table.add_row(
        "accurate",
        "정확한 전사",
        "WhisperX",
        "-"
    )
    mode_table.add_row(
        "hybrid",
        "하이브리드 (권장)",
        "Gemini",
        "+ WhisperX 타임스탬프 정렬"
    )
    mode_table.add_row(
        "full",
        "최고 품질",
        "Gemini",
        "+ WhisperX 정렬 + LLM 교정"
    )

    console.print(mode_table)

    # 비용 정보
    console.print()
    cost_table = Table(title="예상 비용 (1시간 기준)")
    cost_table.add_column("모드", style="cyan")
    cost_table.add_column("비용", style="green")

    cost_table.add_row("fast (Gemini)", "~$1.50")
    cost_table.add_row("accurate (WhisperX)", "GPU 전기료만")
    cost_table.add_row("hybrid", "~$1.50 + GPU")
    cost_table.add_row("full", "~$1.50 + GPU + ~$0.50 (LLM)")

    console.print(cost_table)


@app.command()
def check() -> None:
    """
    시스템 요구사항 및 API 키 확인

    예시:
        vtt check
    """
    import os
    import shutil

    console.print("[bold]시스템 요구사항 확인[/bold]\n")

    checks = []

    # FFmpeg 확인
    ffmpeg_path = shutil.which("ffmpeg")
    checks.append(("FFmpeg", "✓ 설치됨" if ffmpeg_path else "✗ 설치 필요", bool(ffmpeg_path)))

    # Python 버전
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    checks.append(("Python", f"{'✓' if py_ok else '✗'} {py_version}", py_ok))

    # Gemini API Key
    gemini_key = os.getenv("GEMINI_API_KEY")
    checks.append(("GEMINI_API_KEY", "✓ 설정됨" if gemini_key else "✗ 미설정", bool(gemini_key)))

    # Anthropic API Key (선택)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    checks.append(("ANTHROPIC_API_KEY", "✓ 설정됨" if anthropic_key else "○ 미설정 (선택)", True))

    # Hugging Face Token (선택)
    hf_token = os.getenv("HF_TOKEN")
    checks.append(("HF_TOKEN", "✓ 설정됨" if hf_token else "○ 미설정 (선택)", True))

    # GPU 확인 (상세 정보 포함)
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            # VRAM에 따른 권장 모델
            if vram_gb <= 4:
                recommended = "small (int8)"
            elif vram_gb <= 6:
                recommended = "medium (int8)"
            elif vram_gb <= 8:
                recommended = "large-v3 (int8)"
            else:
                recommended = "large-v3 (float16)"
            checks.append(("GPU", f"[green]OK[/green] {gpu_name}", True))
            checks.append(("VRAM", f"{vram_gb:.1f} GB", True))
            checks.append(("권장 모델", recommended, True))
        else:
            checks.append(("GPU (CUDA)", "[yellow]CPU만 사용 (느림)[/yellow]", True))
    except ImportError:
        checks.append(("GPU (CUDA)", "[yellow]torch 미설치[/yellow]", True))

    # WhisperX 확인
    try:
        import whisperx
        checks.append(("WhisperX", "✓ 설치됨", True))
    except ImportError:
        checks.append(("WhisperX", "○ 미설치 (선택)", True))

    # 결과 테이블
    table = Table(title="요구사항 확인")
    table.add_column("항목", style="cyan")
    table.add_column("상태", style="white")

    all_required_ok = True
    for name, status, ok in checks:
        if "✗" in status:
            table.add_row(name, f"[red]{status}[/red]")
            all_required_ok = False
        elif "○" in status:
            table.add_row(name, f"[yellow]{status}[/yellow]")
        else:
            table.add_row(name, f"[green]{status}[/green]")

    console.print(table)

    if all_required_ok:
        console.print("\n[green]✓ 기본 요구사항 충족[/green]")
    else:
        console.print("\n[red]✗ 필수 요구사항이 충족되지 않았습니다[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
