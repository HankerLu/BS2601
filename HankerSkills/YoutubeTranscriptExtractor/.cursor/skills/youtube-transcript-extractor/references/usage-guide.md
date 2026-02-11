# YouTube 字幕提取器使用指南

## 目录
- [概述](#概述)
- [脚本功能](#脚本功能)
- [参数说明](#参数说明)
- [使用示例](#使用示例)
- [常见语言代码](#常见语言代码)
- [错误处理](#错误处理)

## 概述
本指南说明如何使用 `extract_transcript.py` 脚本提取 YouTube 视频字幕。该脚本支持自动生成字幕和手动上传字幕，并提供多语言和时间戳选项。

## 脚本功能
- 提取 YouTube 视频的字幕文本
- 支持自动生成字幕和手动上传字幕
- 支持多语言字幕选择
- 可选择是否包含时间戳
- 自动选择最佳字幕（优先手动上传）

## 参数说明

### 必需参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--video_url` | string | YouTube 视频 URL，支持多种格式 |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--language` | string | None | 字幕语言代码（如 "zh", "en"），默认选择可用字幕 |
| `--include_timestamps` | flag | False | 是否在输出中包含时间戳 |

## 使用示例

### 基本用法

提取视频的可用字幕（自动选择语言）:
```bash
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### 指定语言

提取中文字幕:
```bash
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --language "zh"
```

提取英文字幕:
```bash
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --language "en"
```

### 包含时间戳

提取带时间戳的字幕:
```bash
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --include_timestamps
```

### 完整示例

提取中文字幕并包含时间戳:
```bash
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --language "zh" \
  --include_timestamps
```

### 支持的 URL 格式

脚本支持以下 YouTube URL 格式:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

## 常见语言代码

| 语言代码 | 语言名称 |
|----------|----------|
| zh | 中文 |
| en | 英语 |
| ja | 日语 |
| ko | 韩语 |
| es | 西班牙语 |
| fr | 法语 |
| de | 德语 |
| pt | 葡萄牙语 |
| ru | 俄语 |
| ar | 阿拉伯语 |

## 错误处理

### 常见错误

| 错误类型 | 原因 | 解决方案 |
|----------|------|----------|
| `无法从 URL 中提取视频 ID` | URL 格式不正确 | 检查 URL 是否为有效的 YouTube 视频 URL |
| `视频 XXX 没有找到字幕` | 视频无字幕或受地区限制 | 尝试其他视频，或使用 VPN 访问 |
| `视频 XXX 不可用` | 视频已被删除或设为私密 | 确认视频是否仍然可用 |
| `提取字幕时发生意外错误` | 网络问题或其他异常 | 检查网络连接，重试操作 |

### 字幕选择策略

脚本按以下优先级选择字幕:
1. 手动上传字幕（指定语言）
2. 自动生成字幕（指定语言）
3. 手动上传字幕（任意语言）
4. 自动生成字幕（任意语言）

### 输出格式

**纯文本输出**:
```
视频 ID: dQw4w9WgXcQ
字幕语言: zh（手动上传）
字幕类型: 纯文本
--------------------------------------------------------------------------------
这是第一句字幕
这是第二句字幕
这是第三句字幕
```

**带时间戳输出**:
```
视频 ID: dQw4w9WgXcQ
字幕语言: zh（手动上传）
字幕类型: 带时间戳
--------------------------------------------------------------------------------
[0.00s - 3.50s] 这是第一句字幕
[3.50s - 6.20s] 这是第二句字幕
[6.20s - 9.80s] 这是第三句字幕
```

## 注意事项

- 部分视频可能无字幕，脚本会返回错误提示
- 地区限制可能影响字幕获取，某些字幕仅在特定地区可用
- 自动生成的字幕可能包含语法错误或识别错误
- 建议优先使用手动上传的字幕以获得更好的质量
