import re
from typing import Tuple, List


def generate_toc_with_anchors(markdown: str) -> Tuple[str, str]:
    """
    为Markdown生成带锚点的目录，并为标题添加id属性
    
    :param markdown: 原始Markdown文本
    :return: (生成的目录内容, 添加了锚点的Markdown内容)
    """
    lines = markdown.split('\n')
    toc_lines = []
    processed_lines = []
    heading_counter = {}
    
    for line in lines:
        # 匹配 ## 级别的标题（不包括 # 一级标题）
        heading_match = re.match(r'^(#{2,6})\s+(.+)$', line)
        
        if heading_match:
            level_marks = heading_match.group(1)
            heading_text = heading_match.group(2).strip()
            level = len(level_marks)
            
            # 移除可能的标记符号（如 *Content-[mm:ss]）
            clean_heading = re.sub(r'\s*\*?Content-\[?\d{1,2}:\d{2}\]?\*?', '', heading_text)
            clean_heading = re.sub(r'\s*\[原片\s*@\s*\d{2}:\d{2}\]\([^)]+\)', '', clean_heading)
            clean_heading = clean_heading.strip()
            
            # 生成唯一的锚点ID
            anchor_base = re.sub(r'[^\w\u4e00-\u9fa5\s-]', '', clean_heading)
            anchor_base = re.sub(r'\s+', '-', anchor_base).lower()
            
            # 处理重复标题
            if anchor_base in heading_counter:
                heading_counter[anchor_base] += 1
                anchor_id = f"{anchor_base}-{heading_counter[anchor_base]}"
            else:
                heading_counter[anchor_base] = 0
                anchor_id = anchor_base
            
            # 为TOC添加条目（仅二级和三级标题）
            if level == 2:
                toc_lines.append(f"- [{clean_heading}](#{anchor_id})")
            elif level == 3:
                toc_lines.append(f"  - [{clean_heading}](#{anchor_id})")
            
            # 为标题添加锚点（使用HTML）
            processed_lines.append(f'{level_marks} <span id="{anchor_id}">{heading_text}</span>')
        else:
            processed_lines.append(line)
    
    toc_content = '\n'.join(toc_lines) if toc_lines else ''
    processed_markdown = '\n'.join(processed_lines)
    
    return toc_content, processed_markdown


def replace_content_markers(markdown: str, video_id: str, platform: str = 'bilibili') -> str:
    """
    替换 *Content-04:16*、Content-04:16 或 Content-[04:16] 为超链接，跳转到对应平台视频的时间位置
    同时移除多余的星号标记
    """
    # 匹配多种形式：*Content-[mm:ss]、*Content-mm:ss、Content-[mm:ss]、Content-mm:ss
    # 修改正则以捕获前导星号
    pattern = r"\*?Content-(?:\[(\d{1,2}):(\d{2})\]|(\d{1,2}):(\d{2}))\*?"

    def replacer(match):
        # 提取分钟和秒
        mm = match.group(1) or match.group(3)
        ss = match.group(2) or match.group(4)
        
        # 确保时间格式为两位数
        mm = mm.zfill(2)
        ss = ss.zfill(2)
        
        total_seconds = int(mm) * 60 + int(ss)

        if platform == 'bilibili':
            url = f"https://www.bilibili.com/video/{video_id}?t={total_seconds}"
        elif platform == 'youtube':
            url = f"https://www.youtube.com/watch?v={video_id}&t={total_seconds}s"
        elif platform == 'douyin':
            url = f"https://www.douyin.com/video/{video_id}"
        else:
            return f"({mm}:{ss})"

        return f" [原片 @ {mm}:{ss}]({url})"

    return re.sub(pattern, replacer, markdown)
