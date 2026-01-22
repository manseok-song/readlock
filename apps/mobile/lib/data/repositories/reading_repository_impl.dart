import 'package:dartz/dartz.dart';

import '../../core/errors/failures.dart';
import '../../core/errors/exceptions.dart';
import '../../domain/entities/reading_session.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/local/reading_local_datasource.dart';

/// Reading repository interface
abstract class ReadingRepository {
  Future<Either<ReadingFailure, ReadingSession>> startSession({
    required String userBookId,
    int? startPage,
  });

  Future<Either<ReadingFailure, ReadingSessionResult>> endSession({
    required String sessionId,
    required int endPage,
    int? focusScore,
  });

  Future<Either<ReadingFailure, Unit>> pauseSession(String sessionId);

  Future<Either<ReadingFailure, Unit>> resumeSession(String sessionId);

  Future<Either<ReadingFailure, ReadingSession?>> getActiveSession();

  Future<Either<ReadingFailure, List<ReadingSession>>> getSessionHistory({
    String? userBookId,
    DateTime? startDate,
    DateTime? endDate,
    int page = 1,
    int pageSize = 20,
  });

  Future<Either<ReadingFailure, ReadingStats>> getStats({
    required String period,
    DateTime? startDate,
    DateTime? endDate,
  });

  Future<Either<ReadingFailure, ReadingProfile>> getReadingProfile();
}

/// Reading repository implementation
class ReadingRepositoryImpl implements ReadingRepository {
  final ApiClient _apiClient;
  final ReadingLocalDatasource _localDatasource;

  ReadingRepositoryImpl({
    required ApiClient apiClient,
    required ReadingLocalDatasource localDatasource,
  })  : _apiClient = apiClient,
        _localDatasource = localDatasource;

  @override
  Future<Either<ReadingFailure, ReadingSession>> startSession({
    required String userBookId,
    int? startPage,
  }) async {
    try {
      final response = await _apiClient.post(
        '/reading/sessions',
        data: {
          'user_book_id': userBookId,
          if (startPage != null) 'start_page': startPage,
        },
      );

      final session = ReadingSession.fromJson(response.data);

      // Save active session locally for offline support
      await _localDatasource.saveActiveSession(session);

      return Right(session);
    } on ConflictException {
      return const Left(ReadingFailure.sessionAlreadyActive());
    } on NetworkException catch (e) {
      // Create offline session
      final offlineSession = await _localDatasource.createOfflineSession(
        userBookId: userBookId,
        startPage: startPage ?? 0,
      );
      return Right(offlineSession);
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, ReadingSessionResult>> endSession({
    required String sessionId,
    required int endPage,
    int? focusScore,
  }) async {
    try {
      final response = await _apiClient.post(
        '/reading/sessions/$sessionId/end',
        data: {
          'end_page': endPage,
          if (focusScore != null) 'focus_score': focusScore,
        },
      );

      final result = ReadingSessionResult.fromJson(response.data);

      // Clear active session
      await _localDatasource.clearActiveSession();

      // Sync any pending offline sessions
      await _syncOfflineSessions();

      return Right(result);
    } on NotFoundException {
      return const Left(ReadingFailure.sessionNotFound());
    } on NetworkException catch (e) {
      // Save session locally for later sync
      await _localDatasource.markSessionForSync(
        sessionId: sessionId,
        endPage: endPage,
        focusScore: focusScore,
      );

      // Return estimated result
      final estimatedResult = await _localDatasource.estimateSessionResult(
        sessionId: sessionId,
        endPage: endPage,
      );
      return Right(estimatedResult);
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, Unit>> pauseSession(String sessionId) async {
    try {
      await _apiClient.post('/reading/sessions/$sessionId/pause');
      await _localDatasource.pauseSession(sessionId);
      return const Right(unit);
    } on NotFoundException {
      return const Left(ReadingFailure.sessionNotFound());
    } on NetworkException {
      // Save pause state locally
      await _localDatasource.pauseSession(sessionId);
      return const Right(unit);
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, Unit>> resumeSession(String sessionId) async {
    try {
      await _apiClient.post('/reading/sessions/$sessionId/resume');
      await _localDatasource.resumeSession(sessionId);
      return const Right(unit);
    } on NotFoundException {
      return const Left(ReadingFailure.sessionNotFound());
    } on NetworkException {
      // Save resume state locally
      await _localDatasource.resumeSession(sessionId);
      return const Right(unit);
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, ReadingSession?>> getActiveSession() async {
    try {
      final response = await _apiClient.get('/reading/sessions/active');

      if (response.data == null) {
        return const Right(null);
      }

      final session = ReadingSession.fromJson(response.data);
      await _localDatasource.saveActiveSession(session);
      return Right(session);
    } on NotFoundException {
      // Check for local active session
      final localSession = await _localDatasource.getActiveSession();
      return Right(localSession);
    } on NetworkException {
      // Return local active session if any
      final localSession = await _localDatasource.getActiveSession();
      return Right(localSession);
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, List<ReadingSession>>> getSessionHistory({
    String? userBookId,
    DateTime? startDate,
    DateTime? endDate,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
      };
      if (userBookId != null) queryParams['user_book_id'] = userBookId;
      if (startDate != null) queryParams['start_date'] = startDate.toIso8601String();
      if (endDate != null) queryParams['end_date'] = endDate.toIso8601String();

      final response = await _apiClient.get(
        '/reading/sessions',
        queryParameters: queryParams,
      );

      final sessions = (response.data['items'] as List)
          .map((json) => ReadingSession.fromJson(json))
          .toList();

      return Right(sessions);
    } on NetworkException catch (e) {
      // Try to return cached data
      final cachedSessions = await _localDatasource.getCachedSessions(
        userBookId: userBookId,
        startDate: startDate,
        endDate: endDate,
      );
      if (cachedSessions.isNotEmpty) {
        return Right(cachedSessions);
      }
      return Left(ReadingFailure.networkError(e.message));
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, ReadingStats>> getStats({
    required String period,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'period': period,
      };
      if (startDate != null) queryParams['start_date'] = startDate.toIso8601String();
      if (endDate != null) queryParams['end_date'] = endDate.toIso8601String();

      final response = await _apiClient.get(
        '/reading/stats',
        queryParameters: queryParams,
      );

      return Right(ReadingStats.fromJson(response.data));
    } on NetworkException catch (e) {
      return Left(ReadingFailure.networkError(e.message));
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<ReadingFailure, ReadingProfile>> getReadingProfile() async {
    try {
      final response = await _apiClient.get('/reading/profile');
      return Right(ReadingProfile.fromJson(response.data));
    } on NetworkException catch (e) {
      return Left(ReadingFailure.networkError(e.message));
    } catch (e) {
      return Left(ReadingFailure.unknown(e.toString()));
    }
  }

  Future<void> _syncOfflineSessions() async {
    final pendingSessions = await _localDatasource.getPendingSyncSessions();

    for (final session in pendingSessions) {
      try {
        if (session.isOffline) {
          // Create session on server
          await _apiClient.post(
            '/reading/sessions/sync',
            data: session.toJson(),
          );
        } else {
          // Sync end data
          await _apiClient.post(
            '/reading/sessions/${session.id}/end',
            data: {
              'end_page': session.endPage,
              'focus_score': session.focusScore,
            },
          );
        }
        await _localDatasource.markSessionSynced(session.id);
      } catch (e) {
        // Will retry on next sync
      }
    }
  }
}
