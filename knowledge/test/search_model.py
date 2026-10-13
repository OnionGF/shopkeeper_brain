import os
from pathlib import Path

# 默认缓存路径
cache_dir = Path(os.path.expanduser("~/.cache/modelscope/hub"))

if not cache_dir.exists():
    print("未找到默认缓存目录，你可能使用了自定义路径")
else:
    print("=== 已下载的 ModelScope 模型列表 ===")
    total_size = 0
    # 遍历机构/作者目录
    for org in cache_dir.iterdir():
        if org.is_dir():
            # 遍历每个模型
            for model in org.iterdir():
                if model.is_dir():
                    # 计算文件夹大小
                    size = sum(f.stat().st_size for f in model.rglob("*") if f.is_file())
                    size_gb = size / 1024 ** 3
                    total_size += size
                    print(f"{org.name}/{model.name}  |  {size_gb:.2f} GB")

    print(f"\n总计占用空间：{total_size / 1024 ** 3:.2f} GB")
