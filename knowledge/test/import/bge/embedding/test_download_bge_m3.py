import os
from modelscope import snapshot_download

# 替换成你的目标保存路径
target_dir = os.path.expanduser("~/Developer/Models/bge-m3")

model_path = snapshot_download(
    model_id="BAAI/bge-m3",
    local_dir=target_dir
)

print("模型文件完整路径：", model_path)
