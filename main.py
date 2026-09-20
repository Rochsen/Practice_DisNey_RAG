import os


def main():
    dir_path = "disney_knowledge_base"

    # os.walk 直接提供 files 列表，无需再手动遍历子目录
    query_fp = [
        os.path.join(root, file)
        for root, _, files in os.walk(dir_path)
        for file in files
    ]
    for fp in query_fp:
        print(fp)


if __name__ == "__main__":
    main()
