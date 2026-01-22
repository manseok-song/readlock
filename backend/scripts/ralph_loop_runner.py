#!/usr/bin/env python3
"""
ReadLock 2.0 Ralph Loop Test Runner
모든 백엔드 서비스의 기능을 테스트하고 실패 시 수정 가이드를 제공합니다.
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

# Windows UTF-8 console encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

try:
    import httpx
except ImportError:
    print("httpx 패키지가 필요합니다: pip install httpx")
    sys.exit(1)


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    response: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class PhaseResult:
    name: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == TestStatus.FAILED)


class RalphLoopRunner:
    """ReadLock API 테스트 러너"""

    BASE_URLS = {
        "auth": "http://localhost:8000",
        "book": "http://localhost:8001",
        "reading": "http://localhost:8002",
        "community": "http://localhost:8003",
        "user": "http://localhost:8004",
        "map": "http://localhost:8005",
        "ai": "http://localhost:8006",
        "notification": "http://localhost:8007",
        "gamification": "http://localhost:8008",
        "subscription": "http://localhost:8009",
    }

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.test_user = {
            "email": f"test_{int(time.time())}@readlock.com",
            "password": "TestPassword123!",
            "nickname": f"테스트유저{int(time.time()) % 10000}"
        }
        self.phase_results: List[PhaseResult] = []

    def log(self, level: str, message: str):
        """로그 출력"""
        colors = {
            "INFO": "\033[94m",
            "PASS": "\033[92m",
            "FAIL": "\033[91m",
            "WARN": "\033[93m",
        }
        reset = "\033[0m"
        color = colors.get(level, "")
        print(f"{color}[{level}]{reset} {message}")

    def api_call(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        auth: bool = False,
    ) -> httpx.Response:
        """API 호출"""
        headers = {"Content-Type": "application/json"}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        if method == "GET":
            return self.client.get(url, headers=headers)
        elif method == "POST":
            return self.client.post(url, json=data, headers=headers)
        elif method == "PUT":
            return self.client.put(url, json=data, headers=headers)
        elif method == "DELETE":
            return self.client.delete(url, headers=headers)
        elif method == "PATCH":
            return self.client.patch(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unknown method: {method}")

    def run_test(
        self,
        name: str,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        auth: bool = False,
        expected_status: List[int] = None,
    ) -> TestResult:
        """단일 테스트 실행"""
        if expected_status is None:
            expected_status = [200]

        start_time = time.time()
        try:
            response = self.api_call(method, url, data, auth)
            duration = time.time() - start_time

            if response.status_code in expected_status:
                self.log("PASS", f"{name} - {response.status_code}")
                return TestResult(
                    name=name,
                    status=TestStatus.PASSED,
                    duration=duration,
                    response=response.json() if response.text else None,
                )
            else:
                self.log("FAIL", f"{name} - Expected {expected_status}, got {response.status_code}")
                return TestResult(
                    name=name,
                    status=TestStatus.FAILED,
                    duration=duration,
                    message=f"Expected {expected_status}, got {response.status_code}",
                    response=response.json() if response.text else None,
                )
        except Exception as e:
            duration = time.time() - start_time
            self.log("FAIL", f"{name} - Error: {str(e)}")
            return TestResult(
                name=name,
                status=TestStatus.ERROR,
                duration=duration,
                error=str(e),
            )

    def test_health_checks(self) -> PhaseResult:
        """Phase 0: 헬스체크"""
        self.log("INFO", "=== Phase 0: 서비스 헬스체크 ===")
        phase = PhaseResult(name="Health Checks")

        for service, base_url in self.BASE_URLS.items():
            result = self.run_test(
                name=f"{service} health",
                method="GET",
                url=f"{base_url}/health",
                expected_status=[200],
            )
            phase.results.append(result)

        return phase

    def test_auth_service(self) -> PhaseResult:
        """Phase 1: Auth Service 테스트"""
        self.log("INFO", "=== Phase 1: Auth Service 테스트 ===")
        phase = PhaseResult(name="Auth Service")
        base_url = self.BASE_URLS["auth"]

        # 회원가입
        result = self.run_test(
            name="회원가입",
            method="POST",
            url=f"{base_url}/v1/auth/register",
            data=self.test_user,
            expected_status=[201, 409],  # 201 created or 409 already exists
        )
        phase.results.append(result)

        if result.status == TestStatus.FAILED:
            # 기존 테스트 계정으로 시도
            self.test_user["email"] = "test@readlock.com"

        # 로그인
        result = self.run_test(
            name="로그인",
            method="POST",
            url=f"{base_url}/v1/auth/login",
            data={
                "email": self.test_user["email"],
                "password": self.test_user["password"],
            },
            expected_status=[200],
        )
        phase.results.append(result)

        if result.status == TestStatus.PASSED and result.response:
            # Handle nested response structure: data.tokens.accessToken
            data = result.response.get("data", {})
            tokens = data.get("tokens", {})
            self.access_token = tokens.get("accessToken")
            self.refresh_token = tokens.get("refreshToken")
            if self.access_token:
                self.log("INFO", f"토큰 획득 성공 (length: {len(self.access_token)})")

        # 사용자 정보 조회
        if self.access_token:
            result = self.run_test(
                name="현재 사용자 정보",
                method="GET",
                url=f"{base_url}/v1/auth/me",
                auth=True,
                expected_status=[200],
            )
            phase.results.append(result)

            # 토큰 갱신
            if self.refresh_token:
                result = self.run_test(
                    name="토큰 갱신",
                    method="POST",
                    url=f"{base_url}/v1/auth/refresh",
                    data={"refreshToken": self.refresh_token},
                    expected_status=[200],
                )
                phase.results.append(result)

        return phase

    def test_gamification_service(self) -> PhaseResult:
        """Phase 9: Gamification Service 테스트"""
        self.log("INFO", "=== Phase 9: Gamification Service 테스트 ===")
        phase = PhaseResult(name="Gamification Service")
        base_url = self.BASE_URLS["gamification"]

        if not self.access_token:
            self.log("WARN", "인증 토큰 없음 - 스킵")
            return phase

        tests = [
            ("전체 뱃지 조회", "GET", f"{base_url}/api/v1/badges/"),
            ("내 뱃지 조회", "GET", f"{base_url}/api/v1/badges/me"),
            ("뱃지 진행도", "GET", f"{base_url}/api/v1/badges/progress"),
            ("내 레벨 조회", "GET", f"{base_url}/api/v1/levels/me"),
            ("레벨 설정 조회", "GET", f"{base_url}/api/v1/levels/config"),
            ("상점 아이템", "GET", f"{base_url}/api/v1/shop/items"),
            ("코인 잔액", "GET", f"{base_url}/api/v1/shop/coins"),
            ("리더보드 (독서시간)", "GET", f"{base_url}/api/v1/leaderboard/reading-time"),
        ]

        for name, method, url in tests:
            result = self.run_test(name, method, url, auth=True)
            phase.results.append(result)

        return phase

    def test_subscription_service(self) -> PhaseResult:
        """Phase 10: Subscription Service 테스트"""
        self.log("INFO", "=== Phase 10: Subscription Service 테스트 ===")
        phase = PhaseResult(name="Subscription Service")
        base_url = self.BASE_URLS["subscription"]

        if not self.access_token:
            self.log("WARN", "인증 토큰 없음 - 스킵")
            return phase

        tests = [
            ("구독 플랜 조회", "GET", f"{base_url}/api/v1/subscriptions/plans"),
            ("내 구독 정보", "GET", f"{base_url}/api/v1/subscriptions/me", [200, 404]),
            ("프리미엄 기능", "GET", f"{base_url}/api/v1/subscriptions/features"),
            ("결제 수단 조회", "GET", f"{base_url}/api/v1/payments/methods"),
            ("결제 내역", "GET", f"{base_url}/api/v1/payments/history"),
            ("코인 패키지", "GET", f"{base_url}/api/v1/payments/coins/packages"),
        ]

        for item in tests:
            name, method, url = item[0], item[1], item[2]
            expected = item[3] if len(item) > 3 else [200]
            result = self.run_test(name, method, url, auth=True, expected_status=expected)
            phase.results.append(result)

        return phase

    def test_other_services(self) -> PhaseResult:
        """기타 서비스 테스트"""
        self.log("INFO", "=== 기타 서비스 테스트 ===")
        phase = PhaseResult(name="Other Services")

        if not self.access_token:
            self.log("WARN", "인증 토큰 없음 - 스킵")
            return phase

        tests = [
            ("Book - 서재", "GET", f"{self.BASE_URLS['book']}/api/v1/books/me/books"),
            ("Reading - 통계", "GET", f"{self.BASE_URLS['reading']}/api/v1/reading/stats"),
            ("Reading - 스트릭", "GET", f"{self.BASE_URLS['reading']}/api/v1/reading/streak"),
            ("Community - 피드", "GET", f"{self.BASE_URLS['community']}/api/v1/feed/"),
            ("User - 프로필", "GET", f"{self.BASE_URLS['user']}/api/v1/profile/", [200, 404]),
            ("Map - 서점검색", "GET", f"{self.BASE_URLS['map']}/api/v1/bookstores/nearby?latitude=37.5665&longitude=126.9780"),
            ("AI - 추천", "GET", f"{self.BASE_URLS['ai']}/api/v1/recommendations/personalized"),
            ("Notification - 알림", "GET", f"{self.BASE_URLS['notification']}/api/v1/notifications/"),
        ]

        for item in tests:
            name, method, url = item[0], item[1], item[2]
            expected = item[3] if len(item) > 3 else [200]
            result = self.run_test(name, method, url, auth=True, expected_status=expected)
            phase.results.append(result)

        return phase

    def print_summary(self):
        """결과 요약 출력"""
        print("\n" + "=" * 50)
        print("          테스트 결과 요약")
        print("=" * 50)

        total_passed = 0
        total_failed = 0

        for phase in self.phase_results:
            print(f"\n[PHASE] {phase.name}")
            print(f"   [PASS] 통과: {phase.passed}")
            print(f"   [FAIL] 실패: {phase.failed}")

            total_passed += phase.passed
            total_failed += phase.failed

            # 실패한 테스트 상세
            for result in phase.results:
                if result.status != TestStatus.PASSED:
                    print(f"      - {result.name}: {result.message or result.error}")

        print("\n" + "-" * 50)
        print(f"전체 통과: {total_passed}")
        print(f"전체 실패: {total_failed}")
        print("-" * 50)

        if total_failed == 0:
            print("\n[SUCCESS] 모든 테스트 통과!")
            return True
        else:
            print("\n[WARNING] 일부 테스트 실패 - 수정이 필요합니다.")
            self.print_fix_suggestions()
            return False

    def print_fix_suggestions(self):
        """수정 가이드 출력"""
        print("\n[GUIDE] 수정 가이드:")
        print("-" * 50)

        for phase in self.phase_results:
            for result in phase.results:
                if result.status == TestStatus.FAILED:
                    print(f"\n[X] {result.name}")
                    print(f"   문제: {result.message}")

                    # 상태 코드별 수정 가이드
                    if "401" in str(result.message):
                        print("   수정: JWT 토큰 검증 로직 확인 (shared/middleware/auth.py)")
                    elif "404" in str(result.message):
                        print("   수정: 라우트 등록 확인 (main.py, api/__init__.py)")
                    elif "422" in str(result.message):
                        print("   수정: 스키마 정의 확인 (schemas/*.py)")
                    elif "500" in str(result.message):
                        print("   수정: 서비스 로직 오류 확인 (services/*.py)")

                elif result.status == TestStatus.ERROR:
                    print(f"\n[!] {result.name}")
                    print(f"   에러: {result.error}")
                    if "Connection" in str(result.error):
                        print("   수정: 서비스가 실행 중인지 확인 (docker-compose ps)")

    def save_report(self, filename: str = "test-report.json"):
        """테스트 결과 저장"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "phases": []
        }

        for phase in self.phase_results:
            phase_data = {
                "name": phase.name,
                "passed": phase.passed,
                "failed": phase.failed,
                "results": [
                    {
                        "name": r.name,
                        "status": r.status.value,
                        "duration": r.duration,
                        "message": r.message,
                        "error": r.error,
                    }
                    for r in phase.results
                ]
            }
            report["phases"].append(phase_data)

        Path("test-reports").mkdir(exist_ok=True)
        with open(f"test-reports/{filename}", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[REPORT] 리포트 저장: test-reports/{filename}")

    def run(self):
        """전체 테스트 실행"""
        print("=" * 50)
        print("   ReadLock 2.0 API 테스트 시작")
        print("=" * 50)
        print()

        # Phase 0: 헬스체크
        self.phase_results.append(self.test_health_checks())
        print()

        # Phase 1: Auth
        self.phase_results.append(self.test_auth_service())
        print()

        # Phase 9: Gamification
        self.phase_results.append(self.test_gamification_service())
        print()

        # Phase 10: Subscription
        self.phase_results.append(self.test_subscription_service())
        print()

        # Other Services
        self.phase_results.append(self.test_other_services())

        # 결과
        success = self.print_summary()
        self.save_report()

        return 0 if success else 1


if __name__ == "__main__":
    runner = RalphLoopRunner()
    sys.exit(runner.run())
