# ReadLock 2.0 - Flutter 프로젝트 구조 및 핵심 코드

**Version:** 2.0  
**Framework:** Flutter 3.16+ / Dart 3.2+

---

## 1. 프로젝트 구조

```
readlock/
├── android/                          # Android 네이티브 코드
│   └── app/src/main/
│       ├── kotlin/.../
│       │   ├── MainActivity.kt
│       │   └── ReadingLockService.kt # 폰잠금 Foreground Service
│       └── AndroidManifest.xml
│
├── ios/                              # iOS 네이티브 코드
│   └── Runner/
│       ├── AppDelegate.swift
│       └── Info.plist
│
├── web/                              # Web 설정
│   └── index.html
│
├── lib/
│   ├── main.dart                     # 앱 진입점
│   ├── app.dart                      # MaterialApp 설정
│   │
│   ├── core/                         # 공통 유틸리티
│   │   ├── constants/
│   │   │   ├── app_constants.dart
│   │   │   ├── api_endpoints.dart
│   │   │   └── storage_keys.dart
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   ├── app_colors.dart
│   │   │   └── app_typography.dart
│   │   ├── utils/
│   │   │   ├── extensions.dart
│   │   │   ├── validators.dart
│   │   │   └── formatters.dart
│   │   └── errors/
│   │       ├── failures.dart
│   │       └── exceptions.dart
│   │
│   ├── data/                         # 데이터 레이어
│   │   ├── datasources/
│   │   │   ├── remote/
│   │   │   │   ├── api_client.dart
│   │   │   │   ├── auth_api.dart
│   │   │   │   ├── book_api.dart
│   │   │   │   ├── reading_api.dart
│   │   │   │   └── community_api.dart
│   │   │   └── local/
│   │   │       ├── hive_storage.dart
│   │   │       └── secure_storage.dart
│   │   ├── repositories/
│   │   │   ├── auth_repository_impl.dart
│   │   │   ├── book_repository_impl.dart
│   │   │   └── reading_repository_impl.dart
│   │   └── models/
│   │       ├── request/
│   │       └── response/
│   │
│   ├── domain/                       # 도메인 레이어
│   │   ├── entities/
│   │   │   ├── user.dart
│   │   │   ├── book.dart
│   │   │   ├── quote.dart
│   │   │   ├── review.dart
│   │   │   └── reading_session.dart
│   │   ├── repositories/
│   │   │   ├── auth_repository.dart
│   │   │   ├── book_repository.dart
│   │   │   └── reading_repository.dart
│   │   └── usecases/
│   │       ├── auth/
│   │       ├── book/
│   │       └── reading/
│   │
│   ├── presentation/                 # UI 레이어
│   │   ├── providers/                # Riverpod providers
│   │   │   ├── auth_provider.dart
│   │   │   ├── book_provider.dart
│   │   │   ├── reading_provider.dart
│   │   │   └── theme_provider.dart
│   │   ├── screens/
│   │   │   ├── splash/
│   │   │   ├── onboarding/
│   │   │   ├── auth/
│   │   │   ├── home/
│   │   │   ├── library/
│   │   │   ├── reading/
│   │   │   ├── discover/
│   │   │   ├── avatar/
│   │   │   └── profile/
│   │   ├── widgets/
│   │   │   ├── common/
│   │   │   ├── book/
│   │   │   ├── reading/
│   │   │   └── community/
│   │   └── routes/
│   │       └── app_router.dart
│   │
│   └── services/                     # 플랫폼 서비스
│       ├── reading_lock_service.dart
│       ├── notification_service.dart
│       ├── barcode_scanner_service.dart
│       └── location_service.dart
│
├── test/                             # 테스트
│   ├── unit/
│   ├── widget/
│   └── integration/
│
├── pubspec.yaml                      # 의존성
├── analysis_options.yaml             # Lint 설정
└── README.md
```

---

## 2. pubspec.yaml

