import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:geolocator/geolocator.dart';
import '../../data/datasources/remote/api_client.dart';

part 'map_provider.freezed.dart';

// Bookstore Entity
class Bookstore {
  final String id;
  final String name;
  final String address;
  final double latitude;
  final double longitude;
  final double distance;
  final double? rating;
  final int reviewCount;
  final String? phone;
  final String? website;
  final Map<String, String>? openingHours;
  final List<String> features;
  final List<String> imageUrls;
  final bool isFavorite;

  Bookstore({
    required this.id,
    required this.name,
    required this.address,
    required this.latitude,
    required this.longitude,
    required this.distance,
    this.rating,
    required this.reviewCount,
    this.phone,
    this.website,
    this.openingHours,
    required this.features,
    required this.imageUrls,
    required this.isFavorite,
  });

  factory Bookstore.fromJson(Map<String, dynamic> json) {
    return Bookstore(
      id: json['id'],
      name: json['name'],
      address: json['address'],
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      distance: (json['distance'] as num?)?.toDouble() ?? 0,
      rating: (json['rating'] as num?)?.toDouble(),
      reviewCount: json['review_count'] ?? 0,
      phone: json['phone'],
      website: json['website'],
      openingHours: json['opening_hours'] != null
          ? Map<String, String>.from(json['opening_hours'])
          : null,
      features: List<String>.from(json['features'] ?? []),
      imageUrls: List<String>.from(json['image_urls'] ?? []),
      isFavorite: json['is_favorite'] ?? false,
    );
  }
}

// Map State
@freezed
class MapState with _$MapState {
  const factory MapState({
    @Default([]) List<Bookstore> bookstores,
    @Default(false) bool isLoading,
    Position? currentPosition,
    Bookstore? selectedBookstore,
    @Default([]) List<String> activeFilters,
    String? error,
  }) = _MapState;
}

// Checkin State
@freezed
class CheckinState with _$CheckinState {
  const factory CheckinState({
    @Default([]) List<CheckinRecord> checkins,
    @Default(false) bool isLoading,
    @Default(false) bool isCheckingIn,
    String? error,
  }) = _CheckinState;
}

class CheckinRecord {
  final String id;
  final String bookstoreId;
  final String bookstoreName;
  final DateTime checkinAt;
  final int coinsEarned;
  final int expEarned;

  CheckinRecord({
    required this.id,
    required this.bookstoreId,
    required this.bookstoreName,
    required this.checkinAt,
    required this.coinsEarned,
    required this.expEarned,
  });

  factory CheckinRecord.fromJson(Map<String, dynamic> json) {
    return CheckinRecord(
      id: json['id'],
      bookstoreId: json['bookstore_id'],
      bookstoreName: json['bookstore_name'],
      checkinAt: DateTime.parse(json['checkin_at']),
      coinsEarned: json['coins_earned'] ?? 0,
      expEarned: json['exp_earned'] ?? 0,
    );
  }
}

// Map Provider
class MapNotifier extends StateNotifier<MapState> {
  final ApiClient _apiClient;

  MapNotifier(this._apiClient) : super(const MapState());

  Future<void> getCurrentLocation() async {
    try {
      final permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        final requested = await Geolocator.requestPermission();
        if (requested == LocationPermission.denied ||
            requested == LocationPermission.deniedForever) {
          state = state.copyWith(error: 'Location permission denied');
          return;
        }
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );

      state = state.copyWith(currentPosition: position);
      await loadNearbyBookstores();
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> loadNearbyBookstores({double? radius}) async {
    if (state.currentPosition == null) return;

    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get(
        '/map/bookstores/nearby',
        queryParameters: {
          'latitude': state.currentPosition!.latitude,
          'longitude': state.currentPosition!.longitude,
          'radius': radius ?? 5.0,
          if (state.activeFilters.isNotEmpty)
            'features': state.activeFilters.join(','),
        },
      );

      final bookstores = (response.data['bookstores'] as List)
          .map((json) => Bookstore.fromJson(json))
          .toList();

      state = state.copyWith(bookstores: bookstores, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> searchBookstores(String query) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get(
        '/map/bookstores/search',
        queryParameters: {
          'query': query,
          if (state.currentPosition != null) ...{
            'latitude': state.currentPosition!.latitude,
            'longitude': state.currentPosition!.longitude,
          },
        },
      );

      final bookstores = (response.data['bookstores'] as List)
          .map((json) => Bookstore.fromJson(json))
          .toList();

      state = state.copyWith(bookstores: bookstores, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  void selectBookstore(Bookstore? bookstore) {
    state = state.copyWith(selectedBookstore: bookstore);
  }

  void setFilters(List<String> filters) {
    state = state.copyWith(activeFilters: filters);
    loadNearbyBookstores();
  }

  Future<void> toggleFavorite(String bookstoreId) async {
    final index = state.bookstores.indexWhere((b) => b.id == bookstoreId);
    if (index == -1) return;

    final bookstore = state.bookstores[index];

    try {
      if (bookstore.isFavorite) {
        await _apiClient.delete('/map/bookstores/$bookstoreId/favorite');
      } else {
        await _apiClient.post('/map/bookstores/$bookstoreId/favorite');
      }

      final updatedBookstores = List<Bookstore>.from(state.bookstores);
      updatedBookstores[index] = Bookstore(
        id: bookstore.id,
        name: bookstore.name,
        address: bookstore.address,
        latitude: bookstore.latitude,
        longitude: bookstore.longitude,
        distance: bookstore.distance,
        rating: bookstore.rating,
        reviewCount: bookstore.reviewCount,
        phone: bookstore.phone,
        website: bookstore.website,
        openingHours: bookstore.openingHours,
        features: bookstore.features,
        imageUrls: bookstore.imageUrls,
        isFavorite: !bookstore.isFavorite,
      );

      state = state.copyWith(bookstores: updatedBookstores);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }
}

// Checkin Provider
class CheckinNotifier extends StateNotifier<CheckinState> {
  final ApiClient _apiClient;

  CheckinNotifier(this._apiClient) : super(const CheckinState());

  Future<void> loadCheckinHistory() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/map/checkins/me');

      final checkins = (response.data['checkins'] as List)
          .map((json) => CheckinRecord.fromJson(json))
          .toList();

      state = state.copyWith(checkins: checkins, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<CheckinResult?> checkin({
    required String bookstoreId,
    required double latitude,
    required double longitude,
  }) async {
    state = state.copyWith(isCheckingIn: true, error: null);

    try {
      final response = await _apiClient.post(
        '/map/checkins',
        data: {
          'bookstore_id': bookstoreId,
          'latitude': latitude,
          'longitude': longitude,
        },
      );

      state = state.copyWith(isCheckingIn: false);

      return CheckinResult(
        success: true,
        coinsEarned: response.data['coins_earned'] ?? 0,
        expEarned: response.data['exp_earned'] ?? 0,
        message: response.data['message'],
      );
    } catch (e) {
      state = state.copyWith(isCheckingIn: false, error: e.toString());
      return CheckinResult(success: false, message: e.toString());
    }
  }
}

class CheckinResult {
  final bool success;
  final int coinsEarned;
  final int expEarned;
  final String? message;

  CheckinResult({
    required this.success,
    this.coinsEarned = 0,
    this.expEarned = 0,
    this.message,
  });
}

// Providers
final mapProvider = StateNotifierProvider<MapNotifier, MapState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return MapNotifier(apiClient);
});

final checkinProvider = StateNotifierProvider<CheckinNotifier, CheckinState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return CheckinNotifier(apiClient);
});
