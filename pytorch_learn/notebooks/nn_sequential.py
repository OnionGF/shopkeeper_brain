
import torch
from torch import nn
from torchsummary import summary

x = torch.tensor([[1,2,3],[4,5,6],[7,8,9]]).float()

model = nn.Sequential(
    nn.Linear(3, 4),
    nn.Tanh(),
    nn.Linear(4,4),
    nn.ReLU(),
    nn.Linear(4,2),
    nn.Softmax(dim=-1),
)

# 保存模型参数
# torch.save(model.state_dict(), "model.pth")

#加载模型
state_dict = torch.load("model.pth")
model.load_state_dict(state_dict) # 加载参数（用保存的参数覆盖随机生成的参数）

# 3、向前传播
y = model(x)
print(y)





# summary(model, input_size=(3, ), device="cpu", batch_size=20)


