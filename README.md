# ReadLock 2.0

> 폰잠금 기반 몰입형 독서 환경과 커뮤니티 공유, AI 추천을 결합한 소셜 독서 플랫폼

[![Backend Tests](https://img.shields.io/badge/tests-55%20passed-brightgreen)](./backend/test-reports/)
[![Flutter](https://img.shields.io/badge/Flutter-3.16+-blue)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)

## 프로젝트 개요

ReadLock은 스마트폰 잠금 기능을 활용하여 독서에 집중할 수 있는 환경을 제공하고, 독서 기록과 커뮤니티 기능을 통해 독서 습관 형성을 돕는 소셜 독서 플랫폼입니다.

---

## 아키텍처

### 시스템 전체 구조

```mermaid
flowchart TB
    subgraph Client["📱 Client Layer"]
        Flutter["Flutter App<br/>(Android/iOS)"]
        Web["Web App<br/>(Flutter Web)"]
    end

    subgraph Gateway["🚪 API Gateway"]
        ALB["AWS ALB<br/>Load Balancer"]
    end

    subgraph Services["⚙️ Microservices (ECS Fargate)"]
        Auth["Auth Service<br/>:8000"]
        Book["Book Service<br/>:8001"]
        Reading["Reading Service<br/>:8002"]
        Community["Community Service<br/>:8003"]
        User["User Service<br/>:8004"]
        Map["Map Service<br/>:8005"]
        AI["AI Service<br/>:8006"]
        Notification["Notification Service<br/>:8007"]
        Gamification["Gamification Service<br/>:8008"]
        Subscription["Subscription Service<br/>:8009"]
    end

    subgraph Data["💾 Data Layer"]
        PostgreSQL[(PostgreSQL 15<br/>Aurora)]
        Redis[(Redis 7<br/>ElastiCache)]
    end

    subgraph External["🌐 External APIs"]
        Naver["Naver Book API"]
        FCM["Firebase FCM"]
        OAuth["OAuth Providers<br/>(Google, Apple, Kakao)"]
    end

    Flutter --> ALB
    Web --> ALB
    ALB --> Services
    Services --> PostgreSQL
    Services --> Redis
    Book --> Naver
    Notification --> FCM
    Auth --> OAuth

    style Client fill:#e1f5fe
    style Gateway fill:#fff3e0
    style Services fill:#e8f5e9
    style Data fill:#fce4ec
    style External fill:#f3e5f5
```

### 백엔드 마이크로서비스 아키텍처

```mermaid
flowchart LR
    subgraph Core["🔐 Core Services"]
        Auth["Auth Service<br/>━━━━━━━━━━<br/>• JWT 인증<br/>• OAuth 로그인<br/>• 토큰 관리"]
        User["User Service<br/>━━━━━━━━━━<br/>• 프로필 관리<br/>• 팔로우/팔로잉<br/>• 독서 목표"]
    end

    subgraph Domain["📚 Domain Services"]
        Book["Book Service<br/>━━━━━━━━━━<br/>• 책 검색 (Naver)<br/>• 서재 관리<br/>• ISBN 조회"]
        Reading["Reading Service<br/>━━━━━━━━━━<br/>• 독서 세션<br/>• 통계/스트릭<br/>• 일일 기록"]
        Community["Community Service<br/>━━━━━━━━━━<br/>• 인용구/리뷰<br/>• 피드<br/>• 좋아요/댓글"]
        Map["Map Service<br/>━━━━━━━━━━<br/>• 서점 검색<br/>• 체크인<br/>• 즐겨찾기"]
    end

    subgraph Support["🎮 Support Services"]
        AI["AI Service<br/>━━━━━━━━━━<br/>• 맞춤 추천<br/>• 유사 도서<br/>• 인사이트"]
        Notification["Notification<br/>━━━━━━━━━━<br/>• 푸시 알림<br/>• 알림 설정<br/>• FCM 연동"]
        Gamification["Gamification<br/>━━━━━━━━━━<br/>• 레벨/뱃지<br/>• 상점/코인<br/>• 리더보드"]
        Subscription["Subscription<br/>━━━━━━━━━━<br/>• 구독 플랜<br/>• 결제 연동<br/>• 코인 관리"]
    end

    Auth --> User
    User --> Book
    User --> Reading
    User --> Community
    Book --> Reading
    Reading --> Gamification
    Community --> Notification
    AI --> Book
    AI --> Reading

    style Core fill:#ffcdd2
    style Domain fill:#c8e6c9
    style Support fill:#bbdefb
```

### Flutter Clean Architecture

```mermaid
flowchart TB
    subgraph Presentation["🎨 Presentation Layer"]
        direction TB
        Screens["Screens<br/>━━━━━━━━━━<br/>• SplashScreen<br/>• HomeScreen<br/>• LibraryScreen<br/>• ReadingScreen<br/>• ProfileScreen"]
        Widgets["Widgets<br/>━━━━━━━━━━<br/>• BookCard<br/>• ReadingTimer<br/>• StatisticsChart"]
        Providers["Providers (Riverpod)<br/>━━━━━━━━━━<br/>• AuthProvider<br/>• BookProvider<br/>• ReadingProvider"]
    end

    subgraph Domain["🏛️ Domain Layer"]
        direction TB
        Entities["Entities<br/>━━━━━━━━━━<br/>• User<br/>• Book<br/>• ReadingSession<br/>• Quote"]
        UseCases["Use Cases<br/>━━━━━━━━━━<br/>• LoginUseCase<br/>• GetBooksUseCase<br/>• StartReadingUseCase"]
        RepoInterface["Repository Interfaces<br/>━━━━━━━━━━<br/>• IAuthRepository<br/>• IBookRepository<br/>• IReadingRepository"]
    end

    subgraph Data["💿 Data Layer"]
        direction TB
        RepoImpl["Repository Impl<br/>━━━━━━━━━━<br/>• AuthRepositoryImpl<br/>• BookRepositoryImpl"]
        Remote["Remote DataSource<br/>━━━━━━━━━━<br/>• ApiClient (Dio)<br/>• AuthApi<br/>• BookApi"]
        Local["Local DataSource<br/>━━━━━━━━━━<br/>• SecureStorage<br/>• SharedPreferences<br/>• SQLite Cache"]
        Models["Models<br/>━━━━━━━━━━<br/>• UserModel<br/>• BookModel<br/>• (JSON ↔ Entity)"]
    end

    Screens --> Providers
    Providers --> UseCases
    UseCases --> RepoInterface
    RepoInterface -.->|implements| RepoImpl
    RepoImpl --> Remote
    RepoImpl --> Local
    Remote --> Models
    Local --> Models
    Models -.->|maps to| Entities

    style Presentation fill:#e3f2fd
    style Domain fill:#fff8e1
    style Data fill:#fce4ec
```

### 데이터 흐름 (독서 세션 예시)

```mermaid
sequenceDiagram
    autonumber
    participant App as 📱 Flutter App
    participant Lock as 🔒 Phone Lock<br/>(Native)
    participant API as ⚙️ Reading Service
    participant DB as 💾 PostgreSQL
    participant Redis as 📦 Redis
    participant Gamify as 🎮 Gamification

    App->>Lock: 독서 시작 요청
    Lock->>Lock: Foreground Service 시작<br/>DND 모드 활성화
    App->>API: POST /sessions<br/>{book_id, start_page}
    API->>DB: INSERT reading_session
    DB-->>API: session_id
    API-->>App: {session_id, started_at}

    Note over App,Lock: 📖 독서 진행 중...

    App->>Lock: 독서 종료 요청
    Lock->>Lock: DND 해제<br/>Service 종료
    App->>API: PATCH /sessions/{id}<br/>{end_page, duration}
    API->>DB: UPDATE reading_session
    API->>Redis: UPDATE daily_stats
    API->>Gamify: POST /events<br/>{type: reading_complete}
    Gamify->>DB: UPDATE user_level, badges
    Gamify-->>API: {xp_gained, new_badges}
    API-->>App: {session, stats, rewards}
```

### AWS 인프라 구조

```mermaid
flowchart TB
    subgraph VPC["☁️ AWS VPC (10.0.0.0/16)"]
        subgraph Public["Public Subnets"]
            ALB["Application<br/>Load Balancer"]
            NAT["NAT Gateway"]
        end

        subgraph Private["Private Subnets"]
            subgraph ECS["ECS Fargate Cluster"]
                Auth["Auth<br/>Service"]
                Book["Book<br/>Service"]
                Reading["Reading<br/>Service"]
                More["...7 more<br/>services"]
            end

            subgraph Data["Data Tier"]
                Aurora["Aurora<br/>PostgreSQL"]
                ElastiCache["ElastiCache<br/>Redis"]
            end
        end
    end

    subgraph External["External"]
        CloudFront["CloudFront<br/>CDN"]
        S3["S3<br/>Static Assets"]
        Route53["Route 53<br/>DNS"]
        ECR["ECR<br/>Container Registry"]
    end

    subgraph Monitoring["Monitoring"]
        CloudWatch["CloudWatch<br/>Logs & Metrics"]
        XRay["X-Ray<br/>Tracing"]
    end

    Route53 --> CloudFront
    CloudFront --> ALB
    CloudFront --> S3
    ALB --> ECS
    ECS --> Aurora
    ECS --> ElastiCache
    ECS --> NAT
    NAT --> Internet((Internet))
    ECR -.-> ECS
    ECS --> CloudWatch
    ECS --> XRay

    style VPC fill:#fff3e0
    style Public fill:#e3f2fd
    style Private fill:#e8f5e9
    style External fill:#fce4ec
    style Monitoring fill:#f3e5f5
```

### 서비스 통신 매트릭스

```mermaid
flowchart LR
    subgraph Legend["범례"]
        direction LR
        L1["🔵 동기 호출 (REST)"]
        L2["🟢 이벤트 기반 (Redis Pub/Sub)"]
        L3["🟡 캐시 조회"]
    end
```

| From ↓ / To → | Auth | User | Book | Reading | Community | Gamification | Notification |
|---------------|:----:|:----:|:----:|:-------:|:---------:|:------------:|:------------:|
| **Flutter**   | 🔵   | 🔵   | 🔵   | 🔵      | 🔵        | 🔵           | 🔵           |
| **Auth**      | -    | 🔵   | -    | -       | -         | -            | -            |
| **Reading**   | -    | 🔵   | 🔵   | -       | -         | 🟢           | 🟢           |
| **Community** | -    | 🔵   | 🔵   | -       | -         | 🟢           | 🟢           |
| **AI**        | -    | 🟡   | 🟡   | 🟡      | -         | -            | -            |

---

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

# 앱 실행 (모바일)
flutter run

# 웹 빌드
flutter build web --release

# 웹 로컬 서버 실행
cd build/web
python -m http.server 3000
# 브라우저에서 http://localhost:3000 접속
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