```yaml
name: readlock
description: 소셜 독서 플랫폼 - 폰잠금 독서, 커뮤니티, AI 추천
publish_to: 'none'
version: 2.0.0+1

environment:
  sdk: '>=3.2.0 <4.0.0'
  flutter: '>=3.16.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter

  # 상태관리
  flutter_riverpod: ^2.4.9
  riverpod_annotation: ^2.3.3
  
  # 네트워킹
  dio: ^5.4.0
  retrofit: ^4.0.3
  
  # 로컬 저장소
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  flutter_secure_storage: ^9.0.0
  shared_preferences: ^2.2.2
  
  # 인증
  firebase_core: ^2.24.2
  firebase_auth: ^4.16.0
  google_sign_in: ^6.2.1
  sign_in_with_apple: ^5.0.0
  kakao_flutter_sdk_user: ^1.6.1
  
  # 카메라/바코드
  mobile_scanner: ^4.0.1
  
  # 지도
  google_maps_flutter: ^2.5.3
  geolocator: ^10.1.0
  geocoding: ^2.1.1
  
  # UI/UX
  flutter_animate: ^4.3.0
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  flutter_svg: ^2.0.9
  lottie: ^2.7.0
  
  # 결제
  in_app_purchase: ^3.1.13
  
  # 푸시 알림
  firebase_messaging: ^14.7.9
  flutter_local_notifications: ^16.3.0
  
  # 분석
  firebase_analytics: ^10.7.4
  firebase_crashlytics: ^3.4.8
  
  # 유틸리티
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  intl: ^0.18.1
  go_router: ^13.0.1
  logger: ^2.0.2+1
  equatable: ^2.0.5
  dartz: ^0.10.1
  
  # 플랫폼
  url_launcher: ^6.2.2
  share_plus: ^7.2.1
  package_info_plus: ^5.0.1
  device_info_plus: ^9.1.1
  connectivity_plus: ^5.0.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.1
  
  # 코드 생성
  build_runner: ^2.4.8
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  retrofit_generator: ^8.0.6
  riverpod_generator: ^2.3.9
  hive_generator: ^2.0.1
  
  # 테스트
  mockito: ^5.4.4
  mocktail: ^1.0.2

flutter:
  uses-material-design: true
  
  assets:
    - assets/images/
    - assets/icons/
    - assets/animations/
    
  fonts:
    - family: Pretendard
      fonts:
        - asset: assets/fonts/Pretendard-Regular.otf
        - asset: assets/fonts/Pretendard-Medium.otf
          weight: 500
        - asset: assets/fonts/Pretendard-SemiBold.otf
          weight: 600
        - asset: assets/fonts/Pretendard-Bold.otf
          weight: 700
```

---

## 3. 핵심 코드

### 3.1 main.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'app.dart';
import 'core/constants/storage_keys.dart';
import 'firebase_options.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Firebase 초기화
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  
  // Hive 초기화
  await Hive.initFlutter();
  await Hive.openBox(StorageKeys.settingsBox);
  await Hive.openBox(StorageKeys.cacheBox);
  
  // 세로 모드 고정 (선택적)
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);
  
  runApp(
    const ProviderScope(
      child: ReadLockApp(),
    ),
  );
}
```

### 3.2 app.dart

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/theme/app_theme.dart';
import 'presentation/providers/theme_provider.dart';
import 'presentation/routes/app_router.dart';

class ReadLockApp extends ConsumerWidget {
  const ReadLockApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'ReadLock',
      debugShowCheckedModeBanner: false,
      
      // 테마
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeMode,
      
      // 라우팅
      routerConfig: router,
      
      // 국제화
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('ko', 'KR'),
        Locale('en', 'US'),
      ],
      locale: const Locale('ko', 'KR'),
    );
  }
}
```

### 3.3 API Client (Dio + Retrofit)

