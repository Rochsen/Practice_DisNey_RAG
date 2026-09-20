"""
utils 模块，包含一些常用的工具函数
"""

from .imageEncode import parseBase64Image
from .embedding import get_multiModal_embedding


if __name__ == "__main__":
    # 测试 parseBase64Image 函数
    test_parseBase64Image = parseBase64Image(
        "D:\\project\\MyPratice\\Practice_DisNey_RAG\\disney_knowledge_base\\1-产品与服务详情\\迪士尼邮轮价格6.jpeg"
    )
    print(test_parseBase64Image)

    # 测试 get_multiModal_embedding 函数
    test_get_multiModal_embedding = get_multiModal_embedding(
        test_parseBase64Image, type="image"
    )
    print(test_get_multiModal_embedding)
