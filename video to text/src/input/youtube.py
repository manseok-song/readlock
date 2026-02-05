"""YouTube 다운로더 - yt-dlp 기반"""

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import subprocess
import shutil


@dataclass
class VideoInfo:
    """YouTube 영상 정보"""
    title: str
    duration: float  # 초
    channel: str
    url: str
    thumbnail: Optional[str] = None

    @property
    def duration_formatted(self) -> str:
        """포맷된 시간 (HH:MM:SS 또는 MM:SS)"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"


class YouTubeDownloader:
    """
    YouTube 영상 다운로더

    yt-dlp를 사용하여 YouTube 영상을 다운로드합니다.
    오디오만 추출하여 전사에 최적화된 형식으로 변환합니다.
    """

    # YouTube URL 패턴
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(tempfile.gettempdir())
        self._check_yt_dlp()

    def _check_yt_dlp(self) -> None:
        """yt-dlp 설치 확인"""
        if not shutil.which("yt-dlp"):
            raise RuntimeError(
                "yt-dlp가 설치되어 있지 않습니다. "
                "'pip install yt-dlp' 또는 'winget install yt-dlp'로 설치하세요."
            )

    @classmethod
    def is_youtube_url(cls, url: str) -> bool:
        """YouTube URL인지 확인"""
        for pattern in cls.YOUTUBE_PATTERNS:
            if re.match(pattern, url):
                return True
        return False

    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID 추출"""
        for pattern in cls.YOUTUBE_PATTERNS:
            match = re.match(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_video_info(self, url: str) -> VideoInfo:
        """영상 정보 가져오기"""
        try:
            import json
            result = subprocess.run(
                [
                    "yt-dlp", "-j", "--no-download",
                    "--js-runtimes", "nodejs",
                    "--extractor-args", "youtube:player_client=web",
                    "--no-warnings",
                    url
                ],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return VideoInfo(
                title=data.get("title", "Unknown"),
                duration=float(data.get("duration", 0)),
                channel=data.get("channel", "Unknown"),
                url=url,
                thumbnail=data.get("thumbnail")
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"영상 정보를 가져올 수 없습니다: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"영상 정보 파싱 실패: {e}")

    def download(
        self,
        url: str,
        output_path: Optional[Path] = None,
        audio_only: bool = True,
        format: str = "wav",
    ) -> Path:
        """
        YouTube 영상 다운로드

        Args:
            url: YouTube URL
            output_path: 출력 파일 경로 (미지정시 임시 디렉토리)
            audio_only: 오디오만 추출 (기본 True)
            format: 오디오 포맷 (wav, mp3, m4a)

        Returns:
            다운로드된 파일 경로
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"유효하지 않은 YouTube URL: {url}")

        if output_path is None:
            output_path = self.output_dir / f"youtube_{video_id}.{format}"

        # yt-dlp 옵션 구성
        cmd = [
            "yt-dlp",
            "--js-runtimes", "nodejs",
            "--extractor-args", "youtube:player_client=web",
        ]

        if audio_only:
            cmd.extend([
                "-x",  # 오디오 추출
                "--audio-format", format,
                "--audio-quality", "0",  # 최고 품질
            ])

        cmd.extend([
            "-o", str(output_path.with_suffix(".%(ext)s")),
            "--no-playlist",  # 재생목록 무시
            "--no-warnings",
            url
        ])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"다운로드 실패: {e.stderr}")

        # 실제 생성된 파일 찾기
        expected_path = output_path.with_suffix(f".{format}")
        if expected_path.exists():
            return expected_path

        # 확장자가 다를 수 있음
        for ext in [format, "m4a", "webm", "mp3", "wav"]:
            check_path = output_path.with_suffix(f".{ext}")
            if check_path.exists():
                return check_path

        raise FileNotFoundError(f"다운로드된 파일을 찾을 수 없습니다: {output_path}")

    def download_audio_for_transcription(
        self,
        url: str,
        output_dir: Optional[Path] = None,
    ) -> tuple[Path, VideoInfo]:
        """
        전사용 오디오 다운로드 (최적화된 설정)

        Args:
            url: YouTube URL
            output_dir: 출력 디렉토리

        Returns:
            (오디오 파일 경로, 영상 정보)
        """
        # 영상 정보 가져오기
        info = self.get_video_info(url)

        # 출력 경로 설정
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = self.output_dir

        # 파일명 정리 (특수문자 제거)
        safe_title = re.sub(r'[<>:"/\\|?*]', '', info.title)[:50]
        output_path = output_dir / f"{safe_title}.wav"

        # 다운로드
        audio_path = self.download(url, output_path, audio_only=True, format="wav")

        return audio_path, info


def download_youtube(url: str, output_dir: Optional[str] = None) -> tuple[Path, VideoInfo]:
    """
    편의 함수: YouTube 영상을 전사용으로 다운로드

    Args:
        url: YouTube URL
        output_dir: 출력 디렉토리 (미지정시 임시 디렉토리)

    Returns:
        (오디오 파일 경로, 영상 정보)

    Example:
        audio_path, info = download_youtube("https://youtube.com/watch?v=xxx")
        print(f"다운로드 완료: {info.title} ({info.duration}초)")
    """
    downloader = YouTubeDownloader()
    return downloader.download_audio_for_transcription(
        url,
        Path(output_dir) if output_dir else None
    )