```dart
// lib/data/datasources/remote/api_client.dart
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../../core/constants/api_endpoints.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: ApiEndpoints.baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 10),
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  ));

  dio.interceptors.addAll([
    AuthInterceptor(ref),
    LogInterceptor(
      requestBody: true,
      responseBody: true,
    ),
  ]);

  return dio;
});

class AuthInterceptor extends Interceptor {
  final Ref ref;
  final _storage = const FlutterSecureStorage();

  AuthInterceptor(this.ref);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // 토큰 갱신 시도
      final refreshed = await _refreshToken();
      if (refreshed) {
        // 원래 요청 재시도
        final response = await _retry(err.requestOptions);
        return handler.resolve(response);
      }
    }
    handler.next(err);
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final dio = Dio(BaseOptions(baseUrl: ApiEndpoints.baseUrl));
      final response = await dio.post('/auth/refresh', data: {
        'refreshToken': refreshToken,
      });

      final newAccessToken = response.data['data']['tokens']['accessToken'];
      final newRefreshToken = response.data['data']['tokens']['refreshToken'];

      await _storage.write(key: 'access_token', value: newAccessToken);
      await _storage.write(key: 'refresh_token', value: newRefreshToken);

      return true;
    } catch (e) {
      return false;
    }
  }

  Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    final token = await _storage.read(key: 'access_token');
    final options = Options(
      method: requestOptions.method,
      headers: {
        ...requestOptions.headers,
        'Authorization': 'Bearer $token',
      },
    );

    return Dio().request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }
}
```

### 3.4 Book API (Retrofit)

```dart
// lib/data/datasources/remote/book_api.dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../../models/response/api_response.dart';
import '../../models/response/book_response.dart';

part 'book_api.g.dart';

@RestApi()
abstract class BookApi {
  factory BookApi(Dio dio, {String baseUrl}) = _BookApi;

  /// 도서 검색 (네이버 책 API)
  @GET('/books/search')
  Future<ApiResponse<BookSearchResponse>> searchBooks({
    @Query('query') required String query,
    @Query('display') int display = 10,
    @Query('start') int start = 1,
    @Query('sort') String sort = 'sim',
  });

  /// ISBN으로 도서 조회
  @GET('/books/{isbn}')
  Future<ApiResponse<BookDetailResponse>> getBookByIsbn(
    @Path('isbn') String isbn,
  );

  /// 바코드 스캔
  @POST('/books/scan')
  Future<ApiResponse<BookDetailResponse>> scanBarcode(
    @Body() Map<String, String> body,
  );

  /// 내 책장 목록
  @GET('/me/books')
  Future<ApiResponse<UserBooksResponse>> getMyBooks({
    @Query('status') String? status,
    @Query('page') int page = 1,
    @Query('limit') int limit = 20,
  });

  /// 책장에 도서 추가
  @POST('/me/books')
  Future<ApiResponse<UserBookResponse>> addToBookshelf(
    @Body() Map<String, dynamic> body,
  );

  /// 독서 상태 업데이트
  @PATCH('/me/books/{id}')
  Future<ApiResponse<UserBookResponse>> updateUserBook(
    @Path('id') String id,
    @Body() Map<String, dynamic> body,
  );

  /// 책장에서 삭제
  @DELETE('/me/books/{id}')
  Future<ApiResponse<void>> removeFromBookshelf(
    @Path('id') String id,
  );
}

// Provider
final bookApiProvider = Provider<BookApi>((ref) {
  final dio = ref.watch(dioProvider);
  return BookApi(dio);
});
```

### 3.5 Book Repository

