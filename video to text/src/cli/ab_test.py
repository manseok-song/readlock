"""A/B 테스트 스크립트 - Gemini 2.5 Pro vs 3 Flash 비교"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

# src 경로 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.stt.gemini import GeminiSTT, GeminiConfig
from src.audio.extractor import AudioExtractor

app = typer.Typer(invoke_without_command=True)


class ABTestRunner:
    """A/B 테스트 실행기"""

    def __init__(
        self,
        video_path: str,
        ground_truth_speakers: list[str],
        ground_truth_policies: list[str],
    ):
        self.video_path = Path(video_path)
        self.ground_truth_speakers = [s.lower() for s in ground_truth_speakers]
        self.ground_truth_policies = [p.lower() for p in ground_truth_policies]
        self.results = {}

    async def run_model(self, model_name: str, config: GeminiConfig) -> dict:
        """단일 모델로 전사 실행"""
        print(f"\n[{model_name}] 테스트 시작...")

        stt = GeminiSTT(config)
        start_time = time.time()

        try:
            result = await stt.transcribe(
                str(self.video_path),
                language="ko",
                num_speakers=None,  # 자동 감지
            )
            elapsed = time.time() - start_time

            # 결과 분석
            detected_speakers = set()
            detected_policies = set()
            full_text = ""

            for seg in result.segments:
                if seg.speaker:
                    detected_speakers.add(seg.speaker.lower())
                full_text += seg.text + " "

            # 정책명 추출 (간단한 휴리스틱)
            for policy in self.ground_truth_policies:
                if policy.lower() in full_text.lower():
                    detected_policies.add(policy.lower())

            print(f"[{model_name}] 완료: {elapsed:.1f}초, 세그먼트 {len(result.segments)}개")

            return {
                "model": model_name,
                "success": True,
                "elapsed_seconds": elapsed,
                "num_segments": len(result.segments),
                "num_speakers": result.num_speakers,
                "detected_speakers": list(detected_speakers),
                "detected_policies": list(detected_policies),
                "full_text_length": len(full_text),
            }

        except Exception as e:
            print(f"[{model_name}] 실패: {e}")
            return {
                "model": model_name,
                "success": False,
                "error": str(e),
            }

    def calculate_accuracy(self, detected: list, ground_truth: list) -> float:
        """정확도 계산 (recall 기반)"""
        if not ground_truth:
            return 1.0

        detected_lower = [d.lower() for d in detected]
        matches = sum(1 for gt in ground_truth if any(gt in d for d in detected_lower))
        return matches / len(ground_truth)

    async def run_ab_test(self) -> dict:
        """A/B 테스트 실행"""
        print(f"\n{'='*60}")
        print(f"A/B 테스트 시작")
        print(f"{'='*60}")
        print(f"파일: {self.video_path}")
        print(f"정답 화자: {self.ground_truth_speakers}")
        print(f"정답 정책: {self.ground_truth_policies}")

        # Model A: Gemini 2.5 Pro
        config_a = GeminiConfig(
            model="gemini-2.5-pro",
            temperature=0.1,  # 기존 설정
        )

        # Model B: Gemini 3 Flash
        config_b = GeminiConfig(
            model="gemini-3-flash-preview",
            thinking_level="medium",
            media_resolution="low",
            temperature=1.0,  # 권장 설정
        )

        # 순차 실행 (API 부하 방지)
        result_a = await self.run_model("Gemini 2.5 Pro", config_a)
        result_b = await self.run_model("Gemini 3 Flash", config_b)

        # 정확도 계산
        if result_a.get("success"):
            result_a["speaker_accuracy"] = self.calculate_accuracy(
                result_a["detected_speakers"], self.ground_truth_speakers
            )
            result_a["policy_accuracy"] = self.calculate_accuracy(
                result_a["detected_policies"], self.ground_truth_policies
            )

        if result_b.get("success"):
            result_b["speaker_accuracy"] = self.calculate_accuracy(
                result_b["detected_speakers"], self.ground_truth_speakers
            )
            result_b["policy_accuracy"] = self.calculate_accuracy(
                result_b["detected_policies"], self.ground_truth_policies
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "video_path": str(self.video_path),
            "ground_truth": {
                "speakers": self.ground_truth_speakers,
                "policies": self.ground_truth_policies,
            },
            "results": {
                "gemini_2_5_pro": result_a,
                "gemini_3_flash": result_b,
            },
        }


def print_comparison_table(report: dict):
    """비교 결과 테이블 출력 (Simple print version)"""
    result_a = report["results"]["gemini_2_5_pro"]
    result_b = report["results"]["gemini_3_flash"]

    print("\n" + "="*70)
    print("A/B 테스트 결과 비교")
    print("="*70)

    # 성공 여부
    status_a = "성공" if result_a.get("success") else "실패"
    status_b = "성공" if result_b.get("success") else "실패"
    print(f"{'상태':<15} | {'2.5 Pro':<20} | {'3 Flash':<20}")
    print(f"{'-'*15} | {'-'*20} | {'-'*20}")
    print(f"{'결과':<15} | {status_a:<20} | {status_b:<20}")

    if result_a.get("success") and result_b.get("success"):
        # 처리 시간
        time_a = result_a["elapsed_seconds"]
        time_b = result_b["elapsed_seconds"]
        time_winner = "3 Flash 승리" if time_b < time_a else "2.5 Pro 승리"
        print(f"{'처리 시간':<15} | {time_a:.1f}초{'':<14} | {time_b:.1f}초{'':<14} <- {time_winner}")

        # 화자 정확도
        acc_a = result_a.get("speaker_accuracy", 0)
        acc_b = result_b.get("speaker_accuracy", 0)
        acc_winner = "3 Flash 승리" if acc_b > acc_a else ("2.5 Pro 승리" if acc_a > acc_b else "동점")
        print(f"{'화자 정확도':<15} | {acc_a * 100:.1f}%{'':<16} | {acc_b * 100:.1f}%{'':<16} <- {acc_winner}")

        # 정책 정확도
        pol_a = result_a.get("policy_accuracy", 0)
        pol_b = result_b.get("policy_accuracy", 0)
        pol_winner = "3 Flash 승리" if pol_b > pol_a else ("2.5 Pro 승리" if pol_a > pol_b else "동점")
        print(f"{'정책 정확도':<15} | {pol_a * 100:.1f}%{'':<16} | {pol_b * 100:.1f}%{'':<16} <- {pol_winner}")

        # 세그먼트 수
        print(f"{'세그먼트 수':<15} | {result_a['num_segments']:<20} | {result_b['num_segments']:<20}")

        # 감지된 화자
        speakers_a = ", ".join(result_a["detected_speakers"][:5]) or "없음"
        speakers_b = ", ".join(result_b["detected_speakers"][:5]) or "없음"
        print(f"{'감지된 화자':<15} | {speakers_a:<20} | {speakers_b:<20}")

    print("="*70)

    # 최종 권장
    print("\n[최종 분석]")

    if result_a.get("success") and result_b.get("success"):
        speaker_ok = result_b.get("speaker_accuracy", 0) >= 0.95
        policy_ok = result_b.get("policy_accuracy", 0) >= 0.90

        if speaker_ok and policy_ok:
            print(">>> Gemini 3 Flash 도입 권장")
            print("    - 화자 정확도 95% 이상 달성")
            print("    - 정책 정확도 90% 이상 달성")
        elif result_b.get("speaker_accuracy", 0) >= 0.90:
            print(">>> 추가 튜닝 필요")
            print("    - 화자 정확도 90-95% 구간")
            print("    - thinking_level=high 또는 프롬프트 개선 필요")
        else:
            print(">>> Gemini 3 Flash 도입 보류")
            print("    - 화자 정확도 90% 미만")
            print("    - 2.5 Pro 유지 권장")


@app.command()
def run(
    video: str = typer.Argument(..., help="테스트할 영상 파일 경로"),
    speakers: str = typer.Option(
        "사회자,박강산",
        "--speakers", "-s",
        help="정답 화자 목록 (쉼표 구분)",
    ),
    policies: str = typer.Option(
        "",
        "--policies", "-p",
        help="정답 정책명 목록 (쉼표 구분)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="결과 JSON 저장 경로",
    ),
):
    """
    A/B 테스트 실행: Gemini 2.5 Pro vs 3 Flash

    예시:
        python -m src.cli.ab_test run video.mp4 -s "사회자,박강산,김철수" -p "청년희망적금"
    """
    speaker_list = [s.strip() for s in speakers.split(",") if s.strip()]
    policy_list = [p.strip() for p in policies.split(",") if p.strip()]

    runner = ABTestRunner(video, speaker_list, policy_list)
    report = asyncio.run(runner.run_ab_test())

    # 결과 출력
    print_comparison_table(report)

    # JSON 저장
    if output:
        output_path = Path(output)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n결과 저장됨: {output_path}")
    else:
        # 기본 경로에 저장
        default_output = Path("test_output") / f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        default_output.parent.mkdir(exist_ok=True)
        default_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"\n결과 저장됨: {default_output}")


if __name__ == "__main__":
    app()
