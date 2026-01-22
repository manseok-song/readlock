import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PremiumScreen extends ConsumerWidget {
  const PremiumScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('프리미엄'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    theme.colorScheme.primary,
                    theme.colorScheme.tertiary,
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.workspace_premium,
                    size: 64,
                    color: Colors.amber,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'ReadLock 프리미엄',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '더 나은 독서 경험을 위한 프리미엄 기능',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Features
            Text(
              '프리미엄 혜택',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            _FeatureItem(
              icon: Icons.auto_awesome,
              title: 'AI 도서 추천',
              description: '당신의 취향에 맞는 맞춤 도서 추천',
            ),
            _FeatureItem(
              icon: Icons.analytics,
              title: '상세 통계',
              description: '더 자세한 독서 패턴 분석',
            ),
            _FeatureItem(
              icon: Icons.palette,
              title: '추가 테마',
              description: '다양한 앱 테마와 독서 모드',
            ),
            _FeatureItem(
              icon: Icons.stars,
              title: '독점 뱃지',
              description: '프리미엄 전용 뱃지 획득',
            ),
            _FeatureItem(
              icon: Icons.home_work,
              title: '마이룸 확장',
              description: '추가 가구와 데코레이션',
            ),
            _FeatureItem(
              icon: Icons.block,
              title: '광고 제거',
              description: '모든 광고 없이 깔끔한 경험',
            ),

            const SizedBox(height: 24),

            // Pricing
            Text(
              '구독 플랜',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: _PlanCard(
                    title: '월간',
                    price: '₩4,900',
                    period: '/월',
                    isRecommended: false,
                    onTap: () => _subscribe(context, 'monthly'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _PlanCard(
                    title: '연간',
                    price: '₩39,000',
                    period: '/년',
                    isRecommended: true,
                    savings: '33% 할인',
                    onTap: () => _subscribe(context, 'yearly'),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // Terms
            Text(
              '* 구독은 자동으로 갱신됩니다. 언제든지 취소할 수 있습니다.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 8),

            TextButton(
              onPressed: () {
                // TODO: Show terms
              },
              child: const Text('이용약관 보기'),
            ),
          ],
        ),
      ),
    );
  }

  void _subscribe(BuildContext context, String plan) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('구독하기'),
        content: Text('$plan 플랜을 구독하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              // TODO: Process payment
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('결제 기능은 준비 중입니다')),
              );
            },
            child: const Text('구독'),
          ),
        ],
      ),
    );
  }
}

class _FeatureItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;

  const _FeatureItem({
    required this.icon,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              icon,
              color: theme.colorScheme.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  final String title;
  final String price;
  final String period;
  final bool isRecommended;
  final String? savings;
  final VoidCallback onTap;

  const _PlanCard({
    required this.title,
    required this.price,
    required this.period,
    required this.isRecommended,
    this.savings,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: isRecommended ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: isRecommended
            ? BorderSide(color: theme.colorScheme.primary, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              if (isRecommended)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    '추천',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onPrimary,
                    ),
                  ),
                ),
              if (isRecommended) const SizedBox(height: 8),
              Text(
                title,
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              RichText(
                text: TextSpan(
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                  children: [
                    TextSpan(text: price),
                    TextSpan(
                      text: period,
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              if (savings != null) ...[
                const SizedBox(height: 4),
                Text(
                  savings!,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: Colors.green,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
