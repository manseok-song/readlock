import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../data/datasources/remote/api_client.dart';

part 'subscription_provider.freezed.dart';

// Plan Feature
class PlanFeature {
  final String id;
  final String name;
  final String description;
  final bool included;

  PlanFeature({
    required this.id,
    required this.name,
    required this.description,
    required this.included,
  });

  factory PlanFeature.fromJson(Map<String, dynamic> json) {
    return PlanFeature(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      included: json['included'] ?? false,
    );
  }
}

// Plan
class SubscriptionPlan {
  final String id;
  final String name;
  final String description;
  final double priceMonthly;
  final double priceYearly;
  final String currency;
  final List<PlanFeature> features;
  final bool isPopular;
  final int trialDays;

  SubscriptionPlan({
    required this.id,
    required this.name,
    required this.description,
    required this.priceMonthly,
    required this.priceYearly,
    required this.currency,
    required this.features,
    required this.isPopular,
    required this.trialDays,
  });

  factory SubscriptionPlan.fromJson(Map<String, dynamic> json) {
    return SubscriptionPlan(
      id: json['id'],
      name: json['name'],
      description: json['description'],
      priceMonthly: (json['price_monthly'] as num).toDouble(),
      priceYearly: (json['price_yearly'] as num).toDouble(),
      currency: json['currency'] ?? 'KRW',
      features: (json['features'] as List)
          .map((f) => PlanFeature.fromJson(f))
          .toList(),
      isPopular: json['is_popular'] ?? false,
      trialDays: json['trial_days'] ?? 0,
    );
  }
}

// Subscription
class Subscription {
  final String? id;
  final SubscriptionPlan? plan;
  final String status;
  final DateTime? currentPeriodStart;
  final DateTime? currentPeriodEnd;
  final bool cancelAtPeriodEnd;
  final DateTime? trialEnd;

  Subscription({
    this.id,
    this.plan,
    required this.status,
    this.currentPeriodStart,
    this.currentPeriodEnd,
    required this.cancelAtPeriodEnd,
    this.trialEnd,
  });

  bool get isActive => status == 'active' || status == 'trialing';
  bool get isTrial => status == 'trialing';
  bool get isPremium => isActive && plan != null && plan!.id != 'free';

  factory Subscription.fromJson(Map<String, dynamic> json) {
    return Subscription(
      id: json['id'],
      plan: json['plan'] != null ? SubscriptionPlan.fromJson(json['plan']) : null,
      status: json['status'] ?? 'none',
      currentPeriodStart: json['current_period_start'] != null
          ? DateTime.parse(json['current_period_start'])
          : null,
      currentPeriodEnd: json['current_period_end'] != null
          ? DateTime.parse(json['current_period_end'])
          : null,
      cancelAtPeriodEnd: json['cancel_at_period_end'] ?? false,
      trialEnd: json['trial_end'] != null
          ? DateTime.parse(json['trial_end'])
          : null,
    );
  }

  factory Subscription.none() {
    return Subscription(status: 'none', cancelAtPeriodEnd: false);
  }
}

// Payment Method
class PaymentMethod {
  final String id;
  final String type;
  final String? last4;
  final String? brand;
  final int? expMonth;
  final int? expYear;
  final bool isDefault;
  final DateTime createdAt;

  PaymentMethod({
    required this.id,
    required this.type,
    this.last4,
    this.brand,
    this.expMonth,
    this.expYear,
    required this.isDefault,
    required this.createdAt,
  });

