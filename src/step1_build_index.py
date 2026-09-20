from utils import parseBase64Image
from utils import get_multiModal_embedding


def get_text_embedding(input_text):
    """获取文本向量"""
    if not input_text:
        raise Exception("输入文本不能为空")
    return get_multiModal_embedding(input_text, type="text")


def get_image_embedding(input_image):
    """获取图片向量"""
    if not input_image:
        raise Exception("输入图片不能为空")
    base64_image = parseBase64Image(input_image)
    return get_multiModal_embedding(base64_image, type="image")
