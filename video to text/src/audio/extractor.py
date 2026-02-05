"""오디오 추출 모듈 - FFmpeg를 사용하여 영상에서 오디오 추출"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class ExtractionConfig(BaseModel):
    """오디오 추출 설정"""
    format: str = "wav"
    sample_rate: int = 16000
    channels: int = 1  # 모노 (화자분리 최적화)
    ffmpeg_path: Optional[str] = None


class AudioExtractor:
    """FFmpeg 기반 오디오 추출기"""

    def __init__(self, config: Optional[ExtractionConfig] = None):
        self.config = config or ExtractionConfig()
        self.ffmpeg = self.config.ffmpeg_path or "ffmpeg"

    def _check_ffmpeg(self) -> bool:
        """FFmpeg 설치 확인"""
        try:
            result = subprocess.run(
                [self.ffmpeg, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def extract(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
    ) -> Path:
        """
        영상/오디오 파일에서 오디오 추출

        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로 (없으면 임시 파일 생성)

        Returns:
            추출된 오디오 파일 경로

        Raises:
            FileNotFoundError: 입력 파일이 없을 때
            RuntimeError: FFmpeg 실행 실패 시
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg가 설치되어 있지 않거나 PATH에 없습니다")

        # 출력 경로 결정
        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix="vtt_")
            output_path = Path(temp_dir) / f"audio.{self.config.format}"
        else:
            output_path = Path(output_path)

        # FFmpeg 명령 구성
        cmd = [
            self.ffmpeg,
            "-i", str(input_path),
            "-vn",  # 비디오 제외
            "-acodec", "pcm_s16le" if self.config.format == "wav" else "aac",
            "-ar", str(self.config.sample_rate),
            "-ac", str(self.config.channels),
            "-y",  # 덮어쓰기
            str(output_path)
        ]

        # 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10분 타임아웃
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"오디오 추출 실패: {result.stderr}"
            )

        return output_path

    def extract_segment(
        self,
        input_path: str | Path,
        start_time: float,
        end_time: float,
        output_path: Optional[str | Path] = None,
    ) -> Path:
        """
        특정 구간의 오디오만 추출

        Args:
            input_path: 입력 파일 경로
            start_time: 시작 시간 (초)
            end_time: 종료 시간 (초)
            output_path: 출력 파일 경로

        Returns:
            추출된 오디오 파일 경로
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_path}")

        if output_path is None:
            temp_dir = tempfile.mkdtemp(prefix="vtt_seg_")
            output_path = Path(temp_dir) / f"segment.{self.config.format}"
        else:
            output_path = Path(output_path)

        duration = end_time - start_time

        cmd = [
            self.ffmpeg,
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-vn",
            "-acodec", "pcm_s16le" if self.config.format == "wav" else "aac",
            "-ar", str(self.config.sample_rate),
            "-ac", str(self.config.channels),
            "-y",
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise RuntimeError(f"오디오 구간 추출 실패: {result.stderr}")

        return output_path
