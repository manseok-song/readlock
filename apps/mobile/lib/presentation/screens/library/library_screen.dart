import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../routes/app_router.dart';

class LibraryScreen extends ConsumerStatefulWidget {
  const LibraryScreen({super.key});

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('내 책장'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => context.push(RoutePaths.bookSearch),
          ),
          IconButton(
            icon: const Icon(Icons.qr_code_scanner),
            onPressed: () => context.push(RoutePaths.barcodeScanner),
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '읽는 중'),
            Tab(text: '읽고 싶은'),
            Tab(text: '완독'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _BookList(status: 'reading'),
          _BookList(status: 'wishlist'),
          _BookList(status: 'completed'),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddOptions(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddOptions(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.qr_code_scanner),
              title: const Text('바코드 스캔'),
              onTap: () {
                Navigator.pop(context);
                context.push(RoutePaths.barcodeScanner);
              },
            ),
            ListTile(
              leading: const Icon(Icons.search),
              title: const Text('책 검색'),
              onTap: () {
                Navigator.pop(context);
                context.push(RoutePaths.bookSearch);
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _BookList extends StatelessWidget {
  final String status;

  const _BookList({required this.status});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    // TODO: Replace with actual book list from provider
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            _getEmptyIcon(),
            size: 64,
            color: theme.colorScheme.outline,
          ),
          const SizedBox(height: 16),
          Text(
            _getEmptyMessage(),
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: () => context.push(RoutePaths.bookSearch),
            icon: const Icon(Icons.add),
            label: const Text('책 추가하기'),
          ),
        ],
      ),
    );
  }

  IconData _getEmptyIcon() {
    switch (status) {
      case 'reading':
        return Icons.menu_book_outlined;
      case 'wishlist':
        return Icons.bookmark_border;
      case 'completed':
        return Icons.done_all;
      default:
        return Icons.book_outlined;
    }
  }

  String _getEmptyMessage() {
    switch (status) {
      case 'reading':
        return '읽고 있는 책이 없어요';
      case 'wishlist':
        return '읽고 싶은 책이 없어요';
      case 'completed':
        return '완독한 책이 없어요';
      default:
        return '책이 없어요';
    }
  }
}
