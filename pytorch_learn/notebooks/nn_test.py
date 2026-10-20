
import torch
import torch.nn as nn

class MyModule(nn.Module):
    def __init__(self):
        # 调用父类的init方法
        super().__init__()

        # 定义3个全链接层
        self.linear1 = nn.Linear(3, 4)
        self.linear2 = nn.Linear(4, 4)
        self.out = nn.Linear(4, 2)

    def forward(self, x):
        # 逐层计算向前传播
        x = self.linear1(x)
        x = torch.tanh_(x)

        x = self.linear2(x)
        x = torch.relu(x)

        x = self.out(x)
        y = torch.softmax(x, dim=-1)
        return y

if __name__ == "__main__":
    # 定义输入数据

    x = torch.randn(10, 3) # 10条数据 每条数据3个特征

    # 创建模型
    model = MyModule()

    # 向前传播计算
    y = model(x)

    print(y)

    # 查看参数

    # print(model.linear1.weight)
    # print(model.linear1.bias)
    #
    #
    # for name, param in model.named_parameters():
    #     print(name, param)

    dict = model.state_dict()
    print(dict)

    # 模型结构： torchsummary 第三方库

    from torchsummary import summary

    summary(model, input_size=(3, ), batch_size=10, device="cpu")

