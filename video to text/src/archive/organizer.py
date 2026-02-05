"""아카이브 구조화 모듈

전사 결과와 관련 파일들을 체계적인 폴더 구조로 저장합니다.

출력 구조:
📁 election_archive/
└── 📁 {timestamp}_{title}/
    ├── 📹 original.mp4
    ├── 📺 subtitled.mp4
    ├── 📄 transcript.srt
    ├── 📄 transcript.vtt
    ├── 📄 transcript.txt
    ├── 📄 transcript.docx
    ├── 📊 metadata.json
    ├── 📊 quality_report.json
    └── 📁 rag_data/
        ├── knowledge_base.json
        ├── candidates.json
        └── policies.json
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.stt.base import TranscriptionResult
    from src.rag.knowledge_builder import KnowledgeBase
    from src.quality.scorer import QualityScore


@dataclass
class ArchiveResult:
    """아카이브 결과"""
    path: Path                              # 아카이브 폴더 경로
    files: dict[str, Path] = field(default_factory=dict)  # 파일 목록
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def original_video(self) -> Optional[Path]:
        return self.files.get("original_video")

    @property
    def subtitled_video(self) -> Optional[Path]:
        return self.files.get("subtitled_video")

    @property
    def srt_file(self) -> Optional[Path]:
        return self.files.get("srt")

    @property
    def docx_file(self) -> Optional[Path]:
        return self.files.get("docx")

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "files": {k: str(v) for k, v in self.files.items()},
            "created_at": self.created_at,
        }


class ArchiveOrganizer:
    """아카이브 구조화 관리자"""

    def __init__(self, base_dir: str | Path = "election_archive"):
        """
        Args:
            base_dir: 아카이브 기본 디렉토리
        """
        self.base_dir = Path(base_dir)

    def _generate_folder_name(
        self,
        title: Optional[str] = None,
        election_type: Optional[str] = None,
        region: Optional[str] = None
    ) -> str:
        """폴더 이름 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if title:
            # 파일명에 사용할 수 없는 문자 제거
            safe_title = "".join(
                c if c.isalnum() or c in "_ -" else "_"
                for c in title
            )
            return f"{timestamp}_{safe_title}"

        parts = [timestamp]
        if election_type:
            parts.append(election_type)
        if region:
            parts.append(region)

        return "_".join(parts)

    def _rollback_files(self, files: dict[str, Path], archive_path: Path):
        """트랜잭션 롤백: 복사된 파일들 삭제"""
        import logging
        logger = logging.getLogger(__name__)

        for key, file_path in files.items():
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"롤백: {file_path} 삭제됨")
            except Exception as e:
                logger.warning(f"롤백 실패 ({file_path}): {e}")

        # rag_data 디렉토리 삭제 시도
        rag_dir = archive_path / "rag_data"
        if rag_dir.exists():
            try:
                shutil.rmtree(rag_dir)
            except Exception:
                pass

        # 빈 아카이브 폴더 삭제 시도
        try:
            if archive_path.exists() and not any(archive_path.iterdir()):
                archive_path.rmdir()
                logger.info(f"롤백: 빈 폴더 {archive_path} 삭제됨")
        except Exception:
            pass

    def organize(
        self,
        original_video: Optional[str | Path] = None,
        subtitled_video: Optional[str | Path] = None,
        transcription: Optional["TranscriptionResult"] = None,
        srt_file: Optional[str | Path] = None,
        vtt_file: Optional[str | Path] = None,
        txt_file: Optional[str | Path] = None,
        docx_file: Optional[str | Path] = None,
        knowledge_base: Optional["KnowledgeBase"] = None,
        quality_score: Optional["QualityScore"] = None,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
        copy_files: bool = True
    ) -> ArchiveResult:
        """
        아카이브 구조화 (트랜잭션 지원)

        Args:
            original_video: 원본 영상 경로
            subtitled_video: 자막이 삽입된 영상 경로
            transcription: 전사 결과
            srt_file: SRT 자막 파일 경로
            vtt_file: VTT 자막 파일 경로
            txt_file: 텍스트 파일 경로
            docx_file: DOCX 문서 경로
            knowledge_base: 선거 지식 베이스
            quality_score: 품질 점수
            title: 아카이브 제목
            metadata: 추가 메타데이터
            copy_files: True면 파일 복사, False면 이동

        Returns:
            ArchiveResult

        Raises:
            ArchiveError: 아카이브 실패 시 (롤백 수행)
        """
        import logging
        logger = logging.getLogger(__name__)

        # 폴더 이름 생성
        election_type = None
        region = None
        if knowledge_base:
            election_type = knowledge_base.election_type
            region = knowledge_base.region

        folder_name = self._generate_folder_name(title, election_type, region)
        archive_path = self.base_dir / folder_name

        files = {}
        file_operation = shutil.copy2 if copy_files else shutil.move

        try:
            archive_path.mkdir(parents=True, exist_ok=True)

            # 1. 원본 영상 저장
            if original_video:
                original_video = Path(original_video)
                if original_video.exists():
                    dest = archive_path / f"original{original_video.suffix}"
                    file_operation(str(original_video), str(dest))
                    files["original_video"] = dest
                    logger.info(f"원본 영상 저장: {dest}")

            # 2. 자막 영상 저장
            if subtitled_video:
                subtitled_video = Path(subtitled_video)
                if subtitled_video.exists():
                    dest = archive_path / f"subtitled{subtitled_video.suffix}"
                    file_operation(str(subtitled_video), str(dest))
                    files["subtitled_video"] = dest
                    logger.info(f"자막 영상 저장: {dest}")

            # 3. 자막 파일 저장
            for file_path, key, default_name in [
                (srt_file, "srt", "transcript.srt"),
                (vtt_file, "vtt", "transcript.vtt"),
                (txt_file, "txt", "transcript.txt"),
                (docx_file, "docx", "transcript.docx"),
            ]:
                if file_path:
                    file_path = Path(file_path)
                    if file_path.exists():
                        dest = archive_path / default_name
                        file_operation(str(file_path), str(dest))
                        files[key] = dest
                        logger.info(f"{key} 파일 저장: {dest}")

            # 4. 전사 결과 JSON 저장
            if transcription:
                json_path = archive_path / "transcript.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    # Pydantic v2: model_dump(), Pydantic v1: dict()
                    if hasattr(transcription, "model_dump"):
                        data = transcription.model_dump()
                    else:
                        data = transcription.dict()
                    json.dump(data, f, ensure_ascii=False, indent=2)
                files["transcript_json"] = json_path

            # 5. RAG 데이터 저장
            if knowledge_base:
                rag_dir = archive_path / "rag_data"
                rag_dir.mkdir(exist_ok=True)

                # 전체 지식 베이스
                kb_path = rag_dir / "knowledge_base.json"
                with open(kb_path, "w", encoding="utf-8") as f:
                    json.dump(knowledge_base.to_dict(), f, ensure_ascii=False, indent=2)
                files["knowledge_base"] = kb_path

                # 후보자 정보
                if knowledge_base.candidates:
                    candidates_path = rag_dir / "candidates.json"
                    candidates_data = [
                        {
                            "name": c.name,
                            "party": c.party,
                            "number": c.number,
                            "region": c.region,
                            "position": c.position,
                            "aliases": c.aliases,
                        }
                        for c in knowledge_base.candidates
                    ]
                    with open(candidates_path, "w", encoding="utf-8") as f:
                        json.dump(candidates_data, f, ensure_ascii=False, indent=2)
                    files["candidates"] = candidates_path

                # 정책 정보
                if knowledge_base.policies:
                    policies_path = rag_dir / "policies.json"
                    policies_data = [
                        {
                            "name": p.name,
                            "description": p.description,
                            "candidate": p.candidate,
                            "category": p.category,
                            "keywords": p.keywords,
                        }
                        for p in knowledge_base.policies
                    ]
                    with open(policies_path, "w", encoding="utf-8") as f:
                        json.dump(policies_data, f, ensure_ascii=False, indent=2)
                    files["policies"] = policies_path

            # 6. 품질 리포트 저장
            if quality_score:
                quality_path = archive_path / "quality_report.json"
                with open(quality_path, "w", encoding="utf-8") as f:
                    json.dump(quality_score.to_dict(), f, ensure_ascii=False, indent=2)
                files["quality_report"] = quality_path

            # 7. 메타데이터 저장
            full_metadata = {
                "title": title,
                "created_at": datetime.now().isoformat(),
                "files": {k: str(v.name) for k, v in files.items()},
            }
            if metadata:
                full_metadata.update(metadata)
            if knowledge_base:
                full_metadata["election_type"] = knowledge_base.election_type
                full_metadata["region"] = knowledge_base.region
                full_metadata["election_date"] = knowledge_base.election_date
            if quality_score:
                full_metadata["quality_grade"] = quality_score.grade
                full_metadata["quality_score"] = round(quality_score.total, 4)

            metadata_path = archive_path / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(full_metadata, f, ensure_ascii=False, indent=2)
            files["metadata"] = metadata_path

            logger.info(f"아카이브 완료: {archive_path}")
            return ArchiveResult(
                path=archive_path,
                files=files,
            )

        except Exception as e:
            # 트랜잭션 롤백
            logger.error(f"아카이브 실패, 롤백 수행: {e}")
            self._rollback_files(files, archive_path)
            raise RuntimeError(f"아카이브 생성 실패: {e}") from e

    def list_archives(self) -> list[dict]:
        """아카이브 목록 조회"""
        if not self.base_dir.exists():
            return []

        archives = []
        for folder in sorted(self.base_dir.iterdir(), reverse=True):
            if folder.is_dir():
                metadata_path = folder / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    metadata["folder"] = str(folder)
                    archives.append(metadata)
                else:
                    archives.append({
                        "folder": str(folder),
                        "title": folder.name,
                    })

        return archives

    def load_archive(self, folder_path: str | Path) -> Optional[ArchiveResult]:
        """아카이브 로드"""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            return None

        files = {}
        for file in folder_path.iterdir():
            if file.is_file():
                if file.name.startswith("original"):
                    files["original_video"] = file
                elif file.name.startswith("subtitled"):
                    files["subtitled_video"] = file
                elif file.suffix == ".srt":
                    files["srt"] = file
                elif file.suffix == ".vtt":
                    files["vtt"] = file
                elif file.suffix == ".txt":
                    files["txt"] = file
                elif file.suffix == ".docx":
                    files["docx"] = file
                elif file.name == "transcript.json":
                    files["transcript_json"] = file
                elif file.name == "quality_report.json":
                    files["quality_report"] = file
                elif file.name == "metadata.json":
                    files["metadata"] = file

        rag_dir = folder_path / "rag_data"
        if rag_dir.exists():
            if (rag_dir / "knowledge_base.json").exists():
                files["knowledge_base"] = rag_dir / "knowledge_base.json"
            if (rag_dir / "candidates.json").exists():
                files["candidates"] = rag_dir / "candidates.json"
            if (rag_dir / "policies.json").exists():
                files["policies"] = rag_dir / "policies.json"

        # created_at 추출
        created_at = datetime.now().isoformat()
        if "metadata" in files:
            with open(files["metadata"], "r", encoding="utf-8") as f:
                metadata = json.load(f)
                created_at = metadata.get("created_at", created_at)

        return ArchiveResult(
            path=folder_path,
            files=files,
            created_at=created_at,
        )


def create_archive(
    original_video: Optional[str | Path] = None,
    base_dir: str = "election_archive",
    **kwargs
) -> ArchiveResult:
    """아카이브 생성 헬퍼 함수"""
    organizer = ArchiveOrganizer(base_dir)
    return organizer.organize(original_video=original_video, **kwargs)
