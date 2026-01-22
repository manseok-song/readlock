import 'package:equatable/equatable.dart';

/// Base failure class for domain layer errors
abstract class Failure extends Equatable {
  final String message;
  final String? code;
  final dynamic details;

  const Failure({
    required this.message,
    this.code,
    this.details,
  });

  @override
  List<Object?> get props => [message, code, details];
}

/// Server-related failures
class ServerFailure extends Failure {
  const ServerFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);
}

/// Network-related failures
class NetworkFailure extends Failure {
  const NetworkFailure([String message = '네트워크 연결을 확인해주세요.'])
      : super(message: message);
}

/// Cache-related failures
class CacheFailure extends Failure {
  const CacheFailure([String message = '캐시 데이터를 불러올 수 없습니다.'])
      : super(message: message);
}

/// Authentication-related failures
class AuthFailure extends Failure {
  const AuthFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  // Predefined auth failures
  static const invalidCredentials = AuthFailure(
    '이메일 또는 비밀번호가 올바르지 않습니다.',
    code: 'AUTH_001',
  );

  static const tokenExpired = AuthFailure(
    '세션이 만료되었습니다. 다시 로그인해주세요.',
    code: 'AUTH_002',
  );

  static const unauthorized = AuthFailure(
    '접근 권한이 없습니다.',
    code: 'AUTH_004',
  );

  static const emailAlreadyExists = AuthFailure(
    '이미 사용 중인 이메일입니다.',
    code: 'USER_002',
  );

  static const nicknameAlreadyExists = AuthFailure(
    '이미 사용 중인 닉네임입니다.',
    code: 'USER_003',
  );
}

/// Validation-related failures
class ValidationFailure extends Failure {
  const ValidationFailure(String message, {String? code})
      : super(message: message, code: code);
}

/// Book-related failures
class BookFailure extends Failure {
  const BookFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  static const notFound = BookFailure(
    '도서를 찾을 수 없습니다.',
    code: 'BOOK_001',
  );

  static const invalidIsbn = BookFailure(
    '잘못된 ISBN입니다.',
    code: 'BOOK_002',
  );

  static const alreadyInLibrary = BookFailure(
    '이미 책장에 추가된 도서입니다.',
    code: 'BOOK_003',
  );

  static const notInLibrary = BookFailure(
    '책장에 없는 도서입니다.',
    code: 'BOOK_004',
  );
}

/// Reading session-related failures
class ReadingSessionFailure extends Failure {
  const ReadingSessionFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  static const sessionInProgress = ReadingSessionFailure(
    '이미 진행 중인 독서 세션이 있습니다.',
    code: 'SESSION_001',
  );

  static const sessionNotFound = ReadingSessionFailure(
    '독서 세션을 찾을 수 없습니다.',
    code: 'SESSION_002',
  );
}

/// Shop-related failures
class ShopFailure extends Failure {
  const ShopFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  static const insufficientCoins = ShopFailure(
    '코인이 부족합니다.',
    code: 'SHOP_001',
  );

  static const levelRequired = ShopFailure(
    '레벨이 부족합니다.',
    code: 'SHOP_002',
  );

  static const itemNotFound = ShopFailure(
    '아이템을 찾을 수 없습니다.',
    code: 'SHOP_003',
  );

  static const alreadyOwned = ShopFailure(
    '이미 보유한 아이템입니다.',
    code: 'SHOP_004',
  );
}

/// Subscription-related failures
class SubscriptionFailure extends Failure {
  const SubscriptionFailure(
    String message, {
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  static const verificationFailed = SubscriptionFailure(
    '영수증 검증에 실패했습니다.',
    code: 'SUB_001',
  );

  static const alreadySubscribed = SubscriptionFailure(
    '이미 활성화된 구독이 있습니다.',
    code: 'SUB_002',
  );
}

/// Rate limit failures
class RateLimitFailure extends Failure {
  const RateLimitFailure([
    String message = '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.',
  ]) : super(message: message, code: 'RATE_001');
}

/// Permission failures
class PermissionFailure extends Failure {
  final String permission;

  const PermissionFailure({
    required this.permission,
    required String message,
  }) : super(message: message);

  @override
  List<Object?> get props => [message, permission];
}