```dart
// lib/domain/repositories/book_repository.dart
import 'package:dartz/dartz.dart';
import '../entities/book.dart';
import '../../core/errors/failures.dart';

abstract class BookRepository {
  Future<Either<Failure, List<Book>>> searchBooks({
    required String query,
    int display = 10,
    int start = 1,
  });

  Future<Either<Failure, Book>> getBookByIsbn(String isbn);
  
  Future<Either<Failure, Book>> scanBarcode(String isbn);

  Future<Either<Failure, List<UserBook>>> getMyBooks({
    String? status,
    int page = 1,
  });

  Future<Either<Failure, UserBook>> addToBookshelf({
    required String isbn,
    required String status,
    int? totalPages,
  });

  Future<Either<Failure, UserBook>> updateUserBook({
    required String id,
    String? status,
    int? currentPage,
  });

  Future<Either<Failure, void>> removeFromBookshelf(String id);
}

// lib/data/repositories/book_repository_impl.dart
import 'package:dartz/dartz.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/repositories/book_repository.dart';
import '../../domain/entities/book.dart';
import '../../core/errors/failures.dart';
import '../datasources/remote/book_api.dart';

class BookRepositoryImpl implements BookRepository {
  final BookApi _api;

  BookRepositoryImpl(this._api);

  @override
  Future<Either<Failure, List<Book>>> searchBooks({
    required String query,
    int display = 10,
    int start = 1,
  }) async {
    try {
      final response = await _api.searchBooks(
        query: query,
        display: display,
        start: start,
      );
      
      if (response.success) {
        final books = response.data!.items
            .map((item) => Book.fromJson(item))
            .toList();
        return Right(books);
      } else {
        return Left(ServerFailure(response.error?.message ?? '검색 실패'));
      }
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, Book>> scanBarcode(String isbn) async {
    try {
      final response = await _api.scanBarcode({'isbn': isbn});
      
      if (response.success) {
        return Right(Book.fromJson(response.data!.book));
      } else {
        return Left(ServerFailure(response.error?.message ?? '스캔 실패'));
      }
    } catch (e) {
      return Left(ServerFailure(e.toString()));
    }
  }

  // ... 나머지 메서드 구현
}

final bookRepositoryProvider = Provider<BookRepository>((ref) {
  final api = ref.watch(bookApiProvider);
  return BookRepositoryImpl(api);
});
```

### 3.6 Reading Session Provider (Riverpod)

```dart
// lib/presentation/providers/reading_provider.dart
import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../domain/entities/reading_session.dart';
import '../../domain/entities/book.dart';
import '../../services/reading_lock_service.dart';

part 'reading_provider.g.dart';

/// 현재 독서 세션 상태
@freezed
class ReadingState with _$ReadingState {
  const factory ReadingState({
    UserBook? currentBook,
    ReadingSession? session,
    @Default(0) int elapsedSeconds,
    @Default(false) bool isReading,
    @Default(false) bool isLocked,
  }) = _ReadingState;
}

@riverpod
class ReadingNotifier extends _$ReadingNotifier {
  Timer? _timer;
  final _lockService = ReadingLockService();

  @override
  ReadingState build() {
    ref.onDispose(() {
      _timer?.cancel();
    });
    return const ReadingState();
  }

  /// 독서 시작
  Future<void> startReading(UserBook book, {bool enableLock = true}) async {
    // API 호출로 세션 생성
    final repository = ref.read(readingRepositoryProvider);
    final result = await repository.startSession(
      userBookId: book.id,
      platform: _getPlatform(),
    );

    result.fold(
      (failure) => throw Exception(failure.message),
      (session) {
        state = state.copyWith(
          currentBook: book,
          session: session,
          isReading: true,
          elapsedSeconds: 0,
        );

        // 타이머 시작
        _startTimer();

        // 폰잠금 활성화 (Android only)
        if (enableLock) {
          _enableLock();
        }
      },
    );
  }

  /// 독서 종료
  Future<ReadingSessionResult?> stopReading({int pagesRead = 0}) async {
    _timer?.cancel();
    _disableLock();

    if (state.session == null) return null;

    final repository = ref.read(readingRepositoryProvider);
    final result = await repository.endSession(
      sessionId: state.session!.id,
      pagesRead: pagesRead,
      wasLocked: state.isLocked,
    );

    return result.fold(
      (failure) {
        // 에러 처리
        return null;
      },
      (sessionResult) {
        state = const ReadingState();
        return sessionResult;
      },
    );
  }

  /// 일시정지
  void pause() {
    _timer?.cancel();
    state = state.copyWith(isReading: false);
  }

  /// 재개
  void resume() {
    _startTimer();
    state = state.copyWith(isReading: true);
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (_) {
      state = state.copyWith(
        elapsedSeconds: state.elapsedSeconds + 1,
      );
    });
  }

  void _enableLock() {
    _lockService.enableLock();
    state = state.copyWith(isLocked: true);
  }

  void _disableLock() {
    _lockService.disableLock();
    state = state.copyWith(isLocked: false);
  }

  String _getPlatform() {
    if (kIsWeb) return 'web';
    if (Platform.isAndroid) return 'android';
    if (Platform.isIOS) return 'ios';
    return 'unknown';
  }
}

/// 독서 통계 Provider
@riverpod
Future<ReadingStats> readingStats(ReadingStatsRef ref, {String period = 'month'}) async {
  final repository = ref.watch(readingRepositoryProvider);
  final result = await repository.getReadingStats(period: period);
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (stats) => stats,
  );
}

/// 오늘의 독서 목표 Provider
@riverpod
Future<DailyGoalProgress> dailyGoal(DailyGoalRef ref) async {
  final repository = ref.watch(readingRepositoryProvider);
  final result = await repository.getDailyGoalProgress();
  
  return result.fold(
    (failure) => throw Exception(failure.message),
    (progress) => progress,
  );
}
```

