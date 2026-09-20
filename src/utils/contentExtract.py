import os
import pymupdf as fitz
from docx import Document as DocxDocument


def parse_docx(file_path):
    """解析 DOCX 文件，提取全部文本和图片
    Args:
        file_path (str): DOCX 文件位置
    Returns:
        list: 包含文本和图片信息的列表
    """
    doc = DocxDocument(file_path)
    all_text = []

    for element in doc.element.body:
        if element.tag.endswith("p"):
            paragraph_text = ""
            for run in element.findall(
                ".//w:t",
                {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"},
            ):
                paragraph_text += run.text if run.text else ""
            if paragraph_text.strip():
                all_text.append(paragraph_text.strip())

        elif element.tag.endswith("tbl"):
            table = [t for t in doc.tables if t._element is element][0]
            if table.rows:
                md_table = []
                header = [cell.text.strip() for cell in table.rows[0].cells]
                md_table.append("| " + " | ".join(header) + " |")
                md_table.append("|" + "---|" * len(header))
                for row in table.rows[1:]:
                    row_data = [cell.text.strip() for cell in row.cells]
                    md_table.append("| " + " | ".join(row_data) + " |")
                all_text.append("\n".join(md_table))

    return "\n".join(all_text)


def parse_pdf(file_path, image_dir):
    """解析 PDF 文件，提取全部文本和图片
    Args:
        file_path (str): PDF 文件位置
        image_dir (str): 图片保存目录
    Returns:
        list: 包含文本和图片信息的列表
    """
    doc = fitz.open(file_path)
    content_chunks = []

    # 提取文本
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        content_chunks.append({"type": "text", "content": text, "page": page_num + 1})

        # 提取图片
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_path = os.path.join(
                image_dir,
                f"{os.path.basename(file_path)}_p{page_num + 1}_{img_index}.{image_ext}",
            )

            if not os.path.exists(image_path):
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
            
            content_chunks.append(
                {"type": "image", "path": image_path, "page": page_num + 1}
            )

    return content_chunks


if __name__ == "__main__":
    # 测试 DOCX 文件
    file_path = "D:\\project\\MyPratice\\Practice_DisNey_RAG\\disney_knowledge_base\\1-产品与服务详情\\迪士尼产品.docx"
    content_docx = parse_docx(file_path)
    print(content_docx)

    # 测试 PDF 文件
    file_path = "D:\\project\\MyPratice\\Practice_DisNey_RAG\\disney_knowledge_base\\1-产品与服务详情\\迪士尼公司发展分析.pdf"
    content_pdf = parse_pdf(
        file_path,
        image_dir="D:\\project\\MyPratice\\Practice_DisNey_RAG\\disney_knowledge_base\\pdfImagedir",
    )
    print(content_pdf)
