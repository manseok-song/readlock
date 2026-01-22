import 'package:freezed_annotation/freezed_annotation.dart';
import 'user.dart';

part 'bookstore.freezed.dart';
part 'bookstore.g.dart';

@freezed
class Bookstore with _$Bookstore {
  const factory Bookstore({
    required String id,
    required String name,
    required String address,
    required double lat,
    required double lng,
    int? distance,
    String? phone,
    Map<String, String>? hours,
    String? description,
    @Default([]) List<String> features,
    String? imageUrl,
    @Default(0.0) double rating,
    @Default(0) int reviewCount,
    @Default(false) bool isVerified,
  }) = _Bookstore;

  factory Bookstore.fromJson(Map<String, dynamic> json) =>
      _$BookstoreFromJson(json);
}

@freezed
class BookstoreVisit with _$BookstoreVisit {
  const factory BookstoreVisit({
    required String id,
    required String bookstoreId,
    required String userId,
    required DateTime visitedAt,
    Bookstore? bookstore,
  }) = _BookstoreVisit;

  factory BookstoreVisit.fromJson(Map<String, dynamic> json) =>
      _$BookstoreVisitFromJson(json);
}

@freezed
class BookstoreReview with _$BookstoreReview {
  const factory BookstoreReview({
    required String id,
    required String bookstoreId,
    required String userId,
    required double rating,
    required String content,
    required DateTime createdAt,
    PublicUserProfile? author,
  }) = _BookstoreReview;

  factory BookstoreReview.fromJson(Map<String, dynamic> json) =>
      _$BookstoreReviewFromJson(json);
}

/// Bookstore features enum
enum BookstoreFeature {
  cafe,
  kids,
  event,
  indie,
  rare,
  secondhand,
  delivery,
  parking,
}

extension BookstoreFeatureExtension on BookstoreFeature {
  String get displayName {
    switch (this) {
      case BookstoreFeature.cafe:
        return '카페';
      case BookstoreFeature.kids:
        return '어린이';
      case BookstoreFeature.event:
        return '이벤트';
      case BookstoreFeature.indie:
        return '독립출판';
      case BookstoreFeature.rare:
        return '희귀본';
      case BookstoreFeature.secondhand:
        return '중고';
      case BookstoreFeature.delivery:
        return '배달';
      case BookstoreFeature.parking:
        return '주차';
    }
  }

  String get emoji {
    switch (this) {
      case BookstoreFeature.cafe:
        return '☕';
      case BookstoreFeature.kids:
        return '👶';
      case BookstoreFeature.event:
        return '🎉';
      case BookstoreFeature.indie:
        return '📕';
      case BookstoreFeature.rare:
        return '📜';
      case BookstoreFeature.secondhand:
        return '♻️';
      case BookstoreFeature.delivery:
        return '🚚';
      case BookstoreFeature.parking:
        return '🅿️';
    }
  }
}
