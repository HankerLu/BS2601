#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图文卡片生成脚本 - 现代极简版
根据照片和诗歌文本生成精美的图文卡片
支持极简杂志风和清新ins风两种现代风格
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


def hex_to_rgb(hex_color):
    """十六进制颜色转RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_modern_font(size, bold=False):
    """获取现代无衬线字体（按优先级）"""
    font_paths = [
        # macOS - 苹方
        "/System/Library/Fonts/PingFang.ttc",
        # Windows - 微软雅黑
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\msyhbd.ttc" if bold else "C:\\Windows\\Fonts\\msyh.ttc",
        # Linux - 思源黑体
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    # 使用默认字体
    print("警告：未找到合适的中文字体，使用默认字体", file=sys.stderr)
    return ImageFont.load_default()


def fix_image_orientation(img):
    """修复图片方向（处理EXIF信息）"""
    try:
        from PIL import ExifTags
        exif = img._getexif()
        if exif is not None:
            for tag, value in exif.items():
                if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == 'Orientation':
                    orientation = value
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
                    break
    except:
        pass
    return img


def create_minimal_card(image_path, poem_text, poem_title="无题", output_path="card.png"):
    """创建极简杂志风卡片"""
    # 读取并处理图片
    img = Image.open(image_path)
    img = fix_image_orientation(img)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 图片占据上半部分，调整大小
    target_width = 600
    if img.width > target_width:
        ratio = target_width / img.width
        new_size = (target_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # 创建画布（纯白背景，大量留白）
    padding = 80
    canvas_width = img.width + padding * 2
    canvas_height = img.height + padding * 2 + 300  # 额外300px给文字区域
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#FFFFFF')
    draw = ImageDraw.Draw(canvas)
    
    # 粘贴图片（居中偏上）
    img_x = (canvas_width - img.width) // 2
    img_y = padding
    canvas.paste(img, (img_x, img_y))
    
    # 分隔线（极细灰线）
    line_y = img_y + img.height + 40
    draw.line([(padding + 20, line_y), (canvas_width - padding - 20, line_y)],
              fill='#E2E8F0', width=1)
    
    # 标题（超大字号，黑色）
    title_font = get_modern_font(56, bold=True)
    title_bbox = draw.textbbox((0, 0), poem_title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (canvas_width - title_width) // 2
    title_y = line_y + 50
    draw.text((title_x, title_y), poem_title, fill='#1A1A1A', font=title_font)
    
    # 诗歌正文（小字号，灰色，大量留白）
    poem_font = get_modern_font(22)
    lines = poem_text.split('\n')
    line_height = 36
    text_start_y = title_y + 100  # 增加标题与诗正文的间距
    
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=poem_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (canvas_width - line_width) // 2
        line_y = text_start_y + i * line_height
        draw.text((line_x, line_y), line, fill='#666666', font=poem_font)
    
    # 极简装饰（右下角小圆点）
    dot_x = canvas_width - padding - 20
    dot_y = canvas_height - padding - 20
    draw.ellipse([(dot_x, dot_y), (dot_x + 6, dot_y + 6)], fill='#A0AEC0')
    
    # 保存卡片
    canvas.save(output_path, 'PNG', quality=95)
    return output_path


def create_instagram_card(image_path, poem_text, poem_title="无题", output_path="card.png"):
    """创建清新ins风卡片"""
    # 读取并处理图片
    img = Image.open(image_path)
    img = fix_image_orientation(img)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 调整图片大小
    target_width = 350
    if img.width > target_width:
        ratio = target_width / img.width
        new_size = (target_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # 创建渐变背景（淡蓝到更淡的蓝）
    bg_color_top = hex_to_rgb('#F0F7FF')
    bg_color_bottom = hex_to_rgb('#E6F2FF')
    
    # 计算画布大小
    padding = 60
    canvas_width = max(img.width + 300, 500)
    canvas_height = max(img.height + 250, 600)
    
    # 创建渐变背景
    canvas = Image.new('RGB', (canvas_width, canvas_height), '#FFFFFF')
    draw = ImageDraw.Draw(canvas)
    
    # 绘制渐变背景
    for y in range(canvas_height):
        ratio = y / canvas_height
        r = int(bg_color_top[0] + (bg_color_bottom[0] - bg_color_top[0]) * ratio)
        g = int(bg_color_top[1] + (bg_color_bottom[1] - bg_color_top[1]) * ratio)
        b = int(bg_color_top[2] + (bg_color_bottom[2] - bg_color_top[2]) * ratio)
        draw.line([(0, y), (canvas_width, y)], fill=(r, g, b), width=1)
    
    draw = ImageDraw.Draw(canvas)
    
    # 图片圆角处理
    corner_radius = 20
    img_rounded = Image.new('RGB', img.size, '#FFFFFF')
    mask = Image.new('L', img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), img.size], radius=corner_radius, fill=255)
    img_rounded.paste(img, (0, 0), mask)
    
    # 柔和阴影
    shadow = Image.new('RGBA', img_rounded.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([(0, 0), img_rounded.size], radius=corner_radius,
                                 fill=(0, 0, 0, 20))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    
    # 粘贴图片（偏心放置，左上）
    img_x = padding
    img_y = padding + 40
    canvas.paste(shadow, (img_x + 8, img_y + 8), shadow)
    canvas.paste(img_rounded, (img_x, img_y), mask)
    
    # emoji装饰（根据季节/情感，这里用通用的花）
    emoji_font = get_modern_font(36)
    emoji = "🌸"
    emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
    draw.text((img_x + img.width - 40, img_y - 20), emoji, font=emoji_font)
    
    # 标题（左对齐，深蓝）
    title_font = get_modern_font(34, bold=True)
    title_x = img_x + img.width + 40
    title_y = img_y + 20
    draw.text((title_x, title_y), poem_title, fill='#2D3748', font=title_font)
    
    # 诗歌正文（左对齐，灰色）
    poem_font = get_modern_font(24)
    lines = poem_text.split('\n')
    line_height = 38
    text_start_y = title_y + 60
    
    for i, line in enumerate(lines):
        line_y = text_start_y + i * line_height
        draw.text((title_x, line_y), line, fill='#718096', font=poem_font)
    
    # 底部装饰（emoji）
    emoji_bottom = "🍂"
    emoji_bottom_font = get_modern_font(28)
    draw.text((title_x, canvas_height - padding - 40), emoji_bottom,
              font=emoji_bottom_font)
    
    # 保存卡片
    canvas.save(output_path, 'PNG', quality=95)
    return output_path


def main():
    parser = argparse.ArgumentParser(description='生成现代精美图文卡片')
    parser.add_argument('--image-path', type=str, required=True,
                        help='原始照片路径')
    parser.add_argument('--poem-text', type=str, required=True,
                        help='诗歌文本')
    parser.add_argument('--poem-title', type=str, default='无题',
                        help='诗词标题（默认：无题）')
    parser.add_argument('--poem-type', type=str, choices=['tang', 'ci'],
                        default='tang', help='诗词类型（tang或ci，默认：tang）')
    parser.add_argument('--style', type=str, choices=['minimal', 'instagram'],
                        default='minimal',
                        help='卡片风格（minimal=极简杂志风，instagram=清新ins风，默认：minimal）')
    parser.add_argument('--output-path', type=str, default='card.png',
                        help='输出图片路径（默认：card.png）')
    
    args = parser.parse_args()
    
    # 检查输入图片是否存在
    if not os.path.exists(args.image_path):
        print(f"错误：图片文件不存在：{args.image_path}", file=sys.stderr)
        sys.exit(1)
    
    # 根据风格生成卡片
    try:
        if args.style == 'minimal':
            print("正在生成极简杂志风卡片...", file=sys.stderr)
            output_path = create_minimal_card(
                args.image_path,
                args.poem_text,
                args.poem_title,
                args.output_path
            )
        else:  # instagram
            print("正在生成清新ins风卡片...", file=sys.stderr)
            output_path = create_instagram_card(
                args.image_path,
                args.poem_text,
                args.poem_title,
                args.output_path
            )
        
        print(f"卡片已生成：{output_path}")
        return output_path
        
    except Exception as e:
        print(f"错误：生成卡片失败 - {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
