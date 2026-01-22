import 'package:hive/hive.dart';

import '../../../domain/entities/book.dart';

/// Local datasource for book data caching
class BookLocalDatasource {
  static const _booksBoxName = 'books_cache';
  static const _userBooksBoxName = 'user_books_cache';

  late Box<Map> _booksBox;
  late Box<Map> _userBooksBox;

  Future<void> init() async {
    _booksBox = await Hive.openBox<Map>(_booksBoxName);
    _userBooksBox = await Hive.openBox<Map>(_userBooksBoxName);
  }

  // Book caching
  Future<void> cacheBook(Book book) async {
    await _booksBox.put(book.id, book.toJson());
    // Also cache by ISBN for quick lookup
    if (book.isbn != null) {
      await _booksBox.put('isbn_${book.isbn}', book.toJson());
    }
  }

  Future<Book?> getBookById(String bookId) async {
    final data = _booksBox.get(bookId);
    if (data == null) return null;
    return Book.fromJson(Map<String, dynamic>.from(data));
  }

  Future<Book?> getBookByIsbn(String isbn) async {
    final data = _booksBox.get('isbn_$isbn');
    if (data == null) return null;
    return Book.fromJson(Map<String, dynamic>.from(data));
  }

  Future<void> clearBooksCache() async {
    await _booksBox.clear();
  }

  // User books caching
  Future<void> cacheUserBooks(List<UserBook> userBooks) async {
    for (final userBook in userBooks) {
      await _userBooksBox.put(userBook.id, userBook.toJson());
    }
  }

  Future<void> addUserBook(UserBook userBook) async {
    await _userBooksBox.put(userBook.id, userBook.toJson());
  }

  Future<void> updateUserBook(UserBook userBook) async {
    await _userBooksBox.put(userBook.id, userBook.toJson());
  }

  Future<void> removeUserBook(String userBookId) async {
    await _userBooksBox.delete(userBookId);
  }

  Future<List<UserBook>> getCachedUserBooks({BookStatus? status}) async {
    final allBooks = _userBooksBox.values.map((data) {
      return UserBook.fromJson(Map<String, dynamic>.from(data));
    }).toList();

    if (status != null) {
      return allBooks.where((book) => book.status == status).toList();
    }

    return allBooks;
  }

  Future<UserBook?> getUserBookById(String userBookId) async {
    final data = _userBooksBox.get(userBookId);
    if (data == null) return null;
    return UserBook.fromJson(Map<String, dynamic>.from(data));
  }

  Future<void> clearUserBooksCache() async {
    await _userBooksBox.clear();
  }

  // Clear all caches
  Future<void> clearAll() async {
    await clearBooksCache();
    await clearUserBooksCache();
  }
}
