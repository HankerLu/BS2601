"""
WebP Animation Merger Tool
--------------------------
此脚本用于将两个 WebP 动画按顺序拼接成一个新的 WebP 文件。
常用于制作 "正放 + 倒放" 的循环动画，以解决首尾帧跳变问题。

Dependencies:
    pip install Pillow

Usage:
    python merge_blink.py <file1> <file2> <output_file>

Arguments:
    file1       : 第一个 WebP 文件路径 (例如: 动作开始部分)
    file2       : 第二个 WebP 文件路径 (例如: 动作结束或倒放部分)
    output_file : 输出的合并后 WebP 文件路径

Example:
    python merge_blink.py cat_blink.webp cat_blink_reverse.webp cat_blink_loop.webp
"""

from PIL import Image, ImageSequence
import os
import argparse
import sys

def merge_webps(file1, file2, output_file):
    if not os.path.exists(file1):
        print(f"Error: File {file1} not found.")
        return
    if not os.path.exists(file2):
        print(f"Error: File {file2} not found.")
        return

    print(f"Loading {file1}...")
    im1 = Image.open(file1)
    print(f"Loading {file2}...")
    im2 = Image.open(file2)

    frames = []
    durations = []

    # Helper to process frames
    def process_frames(im, source_name):
        count = 0
        for frame in ImageSequence.Iterator(im):
            # Copy frame to ensure we have the data
            f = frame.copy()
            frames.append(f)
            # Duration in milliseconds
            d = frame.info.get('duration', 100) 
            durations.append(d)
            count += 1
        print(f"Added {count} frames from {source_name}")

    process_frames(im1, file1)
    process_frames(im2, file2)

    if not frames:
        print("No frames found!")
        return

    print(f"Total frames: {len(frames)}")
    print(f"Saving to {output_file}...")

    # Save
    frames[0].save(
        output_file,
        format='WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        minimize_size=True
    )
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge two WebP files sequentially into a new WebP file.")
    parser.add_argument("file1", nargs='?', help="First WebP file (e.g. forward animation)")
    parser.add_argument("file2", nargs='?', help="Second WebP file (e.g. reverse animation)")
    parser.add_argument("output", nargs='?', help="Output WebP filename")

    args = parser.parse_args()

    # Backwards compatibility / Default behavior if no args provided, 
    # but strictly following user request for CLI args.
    # If args are missing, show help or run default if files exist? 
    # User said "allow it to specify via command line", implies optional or required.
    # I will make them required effectively, but to be nice during dev I'll check.
    
    if args.file1 and args.file2 and args.output:
        merge_webps(args.file1, args.file2, args.output)
    else:
        # If run without arguments, check if we should run the default blink merge as a fallback
        # or just print help. Given the user's request is about *enabling* CLI, 
        # let's print help if not provided.
        if len(sys.argv) == 1:
            print("Usage example: python merge_blink.py cat_blink.webp cat_blink_reverse.webp cat_blink_loop.webp")
            parser.print_help()
        else:
            parser.print_help()
