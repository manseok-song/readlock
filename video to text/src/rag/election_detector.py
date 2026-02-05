"""선거 정보 자동 감지 모듈

영상 초반부를 분석하여 선거 유형, 지역, 후보자 정보를 자동 추출합니다.
Gemini를 사용하여 사회자 인삿말 이후 소개 부분에서 정보를 추출합니다.
"""

import asyncio
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


@dataclass
class DetectedElectionInfo:
    """감지된 선거 정보"""
    election_type: str = ""  # 지방선거, 대통령선거, 총선 등
    position: str = ""  # 시장, 도지사, 구청장, 국회의원 등
    region: str = ""  # 서울시, 경기도, 강남구 등
    election_date: str = ""  # 감지된 선거일
    candidates: List[str] = field(default_factory=list)  # 후보자 이름
    parties: List[str] = field(default_factory=list)  # 정당명
    broadcaster: str = ""  # 방송사
    program_title: str = ""  # 프로그램 제목
    confidence: float = 0.0  # 신뢰도 (0~1)
    raw_intro: str = ""  # 원본 소개 텍스트
    detected_at_seconds: float = 0.0  # 정보가 감지된 시간 위치

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "election_type": self.election_type,
            "position": self.position,
            "region": self.region,
            "election_date": self.election_date,
            "candidates": self.candidates,
            "parties": self.parties,
            "broadcaster": self.broadcaster,
            "program_title": self.program_title,
            "confidence": self.confidence,
            "raw_intro": self.raw_intro,
            "detected_at_seconds": self.detected_at_seconds,
        }