### 3.7 Reading Screen

```dart
// lib/presentation/screens/reading/reading_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../providers/reading_provider.dart';
import '../../widgets/common/animated_counter.dart';

class ReadingScreen extends ConsumerStatefulWidget {
  final UserBook book;

  const ReadingScreen({super.key, required this.book});

  @override
  ConsumerState<ReadingScreen> createState() => _ReadingScreenState();
}

class _ReadingScreenState extends ConsumerState<ReadingScreen> {
  @override
  void initState() {
    super.initState();
    // 전체화면 모드
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    
    // 독서 시작
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(readingNotifierProvider.notifier).startReading(widget.book);
    });
  }

  @override
  void dispose() {
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final readingState = ref.watch(readingNotifierProvider);
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.colorScheme.surface,
      body: SafeArea(
        child: Column(
          children: [
            // 상단 헤더
            _buildHeader(context, readingState),
            
            // 메인 콘텐츠
            Expanded(
              child: _buildMainContent(context, readingState),
            ),
            
            // 하단 컨트롤
            _buildControls(context, readingState),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, ReadingState state) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => _showExitDialog(context),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  widget.book.book.title,
                  style: Theme.of(context).textTheme.titleMedium,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  widget.book.book.author,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          if (state.isLocked)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.green.withOpacity(0.2),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.lock, size: 14, color: Colors.green),
                  const SizedBox(width: 4),
                  Text(
                    '잠금',
                    style: TextStyle(
                      color: Colors.green,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMainContent(BuildContext context, ReadingState state) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // 책 커버
        Hero(
          tag: 'book_${widget.book.id}',
          child: Container(
            width: 150,
            height: 200,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 20,
                  offset: const Offset(0, 10),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: widget.book.book.coverImage != null
                  ? Image.network(
                      widget.book.book.coverImage!,
                      fit: BoxFit.cover,
                    )
                  : Container(
                      color: Colors.grey[300],
                      child: const Icon(Icons.book, size: 60),
                    ),
            ),
          ),
        ).animate().fadeIn().scale(),
        
        const SizedBox(height: 48),
        
        // 타이머
        AnimatedCounter(
          value: state.elapsedSeconds,
          style: Theme.of(context).textTheme.displayLarge?.copyWith(
            fontWeight: FontWeight.w300,
            fontFeatures: [const FontFeature.tabularFigures()],
          ),
        ).animate().fadeIn(delay: 300.ms),
        
        const SizedBox(height: 8),
        
        Text(
          state.isReading ? '독서 중...' : '일시정지',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        
        const SizedBox(height: 24),
        
        // 진행률
        _buildProgressBar(context, state),
      ],
    );
  }

  Widget _buildProgressBar(BuildContext context, ReadingState state) {
    final progress = widget.book.totalPages != null && widget.book.totalPages! > 0
        ? widget.book.currentPage / widget.book.totalPages!
        : 0.0;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('${widget.book.currentPage}p'),
              Text('${(progress * 100).toInt()}%'),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: progress,
            backgroundColor: Theme.of(context).colorScheme.surfaceVariant,
            borderRadius: BorderRadius.circular(4),
          ),
        ],
      ),
    );
  }

  Widget _buildControls(BuildContext context, ReadingState state) {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // 일시정지/재개
          _ControlButton(
            icon: state.isReading ? Icons.pause : Icons.play_arrow,
            label: state.isReading ? '일시정지' : '재개',
            onPressed: () {
              final notifier = ref.read(readingNotifierProvider.notifier);
              if (state.isReading) {
                notifier.pause();
              } else {
                notifier.resume();
              }
            },
          ),
          
          // 완료
          _ControlButton(
            icon: Icons.check_circle,
            label: '완료',
            isPrimary: true,
            onPressed: () => _showCompleteDialog(context),
          ),
        ],
      ),
    );
  }

  Future<void> _showExitDialog(BuildContext context) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('독서 종료'),
        content: const Text('독서를 종료하시겠습니까?\n현재까지의 기록이 저장됩니다.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('종료'),
          ),
        ],
      ),
    );

    if (result == true && mounted) {
      await ref.read(readingNotifierProvider.notifier).stopReading();
      Navigator.pop(context);
    }
  }

  Future<void> _showCompleteDialog(BuildContext context) async {
    final pagesController = TextEditingController();
    
    final result = await showDialog<int>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('독서 완료'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('이번 세션에서 읽은 페이지 수를 입력해주세요.'),
            const SizedBox(height: 16),
            TextField(
              controller: pagesController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '읽은 페이지 수',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () {
              final pages = int.tryParse(pagesController.text) ?? 0;
              Navigator.pop(context, pages);
            },
            child: const Text('완료'),
          ),
        ],
      ),
    );

    if (result != null && mounted) {
      final sessionResult = await ref
          .read(readingNotifierProvider.notifier)
          .stopReading(pagesRead: result);
      
      if (sessionResult != null && mounted) {
        // 결과 화면으로 이동
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => ReadingResultScreen(result: sessionResult),
          ),
        );
      }
    }
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final bool isPrimary;

  const _ControlButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.isPrimary = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 64,
          height: 64,
          decoration: BoxDecoration(
            color: isPrimary
                ? Theme.of(context).colorScheme.primary
                : Theme.of(context).colorScheme.surfaceVariant,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: Icon(
              icon,
              color: isPrimary
                  ? Theme.of(context).colorScheme.onPrimary
                  : Theme.of(context).colorScheme.onSurfaceVariant,
            ),
            iconSize: 28,
            onPressed: onPressed,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
```

