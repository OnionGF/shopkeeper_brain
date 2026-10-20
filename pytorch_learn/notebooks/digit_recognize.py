from pathlib import Path
import sys

import torch
import torch.nn as nn

# 把仓库根目录加入 path，才能 import pytorch_learn.*
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pytorch_learn.common.load_data import get_digital_data

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 1、读取数据
x_train, x_test, y_train, y_test = get_digital_data()

# 2、定义模型
model = nn.Sequential(
    nn.Linear(784, 50),
    nn.ReLU(),

    nn.Linear(50, 100),
    nn.ReLU(),

    nn.Linear(100, 10),
    # nn.Softmax(dim=1) 不需要加Softmax， 因为Softmax和损失整合在一起
)

# 3、加载状态字典
state_dict = torch.load(_DATA_DIR / "nn_example.pt", map_location="cpu", weights_only=True)
model.load_state_dict(state_dict)

# 4、预测
y_pred = model(x_test)

# 5、计算准确率
y_class = torch.argmax(y_pred, dim=-1) # 预测的类别： 最大之所在的下标

# 5.2 计算预测正确的数量
acc_cnt = (y_class == y_test).sum().item()
# y_class.eq(y_class).sum().item()
# torch.sum(y_class == y_test).item()

acc = acc_cnt / len(y_test)

print(f"准确率：{acc:.4f}")

