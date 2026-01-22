# ReadLock 2.0

> 폰잠금 기반 몰입형 독서 환경과 커뮤니티 공유, AI 추천을 결합한 소셜 독서 플랫폼

[![Backend Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](./backend/test-reports/)
[![Flutter](https://img.shields.io/badge/Flutter-3.16+-blue)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)

## 프로젝트 개요

ReadLock은 스마트폰 잠금 기능을 활용하여 독서에 집중할 수 있는 환경을 제공하고, 독서 기록과 커뮤니티 기능을 통해 독서 습관 형성을 돕는 소셜 독서 플랫폼입니다.

### 핵심 기능

- **폰잠금 독서 모드**: 독서 중 스마트폰 사용을 제한하여 집중력 향상
- **독서 통계 대시보드**: 일일/주간/월간 독서 시간 및 패턴 분석
- **소셜 독서 커뮤니티**: 인용구 공유, 책 리뷰, 팔로우/팔로잉
- **서점 지도 & 체크인**: 주변 독립서점 찾기 및 방문 기록
- **AI 책 추천**: 사용자의 독서 패턴 기반 맞춤 추천
- **게이미피케이션**: 레벨, 뱃지, 코인 시스템으로 독서 동기 부여

## 기술 스택

### Frontend (Flutter)
```
Flutter 3.16+
├── State Management: Riverpod 2.0
├── Routing: GoRouter
├── HTTP Client: Dio
├── Local Storage: SharedPreferences, FlutterSecureStorage
├── Code Generation: Freezed, JsonSerializable
└── UI Components: Material Design 3
```

### Backend (FastAPI Microservices)
```
FastAPI + Python 3.11
├── Database: PostgreSQL 15 (Async with asyncpg)
├── Cache: Redis 7
├── ORM: SQLAlchemy 2.0 (Async)
├── Authentication: JWT (PyJWT)
├── Migration: Alembic
└── Container: Docker + Docker Compose
```

### Infrastructure
```
AWS (Terraform)
├── Compute: ECS Fargate
├── Database: Aurora PostgreSQL
├── Cache: ElastiCache Redis
├── CDN: CloudFront
└── Monitoring: CloudWatch
```

## 프로젝트 구조

```
readlock/
├── apps/
│   └── mobile/                 # Flutter 모바일 앱
│       ├── lib/
│       │   ├── core/          # 상수, 테마, 유틸리티
│       │   ├── data/          # Repository 구현, 데이터소스
│       │   ├── domain/        # 엔티티, 유스케이스
│       │   ├── presentation/  # UI (Screens, Widgets, Providers)
│       │   └── services/      # 플랫폼 서비스 (폰잠금 등)
│       ├── android/           # Android 네이티브 코드
│       └── ios/               # iOS 네이티브 코드
│
├── backend/
│   ├── services/              # 마이크로서비스
│   │   ├── auth/              # 인증 서비스 (8000)
│   │   ├── book/              # 책 서비스 (8001)
│   │   ├── reading/           # 독서 서비스 (8002)
│   │   ├── community/         # 커뮤니티 서비스 (8003)
│   │   ├── user/              # 사용자 서비스 (8004)
│   │   ├── map/               # 지도 서비스 (8005)
│   │   ├── ai/                # AI 서비스 (8006)
│   │   ├── notification/      # 알림 서비스 (8007)
│   │   ├── gamification/      # 게이미피케이션 서비스 (8008)
│   │   └── subscription/      # 구독 서비스 (8009)
│   ├── shared/                # 공유 라이브러리
│   │   ├── core/              # 설정, DB, Redis, 보안
│   │   └── middleware/        # 인증, Rate Limit
│   ├── alembic/               # DB 마이그레이션
│   └── scripts/               # 테스트 스크립트
│
├── infra/
│   └── terraform/             # AWS 인프라 코드
│       ├── modules/           # VPC, ECS, RDS, ElastiCache
│       └── environments/      # dev, staging, prod
│
└── docs/                      # 문서
    ├── ReadLock_PRD_v2.0.md
    ├── ReadLock_DataModel_API_v2.0.md
    └── ReadLock_Flutter_Code_v2.0.md
```

## 빠른 시작

### 요구 사항

- Docker & Docker Compose
- Flutter SDK 3.16+
- Python 3.11+

### 백엔드 실행

```bash
# 1. 저장소 클론
git clone https://github.com/manseok-song/readlock.git
cd readlock/backend

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에서 필요한 값 설정

# 3. Docker Compose로 실행
docker-compose up -d

# 4. DB 마이그레이션
docker-compose exec auth-service alembic upgrade head

# 5. 테스트 실행
python scripts/comprehensive_test_runner.py
```

### Flutter 앱 실행

```bash
cd apps/mobile

# 의존성 설치
flutter pub get

# 코드 생성
flutter pub run build_runner build --delete-conflicting-outputs

# 앱 실행
flutter run
```

## API 엔드포인트

### 인증 (Auth Service - :8000)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/v1/auth/register` | 회원가입 |
| POST | `/v1/auth/login` | 로그인 |
| POST | `/v1/auth/refresh` | 토큰 갱신 |
| GET | `/v1/auth/me` | 현재 사용자 정보 |

### 책 (Book Service - :8001)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/books/search` | 책 검색 |
| GET | `/api/v1/books/isbn/{isbn}` | ISBN으로 책 조회 |
| GET | `/api/v1/books/me/books` | 내 서재 |
| POST | `/api/v1/books/me/books` | 서재에 책 추가 |

### 독서 (Reading Service - :8002)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/reading/sessions` | 독서 세션 시작 |
| PATCH | `/api/v1/reading/sessions/{id}` | 독서 세션 종료 |
| GET | `/api/v1/reading/stats` | 독서 통계 |
| GET | `/api/v1/reading/streak` | 연속 독서 기록 |

### 커뮤니티 (Community Service - :8003)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/feed/` | 피드 조회 |
| GET | `/api/v1/feed/trending` | 트렌딩 |
| POST | `/api/v1/quotes/` | 인용구 작성 |
| POST | `/api/v1/reviews/` | 리뷰 작성 |

[전체 API 문서 보기](./ReadLock_DataModel_API_v2.0.md)

## 테스트

### 테스트 실행

```bash
cd backend

# 기본 API 테스트
python scripts/ralph_loop_runner.py

# 종합 테스트 (Flutter 연동, E2E, 부하 테스트 포함)
python scripts/comprehensive_test_runner.py
```

### 테스트 결과 (2026-01-22)

| 테스트 카테고리 | 통과 | 실패 |
|----------------|------|------|
| Flutter 앱 연동 | 16 | 0 |
| 추가 엔드포인트 | 17 | 0 |
| E2E 시나리오 | 19 | 0 |
| 부하 테스트 | 3 | 0 |
| **총계** | **55** | **0** |

### 성능 지표

- 동시 요청 10개: 평균 182ms
- 연속 요청 50개: 125.2 req/s, 평균 8ms
- 혼합 부하 20개: 201.6 req/s

## 환경 변수

### 백엔드 (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/readlock

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Naver API (책 검색)
NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-client-secret
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

기여를 환영합니다! [이슈](https://github.com/manseok-song/readlock/issues)를 통해 버그 리포트나 기능 제안을 해주세요.

## 연락처

- GitHub: [@manseok-song](https://github.com/manseok-song)
