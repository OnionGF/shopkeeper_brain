import torch
import torchvision

print(f"PyTorch 版本: {torch.__version__}")
print(f"TorchVision 版本: {torchvision.__version__}")
print(f"MPS GPU 加速可用: {torch.backends.mps.is_available()}")
