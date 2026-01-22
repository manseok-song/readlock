import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../domain/entities/reading_session.dart';
import '../../routes/app_router.dart';

class ReadingResultScreen extends ConsumerWidget {
  final ReadingSessionResult? result;

  const ReadingResultScreen({super.key, this.result});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),

              // Success icon
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.check_circle,
                  size: 60,
                  color: theme.colorScheme.primary,
                ),
              ).animate().fadeIn().scale(),

              const SizedBox(height: 24),

              // Title
              Text(
                '독서 완료!',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ).animate().fadeIn(delay: 200.ms),

              const SizedBox(height: 8),

              Text(
                '오늘도 좋은 독서 시간이었어요',
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ).animate().fadeIn(delay: 300.ms),

              const SizedBox(height: 48),

              // Stats
              _StatsCard(result: result).animate().fadeIn(delay: 400.ms),

              const SizedBox(height: 24),

              // Rewards
              if (result != null)
                _RewardsSection(rewards: result!.rewards)
                    .animate()
                    .fadeIn(delay: 500.ms),

              const Spacer(),

              // Actions
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () {
                        // TODO: Share result
                      },
                      child: const Text('공유하기'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => context.go(RoutePaths.home),
                      child: const Text('홈으로'),
                    ),
                  ),
                ],
              ).animate().fadeIn(delay: 600.ms),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatsCard extends StatelessWidget {
  final ReadingSessionResult? result;

  const _StatsCard({this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _StatItem(
              icon: Icons.timer,
              value: '${(result?.duration ?? 0) ~/ 60}분',
              label: '독서 시간',
            ),
            _StatItem(
              icon: Icons.menu_book,
              value: '${result?.pagesRead ?? 0}쪽',
              label: '읽은 페이지',
            ),
            _StatItem(
              icon: Icons.local_fire_department,
              value: '${result?.streakDays ?? 0}일',
              label: '연속 독서',
            ),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;

  const _StatItem({
    required this.icon,
    required this.value,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      children: [
        Icon(icon, color: theme.colorScheme.primary),
        const SizedBox(height: 8),
        Text(
          value,
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}

class _RewardsSection extends StatelessWidget {
  final SessionRewards rewards;

  const _RewardsSection({required this.rewards});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      color: theme.colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.monetization_on,
              color: Colors.amber,
            ),
            const SizedBox(width: 8),
            Text(
              '+${rewards.coinsEarned} 코인',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(width: 24),
            Icon(
              Icons.star,
              color: Colors.purple,
            ),
            const SizedBox(width: 8),
            Text(
              '+${rewards.expEarned} 경험치',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