  factory PaymentMethod.fromJson(Map<String, dynamic> json) {
    return PaymentMethod(
      id: json['id'],
      type: json['type'],
      last4: json['last4'],
      brand: json['brand'],
      expMonth: json['exp_month'],
      expYear: json['exp_year'],
      isDefault: json['is_default'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

// States
@freezed
class SubscriptionState with _$SubscriptionState {
  const factory SubscriptionState({
    @Default([]) List<SubscriptionPlan> plans,
    Subscription? currentSubscription,
    @Default({}) Map<String, bool> features,
    @Default(false) bool isLoading,
    @Default(false) bool isProcessing,
    String? error,
  }) = _SubscriptionState;
}

@freezed
class PaymentState with _$PaymentState {
  const factory PaymentState({
    @Default([]) List<PaymentMethod> methods,
    @Default(false) bool isLoading,
    @Default(false) bool isProcessing,
    String? error,
  }) = _PaymentState;
}

// Subscription Provider
class SubscriptionNotifier extends StateNotifier<SubscriptionState> {
  final ApiClient _apiClient;

  SubscriptionNotifier(this._apiClient) : super(const SubscriptionState());

  Future<void> loadPlans() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/subscriptions/plans');
      final plans = (response.data as List)
          .map((json) => SubscriptionPlan.fromJson(json))
          .toList();

      state = state.copyWith(plans: plans, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> loadCurrentSubscription() async {
    try {
      final response = await _apiClient.get('/subscriptions/me');
      final subscription = Subscription.fromJson(response.data);

      state = state.copyWith(currentSubscription: subscription);
    } catch (e) {
      state = state.copyWith(currentSubscription: Subscription.none());
    }
  }

  Future<void> loadFeatures() async {
    try {
      final response = await _apiClient.get('/subscriptions/features');
      final features = Map<String, bool>.from(response.data['features'] ?? {});

      state = state.copyWith(features: features);
    } catch (e) {
      // Silent fail
    }
  }

  Future<SubscribeResult> subscribe({
    required String planId,
    String? paymentMethodId,
    String billingCycle = 'monthly',
  }) async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      final response = await _apiClient.post(
        '/subscriptions/subscribe',
        data: {
          'plan_id': planId,
          'payment_method_id': paymentMethodId,
          'billing_cycle': billingCycle,
        },
      );

      final subscription = Subscription.fromJson(response.data);
      state = state.copyWith(
        currentSubscription: subscription,
        isProcessing: false,
      );

      await loadFeatures();

      return SubscribeResult(success: true, subscription: subscription);
    } catch (e) {
      state = state.copyWith(isProcessing: false, error: e.toString());
      return SubscribeResult(success: false, error: e.toString());
    }
  }

  Future<bool> cancelSubscription() async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      await _apiClient.post('/subscriptions/cancel');

      if (state.currentSubscription != null) {
        state = state.copyWith(
          currentSubscription: Subscription(
            id: state.currentSubscription!.id,
            plan: state.currentSubscription!.plan,
            status: state.currentSubscription!.status,
            currentPeriodStart: state.currentSubscription!.currentPeriodStart,
            currentPeriodEnd: state.currentSubscription!.currentPeriodEnd,
            cancelAtPeriodEnd: true,
            trialEnd: state.currentSubscription!.trialEnd,
          ),
          isProcessing: false,
        );
      }

      return true;
    } catch (e) {
      state = state.copyWith(isProcessing: false, error: e.toString());
      return false;
    }
  }

  Future<bool> resumeSubscription() async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      await _apiClient.post('/subscriptions/resume');

      if (state.currentSubscription != null) {
        state = state.copyWith(
          currentSubscription: Subscription(
            id: state.currentSubscription!.id,
            plan: state.currentSubscription!.plan,
            status: state.currentSubscription!.status,
            currentPeriodStart: state.currentSubscription!.currentPeriodStart,
            currentPeriodEnd: state.currentSubscription!.currentPeriodEnd,
            cancelAtPeriodEnd: false,
            trialEnd: state.currentSubscription!.trialEnd,
          ),
          isProcessing: false,
        );
      }

      return true;
    } catch (e) {
      state = state.copyWith(isProcessing: false, error: e.toString());
      return false;
    }
  }

  bool hasFeature(String featureId) {
    return state.features[featureId] ?? false;
  }
}

class SubscribeResult {
  final bool success;
  final Subscription? subscription;
  final String? error;

  SubscribeResult({required this.success, this.subscription, this.error});
}

// Payment Provider
class PaymentNotifier extends StateNotifier<PaymentState> {
  final ApiClient _apiClient;

  PaymentNotifier(this._apiClient) : super(const PaymentState());

  Future<void> loadPaymentMethods() async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final response = await _apiClient.get('/payments/methods');
      final methods = (response.data as List)
          .map((json) => PaymentMethod.fromJson(json))
          .toList();

      state = state.copyWith(methods: methods, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<bool> addPaymentMethod({
    required String paymentToken,
    bool setDefault = true,
  }) async {
    state = state.copyWith(isProcessing: true, error: null);

    try {
      await _apiClient.post('/payments/methods', data: {
        'payment_token': paymentToken,
        'set_default': setDefault,
      });

      await loadPaymentMethods();
      state = state.copyWith(isProcessing: false);
      return true;
    } catch (e) {
      state = state.copyWith(isProcessing: false, error: e.toString());
      return false;
    }
  }

  Future<bool> removePaymentMethod(String methodId) async {
    try {
      await _apiClient.delete('/payments/methods/$methodId');
      await loadPaymentMethods();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }

  Future<bool> setDefaultMethod(String methodId) async {
    try {
      await _apiClient.post('/payments/methods/$methodId/default');
      await loadPaymentMethods();
      return true;
    } catch (e) {
      state = state.copyWith(error: e.toString());
      return false;
    }
  }
}

// Providers
final subscriptionProvider = StateNotifierProvider<SubscriptionNotifier, SubscriptionState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return SubscriptionNotifier(apiClient);
});

final paymentProvider = StateNotifierProvider<PaymentNotifier, PaymentState>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return PaymentNotifier(apiClient);
});

final isPremiumProvider = Provider<bool>((ref) {
  final subscription = ref.watch(subscriptionProvider).currentSubscription;
  return subscription?.isPremium ?? false;
});

final currentPlanProvider = Provider<SubscriptionPlan?>((ref) {
  return ref.watch(subscriptionProvider).currentSubscription?.plan;
});
