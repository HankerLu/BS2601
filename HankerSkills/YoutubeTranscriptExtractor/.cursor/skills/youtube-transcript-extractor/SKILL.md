---
name: youtube-transcript-extractor
description: 提取YouTube视频字幕/文案，支持自动生成字幕和手动上传字幕，适用于视频内容分析、文案整理、翻译准备等场景
dependency:
  python:
    - youtube-transcript-api>=0.6.2
---

# YouTube 字幕提取器

## 任务目标
- 本 Skill 用于:提取 YouTube 视频的字幕文本内容
- 能力包含:获取自动生成字幕、获取手动上传字幕、支持多语言选择
- 触发条件:用户请求提取 YouTube 视频字幕、分析视频内容、整理视频文案

## 前置准备
- 依赖说明:
  ```
  youtube-transcript-api>=0.6.2
  ```

## 操作步骤
- 标准流程:
  1. **获取视频链接**
     - 确认用户提供的是有效的 YouTube 视频 URL
     - URL 格式示例: https://www.youtube.com/watch?v=VIDEO_ID
  
  2. **提取字幕**
     - 调用 `scripts/extract_transcript.py` 获取字幕文本
     - 输入参数:
       - `video_url`: YouTube 视频链接（必需）
       - `language`: 语言代码（可选，如 'zh', 'en'，默认选择可用的首选语言）
       - `include_timestamps`: 是否包含时间戳（可选，默认 False）
     - 输出:字幕文本内容或错误信息
  
  3. **处理结果**
     - 成功:返回格式化的字幕文本
     - 失败:根据错误类型提示用户（无字幕、地区限制、视频不可用等）

- 可选分支:
  - **多语言字幕**:当视频包含多种语言字幕时，优先选择指定的语言，否则选择第一个可用字幕
  - **字幕类型优先级**:手动上传字幕 > 自动生成字幕

## 资源索引
- 必要脚本:见 [scripts/extract_transcript.py](scripts/extract_transcript.py)(用途与参数:提取 YouTube 视频字幕，支持多语言和时间戳选项)
- 领域参考:见 [references/usage-guide.md](references/usage-guide.md)(何时读取:需要了解详细使用方法、错误处理和语言代码列表时)

## 注意事项
- 部分视频可能无字幕或受地区限制，此时脚本会返回错误提示
- 建议先尝试不指定 language 参数，让脚本自动选择可用字幕
- 如需精确时间信息，可启用 include_timestamps 参数
- 提取的字幕为纯文本格式，已移除 XML 标签和格式符号

## 使用示例
**示例 1: 提取中文字幕**
```python
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --language "zh"
```

**示例 2: 提取带时间戳的英文字幕**
```python
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --language "en" \
  --include_timestamps
```

**示例 3: 自动选择可用字幕**
```python
python scripts/extract_transcript.py \
  --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```
