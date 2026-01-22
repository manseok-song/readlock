import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/theme_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('설정'),
      ),
      body: ListView(
        children: [
          _SettingsSection(
            title: '앱 설정',
            children: [
              _ThemeModeTile(themeMode: themeMode),
              const _SettingsTile(
                icon: Icons.notifications_outlined,
                title: '알림 설정',
              ),
              const _SettingsTile(
                icon: Icons.timer_outlined,
                title: '독서 목표',
              ),
              const _SettingsTile(
                icon: Icons.phone_android,
                title: '폰잠금 설정',
              ),
            ],
          ),
          _SettingsSection(
            title: '계정',
            children: [
              const _SettingsTile(
                icon: Icons.person_outline,
                title: '계정 관리',
              ),
              const _SettingsTile(
                icon: Icons.lock_outline,
                title: '비밀번호 변경',
              ),
              const _SettingsTile(
                icon: Icons.link,
                title: '연결된 계정',
              ),
            ],
          ),
          _SettingsSection(
            title: '지원',
            children: [
              const _SettingsTile(
                icon: Icons.help_outline,
                title: '도움말',
              ),
              const _SettingsTile(
                icon: Icons.feedback_outlined,
                title: '피드백 보내기',
              ),
              const _SettingsTile(
                icon: Icons.description_outlined,
                title: '이용약관',
              ),
              const _SettingsTile(
                icon: Icons.privacy_tip_outlined,
                title: '개인정보 처리방침',
              ),
            ],
          ),
          _SettingsSection(
            title: '정보',
            children: [
              const _SettingsTile(
                icon: Icons.info_outline,
                title: '앱 정보',
                trailing: Text('2.0.0'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const _SettingsSection({
    required this.title,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Text(
            title,
            style: theme.textTheme.titleSmall?.copyWith(
              color: theme.colorScheme.primary,
            ),
          ),
        ),
        ...children,
      ],
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsTile({
    required this.icon,
    required this.title,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      trailing: trailing ?? const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}

class _ThemeModeTile extends ConsumerWidget {
  final ThemeMode themeMode;

  const _ThemeModeTile({required this.themeMode});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListTile(
      leading: Icon(_getIcon()),
      title: const Text('테마'),
      trailing: DropdownButton<ThemeMode>(
        value: themeMode,
        underline: const SizedBox.shrink(),
        onChanged: (mode) {
          if (mode != null) {
            ref.read(themeModeProvider.notifier).setThemeMode(mode);
          }
        },
        items: const [
          DropdownMenuItem(
            value: ThemeMode.system,
            child: Text('시스템'),
          ),
          DropdownMenuItem(
            value: ThemeMode.light,
            child: Text('라이트'),
          ),
          DropdownMenuItem(
            value: ThemeMode.dark,
            child: Text('다크'),
          ),
        ],
      ),
    );
  }

  IconData _getIcon() {
    switch (themeMode) {
      case ThemeMode.light:
        return Icons.light_mode;
      case ThemeMode.dark:
        return Icons.dark_mode;
      case ThemeMode.system:
        return Icons.brightness_auto;
    }
  }
}
