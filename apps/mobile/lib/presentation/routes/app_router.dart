import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../domain/entities/reading_session.dart';
import '../providers/auth_provider.dart';
import '../screens/splash/splash_screen.dart';
import '../screens/onboarding/onboarding_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/library/library_screen.dart';
import '../screens/library/book_detail_screen.dart';
import '../screens/library/book_search_screen.dart';
import '../screens/library/barcode_scanner_screen.dart';
import '../screens/reading/reading_screen.dart';
import '../screens/reading/reading_result_screen.dart';
import '../screens/discover/discover_screen.dart';
import '../screens/profile/profile_screen.dart';
import '../screens/profile/settings_screen.dart';
import '../screens/profile/stats_dashboard_screen.dart';
import '../screens/profile/badges_screen.dart';
import '../screens/profile/avatar_screen.dart';
import '../screens/profile/my_room_screen.dart';
import '../screens/profile/premium_screen.dart';
import '../screens/discover/quote_create_screen.dart';
import '../screens/discover/bookstore_map_screen.dart';

/// Route paths
class RoutePaths {
  RoutePaths._();

  static const splash = '/';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const register = '/register';

  // Main tabs
  static const home = '/home';
  static const library = '/library';
  static const discover = '/discover';
  static const profile = '/profile';

  // Library sub-routes
  static const bookSearch = '/library/search';
  static const bookDetail = '/library/book/:id';
  static const barcodeScanner = '/library/scanner';

  // Reading
  static const reading = '/reading/:bookId';
  static const readingResult = '/reading/result';

  // Profile sub-routes
  static const settings = '/profile/settings';
  static const stats = '/profile/stats';

  // Community
  static const quoteDetail = '/quote/:id';
  static const reviewDetail = '/review/:id';
  static const userProfile = '/user/:id';

  // Map
  static const bookstoreMap = '/map';
  static const bookstoreDetail = '/bookstore/:id';

  // Premium
  static const subscription = '/subscription';
  static const avatar = '/avatar';
  static const myRoom = '/my-room';
  static const shop = '/shop';
  static const achievements = '/achievements';
}

