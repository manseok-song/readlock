"""오디오 분석 모듈 - 메타데이터 추출 및 분석"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class AudioMetadata(BaseModel):
    """오디오 메타데이터"""
    duration: float  # 길이 (초)
    sample_rate: int  # 샘플레이트 (Hz)
    channels: int  # 채널 수
    bit_rate: Optional[int] = None  # 비트레이트 (bps)
    codec: Optional[str] = None  # 코덱명
    format: Optional[str] = None  # 컨테이너 포맷
    file_size: int = 0  # 파일 크기 (bytes)

    @property
    def duration_formatted(self) -> str:
        """포맷된 길이 (HH:MM:SS)"""
        hours, remainder = divmod(int(self.duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def is_stereo(self) -> bool:
        """스테레오 여부"""
        return self.channels >= 2

    @property
    def is_multichannel(self) -> bool:
        """멀티채널 여부 (3채널 이상)"""
        return self.channels > 2


class AudioAnalyzer:
    """FFprobe 기반 오디오 분석기"""

    def __init__(self, ffprobe_path: Optional[str] = None):
        self.ffprobe = ffprobe_path or "ffprobe"

    def _check_ffprobe(self) -> bool:
        """FFprobe 설치 확인"""
        try:
            result = subprocess.run(
                [self.ffprobe, "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def analyze(self, file_path: str | Path) -> AudioMetadata:
        """
        오디오/비디오 파일 분석

        Args:
            file_path: 분석할 파일 경로

        Returns:
            AudioMetadata 객체

        Raises:
            FileNotFoundError: 파일이 없을 때
            RuntimeError: FFprobe 실행 실패 시
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        if not self._check_ffprobe():
            raise RuntimeError("FFprobe가 설치되어 있지 않거나 PATH에 없습니다")

        # FFprobe로 JSON 형식 메타데이터 추출
        cmd = [
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-select_streams", "a:0",  # 첫 번째 오디오 스트림
            str(file_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(f"파일 분석 실패: {result.stderr}")

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"FFprobe 출력 파싱 실패: {e}")

        # 오디오 스트림 정보 추출
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                audio_stream = stream
                break

        if audio_stream is None:
            raise RuntimeError("오디오 스트림을 찾을 수 없습니다")

        format_info = data.get("format", {})

        return AudioMetadata(
            duration=float(audio_stream.get("duration", format_info.get("duration", 0))),
            sample_rate=int(audio_stream.get("sample_rate", 0)),
            channels=int(audio_stream.get("channels", 1)),
            bit_rate=int(audio_stream.get("bit_rate", 0)) if audio_stream.get("bit_rate") else None,
            codec=audio_stream.get("codec_name"),
            format=format_info.get("format_name"),
            file_size=int(format_info.get("size", 0))
        )

    def estimate_processing_time(self, metadata: AudioMetadata) -> dict:
        """
        처리 예상 시간 및 비용 추정

        Args:
            metadata: 오디오 메타데이터

        Returns:
            추정 정보 딕셔너리
        """
        duration_minutes = metadata.duration / 60

        return {
            "duration_minutes": round(duration_minutes, 2),
            "estimated_cost_gemini_flash": round(duration_minutes * 0.0025, 4),  # $0.15/hour
            "estimated_cost_gemini_pro": round(duration_minutes * 0.025, 4),  # $1.50/hour
            "channel_type": "multichannel" if metadata.is_multichannel
                          else "stereo" if metadata.is_stereo
                          else "mono",
            "recommended_engine": "gemini" if duration_minutes < 60 else "whisperx_local"
        }

    def get_audio_quality_score(self, metadata: AudioMetadata) -> dict:
        """
        오디오 품질 점수 계산

        Args:
            metadata: 오디오 메타데이터

        Returns:
            품질 점수 및 권장사항
        """
        score = 100
        issues = []
        recommendations = []

        # 샘플레이트 체크
        if metadata.sample_rate < 16000:
            score -= 20
            issues.append("샘플레이트가 낮습니다 (16kHz 미만)")
            recommendations.append("가능하면 16kHz 이상의 오디오 사용 권장")
        elif metadata.sample_rate < 44100:
            score -= 5
            issues.append("샘플레이트가 표준 이하입니다")

        # 비트레이트 체크
        if metadata.bit_rate and metadata.bit_rate < 128000:
            score -= 15
            issues.append("비트레이트가 낮습니다 (128kbps 미만)")
            recommendations.append("높은 비트레이트의 원본 사용 권장")

        # 채널 체크
        if metadata.channels > 2:
            issues.append(f"멀티채널 오디오 ({metadata.channels}채널)")
            recommendations.append("화자분리 전 모노 또는 스테레오로 변환 권장")

        return {
            "score": max(0, score),
            "quality_level": "high" if score >= 80 else "medium" if score >= 50 else "low",
            "issues": issues,
            "recommendations": recommendations
        }
