"""
author: Rochsen
date: 2026-09-20
desc: 图片转换为 指定编码 的字符串
"""

import base64
import os


def parseBase64Image(image_path):
    """将图片转换为 base64 编码的字符串

    Args:
        image_path (str): 图片位置
    Returns:
        str: base64 编码的图片字符串
    """
    # 读取图片文件
    with open(image_path, "rb") as f:
        base64_img = base64.b64encode(f.read()).decode("utf-8")

    # 获取图片扩展名
    ext = os.path.splitext(image_path)[1][1:]
    if ext == 'jpg':
        ext = 'jpeg'

    # 拼接成符合Data URI Scheme规范的字符串返回，格式为 data:[图片MIME类型];base64,[base64编码内容]，可直接用于前端<img>标签的src属性等场景
    return f"data:image/{ext};base64,{base64_img}"
