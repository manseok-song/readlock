import 'package:freezed_annotation/freezed_annotation.dart';
import 'book.dart';
import 'user.dart';

part 'quote.freezed.dart';
part 'quote.g.dart';

@freezed
class Quote with _$Quote {
  const factory Quote({
    required String id,
    required String userId,
    required String bookId,
    required String content,
    int? pageNumber,
    String? memo,
    @Default(0) int likesCount,
    @Default(true) bool isPublic,
    required DateTime createdAt,
    // Joined fields
    Book? book,
    PublicUserProfile? author,
    @Default(false) bool isLikedByMe,
  }) = _Quote;

  factory Quote.fromJson(Map<String, dynamic> json) => _$QuoteFromJson(json);
}

@freezed
class Review with _$Review {
  const factory Review({
    required String id,
    required String userId,
    required String bookId,
    required double rating,
    required String content,
    @Default(false) bool hasSpoiler,
    @Default(0) int likesCount,
    @Default(true) bool isPublic,
    required DateTime createdAt,
    DateTime? updatedAt,
    // Joined fields
    Book? book,
    PublicUserProfile? author,
    @Default(false) bool isLikedByMe,
    @Default([]) List<ReviewComment> comments,
  }) = _Review;

  factory Review.fromJson(Map<String, dynamic> json) => _$ReviewFromJson(json);
}

@freezed
class ReviewComment with _$ReviewComment {
  const factory ReviewComment({
    required String id,
    required String reviewId,
    required String userId,
    String? parentId,
    required String content,
    required DateTime createdAt,
    PublicUserProfile? author,
    @Default([]) List<ReviewComment> replies,
  }) = _ReviewComment;

  factory ReviewComment.fromJson(Map<String, dynamic> json) =>
      _$ReviewCommentFromJson(json);
}

/// Feed item that can be either a quote or review
@freezed
class FeedItem with _$FeedItem {
  const factory FeedItem.quote(Quote quote) = QuoteFeedItem;
  const factory FeedItem.review(Review review) = ReviewFeedItem;

  factory FeedItem.fromJson(Map<String, dynamic> json) {
    final type = json['type'] as String?;
    if (type == 'quote') {
      return FeedItem.quote(Quote.fromJson(json['data']));
    } else {
      return FeedItem.review(Review.fromJson(json['data']));
    }
  }
}

extension FeedItemExtension on FeedItem {
  DateTime get createdAt => when(
        quote: (q) => q.createdAt,
        review: (r) => r.createdAt,
      );

  String get userId => when(
        quote: (q) => q.userId,
        review: (r) => r.userId,
      );

  PublicUserProfile? get author => when(
        quote: (q) => q.author,
        review: (r) => r.author,
      );

  Book? get book => when(
        quote: (q) => q.book,
        review: (r) => r.book,
      );

  int get likesCount => when(
        quote: (q) => q.likesCount,
        review: (r) => r.likesCount,
      );

  bool get isLikedByMe => when(
        quote: (q) => q.isLikedByMe,
        review: (r) => r.isLikedByMe,
      );
}