---

## 4. 플랫폼별 네이티브 코드

### 4.1 Android - 폰잠금 Service

```kotlin
// android/app/src/main/kotlin/.../ReadingLockService.kt
package com.pubstation.readlock

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class ReadingLockService : Service() {

    companion object {
        const val CHANNEL_ID = "reading_lock_channel"
        const val NOTIFICATION_ID = 1001
        
        fun start(context: Context) {
            val intent = Intent(context, ReadingLockService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }
        
        fun stop(context: Context) {
            context.stopService(Intent(context, ReadingLockService::class.java))
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createNotification()
        startForeground(NOTIFICATION_ID, notification)
        
        // DND 모드 활성화 (권한 필요)
        enableDoNotDisturb()
        
        return START_STICKY
    }

    override fun onDestroy() {
        disableDoNotDisturb()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "독서 모드",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "독서 중 알림 차단"
                setShowBadge(false)
            }
            
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun createNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            packageManager.getLaunchIntentForPackage(packageName),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("독서 중")
            .setContentText("ReadLock이 실행 중입니다")
            .setSmallIcon(R.drawable.ic_book)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun enableDoNotDisturb() {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (notificationManager.isNotificationPolicyAccessGranted) {
            notificationManager.setInterruptionFilter(
                NotificationManager.INTERRUPTION_FILTER_PRIORITY
            )
        }
    }

    private fun disableDoNotDisturb() {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        if (notificationManager.isNotificationPolicyAccessGranted) {
            notificationManager.setInterruptionFilter(
                NotificationManager.INTERRUPTION_FILTER_ALL
            )
        }
    }
}
```

