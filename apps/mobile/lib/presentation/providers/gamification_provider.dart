import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../data/datasources/remote/api_client.dart';

part 'gamification_provider.freezed.dart';

// Badge Entity
class Badge {
  final String id;
  final String name;
  final String description;
  final String iconUrl;
  final String category;
  final String tier;
  final int expReward;
  final int coinReward;

  Badge({
    required this.id,
    required this.name,
    required this.description,
    required this.iconUrl,
    required this.category,
    required this.tier,
    required this.expReward,
    required this.coinReward,
  });

  factory Badge.fromJson(Map<String, dynamic> json) {
    return Badge(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      iconUrl: json['icon_url'],
      category: json['category'],
      tier: json['tier'],
      expReward: json['exp_reward'] ?? 0,
      coinReward: json['coin_reward'] ?? 0,
    );
  }
}

class BadgeProgress {
  final String badgeId;
  final Badge badge;
  final int currentProgress;
  final int requiredProgress;
  final double progressPercent;
  final bool isEarned;

  BadgeProgress({
    required this.badgeId,
    required this.badge,
    required this.currentProgress,
    required this.requiredProgress,
    required this.progressPercent,
    required this.isEarned,
  });

  factory BadgeProgress.fromJson(Map<String, dynamic> json) {
    return BadgeProgress(
      badgeId: json['badge_id'],
      badge: Badge.fromJson(json['badge']),
      currentProgress: json['current_progress'] ?? 0,
      requiredProgress: json['required_progress'] ?? 1,
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0,
      isEarned: json['is_earned'] ?? false,
    );
  }
}

// User Level
class UserLevel {
  final int level;
  final int currentExp;
  final int expToNextLevel;
  final int totalExp;
  final double progressPercent;
  final String title;

  UserLevel({
    required this.level,
    required this.currentExp,
    required this.expToNextLevel,
    required this.totalExp,
    required this.progressPercent,
    required this.title,
  });

  factory UserLevel.fromJson(Map<String, dynamic> json) {
    return UserLevel(
      level: json['level'] ?? 1,
      currentExp: json['current_exp'] ?? 0,
      expToNextLevel: json['exp_to_next_level'] ?? 100,
      totalExp: json['total_exp'] ?? 0,
      progressPercent: (json['progress_percent'] as num?)?.toDouble() ?? 0,
      title: json['title'] ?? 'Novice Reader',
    );
  }
}

// Shop Item
class ShopItem {
  final String id;
  final String name;
  final String description;
  final String category;
  final String? subcategory;
  final int priceCoins;
  final double? priceReal;
  final String previewUrl;
  final bool isLimited;
  final DateTime? availableUntil;
  final int requiredLevel;

  ShopItem({
    required this.id,
    required this.name,
    required this.description,
    required this.category,
    this.subcategory,
    required this.priceCoins,
    this.priceReal,
    required this.previewUrl,
    required this.isLimited,
    this.availableUntil,
    required this.requiredLevel,
  });

  factory ShopItem.fromJson(Map<String, dynamic> json) {
    return ShopItem(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      category: json['category'],
      subcategory: json['subcategory'],
      priceCoins: json['price_coins'] ?? 0,
      priceReal: (json['price_real'] as num?)?.toDouble(),
      previewUrl: json['preview_url'] ?? '',
      isLimited: json['is_limited'] ?? false,
      availableUntil: json['available_until'] != null
          ? DateTime.parse(json['available_until'])
          : null,
      requiredLevel: json['required_level'] ?? 1,
    );
  }
}

class InventoryItem {
  final String id;
  final ShopItem item;
  final DateTime purchasedAt;
  final bool isEquipped;

  InventoryItem({
    required this.id,
    required this.item,
    required this.purchasedAt,
    required this.isEquipped,
  });

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    return InventoryItem(
      id: json['id'],
      item: ShopItem.fromJson(json['item']),
      purchasedAt: DateTime.parse(json['purchased_at']),
      isEquipped: json['is_equipped'] ?? false,
    );
  }
}

