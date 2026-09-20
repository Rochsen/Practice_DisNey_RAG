"""
知识切片策略
"""

import json
import os
import re
from openai import OpenAI


# 固定长度切片
def fixed_length_split(text, chunk_size=512, overlap=50):
    """将文本按固定长度切片
    Args:
        text (str): 输入文本
        chunk_size (int, optional): 每个切片的长度. Defaults to 100.
        overlap (int, optional): 每个切片的重叠长度. Defaults to 50.
    Returns:
        list: 切片后的文本列表
    """
    chunks = []
    start = 0
    while start <= len(text):
        # 计算切片结束位置
        end = start + chunk_size

        # 找出最近的句子边界，确保切片的语义完整性
        if end < len(text):
            # 在有效范围内寻找最靠近切片末尾的句子结束符
            boundary = max(start, end - overlap)
            end_chars = ".!?。！？"
            last_sep = max(
                (text.rfind(c, boundary, end) for c in end_chars), default=-1
            )
            if last_sep != -1:
                end = last_sep + 1

        # 切片
        chunk = text[start:end]
        if chunk.strip():
            # chunk = re.sub(r"\s+", "", chunk)
            chunks.append(chunk.strip())

        # 更新起始位置
        start = end - overlap

    return chunks


def semantic_chunking(text, max_chunk_size=512):
    """基于句子边界的切片 - 按句子分割
    Args:
        text (str): 输入文本
        max_chunk_size (int, optional): 每个切片的最大长度. Defaults to 512.
    Returns:
        list: 切片后的文本列表
    """
    # 使用正则表达式分割句子
    sentences = re.split(r"[.!?。！？\n]+", text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 如果当前句子加入后超过最大长度，保存当前块
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence

    # 添加最后一个块
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def llm_chunking(text, max_chunk_size=512):
    """使用LLM进行语义切片"""
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("警告: 未设置 DASHSCOPE_API_KEY 环境变量，将使用基础语义切片")
        return semantic_chunking(text, max_chunk_size)

    client = OpenAI(api_key=api_key, base_url=os.environ.get("DEEPSEEK_API_URL"))

    prompt = f"""
请将以下文本按照语义完整性进行切片，每个切片不超过{max_chunk_size}字符。
要求：
1. 保持语义完整性
2. 在自然的分割点切分
3. 返回JSON格式的切片列表，格式如下：
{{
  "chunks": [
    "第一个切片内容",
    "第二个切片内容",
    ...
  ]
}}

文本内容：
{text}

请返回JSON格式的切片列表：
"""

    try:
        print("正在调用LLM进行语义切片...")
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的文本切片助手。请严格按照JSON格式返回结果，不要添加任何额外的标记。",
                },
                {"role": "user", "content": prompt},
            ],
        )

        result = response.choices[0].message.content or ""
        print(f"LLM返回结果: {result[:200]}...")

        # 清理结果，移除可能的Markdown代码块标记
        cleaned_result = result.strip()
        if cleaned_result.startswith("```"):
            # 移除开头的 ```json 或 ```
            cleaned_result = re.sub(r"^```(?:json)?\s*", "", cleaned_result)
        if cleaned_result.endswith("```"):
            # 移除结尾的 ```
            cleaned_result = re.sub(r"\s*```$", "", cleaned_result)

        # 解析JSON结果
        chunks_data = json.loads(cleaned_result)

        # 处理不同的返回格式
        if "chunks" in chunks_data:
            return chunks_data["chunks"]
        elif "slice" in chunks_data:
            # 如果返回的是包含"slice"字段的列表
            if isinstance(chunks_data, list):
                return [
                    item.get("slice", "") for item in chunks_data if item.get("slice")
                ]
            else:
                return [chunks_data["slice"]]
        else:
            # 如果直接返回字符串列表
            if isinstance(chunks_data, list):
                return chunks_data
            else:
                print(f"意外的返回格式: {chunks_data}")
                return []

    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"原始结果: {result}")
        # 尝试手动解析
        try:
            # 尝试提取JSON部分
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                chunks_data = json.loads(json_str)
                if "chunks" in chunks_data:
                    return chunks_data["chunks"]
        except Exception as e:
            pass

    except Exception as e:
        print(f"LLM切片失败: {e}")


def hierarchical_chunking(text, target_size=512, preserve_hierarchy=True):
    """层次切片 - 基于文档结构层次进行切片"""
    chunks = []

    # 定义层次标记
    hierarchy_markers = {
        "title1": ["# ", "标题1：", "一、", "1. "],
        "title2": ["## ", "标题2：", "二、", "2. "],
        "title3": ["### ", "标题3：", "三、", "3. "],
        "paragraph": ["\n\n", "\n"],
    }

    # 分割文本为行
    lines = text.split("\n")
    current_chunk = ""
    current_hierarchy = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测当前行的层次级别
        line_level = None
        for level, markers in hierarchy_markers.items():
            for marker in markers:
                if line.startswith(marker):
                    line_level = level
                    break
            if line_level:
                break

        # 如果没有检测到层次标记，默认为段落
        if not line_level:
            line_level = "paragraph"

        # 判断是否需要开始新的切片
        should_start_new_chunk = False

        # 1. 如果遇到更高级别的标题，开始新切片
        if preserve_hierarchy and line_level in ["title1", "title2"]:
            should_start_new_chunk = True

        # 2. 如果当前切片长度超过目标大小
        if len(current_chunk) + len(line) > target_size and current_chunk.strip():
            should_start_new_chunk = True

        # 3. 如果遇到段落分隔符且当前切片已经足够长
        if line_level == "paragraph" and len(current_chunk) > target_size * 0.8:
            should_start_new_chunk = True

        # 开始新切片
        if should_start_new_chunk and current_chunk.strip():
            chunks.append(current_chunk.strip())
            current_chunk = ""
            current_hierarchy = []

        # 添加当前行到切片
        if current_chunk:
            current_chunk += "\n" + line
        else:
            current_chunk = line

        # 更新层次信息
        if line_level != "paragraph":
            current_hierarchy.append(line_level)

    # 处理最后一个切片
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def sliding_window_chunking(text, window_size=512, step_size=256):
    """滑动窗口切片"""
    chunks = []

    for i in range(0, len(text), step_size):
        chunk = text[i : i + window_size]

        if len(chunk.strip()) > 0:
            chunks.append(chunk.strip())

    return chunks


