import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class BadgesScreen extends ConsumerWidget {
  const BadgesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('뱃지'),
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 0.8,
        ),
        itemCount: _badges.length,
        itemBuilder: (context, index) {
          final badge = _badges[index];
          return _BadgeCard(badge: badge);
        },
      ),
    );
  }
}

class _Badge {
  final String id;
  final String name;
  final String description;
  final IconData icon;
  final bool isUnlocked;
  final Color color;

  const _Badge({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.isUnlocked,
    required this.color,
  });
}

final _badges = [
  const _Badge(
    id: 'first_book',
    name: '첫 책',
    description: '첫 번째 책을 책장에 추가',
    icon: Icons.menu_book,
    isUnlocked: false,
    color: Colors.blue,
  ),
  const _Badge(
    id: 'first_complete',
    name: '완독 시작',
    description: '첫 번째 책을 완독',
    icon: Icons.check_circle,
    isUnlocked: false,
    color: Colors.green,
  ),
  const _Badge(
    id: 'streak_7',
    name: '1주일 연속',
    description: '7일 연속 독서',
    icon: Icons.local_fire_department,
    isUnlocked: false,
    color: Colors.orange,
  ),
  const _Badge(
    id: 'streak_30',
    name: '한 달 연속',
    description: '30일 연속 독서',
    icon: Icons.whatshot,
    isUnlocked: false,
    color: Colors.red,
  ),
  const _Badge(
    id: 'hour_10',
    name: '10시간 달성',
    description: '총 10시간 독서',
    icon: Icons.timer,
    isUnlocked: false,
    color: Colors.purple,
  ),
  const _Badge(
    id: 'books_10',
    name: '10권 완독',
    description: '10권의 책을 완독',
    icon: Icons.library_books,
    isUnlocked: false,
    color: Colors.teal,
  ),
  const _Badge(
    id: 'quote_first',
    name: '첫 인용구',
    description: '첫 인용구 저장',
    icon: Icons.format_quote,
    isUnlocked: false,
    color: Colors.indigo,
  ),
  const _Badge(
    id: 'social_first',
    name: '소셜 리더',
    description: '첫 팔로워 획득',
    icon: Icons.people,
    isUnlocked: false,
    color: Colors.pink,
  ),
  const _Badge(
    id: 'bookstore_visit',
    name: '서점 탐험가',
    description: '첫 서점 체크인',
    icon: Icons.storefront,
    isUnlocked: false,
    color: Colors.brown,
  ),
];

class _BadgeCard extends StatelessWidget {
  final _Badge badge;

  const _BadgeCard({required this.badge});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: InkWell(
        onTap: () => _showBadgeDetail(context),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: badge.isUnlocked
                      ? badge.color.withOpacity(0.2)
                      : theme.colorScheme.surfaceContainerHighest,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  badge.icon,
                  size: 28,
                  color: badge.isUnlocked
                      ? badge.color
                      : theme.colorScheme.outline,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                badge.name,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: badge.isUnlocked
                      ? null
                      : theme.colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showBadgeDetail(BuildContext context) {
    final theme = Theme.of(context);

    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: badge.isUnlocked
                    ? badge.color.withOpacity(0.2)
                    : theme.colorScheme.surfaceContainerHighest,
                shape: BoxShape.circle,
              ),
              child: Icon(
                badge.icon,
                size: 40,
                color: badge.isUnlocked
                    ? badge.color
                    : theme.colorScheme.outline,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              badge.name,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              badge.description,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              badge.isUnlocked ? '획득 완료!' : '미획득',
              style: theme.textTheme.labelLarge?.copyWith(
                color: badge.isUnlocked ? Colors.green : theme.colorScheme.outline,
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
