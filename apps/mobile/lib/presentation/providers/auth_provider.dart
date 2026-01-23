import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/constants/storage_keys.dart';
import '../../domain/entities/user.dart';
import '../../data/repositories/auth_repository_impl.dart';
import 'repository_providers.dart';

/// Authentication state
class AuthState {
  final User? user;
  final bool isLoading;
  final bool isLoggedIn;
  final bool isOnboardingComplete;
  final String? error;

  const AuthState({
    this.user,
    this.isLoading = false,
    this.isLoggedIn = false,
    this.isOnboardingComplete = false,
    this.error,
  });

  AuthState copyWith({
    User? user,
    bool? isLoading,
    bool? isLoggedIn,
    bool? isOnboardingComplete,
    String? error,
  }) {
    return AuthState(
      user: user ?? this.user,
      isLoading: isLoading ?? this.isLoading,
      isLoggedIn: isLoggedIn ?? this.isLoggedIn,
      isOnboardingComplete: isOnboardingComplete ?? this.isOnboardingComplete,
      error: error,
    );
  }
}

/// Auth state provider
final authStateProvider = StateNotifierProvider<AuthNotifier, AsyncValue<AuthState>>(
  (ref) => AuthNotifier(ref),
);

/// Auth notifier
class AuthNotifier extends StateNotifier<AsyncValue<AuthState>> {
  final Ref ref;
  final _storage = const FlutterSecureStorage();

  AuthNotifier(this.ref) : super(const AsyncValue.loading()) {
    _initialize();
  }

  Future<void> _initialize() async {
    try {
      final token = await _storage.read(key: StorageKeys.accessToken);
      final box = Hive.box(StorageKeys.settingsBox);
      final onboardingComplete = box.get(StorageKeys.onboardingCompleted, defaultValue: false);

      if (token != null) {
        // Try to get current user
        final repository = ref.read(authRepositoryProvider);
        final result = await repository.getCurrentUser();

        result.fold(
          (failure) {
            // Token is invalid, clear it
            _clearAuth();
            state = AsyncValue.data(AuthState(
              isOnboardingComplete: onboardingComplete,
            ));
          },
          (user) {
            state = AsyncValue.data(AuthState(
              user: user,
              isLoggedIn: true,
              isOnboardingComplete: onboardingComplete,
            ));
          },
        );
      } else {
        state = AsyncValue.data(AuthState(
          isOnboardingComplete: onboardingComplete,
        ));
      }
    } catch (e) {
      state = AsyncValue.data(const AuthState());
    }
  }

  /// Login with email and password
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    final currentState = state.value;
    if (currentState == null) return false;

    state = AsyncValue.data(currentState.copyWith(isLoading: true, error: null));

    final repository = ref.read(authRepositoryProvider);
    final result = await repository.login(email: email, password: password);

    return await result.fold(
      (failure) {
        state = AsyncValue.data(currentState.copyWith(
          isLoading: false,
          error: failure.message,
        ));
        return false;
      },
      (authResult) async {
        await _saveTokens(authResult.tokens);
        state = AsyncValue.data(AuthState(
          user: authResult.user,
          isLoggedIn: true,
          isOnboardingComplete: true,
        ));
        return true;
      },
    );
  }

  /// Register new user
  Future<bool> register({
    required String email,
    required String password,
    required String nickname,
  }) async {
    final currentState = state.value;
    if (currentState == null) return false;

    state = AsyncValue.data(currentState.copyWith(isLoading: true, error: null));

    final repository = ref.read(authRepositoryProvider);
    final result = await repository.register(
      email: email,
      password: password,
      nickname: nickname,
    );

    return await result.fold(
      (failure) {
        state = AsyncValue.data(currentState.copyWith(
          isLoading: false,
          error: failure.message,
        ));
        return false;
      },
      (authResult) async {
        await _saveTokens(authResult.tokens);
        state = AsyncValue.data(AuthState(
          user: authResult.user,
          isLoggedIn: true,
          isOnboardingComplete: true,
        ));
        return true;
      },
    );
  }

  /// Social login
  Future<bool> socialLogin(String provider, String idToken) async {
    final currentState = state.value;
    if (currentState == null) return false;

    state = AsyncValue.data(currentState.copyWith(isLoading: true, error: null));

    final repository = ref.read(authRepositoryProvider);
    final result = await repository.socialLogin(
      provider: provider,
      accessToken: idToken,
    );

    return await result.fold(
      (failure) {
        state = AsyncValue.data(currentState.copyWith(
          isLoading: false,
          error: failure.message,
        ));
        return false;
      },
      (authResult) async {
        await _saveTokens(authResult.tokens);
        state = AsyncValue.data(AuthState(
          user: authResult.user,
          isLoggedIn: true,
          isOnboardingComplete: true,
        ));
        return true;
      },
    );
  }

  /// Logout
  Future<void> logout() async {
    final repository = ref.read(authRepositoryProvider);
    await repository.logout();
    await _clearAuth();

    state = AsyncValue.data(AuthState(
      isOnboardingComplete: state.value!.isOnboardingComplete,
    ));
  }

  /// Complete onboarding
  Future<void> completeOnboarding() async {
    final box = Hive.box(StorageKeys.settingsBox);
    await box.put(StorageKeys.onboardingCompleted, true);

    state = AsyncValue.data(state.value!.copyWith(
      isOnboardingComplete: true,
    ));
  }

  /// Update FCM token
  Future<void> updateFcmToken(String token, String platform) async {
    final repository = ref.read(authRepositoryProvider);
    await repository.updateFcmToken(token, platform);
  }

  /// Refresh user data
  Future<void> refreshUser() async {
    final repository = ref.read(authRepositoryProvider);
    final result = await repository.getCurrentUser();

    result.fold(
      (failure) {
        // Ignore refresh errors
      },
      (user) {
        state = AsyncValue.data(state.value!.copyWith(user: user));
      },
    );
  }

  Future<void> _saveTokens(AuthTokens tokens) async {
    await _storage.write(key: StorageKeys.accessToken, value: tokens.accessToken);
    await _storage.write(key: StorageKeys.refreshToken, value: tokens.refreshToken);
  }

  Future<void> _clearAuth() async {
    await _storage.delete(key: StorageKeys.accessToken);
    await _storage.delete(key: StorageKeys.refreshToken);
    await _storage.delete(key: StorageKeys.userId);
  }
}

/// Current user provider (convenience)
final currentUserProvider = Provider<User?>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.valueOrNull?.user;
});

/// Is logged in provider (convenience)
final isLoggedInProvider = Provider<bool>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.valueOrNull?.isLoggedIn ?? false;
});