class ElectionDetector:
    """영상에서 선거 정보 자동 감지"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 가져옴)
        """
        if not GENAI_AVAILABLE:
            raise RuntimeError("google-genai 패키지가 필요합니다")

        import os
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 필요합니다")

        self.client = genai.Client(api_key=self.api_key)

    async def detect_from_video(
        self,
        video_path: str | Path,
        start_seconds: float = 60,
        duration_seconds: float = 180
    ) -> DetectedElectionInfo:
        """
        영상에서 선거 정보 자동 감지

        "선거방송 준비중" 화면이 길 수 있으므로 기본 1분부터 분석.
        3분 구간을 분석하여 사회자 소개 부분을 찾습니다.

        Args:
            video_path: 영상 파일 경로
            start_seconds: 분석 시작 위치 (초) - 기본 60초 (준비화면 스킵)
            duration_seconds: 분석할 길이 (초) - 기본 180초 (3분)

        Returns:
            감지된 선거 정보
        """
        video_path = Path(video_path)

        # 1. 영상 초반부 추출
        clip_path = await self._extract_clip(
            video_path, start_seconds, duration_seconds
        )

        try:
            # 2. Gemini로 선거 정보 추출
            info = await self._analyze_with_gemini(clip_path, start_seconds)
            return info
        finally:
            # 임시 클립 삭제
            if clip_path and clip_path.exists():
                try:
                    clip_path.unlink()
                except Exception:
                    pass

    async def _extract_clip(
        self,
        video_path: Path,
        start_seconds: float,
        duration_seconds: float
    ) -> Path:
        """영상에서 특정 구간 추출 (FFmpeg 사용)"""

        # 임시 파일 생성
        tmp_file = tempfile.NamedTemporaryFile(
            suffix=".mp4", delete=False
        )
        tmp_path = Path(tmp_file.name)
        tmp_file.close()

        # FFmpeg 명령 구성 (리스트로 전달 - 쉘 인젝션 방지)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_seconds),
            "-i", str(video_path),
            "-t", str(duration_seconds),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-preset", "ultrafast",
            str(tmp_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"[ElectionDetector] FFmpeg 경고: {stderr.decode()[:500]}")

        return tmp_path

    async def _analyze_with_gemini(
        self,
        video_path: Path,
        start_offset: float = 0
    ) -> DetectedElectionInfo:
        """Gemini로 영상 분석하여 선거 정보 추출"""

        print(f"[ElectionDetector] 영상 분석 중: {video_path}")

        # 영상 파일 업로드
        uploaded_file = self.client.files.upload(file=video_path)

        # 파일 처리 대기
        max_wait = 60
        waited = 0
        while uploaded_file.state == "PROCESSING" and waited < max_wait:
            await asyncio.sleep(2)
            waited += 2
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state != "ACTIVE":
            raise RuntimeError(f"파일 업로드 실패: {uploaded_file.state}")

        # 분석 프롬프트
        prompt = """이 영상은 선거 토론회 영상의 초반부입니다.

"선거방송 준비중" 같은 대기 화면을 건너뛰고,
사회자가 "안녕하십니까" 등 인삿말 후 토론회를 소개하는 부분을 찾아주세요.

다음 정보를 JSON 형식으로 추출해주세요:

{
  "election_type": "선거 유형 (지방선거/대통령선거/총선/재보궐선거 중 하나)",
  "position": "선출직 (시장/도지사/구청장/국회의원 등)",
  "region": "지역 (서울시/경기도/강남구 등 구체적으로)",
  "election_date": "선거일 (YYYY-MM-DD 형식, 언급된 경우만)",
  "candidates": ["후보자1 이름", "후보자2 이름"],
  "parties": ["정당1", "정당2"],
  "broadcaster": "방송사명",
  "program_title": "프로그램 제목",
  "confidence": 0.0~1.0 사이 신뢰도,
  "raw_intro": "사회자가 말한 소개 부분 원문",
  "intro_found_at_seconds": 소개 부분이 나온 대략적 시간(초)
}

화면에 표시되는 자막, 로고, 기호번호도 참고하세요.
정보가 없으면 빈 문자열이나 빈 배열로 남겨두세요.

JSON만 출력하세요:"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=uploaded_file.uri,
                                mime_type="video/mp4"
                            ),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ]
            )

            # JSON 파싱
            result_text = response.text.strip()

            # JSON 블록 추출
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                parts = result_text.split("```")
                if len(parts) >= 2:
                    result_text = parts[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]

            result_text = result_text.strip()
            data = json.loads(result_text)

            # 실제 시간 위치 계산
            intro_seconds = data.get("intro_found_at_seconds", 0)
            actual_seconds = start_offset + intro_seconds

            return DetectedElectionInfo(
                election_type=data.get("election_type", ""),
                position=data.get("position", ""),
                region=data.get("region", ""),
                election_date=data.get("election_date", ""),
                candidates=data.get("candidates", []),
                parties=data.get("parties", []),
                broadcaster=data.get("broadcaster", ""),
                program_title=data.get("program_title", ""),
                confidence=float(data.get("confidence", 0.5)),
                raw_intro=data.get("raw_intro", ""),
                detected_at_seconds=actual_seconds
            )

        except json.JSONDecodeError as e:
            print(f"[ElectionDetector] JSON 파싱 실패: {e}")
            print(f"[ElectionDetector] 원본 응답: {result_text[:500]}")
            return DetectedElectionInfo(confidence=0.0)

        except Exception as e:
            print(f"[ElectionDetector] Gemini 분석 실패: {e}")
            return DetectedElectionInfo(confidence=0.0)

        finally:
            # 업로드된 파일 삭제
            try:
                self.client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

    async def detect_with_retry(
        self,
        video_path: str | Path,
        max_attempts: int = 3
    ) -> DetectedElectionInfo:
        """
        여러 시간대에서 시도하여 선거 정보 감지

        "준비중" 화면이 길 수 있으므로 여러 위치에서 시도합니다.

        Args:
            video_path: 영상 파일 경로
            max_attempts: 최대 시도 횟수

        Returns:
            감지된 선거 정보
        """
        # 시도할 시간대 (준비화면이 길 수 있음)
        time_ranges = [
            (60, 180),   # 1분~4분
            (180, 180),  # 3분~6분
            (300, 180),  # 5분~8분
        ]

        best_result = DetectedElectionInfo(confidence=0.0)

        for i, (start, duration) in enumerate(time_ranges[:max_attempts]):
            print(f"[ElectionDetector] 시도 {i+1}/{max_attempts}: {start}초~{start+duration}초 구간")

            try:
                result = await self.detect_from_video(
                    video_path,
                    start_seconds=start,
                    duration_seconds=duration
                )

                # 신뢰도가 높으면 바로 반환
                if result.confidence >= 0.8:
                    print(f"[ElectionDetector] 고신뢰도 결과 발견: {result.confidence}")
                    return result

                # 더 좋은 결과면 저장
                if result.confidence > best_result.confidence:
                    best_result = result

            except Exception as e:
                print(f"[ElectionDetector] 시도 {i+1} 실패: {e}")
                continue

        return best_result


async def detect_election_info(
    file_path: str | Path,
    start_seconds: float = 60,
    duration_seconds: float = 180,
    auto_retry: bool = True
) -> DetectedElectionInfo:
    """
    선거 정보 자동 감지 헬퍼 함수

    Args:
        file_path: 영상/오디오 파일 경로
        start_seconds: 분석 시작 위치 (기본 60초 - 준비화면 스킵)
        duration_seconds: 분석 길이 (기본 180초)
        auto_retry: 실패 시 자동 재시도 (다른 시간대)

    Returns:
        감지된 선거 정보
    """
    detector = ElectionDetector()

    if auto_retry:
        return await detector.detect_with_retry(file_path)
    else:
        return await detector.detect_from_video(
            file_path, start_seconds, duration_seconds
        )
