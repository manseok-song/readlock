import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../data/datasources/remote/api_client.dart';
import '../../data/datasources/local/secure_storage.dart';
import '../../data/datasources/local/book_local_datasource.dart';
import '../../data/datasources/local/reading_local_datasource.dart';
import '../../data/repositories/auth_repository_impl.dart';
import '../../data/repositories/book_repository_impl.dart';
import '../../data/repositories/reading_repository_impl.dart';

/// Re-export apiClientProvider from api_client.dart
export '../../data/datasources/remote/api_client.dart' show apiClientProvider;

/// Secure storage provider
final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

/// Flutter secure storage provider (raw)
final flutterSecureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage(
    aOptions: AndroidOptions(
      encryptedSharedPreferences: true,
    ),
    iOptions: IOSOptions(
      accessibility: KeychainAccessibility.first_unlock,
    ),
  );
});

/// Book local datasource provider
final bookLocalDatasourceProvider = Provider<BookLocalDatasource>((ref) {
  final datasource = BookLocalDatasource();
  // Note: init() should be called during app startup
  return datasource;
});

/// Reading local datasource provider
final readingLocalDatasourceProvider = Provider<ReadingLocalDatasource>((ref) {
  final datasource = ReadingLocalDatasource();
  // Note: init() should be called during app startup
  return datasource;
});

/// Auth repository provider
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final secureStorage = ref.watch(secureStorageProvider);
  return AuthRepositoryImpl(
    apiClient: apiClient,
    secureStorage: secureStorage,
  );
});

/// Book repository provider
final bookRepositoryProvider = Provider<BookRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final localDatasource = ref.watch(bookLocalDatasourceProvider);
  return BookRepositoryImpl(
    apiClient: apiClient,
    localDatasource: localDatasource,
  );
});

/// Reading repository provider
final readingRepositoryProvider = Provider<ReadingRepository>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  final localDatasource = ref.watch(readingLocalDatasourceProvider);
  return ReadingRepositoryImpl(
    apiClient: apiClient,
    localDatasource: localDatasource,
  );
});
