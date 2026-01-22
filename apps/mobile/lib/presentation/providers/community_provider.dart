import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/quote.dart';
import '../../data/datasources/remote/api_client.dart';

part 'community_provider.freezed.dart';

// Feed State
@freezed
class FeedState with _$FeedState {
  const factory FeedState({
    @Default([]) List<CommunityFeedItem> items,
    @Default(false) bool isLoading,
    @Default(false) bool hasMore,
    @Default(1) int currentPage,
    String? error,
  }) = _FeedState;
}

// Quote State
@freezed
class QuoteState with _$QuoteState {
  const factory QuoteState({
    @Default([]) List<Quote> quotes,
    @Default(false) bool isLoading,
    @Default(false) bool isSubmitting,
    String? error,
  }) = _QuoteState;
}

// Review State
@freezed
class ReviewState with _$ReviewState {
  const factory ReviewState({
    @Default([]) List<Review> reviews,
    @Default(false) bool isLoading,
    @Default(false) bool isSubmitting,
    String? error,
  }) = _ReviewState;
}

// Community Feed Item
class CommunityFeedItem {
  final String id;
  final String type; // quote, review
  final String userId;
  final String username;
  final String? userAvatarUrl;
  final String content;
  final String bookTitle;
  final String? bookAuthor;
  final String? bookCoverUrl;
  final int likesCount;
  final int commentsCount;
  final bool isLiked;
  final DateTime createdAt;

  FeedItem({
    required this.id,
    required this.type,
    required this.userId,
    required this.username,
    this.userAvatarUrl,
    required this.content,
    required this.bookTitle,
    this.bookAuthor,
    this.bookCoverUrl,
    required this.likesCount,
    required this.commentsCount,
    required this.isLiked,
    required this.createdAt,
  });

  factory CommunityFeedItem.fromJson(Map<String, dynamic> json) {
    return CommunityFeedItem(
      id: json['id'],
      type: json['type'],
      userId: json['user_id'],
      username: json['username'],
      userAvatarUrl: json['user_avatar_url'],
      content: json['content'],
      bookTitle: json['book_title'],
      bookAuthor: json['book_author'],
      bookCoverUrl: json['book_cover_url'],
      likesCount: json['likes_count'] ?? 0,
      commentsCount: json['comments_count'] ?? 0,
      isLiked: json['is_liked'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

// Feed Provider
class FeedNotifier extends StateNotifier<FeedState> {
  final ApiClient _apiClient;

  FeedNotifier(this._apiClient) : super(const FeedState());

  Future<void> loadFeed({bool refresh = false}) async {
    if (state.isLoading) return;

    state = state.copyWith(
      isLoading: true,
      error: null,
      currentPage: refresh ? 1 : state.currentPage,
    );

    try {
      final response = await _apiClient.get(
        '/community/feed',
        queryParameters: {
          'page': refresh ? 1 : state.currentPage,
          'page_size': 20,
        },
      );

      final items = (response.data['items'] as List)
          .map((json) => CommunityFeedItem.fromJson(json))
          .toList();

      state = state.copyWith(
        items: refresh ? items : [...state.items, ...items],
        isLoading: false,
        hasMore: response.data['has_more'] ?? false,
        currentPage: refresh ? 2 : state.currentPage + 1,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  Future<void> toggleLike(String itemId, String itemType) async {
    final index = state.items.indexWhere((item) => item.id == itemId);
    if (index == -1) return;

    final item = state.items[index];
    final endpoint = itemType == 'quote'
        ? '/community/quotes/$itemId/like'
        : '/community/reviews/$itemId/like';

    try {
      if (item.isLiked) {
        await _apiClient.delete(endpoint);
      } else {
        await _apiClient.post(endpoint);
      }

      final updatedItems = List<CommunityFeedItem>.from(state.items);
      updatedItems[index] = CommunityFeedItem(
        id: item.id,
        type: item.type,
        userId: item.userId,
        username: item.username,
        userAvatarUrl: item.userAvatarUrl,
        content: item.content,
        bookTitle: item.bookTitle,
        bookAuthor: item.bookAuthor,
        bookCoverUrl: item.bookCoverUrl,
        likesCount: item.isLiked ? item.likesCount - 1 : item.likesCount + 1,
        commentsCount: item.commentsCount,
        isLiked: !item.isLiked,
        createdAt: item.createdAt,
      );

      state = state.copyWith(items: updatedItems);
    } catch (e) {
      // Revert on error
    }
  }
}

// Quote Provider
class QuoteNotifier extends StateNotifier<QuoteState> {
  final ApiClient _apiClient;

  QuoteNotifier(this._apiClient) : super(const QuoteState());

  Future<void> loadQuotes(String bookId) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get(
        '/community/quotes',
        queryParameters: {'book_id': bookId},
      );

      final quotes = (response.data['items'] as List)
          .map((json) => Quote.fromJson(json))
          .toList();

      state = state.copyWith(quotes: quotes, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> createQuote({
    required String bookId,
    required String content,
    int? pageNumber,
  }) async {
    state = state.copyWith(isSubmitting: true, error: null);

    try {
      await _apiClient.post('/community/quotes', data: {
        'book_id': bookId,
        'content': content,
        'page_number': pageNumber,
      });

      state = state.copyWith(isSubmitting: false);
      return true;
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
      return false;
    }
  }

  Future<void> deleteQuote(String quoteId) async {
    try {
      await _apiClient.delete('/community/quotes/$quoteId');
      state = state.copyWith(
        quotes: state.quotes.where((q) => q.id != quoteId).toList(),
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }
}

// Review Provider
class ReviewNotifier extends StateNotifier<ReviewState> {
  final ApiClient _apiClient;

  ReviewNotifier(this._apiClient) : super(const ReviewState());

  Future<void> loadReviews(String bookId) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get(
        '/community/reviews',
        queryParameters: {'book_id': bookId},
      );

      final reviews = (response.data['items'] as List)
          .map((json) => Review.fromJson(json))
          .toList();

      state = state.copyWith(reviews: reviews, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> createReview({
    required String bookId,
    required String content,
    required double rating,
  }) async {
    state = state.copyWith(isSubmitting: true, error: null);

    try {
      await _apiClient.post('/community/reviews', data: {
        'book_id': bookId,
        'content': content,
        'rating': rating,
      });

      state = state.copyWith(isSubmitting: false);
      return true;
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
      return false;
    }
  }

  Future<bool> updateReview({
    required String reviewId,
    required String content,
    required double rating,
  }) async {
    state = state.copyWith(isSubmitting: true, error: null);

    try {
      await _apiClient.put('/community/reviews/$reviewId', data: {
        'content': content,
        'rating': rating,
      });

      state = state.copyWith(isSubmitting: false);
      return true;
    } catch (e) {
      state = state.copyWith(isSubmitting: false, error: e.toString());
      return false;
    }
  }

  Future<void> deleteReview(String reviewId) async {
    try {
      await _apiClient.delete('/community/reviews/$reviewId');
      state = state.copyWith(
        reviews: state.reviews.where((r) => r.id != reviewId).toList(),
      );
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }
}

// Providers
final feedProvider = StateNotifierProvider<FeedNotifier, FeedState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return FeedNotifier(apiClient);
});

final quoteProvider = StateNotifierProvider<QuoteNotifier, QuoteState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return QuoteNotifier(apiClient);
});

final reviewProvider = StateNotifierProvider<ReviewNotifier, ReviewState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ReviewNotifier(apiClient);
});
