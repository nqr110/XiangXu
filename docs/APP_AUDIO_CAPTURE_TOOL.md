# 按应用音频捕获工具接口说明

本目录下的 `AppAudioCapture` 为按进程环回采集的辅助程序，供主程序在「仅收录所选应用」/「排除所选应用」时调用，**不修改系统音量**。

## 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--mode` | `include` 仅收录指定进程；`exclude` 仅排除指定进程 | `--mode include` |
| `--pids` | 进程 ID，逗号分隔。include 时可多个；exclude 时仅第一个生效 | `--pids 1234,5678` |
| `--sample-rate` | 输出采样率，默认 16000 | `--sample-rate 16000` |
| `--channels` | 输出声道数，默认 1 | `--channels 1` |
| `--duration` | 可选。录制秒数，不传则持续输出直到 stdin 关闭或 Ctrl+C | `--duration 5`（测试用） |

## 输出格式

- **stdout**：原始 PCM，16-bit 有符号小端，单声道，默认 16 kHz。
- 无额外头或分包；主程序按块大小（如 3200 字节 = 100ms @ 16kHz）读取。

## 退出码

| 码 | 含义 |
|----|------|
| 0 | 正常结束 |
| 1 | 参数错误（如缺少 --mode/--pids） |
| 2 | 系统不支持进程环回（需 Windows 10 21H2+ / 11） |
| 3 | 未找到目标进程或无法打开会话 |
| 4 | 运行时错误（如设备不可用） |

## 技术依赖

- Windows 进程环回：`ActivateAudioInterfaceAsync` + `VIRTUAL_AUDIO_DEVICE_PROCESS_LOOPBACK`，按进程 ID 包含/排除。
- 不依赖 NAudio 的按设备环回；不修改任何应用的静音或音量。

## 构建与放置

- 使用 .NET 6 SDK：在 `tools/AppAudioCapture` 下执行 `dotnet publish -c Release -r win-x64 --self-contained false`，生成物在 `bin/Release/net6.0/win-x64/publish/`。
- 主程序会在项目根目录、`tools/AppAudioCapture`、可执行文件同目录下查找 `AppAudioCapture.exe`。
