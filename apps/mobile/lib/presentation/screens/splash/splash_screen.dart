import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../providers/auth_provider.dart';
import '../../routes/app_router.dart';

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigate();
  }

  Future<void> _navigate() async {
    // Wait for animation and auth check
    await Future.delayed(const Duration(milliseconds: 2000));

    if (!mounted) return;

    final authState = ref.read(authStateProvider);

    authState.when(
      data: (state) {
        if (state.isLoggedIn) {
          context.go(RoutePaths.home);
        } else if (state.isOnboardingComplete) {
          context.go(RoutePaths.login);
        } else {
          context.go(RoutePaths.onboarding);
        }
      },
      loading: () {
        // Still loading, wait more
        Future.delayed(const Duration(milliseconds: 500), _navigate);
      },
      error: (_, __) {
        context.go(RoutePaths.login);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Logo
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Icon(
                Icons.book,
                size: 64,
                color: theme.colorScheme.onPrimary,
              ),
            ).animate().fadeIn().scale(),

            const SizedBox(height: 24),

            // App name
            Text(
              'ReadLock',
              style: theme.textTheme.headlineLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ).animate().fadeIn(delay: 200.ms),

            const SizedBox(height: 8),

            // Tagline
            Text(
              '몰입하는 독서의 시작',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ).animate().fadeIn(delay: 400.ms),

            const SizedBox(height: 48),

            // Loading indicator
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: theme.colorScheme.primary,
              ),
            ).animate().fadeIn(delay: 600.ms),
          ],
        ),
      ),
    );
  }
}
