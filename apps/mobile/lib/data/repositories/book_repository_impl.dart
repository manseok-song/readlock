import 'package:dartz/dartz.dart';

import '../../core/errors/failures.dart';
import '../../core/errors/exceptions.dart';
import '../../domain/entities/book.dart';
import '../datasources/remote/api_client.dart';
import '../datasources/local/book_local_datasource.dart';

/// Book repository interface
abstract class BookRepository {
  Future<Either<BookFailure, List<Book>>> searchBooks({
    required String query,
    int page = 1,
    int pageSize = 20,
  });

  Future<Either<BookFailure, Book>> getBookByIsbn(String isbn);

  Future<Either<BookFailure, List<UserBook>>> getUserBooks({
    BookStatus? status,
    int page = 1,
    int pageSize = 20,
  });

  Future<Either<BookFailure, UserBook>> addBookToLibrary({
    required String bookId,
    BookStatus status = BookStatus.wishlist,
  });

  Future<Either<BookFailure, UserBook>> updateUserBook({
    required String userBookId,
    BookStatus? status,
    int? currentPage,
    double? rating,
  });

  Future<Either<BookFailure, Unit>> removeBookFromLibrary(String userBookId);

  Future<Either<BookFailure, Book>> getBookDetail(String bookId);
}

/// Book repository implementation
class BookRepositoryImpl implements BookRepository {
  final ApiClient _apiClient;
  final BookLocalDatasource _localDatasource;

  BookRepositoryImpl({
    required ApiClient apiClient,
    required BookLocalDatasource localDatasource,
  })  : _apiClient = apiClient,
        _localDatasource = localDatasource;

  @override
  Future<Either<BookFailure, List<Book>>> searchBooks({
    required String query,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _apiClient.get(
        '/books/search',
        queryParameters: {
          'query': query,
          'page': page,
          'page_size': pageSize,
        },
      );

      final books = (response.data['items'] as List)
          .map((json) => Book.fromJson(json))
          .toList();

      return Right(books);
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, Book>> getBookByIsbn(String isbn) async {
    try {
      // Try local cache first
      final cachedBook = await _localDatasource.getBookByIsbn(isbn);
      if (cachedBook != null) {
        return Right(cachedBook);
      }

      final response = await _apiClient.get('/books/isbn/$isbn');
      final book = Book.fromJson(response.data);

      // Cache the book
      await _localDatasource.cacheBook(book);

      return Right(book);
    } on NotFoundException {
      return const Left(BookFailure.notFound());
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, List<UserBook>>> getUserBooks({
    BookStatus? status,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
      };
      if (status != null) {
        queryParams['status'] = status.name;
      }

      final response = await _apiClient.get(
        '/users/me/books',
        queryParameters: queryParams,
      );

      final userBooks = (response.data['items'] as List)
          .map((json) => UserBook.fromJson(json))
          .toList();

      // Cache user books locally
      await _localDatasource.cacheUserBooks(userBooks);

      return Right(userBooks);
    } on NetworkException catch (e) {
      // Try to return cached data on network error
      final cachedBooks = await _localDatasource.getCachedUserBooks(status: status);
      if (cachedBooks.isNotEmpty) {
        return Right(cachedBooks);
      }
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, UserBook>> addBookToLibrary({
    required String bookId,
    BookStatus status = BookStatus.wishlist,
  }) async {
    try {
      final response = await _apiClient.post(
        '/users/me/books',
        data: {
          'book_id': bookId,
          'status': status.name,
        },
      );

      final userBook = UserBook.fromJson(response.data);

      // Update local cache
      await _localDatasource.addUserBook(userBook);

      return Right(userBook);
    } on ConflictException {
      return const Left(BookFailure.alreadyInLibrary());
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, UserBook>> updateUserBook({
    required String userBookId,
    BookStatus? status,
    int? currentPage,
    double? rating,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (status != null) data['status'] = status.name;
      if (currentPage != null) data['current_page'] = currentPage;
      if (rating != null) data['rating'] = rating;

      final response = await _apiClient.patch(
        '/users/me/books/$userBookId',
        data: data,
      );

      final userBook = UserBook.fromJson(response.data);

      // Update local cache
      await _localDatasource.updateUserBook(userBook);

      return Right(userBook);
    } on NotFoundException {
      return const Left(BookFailure.notFound());
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, Unit>> removeBookFromLibrary(String userBookId) async {
    try {
      await _apiClient.delete('/users/me/books/$userBookId');

      // Remove from local cache
      await _localDatasource.removeUserBook(userBookId);

      return const Right(unit);
    } on NotFoundException {
      return const Left(BookFailure.notFound());
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }

  @override
  Future<Either<BookFailure, Book>> getBookDetail(String bookId) async {
    try {
      final response = await _apiClient.get('/books/$bookId');
      final book = Book.fromJson(response.data);

      // Cache the book
      await _localDatasource.cacheBook(book);

      return Right(book);
    } on NotFoundException {
      return const Left(BookFailure.notFound());
    } on NetworkException catch (e) {
      return Left(BookFailure.networkError(e.message));
    } catch (e) {
      return Left(BookFailure.unknown(e.toString()));
    }
  }
}
