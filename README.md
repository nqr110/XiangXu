# 响叙 · 实时语音识别与翻译

基于 Flutter 的 Windows 桌面应用，使用阿里云百炼 gummy-realtime-v1 实现系统音频的实时语音识别与翻译，并支持可配置的字幕悬浮窗。

---

## 环境要求

- **Flutter**：稳定版，支持 Windows 桌面（建议 3.22+）
- **平台**：当前仅支持 Windows（后续可扩展其他桌面平台）
- **阿里云百炼**：需在[百炼控制台](https://bailian.console.aliyun.com/)开通服务并获取 API Key

---

## 开发者指南

### 1. 克隆与依赖

```bash
git clone <仓库地址>
cd XiangXu
flutter pub get
```

### 2. 调试运行

**命令行运行（推荐）：**

```bash
# 在项目根目录执行，默认连接 Windows 设备
flutter run -d windows
```

**指定设备：**

```bash
# 查看可用设备
flutter devices

# 指定 Windows 运行
flutter run -d windows
```

**热重载：** 运行中在终端按 `r` 热重载、按 `R` 热重启。

**调试信息：** 应用内打开「调试信息」页面可查看 WebSocket 连接、音频与识别状态等日志，支持复制到剪贴板。

**Windows 控制台说明：** 运行若出现大量 `accessibility_bridge` / `AXTree` 相关报错，多为 Flutter 引擎在 Windows 上的已知问题，可忽略；一般不影响功能。若出现 `Lost connection to device`，可先升级到最新稳定版 Flutter（`flutter upgrade`）再试。

### 3. 静态分析与测试

```bash
# 代码分析
flutter analyze

# 运行测试
flutter test
```

### 4. 打包发布

**构建 Windows  release：**

```bash
flutter build windows
```

产物目录：`build\windows\x64\runner\Release\`  
其中包含：

- `xiangxu_flutter.exe`：主程序
- `flutter_windows.dll`、各插件 DLL、`data\` 等：运行依赖

**发布给用户：** 将整个 `Release` 目录打包（如 zip），用户解压后直接运行 `xiangxu_flutter.exe` 即可。

**自定义版本号：**

```bash
flutter build windows --build-name=1.0.1 --build-number=2
```

### 5. 首次使用配置

1. 运行应用后进入「设置」页，填写阿里云百炼 **API Key** 并保存。
2. 在「详细配置」中按需选择识别/翻译模式、源语言与目标语言（默认：自动 → 中文）。
3. 在「字幕设置」中可开启字幕小窗并调整位置、样式等。

---

## 项目结构简述

| 路径 | 说明 |
|------|------|
| `lib/main.dart` | 应用入口，多窗口时根据参数启动主窗口或字幕窗 |
| `lib/ui/` | 主界面：主导航壳与各子页面（翻译信息、详细配置、字幕设置等） |
| `lib/overlay/` | 字幕悬浮窗 UI 与窗口创建/通信 |
| `lib/services/` | 阿里云实时服务、配置持久化、系统音频采集（占位） |
| `lib/models/` | 配置、识别结果等数据模型 |
| `lib/providers/` | Riverpod 状态与依赖注入 |
| `windows/` | Windows 原生工程与构建配置 |

---

## 许可证

见 [LICENSE](LICENSE) 文件。