def adaptive_chunking(text, target_size=512, tolerance=0.2):
    """自适应切片 - 根据内容自适应调整"""
    chunks = []

    # 按段落分割
    paragraphs = text.split("\n\n")

    current_chunk = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 如果当前段落加入后超过目标大小
        if len(current_chunk) + len(paragraph) > target_size * (1 + tolerance):
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += " " + paragraph if current_chunk else paragraph

    # 处理最后一个块
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


if __name__ == "__main__":
    # 测试文本 - 普通文本
    text = """
    迪士尼乐园提供多种门票类型以满足不同游客需求。一日票是最基础的门票类型，可在购买时选定日期使用，价格根据季节浮动。两日票需要连续两天使用，总价比购买两天单日票优惠约9折。特定日票包含部分节庆活动时段，需注意门票标注的有效期限。

    购票渠道以官方渠道为主，包括上海迪士尼官网、官方App、微信公众号及小程序。第三方平台如飞猪、携程等合作代理商也可购票，但需认准官方授权标识。所有电子票需绑定身份证件，港澳台居民可用通行证，外籍游客用护照，儿童票需提供出生证明或户口本复印件。

    生日福利需在官方渠道登记，可获赠生日徽章和甜品券。半年内有效结婚证持有者可购买特别套票，含皇家宴会厅双人餐。军人优惠现役及退役军人凭证件享8折，需至少提前3天登记审批。
    """

    # 测试文本 - 包含层次结构
    text_hierarchy = """
    # 迪士尼乐园门票指南

    ## 一、门票类型介绍

    ### 1. 基础门票类型
    迪士尼乐园提供多种门票类型以满足不同游客需求。一日票是最基础的门票类型，可在购买时选定日期使用，价格根据季节浮动。两日票需要连续两天使用，总价比购买两天单日票优惠约9折。特定日票包含部分节庆活动时段，需注意门票标注的有效期限。

    ### 2. 特殊门票类型
    年票适合经常游玩的游客，提供更多优惠和特权。VIP门票包含快速通道服务，可减少排队时间。团体票适用于10人以上团队，享受团体折扣。

    ## 二、购票渠道与流程

    ### 1. 官方购票渠道
    购票渠道以官方渠道为主，包括上海迪士尼官网、官方App、微信公众号及小程序。这些渠道提供最可靠的服务和最新的票务信息。

    ### 2. 第三方平台
    第三方平台如飞猪、携程等合作代理商也可购票，但需认准官方授权标识。建议优先选择官方渠道以确保购票安全。

    ### 3. 证件要求
    所有电子票需绑定身份证件，港澳台居民可用通行证，外籍游客用护照，儿童票需提供出生证明或户口本复印件。

    ## 三、入园须知

    ### 1. 入园时间
    乐园通常在上午8:00开园，晚上8:00闭园，具体时间可能因季节和特殊活动调整。建议提前30分钟到达园区。

    ### 2. 安全检查
    入园前需要进行安全检查，禁止携带危险物品、玻璃制品等。建议轻装简行，提高入园效率。

    ### 3. 园区服务
    园区内提供寄存服务、轮椅租赁、婴儿车租赁等服务，可在游客服务中心咨询详情。

    生日福利需在官方渠道登记，可获赠生日徽章和甜品券。半年内有效结婚证持有者可购买特别套票，含皇家宴会厅双人餐。军人优惠现役及退役军人凭证件享8折，需至少提前3天登记审批。
    """

    print("\n=== 固定长度切片测试 ===")
    chunks = fixed_length_split(text, 100, 50)
    print(chunks)

    print("\n=== 句子边界切片测试 ===")
    chunks = semantic_chunking(text, 100)
    print(chunks)

    print("\n=== 层次结构切片测试 ===")
    chunks = hierarchical_chunking(
        text_hierarchy, target_size=300, preserve_hierarchy=True
    )
    print(chunks)

    print("\n=== 自适应切片测试 ===")
    chunks = adaptive_chunking(text, target_size=200, tolerance=0.3)
    print(chunks)

    print("\n=== LLM语义切片测试 ===")
    try:
        chunks = llm_chunking(text, max_chunk_size=300)
        print(f"LLM语义切片生成 {len(chunks)} 个切片:")
        for i, chunk in enumerate(chunks):
            print(f"LLM语义块 {i+1} (长度: {len(chunk)}): {chunk}")
    except Exception as e:
        print(f"LLM切片测试失败: {e}")