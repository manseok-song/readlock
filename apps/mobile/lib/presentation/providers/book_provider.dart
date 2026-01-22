import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/entities/book.dart';
import '../../data/repositories/book_repository_impl.dart';

/// Search query state
class BookSearchState {
  final String query;
  final List<Book> results;
  final bool isLoading;
  final bool hasMore;
  final int page;
  final String? error;

  const BookSearchState({
    this.query = '',
    this.results = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
  });

  BookSearchState copyWith({
    String? query,
    List<Book>? results,
    bool? isLoading,
    bool? hasMore,
    int? page,
    String? error,
  }) {
    return BookSearchState(
      query: query ?? this.query,
      results: results ?? this.results,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      page: page ?? this.page,
      error: error,
    );
  }
}

/// Book search notifier
class BookSearchNotifier extends StateNotifier<BookSearchState> {
  final BookRepository _repository;

  BookSearchNotifier({required BookRepository repository})
      : _repository = repository,
        super(const BookSearchState());

  /// Search for books
  Future<void> search(String query) async {
    if (query.isEmpty) {
      state = const BookSearchState();
      return;
    }

    state = state.copyWith(
      query: query,
      isLoading: true,
      results: [],
      page: 1,
      error: null,
    );

    final result = await _repository.searchBooks(
      query: query,
      page: 1,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (books) {
        state = state.copyWith(
          results: books,
          isLoading: false,
          hasMore: books.length >= 20,
        );
      },
    );
  }

  /// Load more results
  Future<void> loadMore() async {
    if (state.isLoading || !state.hasMore || state.query.isEmpty) return;

    state = state.copyWith(isLoading: true);

    final nextPage = state.page + 1;
    final result = await _repository.searchBooks(
      query: state.query,
      page: nextPage,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (books) {
        state = state.copyWith(
          results: [...state.results, ...books],
          isLoading: false,
          hasMore: books.length >= 20,
          page: nextPage,
        );
      },
    );
  }

  /// Clear search
  void clear() {
    state = const BookSearchState();
  }
}

/// User library state
class UserLibraryState {
  final List<UserBook> books;
  final bool isLoading;
  final bool hasMore;
  final int page;
  final BookStatus? filter;
  final String? error;

  const UserLibraryState({
    this.books = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.page = 1,
    this.filter,
    this.error,
  });

  UserLibraryState copyWith({
    List<UserBook>? books,
    bool? isLoading,
    bool? hasMore,
    int? page,
    BookStatus? filter,
    String? error,
  }) {
    return UserLibraryState(
      books: books ?? this.books,
      isLoading: isLoading ?? this.isLoading,
      hasMore: hasMore ?? this.hasMore,
      page: page ?? this.page,
      filter: filter ?? this.filter,
      error: error,
    );
  }

  /// Get filtered books by status
  List<UserBook> get readingBooks =>
      books.where((b) => b.status == BookStatus.reading).toList();

  List<UserBook> get wishlistBooks =>
      books.where((b) => b.status == BookStatus.wishlist).toList();

  List<UserBook> get completedBooks =>
      books.where((b) => b.status == BookStatus.completed).toList();
}

/// User library notifier
class UserLibraryNotifier extends StateNotifier<UserLibraryState> {
  final BookRepository _repository;

  UserLibraryNotifier({required BookRepository repository})
      : _repository = repository,
        super(const UserLibraryState()) {
    loadBooks();
  }

  /// Load user's books
  Future<void> loadBooks({BookStatus? status}) async {
    state = state.copyWith(
      isLoading: true,
      filter: status,
      books: [],
      page: 1,
      error: null,
    );

    final result = await _repository.getUserBooks(
      status: status,
      page: 1,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (books) {
        state = state.copyWith(
          books: books,
          isLoading: false,
          hasMore: books.length >= 20,
        );
      },
    );
  }

  /// Load more books
  Future<void> loadMore() async {
    if (state.isLoading || !state.hasMore) return;

    state = state.copyWith(isLoading: true);

    final nextPage = state.page + 1;
    final result = await _repository.getUserBooks(
      status: state.filter,
      page: nextPage,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          error: failure.message,
        );
      },
      (books) {
        state = state.copyWith(
          books: [...state.books, ...books],
          isLoading: false,
          hasMore: books.length >= 20,
          page: nextPage,
        );
      },
    );
  }

  /// Add book to library
  Future<bool> addBook({
    required String bookId,
    BookStatus status = BookStatus.wishlist,
  }) async {
    final result = await _repository.addBookToLibrary(
      bookId: bookId,
      status: status,
    );

    return result.fold(
      (failure) {
        state = state.copyWith(error: failure.message);
        return false;
      },
      (userBook) {
        state = state.copyWith(
          books: [userBook, ...state.books],
        );
        return true;
      },
    );
  }

  /// Update book status
  Future<bool> updateBookStatus({
    required String userBookId,
    required BookStatus status,
  }) async {
    final result = await _repository.updateUserBook(
      userBookId: userBookId,
      status: status,
    );

    return result.fold(
      (failure) {
        state = state.copyWith(error: failure.message);
        return false;
      },
      (updatedBook) {
        final updatedBooks = state.books.map((book) {
          return book.id == userBookId ? updatedBook : book;
        }).toList();
        state = state.copyWith(books: updatedBooks);
        return true;
      },
    );
  }

  /// Update reading progress
  Future<bool> updateProgress({
    required String userBookId,
    required int currentPage,
  }) async {
    final result = await _repository.updateUserBook(
      userBookId: userBookId,
      currentPage: currentPage,
    );

    return result.fold(
      (failure) => false,
      (updatedBook) {
        final updatedBooks = state.books.map((book) {
          return book.id == userBookId ? updatedBook : book;
        }).toList();
        state = state.copyWith(books: updatedBooks);
        return true;
      },
    );
  }

  /// Remove book from library
  Future<bool> removeBook(String userBookId) async {
    final result = await _repository.removeBookFromLibrary(userBookId);

    return result.fold(
      (failure) {
        state = state.copyWith(error: failure.message);
        return false;
      },
      (_) {
        state = state.copyWith(
          books: state.books.where((b) => b.id != userBookId).toList(),
        );
        return true;
      },
    );
  }

  /// Refresh library
  Future<void> refresh() async {
    await loadBooks(status: state.filter);
  }
}

/// Providers
final bookSearchProvider = StateNotifierProvider<BookSearchNotifier, BookSearchState>((ref) {
  // TODO: Get proper repository instance
  throw UnimplementedError('Provider not properly initialized');
});

final userLibraryProvider = StateNotifierProvider<UserLibraryNotifier, UserLibraryState>((ref) {
  // TODO: Get proper repository instance
  throw UnimplementedError('Provider not properly initialized');
});

/// Single book detail provider
final bookDetailProvider = FutureProvider.family<Book?, String>((ref, bookId) async {
  // TODO: Implement book detail fetching
  return null;
});

/// User book by ID provider
final userBookProvider = FutureProvider.family<UserBook?, String>((ref, userBookId) async {
  // TODO: Implement user book fetching
  return null;
});
