import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../domain/entities/book.dart';
import '../../providers/book_provider.dart';

class BookSearchScreen extends ConsumerStatefulWidget {
  const BookSearchScreen({super.key});

  @override
  ConsumerState<BookSearchScreen> createState() => _BookSearchScreenState();
}

class _BookSearchScreenState extends ConsumerState<BookSearchScreen> {
  final _searchController = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _focusNode.requestFocus();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final searchState = ref.watch(bookSearchProvider);

    return Scaffold(
      appBar: AppBar(
        title: TextField(
          controller: _searchController,
          focusNode: _focusNode,
          decoration: const InputDecoration(
            hintText: '책 제목, 저자, ISBN 검색',
            border: InputBorder.none,
          ),
          textInputAction: TextInputAction.search,
          onSubmitted: _search,
        ),
        actions: [
          if (_searchController.text.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.clear),
              onPressed: () {
                _searchController.clear();
                ref.read(bookSearchProvider.notifier).clear();
                setState(() {});
              },
            ),
        ],
      ),
      body: _buildBody(searchState, theme),
    );
  }

  Widget _buildBody(BookSearchState searchState, ThemeData theme) {
    if (searchState.query.isEmpty) {
      return _EmptyState();
    }

    if (searchState.isLoading && searchState.results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              '"${searchState.query}" 검색 중...',
              style: theme.textTheme.bodyMedium,
            ),
          ],
        ),
      );
    }

    if (searchState.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: theme.colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              searchState.error!,
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.error,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => _search(searchState.query),
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (searchState.results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.search_off,
              size: 64,
              color: theme.colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              '"${searchState.query}"에 대한 검색 결과가 없습니다',
              style: theme.textTheme.bodyLarge?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: searchState.results.length + (searchState.hasMore ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == searchState.results.length) {
          // Load more trigger
          if (!searchState.isLoading) {
            ref.read(bookSearchProvider.notifier).loadMore();
          }
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),
          );
        }

        final book = searchState.results[index];
        return _BookSearchResultCard(
          book: book,
          onTap: () => _addBookToLibrary(book),
        );
      },
    );
  }

  void _search(String query) {
    if (query.trim().isEmpty) return;
    ref.read(bookSearchProvider.notifier).search(query.trim());
  }

  Future<void> _addBookToLibrary(Book book) async {
    final result = await showDialog<BookStatus>(
      context: context,
      builder: (context) => _AddBookDialog(book: book),
    );

    if (result != null && mounted) {
      final success = await ref.read(userLibraryProvider.notifier).addBook(
        bookId: book.id,
        status: result,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              success ? '책이 서재에 추가되었습니다' : '책을 추가하지 못했습니다',
            ),
          ),
        );

        if (success) {
          Navigator.of(context).pop();
        }
      }
    }
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search,
            size: 64,
            color: theme.colorScheme.outline,
          ),
          const SizedBox(height: 16),
          Text(
            '책을 검색해보세요',
            style: theme.textTheme.bodyLarge?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '제목, 저자, ISBN으로 검색할 수 있어요',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _BookSearchResultCard extends StatelessWidget {
  final Book book;
  final VoidCallback onTap;

  const _BookSearchResultCard({
    required this.book,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Book cover
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: book.coverImageUrl != null
                    ? Image.network(
                        book.coverImageUrl!,
                        width: 60,
                        height: 90,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => _DefaultBookCover(),
                      )
                    : _DefaultBookCover(),
              ),
              const SizedBox(width: 12),
              // Book info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      book.title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      book.author,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                    if (book.publisher != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        book.publisher!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.outline,
                        ),
                      ),
                    ],
                    if (book.totalPages != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${book.totalPages}페이지',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.outline,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              // Add button
              IconButton(
                icon: Icon(
                  Icons.add_circle_outline,
                  color: theme.colorScheme.primary,
                ),
                onPressed: onTap,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DefaultBookCover extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 60,
      height: 90,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(
        Icons.book,
        size: 32,
        color: Theme.of(context).colorScheme.outline,
      ),
    );
  }
}

class _AddBookDialog extends StatelessWidget {
  final Book book;

  const _AddBookDialog({required this.book});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return AlertDialog(
      title: const Text('서재에 추가'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            book.title,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            book.author,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 16),
          const Text('어느 목록에 추가하시겠어요?'),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('취소'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, BookStatus.wishlist),
          child: const Text('읽고 싶은 책'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context, BookStatus.reading),
          child: const Text('읽는 중'),
        ),
      ],
    );
  }
}
