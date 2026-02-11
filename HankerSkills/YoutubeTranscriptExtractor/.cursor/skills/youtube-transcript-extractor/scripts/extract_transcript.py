#!/usr/bin/env python3
"""
YouTube 字幕提取脚本
提取 YouTube 视频的字幕文本内容，支持自动生成字幕和手动上传字幕

用法:
  python extract_transcript.py --video_url <URL> [OPTIONS]

示例:
  python extract_transcript.py --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  python extract_transcript.py --video_url "https://youtu.be/dQw4w9WgXcQ" --language "zh"
"""

import argparse
import re
import sys
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable, TranscriptsDisabled


def extract_video_id(video_url):
    """
    从 YouTube URL 中提取视频 ID
    
    Args:
        video_url: YouTube 视频 URL
    
    Returns:
        视频ID
    
    Raises:
        ValueError: 无法从 URL 中提取视频 ID
    """
    # 支持多种 YouTube URL 格式
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            return match.group(1)
    
    raise ValueError(f"无法从 URL 中提取视频 ID: {video_url}")


def get_best_transcript(transcript_list, language=None):
    """
    从字幕列表中选择最佳字幕
    
    优先级: 手动上传 > 自动生成
    
    Args:
        transcript_list: 字幕列表
        language: 目标语言代码（可选）
    
    Returns:
        选择的字幕对象
    """
    if not transcript_list:
        return None
    
    # 将可迭代对象转换为列表以便多次遍历
    transcript_list = list(transcript_list)
    
    # 如果指定了语言，优先选择该语言
    if language:
        # 先查找手动上传的字幕
        for transcript in transcript_list:
            if transcript.language_code == language and not transcript.is_generated:
                return transcript
        
        # 再查找自动生成的字幕
        for transcript in transcript_list:
            if transcript.language_code == language and transcript.is_generated:
                return transcript
    
    # 没有指定语言或未找到匹配语言时，选择第一个可用的手动字幕
    for transcript in transcript_list:
        if not transcript.is_generated:
            return transcript
    
    # 如果没有手动字幕，选择第一个自动生成的字幕
    return transcript_list[0]


def format_transcript(transcript_data, include_timestamps=False):
    """
    格式化字幕文本
    
    Args:
        transcript_data: 字幕数据列表
        include_timestamps: 是否包含时间戳
    
    Returns:
        格式化后的文本
    """
    lines = []
    for item in transcript_data:
        if include_timestamps:
            # 兼容对象访问和字典访问
            if hasattr(item, 'start'):
                start_time = item.start
                duration = item.duration
                text = item.text
            else:
                start_time = item['start']
                duration = item['duration']
                text = item['text']
                
            timestamp = f"[{start_time:.2f}s - {start_time + duration:.2f}s]"
            lines.append(f"{timestamp} {text}")
        else:
            if hasattr(item, 'text'):
                lines.append(item.text)
            else:
                lines.append(item['text'])
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='提取 YouTube 视频字幕',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  %(prog)s --video_url "https://youtu.be/dQw4w9WgXcQ" --language "zh"
  %(prog)s --video_url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --include_timestamps
        """
    )
    
    parser.add_argument(
        '--video_url',
        type=str,
        required=True,
        help='YouTube 视频 URL（必需）'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default=None,
        help='字幕语言代码（可选，如 "zh" 中文、"en" 英文），默认选择可用字幕'
    )
    
    parser.add_argument(
        '--include_timestamps',
        action='store_true',
        help='是否在输出中包含时间戳'
    )
    
    args = parser.parse_args()
    
    try:
        # 提取视频 ID
        video_id = extract_video_id(args.video_url)
        
        # 创建 API 实例并获取字幕列表
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        
        # 选择最佳字幕
        best_transcript = get_best_transcript(transcript_list, args.language)
        
        if best_transcript:
            # 获取字幕数据
            transcript_data = best_transcript.fetch()
            
            # 格式化并输出字幕
            transcript_text = format_transcript(transcript_data, args.include_timestamps)
            
            # 输出元数据
            language_name = best_transcript.language
            is_generated = "（自动生成）" if best_transcript.is_generated else "（手动上传）"
            
            print(f"视频 ID: {video_id}")
            print(f"字幕语言: {language_name} {is_generated}")
            print(f"字幕类型: {'带时间戳' if args.include_timestamps else '纯文本'}")
            print("-" * 80)
            print(transcript_text)
        else:
            print(f"错误: 视频 {video_id} 没有可用的字幕", file=sys.stderr)
            sys.exit(1)
            
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
        
    except NoTranscriptFound:
        print(f"错误: 视频 {video_id} 没有找到字幕", file=sys.stderr)
        print("提示: 该视频可能没有字幕，或字幕受地区限制", file=sys.stderr)
        sys.exit(1)
        
    except TranscriptsDisabled:
        print(f"错误: 视频 {video_id} 的字幕功能已禁用", file=sys.stderr)
        sys.exit(1)
        
    except VideoUnavailable:
        print(f"错误: 视频 {video_id} 不可用（可能已被删除或设为私密）", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:
        print(f"错误: 提取字幕时发生意外错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
