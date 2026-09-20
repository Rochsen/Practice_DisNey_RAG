import os


def search_all_files(dir_path):
    """递归搜索目录下所有文件
    Args:
        dir_path (str): 目录路径
    Returns:
        list: 所有文件路径列表
    """
    query_fp = [
        os.path.join(root, file)
        for root, _, files in os.walk(dir_path)
        for file in files
    ]
    return query_fp