/// Router provider
final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: RoutePaths.splash,
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull?.isLoggedIn ?? false;
      final isOnboardingComplete = authState.valueOrNull?.isOnboardingComplete ?? false;
      final currentPath = state.matchedLocation;

      // Always allow splash
      if (currentPath == RoutePaths.splash) {
        return null;
      }

      // Public routes that don't require auth
      final publicRoutes = [
        RoutePaths.login,
        RoutePaths.register,
        RoutePaths.onboarding,
      ];

      if (publicRoutes.contains(currentPath)) {
        // If logged in, redirect to home
        if (isLoggedIn) {
          return RoutePaths.home;
        }
        return null;
      }

      // Protected routes
      if (!isLoggedIn) {
        // Check if onboarding is complete
        if (!isOnboardingComplete) {
          return RoutePaths.onboarding;
        }
        return RoutePaths.login;
      }

      return null;
    },
    routes: [
      // Splash
      GoRoute(
        path: RoutePaths.splash,
        builder: (context, state) => const SplashScreen(),
      ),

      // Onboarding
      GoRoute(
        path: RoutePaths.onboarding,
        builder: (context, state) => const OnboardingScreen(),
      ),

      // Auth
      GoRoute(
        path: RoutePaths.login,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: RoutePaths.register,
        builder: (context, state) => const RegisterScreen(),
      ),

      // Main shell with bottom navigation
      ShellRoute(
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          // Home
          GoRoute(
            path: RoutePaths.home,
            pageBuilder: (context, state) => const NoTransitionPage(
              child: HomeScreen(),
            ),
          ),

          // Library
          GoRoute(
            path: RoutePaths.library,
            pageBuilder: (context, state) => const NoTransitionPage(
              child: LibraryScreen(),
            ),
            routes: [
              GoRoute(
                path: 'search',
                builder: (context, state) => const BookSearchScreen(),
              ),
              GoRoute(
                path: 'book/:id',
                builder: (context, state) {
                  final bookId = state.pathParameters['id']!;
                  return BookDetailScreen(bookId: bookId);
                },
              ),
              GoRoute(
                path: 'scanner',
                builder: (context, state) => const BarcodeScannerScreen(),
              ),
            ],
          ),

          // Discover
          GoRoute(
            path: RoutePaths.discover,
            pageBuilder: (context, state) => const NoTransitionPage(
              child: DiscoverScreen(),
            ),
          ),

          // Profile
          GoRoute(
            path: RoutePaths.profile,
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ProfileScreen(),
            ),
            routes: [
              GoRoute(
                path: 'settings',
                builder: (context, state) => const SettingsScreen(),
              ),
              GoRoute(
                path: 'stats',
                builder: (context, state) => const StatsDashboardScreen(),
              ),
              GoRoute(
                path: 'badges',
                builder: (context, state) => const BadgesScreen(),
              ),
              GoRoute(
                path: 'avatar',
                builder: (context, state) => const AvatarScreen(),
              ),
              GoRoute(
                path: 'my-room',
                builder: (context, state) => const MyRoomScreen(),
              ),
              GoRoute(
                path: 'premium',
                builder: (context, state) => const PremiumScreen(),
              ),
            ],
          ),
        ],
      ),

      // Quote creation (full screen)
      GoRoute(
        path: '/quote/create',
        builder: (context, state) {
          final extra = state.extra as Map<String, String>?;
          return QuoteCreateScreen(
            bookId: extra?['bookId'],
            bookTitle: extra?['bookTitle'],
          );
        },
      ),

      // Bookstore map (full screen)
      GoRoute(
        path: RoutePaths.bookstoreMap,
        builder: (context, state) => const BookstoreMapScreen(),
      ),

      // Reading (full screen, outside shell)
      GoRoute(
        path: '/reading/:bookId',
        builder: (context, state) {
          final bookId = state.pathParameters['bookId']!;
          return ReadingScreen(bookId: bookId);
        },
      ),
      GoRoute(
        path: RoutePaths.readingResult,
        builder: (context, state) {
          final result = state.extra as ReadingSessionResult?;
          return ReadingResultScreen(result: result);
        },
      ),
    ],
    errorBuilder: (context, state) => ErrorScreen(error: state.error),
  );
});

/// Main shell with bottom navigation
class MainShell extends StatelessWidget {
  final Widget child;

  const MainShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: const MainBottomNavBar(),
    );
  }
}

/// Bottom navigation bar
class MainBottomNavBar extends ConsumerWidget {
  const MainBottomNavBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentPath = GoRouterState.of(context).matchedLocation;
    final currentIndex = _getSelectedIndex(currentPath);

    return NavigationBar(
      selectedIndex: currentIndex,
      onDestinationSelected: (index) => _onItemTapped(context, index),
      destinations: const [
        NavigationDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: '홈',
        ),
        NavigationDestination(
          icon: Icon(Icons.book_outlined),
          selectedIcon: Icon(Icons.book),
          label: '책장',
        ),
        NavigationDestination(
          icon: Icon(Icons.explore_outlined),
          selectedIcon: Icon(Icons.explore),
          label: '발견',
        ),
        NavigationDestination(
          icon: Icon(Icons.person_outline),
          selectedIcon: Icon(Icons.person),
          label: '프로필',
        ),
      ],
    );
  }

  int _getSelectedIndex(String path) {
    if (path.startsWith(RoutePaths.home)) return 0;
    if (path.startsWith(RoutePaths.library)) return 1;
    if (path.startsWith(RoutePaths.discover)) return 2;
    if (path.startsWith(RoutePaths.profile)) return 3;
    return 0;
  }

  void _onItemTapped(BuildContext context, int index) {
    switch (index) {
      case 0:
        context.go(RoutePaths.home);
        break;
      case 1:
        context.go(RoutePaths.library);
        break;
      case 2:
        context.go(RoutePaths.discover);
        break;
      case 3:
        context.go(RoutePaths.profile);
        break;
    }
  }
}

/// Error screen
class ErrorScreen extends StatelessWidget {
  final Exception? error;

  const ErrorScreen({super.key, this.error});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              '페이지를 찾을 수 없습니다',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              error?.toString() ?? '',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(RoutePaths.home),
              child: const Text('홈으로 이동'),
            ),
          ],
        ),
      ),
    );
  }
}
