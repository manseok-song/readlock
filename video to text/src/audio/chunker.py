"""오디오 청크 분할 모듈 - 침묵 감지 기반 정교한 분할"""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from pydantic import BaseModel


class ChunkConfig(BaseModel):
    """청크 분할 설정"""
    # 목표 청크 길이 (초) - 기본 10분
    target_chunk_duration: int = 600
    # 최대 청크 길이 (초) - 기본 15분
    max_chunk_duration: int = 900
    # 최소 청크 길이 (초) - 기본 1분
    min_chunk_duration: int = 60
    # 침묵 감지 임계값 (dB) - -35dB로 더 확실한 침묵만 감지
    silence_threshold_db: int = -35
    # 침묵 최소 지속 시간 (초) - 1초 이상의 확실한 끊김
    min_silence_duration: float = 1.0
    # 청크 간 중복 (초) - 문맥 유지용
    overlap_duration: float = 3.0
    # 오디오 포맷
    format: str = "wav"
    sample_rate: int = 16000


@dataclass
class AudioChunk:
    """분할된 오디오 청크 정보"""
    path: Path
    start_time: float       # 원본 기준 시작 시간 - 중복 제외 (초)
    end_time: float         # 원본 기준 종료 시간 (초)
    duration: float         # 청크 길이 (초)
    index: int              # 청크 인덱스
    actual_start: float     # 청크 파일의 실제 시작 위치 - overlap 포함 (초)


