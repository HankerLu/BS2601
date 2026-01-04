import os
import re
from PIL import Image

# 文件路径
gif_path = 'cat_lick.gif'
png_path = 'cat_lick.png'
html_path = 'index.html'

def analyze_and_sync():
    print("--- 开始分析素材 ---")

    # 1. 分析 GIF 获取动画信息
    if not os.path.exists(gif_path):
        print(f"错误: 找不到 {gif_path}")
        return

    try:
        with Image.open(gif_path) as gif:
            # 获取帧数
            frame_count = getattr(gif, 'n_frames', 1)
            # 获取每帧持续时间 (毫秒)，默认100ms
            duration_per_frame = gif.info.get('duration', 100)
            # 获取 GIF 原始尺寸 (即单帧尺寸)
            gif_width, gif_height = gif.size
            
            # 计算 FPS (1000ms / duration)
            fps = int(1000 / duration_per_frame) if duration_per_frame > 0 else 10
            
            print(f"[GIF 分析结果]")
            print(f"  - 帧数: {frame_count}")
            print(f"  - 单帧尺寸: {gif_width}x{gif_height}")
            print(f"  - 单帧时长: {duration_per_frame}ms")
            print(f"  - 估算 FPS: {fps}")
            
            # 尝试计算列数
            if 'total_width' in locals():
                cols = int(total_width / gif_width)
                rows = int(total_height / gif_height)
                print(f"  - 推断布局: {cols}列 x {rows}行 (Grid)")
            else:
                cols = frame_count # 默认单行
                print("  - 无法读取PNG尺寸，默认假设单行")

    except Exception as e:
        print(f"读取 GIF 失败: {e}")
        return

    # 2. 分析 PNG (仅用于验证，失败不影响同步)
    try:
        # 增加图片像素限制
        Image.MAX_IMAGE_PIXELS = None
        if os.path.exists(png_path):
            with Image.open(png_path) as png:
                total_width, total_height = png.size
                print(f"[PNG 分析结果]")
                print(f"  - 总尺寸: {total_width}x{total_height}")
                
                # 在这里重新计算，因为上面可能还没拿到 total_width
                if 'gif_width' in locals():
                     cols = int(total_width / gif_width)
                     rows = int(total_height / gif_height)
                     print(f"  - 验证布局: {cols}列 x {rows}行")
                
    except Exception as e:
        print(f"PNG 读取跳过: {e}")

    # 3. 同步到 HTML 文件
    if not os.path.exists(html_path):
        print(f"错误: 找不到 {html_path}")
        return

    print("--- 正在同步到 HTML ---")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # 同步帧数
    html_content = re.sub(r'(id="frameCount" value=")\d+(")', f'\g<1>{frame_count}\g<2>', html_content)
    # 同步FPS
    html_content = re.sub(r'(id="fps" value=")\d+(")', f'\g<1>{fps}\g<2>', html_content)
    # 同步列数 (如果有这个input)
    if 'cols' in locals():
        # 如果HTML里还没这个input，可能需要先手动添加，或者这里只做替换
        html_content = re.sub(r'(id="colCount" value=")\d+(")', f'\g<1>{cols}\g<2>', html_content)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"成功! 已将帧数({frame_count})和FPS({fps})写入 {html_path}")

if __name__ == "__main__":
    analyze_and_sync()

