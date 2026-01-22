/// Base exception class
abstract class AppException implements Exception {
  final String message;
  final String? code;
  final dynamic details;

  const AppException({
    required this.message,
    this.code,
    this.details,
  });

  @override
  String toString() => 'AppException: $message (code: $code)';
}

/// Server exception
class ServerException extends AppException {
  final int? statusCode;

  const ServerException({
    required String message,
    String? code,
    dynamic details,
    this.statusCode,
  }) : super(message: message, code: code, details: details);

  @override
  String toString() => 'ServerException: $message (status: $statusCode, code: $code)';
}

/// Network exception
class NetworkException extends AppException {
  const NetworkException({
    String message = '네트워크 연결을 확인해주세요.',
  }) : super(message: message);

  @override
  String toString() => 'NetworkException: $message';
}

/// Cache exception
class CacheException extends AppException {
  const CacheException({
    String message = '캐시 데이터를 불러올 수 없습니다.',
  }) : super(message: message);

  @override
  String toString() => 'CacheException: $message';
}

/// Authentication exception
class AuthException extends AppException {
  const AuthException({
    required String message,
    String? code,
  }) : super(message: message, code: code);

  @override
  String toString() => 'AuthException: $message (code: $code)';
}

/// Validation exception
class ValidationException extends AppException {
  final Map<String, List<String>>? fieldErrors;

  const ValidationException({
    required String message,
    this.fieldErrors,
  }) : super(message: message);

  @override
  String toString() => 'ValidationException: $message';
}

/// Timeout exception
class TimeoutException extends AppException {
  const TimeoutException({
    String message = '요청 시간이 초과되었습니다.',
  }) : super(message: message);

  @override
  String toString() => 'TimeoutException: $message';
}

/// Parse exception
class ParseException extends AppException {
  const ParseException({
    String message = '데이터 파싱에 실패했습니다.',
    dynamic details,
  }) : super(message: message, details: details);

  @override
  String toString() => 'ParseException: $message';
}

/// Platform exception wrapper
class PlatformServiceException extends AppException {
  const PlatformServiceException({
    required String message,
    String? code,
    dynamic details,
  }) : super(message: message, code: code, details: details);

  @override
  String toString() => 'PlatformServiceException: $message (code: $code)';
}
