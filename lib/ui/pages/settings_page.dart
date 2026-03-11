import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/app_providers.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  late TextEditingController _apiKeyController;

  @override
  void initState() {
    super.initState();
    _apiKeyController = TextEditingController();
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = ref.watch(appSettingsProvider);

    ref.listen(appSettingsProvider, (prev, next) {
      next.whenData((s) {
        if (_apiKeyController.text != s.apiKey) {
          _apiKeyController.text = s.apiKey;
        }
      });
    });

    return settings.when(
      data: (s) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_apiKeyController.text.isEmpty && s.apiKey.isNotEmpty) {
            _apiKeyController.text = s.apiKey;
          }
        });
        return SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '阿里云百炼 API Key',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _apiKeyController,
                obscureText: true,
                decoration: const InputDecoration(
                  hintText: '请输入 API Key',
                ),
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: () {
                  final key = _apiKeyController.text.trim();
                  if (key.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('API Key 不能为空')),
                    );
                    return;
                  }
                  ref.read(appSettingsProvider.notifier).patch((s) => s.copyWith(apiKey: key));
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('已保存')),
                  );
                },
                child: const Text('保存'),
              ),
            ],
          ),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('加载失败: $e')),
    );
  }
}
