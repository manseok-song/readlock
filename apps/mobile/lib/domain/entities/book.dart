import 'package:freezed_annotation/freezed_annotation.dart';

part 'book.freezed.dart';
part 'book.g.dart';

@freezed
class Book with _$Book {
  const factory Book({
    required String id,
    required String isbn,
    required String title,
    required String author,
    String? publisher,
    DateTime? publishedDate,
    String? description,
    String? coverImage,
    String? category,
    int? pageCount,
    String? naverLink,
    DateTime? createdAt,
  }) = _Book;

  factory Book.fromJson(Map<String, dynamic> json) => _$BookFromJson(json);
}

@freezed
class UserBook with _$UserBook {
  const UserBook._();

  const factory UserBook({
    required String id,
    required Book book,
    required BookStatus status,
    @Default(0) int currentPage,
    int? totalPages,
    DateTime? startedAt,
    DateTime? finishedAt,
    required DateTime createdAt,
    DateTime? updatedAt,
  }) = _UserBook;

  factory UserBook.fromJson(Map<String, dynamic> json) =>
      _$UserBookFromJson(json);

  double get progress {
    final total = totalPages ?? book.pageCount ?? 0;
    if (total <= 0) return 0;
    return (currentPage / total * 100).clamp(0, 100);
  }

  bool get isReading => status == BookStatus.reading;
  bool get isCompleted => status == BookStatus.completed;
  bool get isWishlist => status == BookStatus.wishlist;
}

enum BookStatus {
  @JsonValue('wishlist')
  wishlist,
  @JsonValue('reading')
  reading,
  @JsonValue('completed')
  completed,
}

extension BookStatusExtension on BookStatus {
  String get displayName {
    switch (this) {
      case BookStatus.wishlist:
        return '읽고 싶은';
      case BookStatus.reading:
        return '읽는 중';
      case BookStatus.completed:
        return '완독';
    }
  }

  String get emoji {
    switch (this) {
      case BookStatus.wishlist:
        return '📚';
      case BookStatus.reading:
        return '📖';
      case BookStatus.completed:
        return '✅';
    }
  }
}

@freezed
class BookSearchResult with _$BookSearchResult {
  const factory BookSearchResult({
    required int total,
    required int start,
    required int display,
    required List<Book> items,
  }) = _BookSearchResult;

  factory BookSearchResult.fromJson(Map<String, dynamic> json) =>
      _$BookSearchResultFromJson(json);
}