class AudioChunker:
    """침묵 감지 기반 오디오 분할기"""

    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        self.ffmpeg = "ffmpeg"

    def get_audio_duration(self, audio_path: Path) -> float:
        """오디오 파일 길이 조회 (초)"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"오디오 길이 조회 실패: {result.stderr}")
        return float(result.stdout.strip())

    def detect_silence_points(self, audio_path: Path) -> List[Tuple[float, float]]:
        """
        FFmpeg silencedetect로 침묵 구간 감지

        Returns:
            List of (start, end) tuples for silence periods
        """
        cmd = [
            self.ffmpeg,
            "-i", str(audio_path),
            "-af", f"silencedetect=noise={self.config.silence_threshold_db}dB:d={self.config.min_silence_duration}",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10분
        )

        # stderr에서 침묵 구간 파싱
        silence_points = []
        current_start = None

        for line in result.stderr.split('\n'):
            if 'silence_start:' in line:
                try:
                    current_start = float(line.split('silence_start:')[1].strip().split()[0])
                except (ValueError, IndexError):
                    continue
            elif 'silence_end:' in line and current_start is not None:
                try:
                    end_part = line.split('silence_end:')[1].strip().split()[0]
                    end = float(end_part)
                    silence_points.append((current_start, end))
                    current_start = None
                except (ValueError, IndexError):
                    continue

        return silence_points

    def find_optimal_split_points(
        self,
        total_duration: float,
        silence_points: List[Tuple[float, float]]
    ) -> List[float]:
        """
        침묵 구간 중 최적의 분할 지점 찾기

        Args:
            total_duration: 전체 오디오 길이 (초)
            silence_points: 침묵 구간 리스트

        Returns:
            분할 지점 리스트 (초)
        """
        if total_duration <= self.config.max_chunk_duration:
            return []  # 분할 불필요

        split_points = []
        current_pos = 0.0

        while current_pos < total_duration:
            # 목표 분할 지점
            target_pos = current_pos + self.config.target_chunk_duration

            if target_pos >= total_duration:
                break

            # 목표 지점 근처에서 침묵 구간 찾기
            # 범위: target - 2분 ~ target + 3분
            search_start = max(current_pos + self.config.min_chunk_duration,
                               target_pos - 120)
            search_end = min(total_duration,
                             target_pos + 180,
                             current_pos + self.config.max_chunk_duration)

            # 범위 내 침묵 구간 필터링
            candidates = []
            for start, end in silence_points:
                silence_duration = end - start
                # 침묵 중간점을 분할 지점으로
                midpoint = (start + end) / 2
                if search_start <= midpoint <= search_end:
                    # 목표와의 거리 계산 (더 긴 침묵일수록 보너스)
                    distance = abs(midpoint - target_pos)
                    # 긴 침묵은 거리 패널티 감소 (1초당 30초 보너스)
                    adjusted_distance = distance - (silence_duration * 30)
                    candidates.append((midpoint, adjusted_distance, silence_duration))

            if candidates:
                # 조정된 거리가 가장 작은 (= 긴 침묵 & 목표 근처) 지점 선택
                best_point = min(candidates, key=lambda x: x[1])[0]
                best_silence = max(candidates, key=lambda x: x[2])[2]
                print(f"[Chunker] 분할 지점 {best_point:.1f}초 (침묵 {best_silence:.1f}초)")
                split_points.append(best_point)
                current_pos = best_point
            else:
                # 침묵 구간이 없으면 강제 분할 (목표 지점)
                print(f"[Chunker] ⚠️ 침묵 없음 - 강제 분할 {target_pos:.1f}초")
                split_points.append(target_pos)
                current_pos = target_pos

        return split_points

    def split_audio(
        self,
        audio_path: str | Path,
        output_dir: Optional[str | Path] = None
    ) -> List[AudioChunk]:
        """
        오디오를 청크로 분할

        Args:
            audio_path: 입력 오디오 파일 경로
            output_dir: 출력 디렉토리 (없으면 임시 디렉토리)

        Returns:
            AudioChunk 리스트
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="vtt_chunks_"))
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # 전체 길이 확인
        total_duration = self.get_audio_duration(audio_path)
        print(f"[Chunker] 전체 오디오 길이: {total_duration:.1f}초 ({total_duration/60:.1f}분)")

        # 분할 필요 여부 확인
        if total_duration <= self.config.max_chunk_duration:
            print(f"[Chunker] 분할 불필요 (최대 {self.config.max_chunk_duration}초 이하)")
            # 원본 파일 복사 또는 링크
            chunk_path = output_dir / f"chunk_000.{self.config.format}"
            self._extract_segment(audio_path, 0, total_duration, chunk_path)
            return [AudioChunk(
                path=chunk_path,
                start_time=0,
                end_time=total_duration,
                duration=total_duration,
                index=0,
                actual_start=0  # 단일 청크는 overlap 없음
            )]

        # 침묵 구간 감지
        print(f"[Chunker] 침묵 구간 감지 중...")
        silence_points = self.detect_silence_points(audio_path)
        print(f"[Chunker] {len(silence_points)}개 침묵 구간 감지됨")

        # 최적 분할 지점 계산
        split_points = self.find_optimal_split_points(total_duration, silence_points)
        print(f"[Chunker] {len(split_points)}개 분할 지점 결정")

        # 청크 생성
        chunks = []
        current_start = 0.0

        for i, split_point in enumerate(split_points + [total_duration]):
            # 중복 구간 적용
            chunk_start = max(0, current_start - self.config.overlap_duration) if i > 0 else 0
            chunk_end = split_point

            chunk_duration = chunk_end - chunk_start
            chunk_path = output_dir / f"chunk_{i:03d}.{self.config.format}"

            print(f"[Chunker] 청크 {i}: {chunk_start:.1f}s ~ {chunk_end:.1f}s ({chunk_duration:.1f}초)")

            # 오디오 추출
            self._extract_segment(audio_path, chunk_start, chunk_end, chunk_path)

            chunks.append(AudioChunk(
                path=chunk_path,
                start_time=current_start,  # 원본 기준 시작 (중복 제외)
                end_time=split_point,       # 원본 기준 종료
                duration=chunk_duration,
                index=i,
                actual_start=chunk_start    # 청크 파일의 실제 시작 위치 (overlap 포함)
            ))

            current_start = split_point

        print(f"[Chunker] 총 {len(chunks)}개 청크 생성 완료")
        return chunks

    def _extract_segment(
        self,
        input_path: Path,
        start_time: float,
        end_time: float,
        output_path: Path
    ) -> None:
        """FFmpeg로 오디오 구간 추출"""
        duration = end_time - start_time

        cmd = [
            self.ffmpeg,
            "-i", str(input_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(self.config.sample_rate),
            "-ac", "1",
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
            raise RuntimeError(f"오디오 추출 실패: {result.stderr}")


def merge_transcriptions(
    chunk_results: List[dict],
    chunks: List[AudioChunk],
    overlap_duration: float = 2.0
) -> dict:
    """
    청크별 전사 결과를 병합 (개선된 중복 제거 로직)

    Args:
        chunk_results: 각 청크의 전사 결과 (segments 포함)
        chunks: AudioChunk 리스트
        overlap_duration: 청크 간 중복 시간

    Returns:
        병합된 전사 결과
    """
    merged_segments = []
    all_speakers = set()

    for chunk, result in zip(chunks, chunk_results):
        if not result or "segments" not in result:
            continue

        # 청크 파일의 실제 시작 위치 (overlap 포함)를 오프셋으로 사용
        # Gemini가 반환하는 타임스탬프는 청크 파일 기준 (0부터 시작)
        time_offset = chunk.actual_start

        # 청크 내 세그먼트 순번 카운터
        seg_counter = 0

        for seg in result["segments"]:
            # 원본 기준 타임스탬프 계산
            seg_start_in_original = seg["start"] + time_offset
            seg_end_in_original = seg["end"] + time_offset

            # 중복 구간 필터링 (첫 청크 제외) - 더 넉넉한 범위 적용
            if chunk.index > 0:
                # 세그먼트 끝이 청크 시작보다 이전이면 완전히 이전 청크에서 처리됨
                # 또는 세그먼트 시작이 청크 시작보다 1초 이상 이전이면 스킵
                if seg_end_in_original <= chunk.start_time:
                    continue
                if seg_start_in_original < chunk.start_time - 1.0:
                    continue

            # 세그먼트 ID 생성: c{청크번호}_s{세그먼트순번} (예: c0_s000, c0_s001, c1_s000)
            segment_id = f"c{chunk.index}_s{seg_counter:03d}"

            # 타임스탬프 보정
            adjusted_seg = {
                "segment_id": segment_id,  # 순서 보장용 고유 ID
                "start": round(seg_start_in_original, 3),  # 소수점 정리
                "end": round(seg_end_in_original, 3),
                "text": seg["text"].strip(),
                "speaker": seg.get("speaker", "화자1"),
                "chunk_index": chunk.index,  # 청크 번호
                "seg_index": seg_counter  # 청크 내 세그먼트 순번
            }

            merged_segments.append(adjusted_seg)
            seg_counter += 1

            if adjusted_seg["speaker"]:
                all_speakers.add(adjusted_seg["speaker"])

    # 세그먼트 ID 기반 정렬 (청크 순서 → 청크 내 순번 → 타임스탬프 오차 무관)
    merged_segments.sort(key=lambda x: (x.get("chunk_index", 0), x.get("seg_index", 0)))

    # 중복 세그먼트 제거 (강화된 로직)
    deduplicated = []
    for seg in merged_segments:
        is_duplicate = False

        # 비교 범위 확대: 최근 20개 (overlap 구간에서 더 많은 세그먼트 비교)
        for existing in deduplicated[-20:]:
            # 시간 근접 체크 (5초 이내로 확대)
            time_diff = abs(seg["start"] - existing["start"])
            if time_diff > 5.0:
                continue

            text1 = seg["text"]
            text2 = existing["text"]

            # 1. 완전 일치
            if text1 == text2:
                is_duplicate = True
                break

            # 2. 포함 관계 (한쪽이 다른 쪽을 포함)
            if text1 in text2 or text2 in text1:
                is_duplicate = True
                break

            # 3. 유사도 체크 (한국어 특성 고려 - 50% 이상 접두사 일치)
            min_len = min(len(text1), len(text2))
            if min_len > 5:  # 5글자 이상일 때만
                common_prefix = 0
                for c1, c2 in zip(text1, text2):
                    if c1 == c2:
                        common_prefix += 1
                    else:
                        break
                # 50% 이상 접두사 일치하면 중복으로 간주
                if common_prefix >= min_len * 0.5:
                    is_duplicate = True
                    break

            # 4. 끝 부분 유사도 체크 (말의 끝이 겹치는 경우)
            if min_len > 10:
                common_suffix = 0
                for c1, c2 in zip(reversed(text1), reversed(text2)):
                    if c1 == c2:
                        common_suffix += 1
                    else:
                        break
                if common_suffix >= min_len * 0.5:
                    is_duplicate = True
                    break

        if not is_duplicate:
            # 디버깅용 필드 제거 (segment_id는 유지 - 순서 추적용)
            internal_fields = {"chunk_index", "seg_index"}
            final_seg = {k: v for k, v in seg.items() if k not in internal_fields}
            deduplicated.append(final_seg)

    removed_count = len(merged_segments) - len(deduplicated)
    if removed_count > 0:
        print(f"[Chunker] 중복 세그먼트 {removed_count}개 제거됨")

    return {
        "segments": deduplicated,
        "num_speakers": len(all_speakers),
        "language": chunk_results[0].get("language", "ko") if chunk_results else "ko"
    }
