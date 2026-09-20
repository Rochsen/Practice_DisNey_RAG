"""
author: Rochsen
date: 2026-09-20
desc: 向量化工具
"""

import dashscope
import os
from dotenv import load_dotenv
from http import HTTPStatus


# 加载 .env 文件
load_dotenv()

# 设置 dashscope
dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

# 读取 API Key
embedding_api_key = os.environ.get("DASHSCOPE_API_KEY")


def get_multiModal_embedding(
    input_content, model="tongyi-embedding-vision-plus", type="text"
):
    """多模态 embedding 调用方法 (dashscope版本)

    Args:
        input_content (str): 输入内容 可以是文本、base64编码的图片、视频url
        model (str, optional): 模型名称
        type (str, optional): 输入内容的类型
    Returns:
        list: 向量列表
    """
    # 检查API密钥是否存在
    if not embedding_api_key:
        raise Exception("DASHSCOPE_API_KEY 环境变量未设置")

    # 构建输入格式
    if type == "text":
        construct_input = [{"text": input_content}]
    elif type == "image":
        construct_input = [{"image": input_content}]
    elif type == "video":
        construct_input = [{"video": input_content}]
    else:
        raise Exception(f"暂不支持{type}类型的向量")

    # 调用接口
    resp = dashscope.MultiModalEmbedding.call(
        api_key=embedding_api_key,
        model=model,
        input=construct_input,
    )

    if resp.status_code != HTTPStatus.OK:
        raise Exception(f"Dashscope 向量化接口调用异常: {resp.message}")

    return resp.output["embeddings"][0]["embedding"]