### 4.2 Flutter Platform Channel

```dart
// lib/services/reading_lock_service.dart
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

class ReadingLockService {
  static const _channel = MethodChannel('com.pubstation.readlock/lock');

  Future<void> enableLock() async {
    if (kIsWeb) {
      // Web: 전체화면 모드 권장
      return;
    }

    if (Platform.isAndroid) {
      try {
        await _channel.invokeMethod('enableLock');
      } on PlatformException catch (e) {
        debugPrint('Failed to enable lock: ${e.message}');
      }
    } else if (Platform.isIOS) {
      // iOS: 화면 꺼짐 방지만 가능
      try {
        await _channel.invokeMethod('keepScreenOn', {'on': true});
      } catch (e) {
        debugPrint('Failed to keep screen on: $e');
      }
    }
  }

  Future<void> disableLock() async {
    if (kIsWeb) return;

    if (Platform.isAndroid) {
      try {
        await _channel.invokeMethod('disableLock');
      } on PlatformException catch (e) {
        debugPrint('Failed to disable lock: ${e.message}');
      }
    } else if (Platform.isIOS) {
      try {
        await _channel.invokeMethod('keepScreenOn', {'on': false});
      } catch (e) {
        debugPrint('Failed to disable keep screen on: $e');
      }
    }
  }

  Future<bool> hasLockPermission() async {
    if (kIsWeb || Platform.isIOS) return false;

    try {
      return await _channel.invokeMethod('hasLockPermission');
    } catch (e) {
      return false;
    }
  }

  Future<void> requestLockPermission() async {
    if (!Platform.isAndroid) return;

    try {
      await _channel.invokeMethod('requestLockPermission');
    } catch (e) {
      debugPrint('Failed to request permission: $e');
    }
  }
}
```

---

## 5. 바코드 스캐너