// States
@freezed
class BadgeState with _$BadgeState {
  const factory BadgeState({
    @Default([]) List<BadgeProgress> badges,
    @Default(false) bool isLoading,
    String? error,
  }) = _BadgeState;
}

@freezed
class LevelState with _$LevelState {
  const factory LevelState({
    UserLevel? level,
    @Default(false) bool isLoading,
    String? error,
  }) = _LevelState;
}

@freezed
class ShopState with _$ShopState {
  const factory ShopState({
    @Default([]) List<ShopItem> items,
    @Default([]) List<InventoryItem> inventory,
    @Default(0) int coinBalance,
    @Default(false) bool isLoading,
    @Default(false) bool isPurchasing,
    String? error,
  }) = _ShopState;
}

// Badge Provider
class BadgeNotifier extends StateNotifier<BadgeState> {
  final ApiClient _apiClient;

  BadgeNotifier(this._apiClient) : super(const BadgeState());

  Future<void> loadBadgeProgress() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/badges/progress');
      final badges = (response.data as List)
          .map((json) => BadgeProgress.fromJson(json))
          .toList();

      state = state.copyWith(badges: badges, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> claimBadge(String badgeId) async {
    try {
      await _apiClient.post('/badges/$badgeId/claim');
      await loadBadgeProgress();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }
}

// Level Provider
class LevelNotifier extends StateNotifier<LevelState> {
  final ApiClient _apiClient;

  LevelNotifier(this._apiClient) : super(const LevelState());

  Future<void> loadLevel() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/levels/me');
      final level = UserLevel.fromJson(response.data);

      state = state.copyWith(level: level, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }
}

// Shop Provider
class ShopNotifier extends StateNotifier<ShopState> {
  final ApiClient _apiClient;

  ShopNotifier(this._apiClient) : super(const ShopState());

  Future<void> loadShopItems({String? category}) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get(
        '/shop/items',
        queryParameters: category != null ? {'category': category} : null,
      );
      final items = (response.data as List)
          .map((json) => ShopItem.fromJson(json))
          .toList();

      state = state.copyWith(items: items, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadInventory() async {
    try {
      final response = await _apiClient.get('/shop/inventory');
      final inventory = (response.data as List)
          .map((json) => InventoryItem.fromJson(json))
          .toList();

      state = state.copyWith(inventory: inventory);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> loadCoinBalance() async {
    try {
      final response = await _apiClient.get('/shop/coins');
      state = state.copyWith(coinBalance: response.data['balance'] ?? 0);
    } catch (e) {
      // Silent fail
    }
  }

  Future<PurchaseResult> purchaseItem(String itemId) async {
    state = state.copyWith(isPurchasing: true, error: null);

    try {
      final response = await _apiClient.post(
        '/shop/purchase',
        data: {'item_id': itemId},
      );

      state = state.copyWith(
        isPurchasing: false,
        coinBalance: response.data['new_balance'] ?? state.coinBalance,
      );

      await loadInventory();

      return PurchaseResult(
        success: true,
        item: ShopItem.fromJson(response.data['item']),
      );
    } catch (e) {
      state = state.copyWith(isPurchasing: false, error: e.toString());
      return PurchaseResult(success: false, error: e.toString());
    }
  }

  Future<bool> equipItem(String itemId) async {
    try {
      await _apiClient.post('/shop/equip/$itemId');
      await loadInventory();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  Future<bool> unequipItem(String itemId) async {
    try {
      await _apiClient.post('/shop/unequip/$itemId');
      await loadInventory();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }
}

class PurchaseResult {
  final bool success;
  final ShopItem? item;
  final String? error;

  PurchaseResult({required this.success, this.item, this.error});
}

// Providers
final badgeProvider = StateNotifierProvider<BadgeNotifier, BadgeState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return BadgeNotifier(apiClient);
});

final levelProvider = StateNotifierProvider<LevelNotifier, LevelState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return LevelNotifier(apiClient);
});

final shopProvider = StateNotifierProvider<ShopNotifier, ShopState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return ShopNotifier(apiClient);
});

final coinBalanceProvider = Provider<int>((ref) {
  return ref.watch(shopProvider).coinBalance;
});
