import 'package:dartz/dartz.dart';

import '../../core/errors/failures.dart';
import '../../core/errors/exceptions.dart';
import '../../domain/entities/user.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/local/secure_storage.dart';

/// Auth repository interface
abstract class AuthRepository {
  Future<Either<AuthFailure, AuthResult>> login({
    required String email,
    required String password,
  });

  Future<Either<AuthFailure, AuthResult>> register({
    required String email,
    required String password,
    required String nickname,
  });

  Future<Either<AuthFailure, AuthResult>> socialLogin({
    required String provider,
    required String accessToken,
  });

  Future<Either<AuthFailure, Unit>> logout();

  Future<Either<AuthFailure, AuthResult>> refreshToken();

  Future<Either<AuthFailure, User>> getCurrentUser();

  Future<bool> isLoggedIn();

  Future<Either<AuthFailure, Unit>> updateFcmToken(String token, String platform);
}

/// Auth repository implementation
class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _apiClient;
  final SecureStorage _secureStorage;

  AuthRepositoryImpl({
    required ApiClient apiClient,
    required SecureStorage secureStorage,
  })  : _apiClient = apiClient,
        _secureStorage = secureStorage;

  @override
  Future<Either<AuthFailure, AuthResult>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/login',
        data: {
          'email': email,
          'password': password,
        },
      );

      // API response structure: { success: true, data: { user, tokens } }
      final data = response.data['data'] ?? response.data;
      final tokensData = data['tokens'] ?? data;
      final userData = data['user'];

      final accessToken = tokensData['accessToken'] ?? tokensData['access_token'];
      final refreshToken = tokensData['refreshToken'] ?? tokensData['refresh_token'];

      if (accessToken == null || refreshToken == null) {
        return const Left(AuthFailure.unknown('Invalid server response: missing tokens'));
      }

      final tokens = AuthTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        expiresIn: tokensData['expiresIn'] ?? tokensData['expires_in'] ?? 1800,
      );

      await _saveTokens(tokens);

      final user = User.fromJson(userData);

      return Right(AuthResult(
        user: user,
        tokens: tokens,
        isNewUser: false,
      ));
    } on UnauthorizedException {
      return const Left(AuthFailure.invalidCredentials());
    } on NetworkException catch (e) {
      return Left(AuthFailure.networkError(e.message));
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<AuthFailure, AuthResult>> register({
    required String email,
    required String password,
    required String nickname,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/register',
        data: {
          'email': email,
          'password': password,
          'nickname': nickname,
        },
      );

      // API response structure: { success: true, data: { user, tokens } }
      final data = response.data['data'] ?? response.data;
      final tokensData = data['tokens'] ?? data;
      final userData = data['user'];

      final accessToken = tokensData['accessToken'] ?? tokensData['access_token'];
      final refreshToken = tokensData['refreshToken'] ?? tokensData['refresh_token'];

      if (accessToken == null || refreshToken == null) {
        return const Left(AuthFailure.unknown('Invalid server response: missing tokens'));
      }

      final tokens = AuthTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        expiresIn: tokensData['expiresIn'] ?? tokensData['expires_in'] ?? 1800,
      );

      await _saveTokens(tokens);

      final user = User.fromJson(userData);

      return Right(AuthResult(
        user: user,
        tokens: tokens,
        isNewUser: true,
      ));
    } on ConflictException {
      return const Left(AuthFailure.emailAlreadyInUse());
    } on ValidationException catch (e) {
      return Left(AuthFailure.validation(e.message));
    } on NetworkException catch (e) {
      return Left(AuthFailure.networkError(e.message));
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<AuthFailure, AuthResult>> socialLogin({
    required String provider,
    required String accessToken,
  }) async {
    try {
      final response = await _apiClient.post(
        '/auth/oauth/$provider',
        data: {
          'access_token': accessToken,
        },
      );

      // API response structure: { success: true, data: { user, tokens, isNewUser } }
      final data = response.data['data'] ?? response.data;
      final tokensData = data['tokens'] ?? data;
      final userData = data['user'];

      final accessToken = tokensData['accessToken'] ?? tokensData['access_token'];
      final refreshToken = tokensData['refreshToken'] ?? tokensData['refresh_token'];

      if (accessToken == null || refreshToken == null) {
        return const Left(AuthFailure.unknown('Invalid server response: missing tokens'));
      }

      final tokens = AuthTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        expiresIn: tokensData['expiresIn'] ?? tokensData['expires_in'] ?? 1800,
      );

      await _saveTokens(tokens);

      final user = User.fromJson(userData);

      return Right(AuthResult(
        user: user,
        tokens: tokens,
        isNewUser: data['isNewUser'] ?? data['is_new_user'] ?? false,
      ));
    } on NetworkException catch (e) {
      return Left(AuthFailure.networkError(e.message));
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<AuthFailure, Unit>> logout() async {
    try {
      await _apiClient.post('/auth/logout');
      await _clearTokens();
      return const Right(unit);
    } catch (e) {
      // Clear tokens even if API call fails
      await _clearTokens();
      return const Right(unit);
    }
  }

  @override
  Future<Either<AuthFailure, AuthResult>> refreshToken() async {
    try {
      final refreshToken = await _secureStorage.getRefreshToken();
      if (refreshToken == null) {
        return const Left(AuthFailure.sessionExpired());
      }

      final response = await _apiClient.post(
        '/auth/refresh',
        data: {
          'refresh_token': refreshToken,
        },
      );

      // API response structure: { success: true, data: { user, tokens } }
      final data = response.data['data'] ?? response.data;
      final tokensData = data['tokens'] ?? data;
      final userData = data['user'];

      final accessToken = tokensData['accessToken'] ?? tokensData['access_token'];
      final refreshToken = tokensData['refreshToken'] ?? tokensData['refresh_token'];

      if (accessToken == null || refreshToken == null) {
        return const Left(AuthFailure.unknown('Invalid server response: missing tokens'));
      }

      final tokens = AuthTokens(
        accessToken: accessToken,
        refreshToken: refreshToken,
        expiresIn: tokensData['expiresIn'] ?? tokensData['expires_in'] ?? 1800,
      );

      await _saveTokens(tokens);

      return Right(AuthResult(
        user: User.fromJson(userData),
        tokens: tokens,
        isNewUser: false,
      ));
    } on UnauthorizedException {
      await _clearTokens();
      return const Left(AuthFailure.sessionExpired());
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<AuthFailure, User>> getCurrentUser() async {
    try {
      final response = await _apiClient.get('/users/me');
      // API response structure: { success: true, data: { ... } }
      final userData = response.data['data'] ?? response.data;
      return Right(User.fromJson(userData));
    } on UnauthorizedException {
      return const Left(AuthFailure.sessionExpired());
    } on NetworkException catch (e) {
      return Left(AuthFailure.networkError(e.message));
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  @override
  Future<bool> isLoggedIn() async {
    final accessToken = await _secureStorage.getAccessToken();
    return accessToken != null;
  }

  @override
  Future<Either<AuthFailure, Unit>> updateFcmToken(String token, String platform) async {
    try {
      await _apiClient.post(
        '/users/me/fcm-token',
        data: {
          'token': token,
          'platform': platform,
        },
      );
      return const Right(unit);
    } on NetworkException catch (e) {
      return Left(AuthFailure.networkError(e.message));
    } catch (e) {
      return Left(AuthFailure.unknown(e.toString()));
    }
  }

  Future<void> _saveTokens(AuthTokens tokens) async {
    await _secureStorage.setAccessToken(tokens.accessToken);
    await _secureStorage.setRefreshToken(tokens.refreshToken);
  }

  Future<void> _clearTokens() async {
    await _secureStorage.deleteAll();
  }
}