```dart
// lib/presentation/screens/library/barcode_scanner_screen.dart
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BarcodeScannerScreen extends ConsumerStatefulWidget {
  const BarcodeScannerScreen({super.key});

  @override
  ConsumerState<BarcodeScannerScreen> createState() => _BarcodeScannerScreenState();
}

class _BarcodeScannerScreenState extends ConsumerState<BarcodeScannerScreen> {
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
    torchEnabled: false,
  );

  bool _isProcessing = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('바코드 스캔'),
        actions: [
          IconButton(
            icon: ValueListenableBuilder(
              valueListenable: _controller.torchState,
              builder: (context, state, child) {
                return Icon(
                  state == TorchState.on ? Icons.flash_on : Icons.flash_off,
                );
              },
            ),
            onPressed: () => _controller.toggleTorch(),
          ),
          IconButton(
            icon: const Icon(Icons.flip_camera_ios),
            onPressed: () => _controller.switchCamera(),
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),
          
          // 스캔 가이드 오버레이
          _buildScanOverlay(),
          
          // 안내 텍스트
          Positioned(
            bottom: 100,
            left: 0,
            right: 0,
            child: Text(
              '책 뒷면의 바코드를 스캔해주세요',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                shadows: [
                  Shadow(
                    color: Colors.black.withOpacity(0.5),
                    blurRadius: 4,
                  ),
                ],
              ),
            ),
          ),
          
          // 로딩 인디케이터
          if (_isProcessing)
            Container(
              color: Colors.black54,
              child: const Center(
                child: CircularProgressIndicator(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildScanOverlay() {
    return CustomPaint(
      painter: ScanOverlayPainter(),
      child: const SizedBox.expand(),
    );
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_isProcessing) return;

    final barcode = capture.barcodes.firstOrNull;
    if (barcode == null || barcode.rawValue == null) return;

    final isbn = barcode.rawValue!;
    
    // ISBN 형식 검증 (10자리 또는 13자리)
    final cleanIsbn = isbn.replaceAll(RegExp(r'[^0-9X]'), '');
    if (cleanIsbn.length != 10 && cleanIsbn.length != 13) return;

    setState(() => _isProcessing = true);

    try {
      final repository = ref.read(bookRepositoryProvider);
      final result = await repository.scanBarcode(cleanIsbn);

      result.fold(
        (failure) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(failure.message)),
          );
        },
        (book) {
          // 책 상세 화면으로 이동
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => BookDetailScreen(book: book),
            ),
          );
        },
      );
    } finally {
      if (mounted) {
        setState(() => _isProcessing = false);
      }
    }
  }
}

class ScanOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black54
      ..style = PaintingStyle.fill;

    final scanRect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2),
      width: size.width * 0.8,
      height: 200,
    );

    // 어두운 배경
    canvas.drawPath(
      Path.combine(
        PathOperation.difference,
        Path()..addRect(Rect.fromLTWH(0, 0, size.width, size.height)),
        Path()..addRRect(RRect.fromRectAndRadius(scanRect, const Radius.circular(12))),
      ),
      paint,
    );

    // 스캔 영역 테두리
    final borderPaint = Paint()
      ..color = Colors.amber
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    canvas.drawRRect(
      RRect.fromRectAndRadius(scanRect, const Radius.circular(12)),
      borderPaint,
    );

    // 코너 강조
    _drawCorners(canvas, scanRect, borderPaint);
  }

  void _drawCorners(Canvas canvas, Rect rect, Paint paint) {
    const cornerLength = 30.0;
    paint.strokeWidth = 5;

    // 좌상단
    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(cornerLength, 0), paint);
    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(0, cornerLength), paint);

    // 우상단
    canvas.drawLine(rect.topRight, rect.topRight + const Offset(-cornerLength, 0), paint);
    canvas.drawLine(rect.topRight, rect.topRight + const Offset(0, cornerLength), paint);

    // 좌하단
    canvas.drawLine(rect.bottomLeft, rect.bottomLeft + const Offset(cornerLength, 0), paint);
    canvas.drawLine(rect.bottomLeft, rect.bottomLeft + const Offset(0, -cornerLength), paint);

    // 우하단
    canvas.drawLine(rect.bottomRight, rect.bottomRight + const Offset(-cornerLength, 0), paint);
    canvas.drawLine(rect.bottomRight, rect.bottomRight + const Offset(0, -cornerLength), paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
```

---

## 6. 빌드 및 배포 설정

### 6.1 Android 빌드 설정

```groovy
// android/app/build.gradle
android {
    compileSdkVersion 34
    
    defaultConfig {
        applicationId "com.pubstation.readlock"
        minSdkVersion 23
        targetSdkVersion 34
        versionCode 1
        versionName "2.0.0"
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### 6.2 iOS 빌드 설정

```xml
<!-- ios/Runner/Info.plist -->
<key>NSCameraUsageDescription</key>
<string>바코드 스캔을 위해 카메라 접근이 필요합니다.</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>주변 독립서점을 찾기 위해 위치 정보가 필요합니다.</string>

<key>UIBackgroundModes</key>
<array>
    <string>fetch</string>
    <string>remote-notification</string>
</array>
```

### 6.3 Web 빌드

```bash
# 웹 빌드 (CanvasKit 렌더러 - 성능 우선)
flutter build web --web-renderer canvaskit --release

# 또는 HTML 렌더러 (호환성 우선)
flutter build web --web-renderer html --release
```
