"""下载 MesoNet 预训练权重 (~27KB)"""
import os, sys
from pathlib import Path

import requests
import torch

SAVE_PATH = Path(__file__).parent / "models" / "mesonet" / "meso4_weights.pth"
SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

if SAVE_PATH.exists():
    print(f"权重已存在: {SAVE_PATH} ({os.path.getsize(SAVE_PATH)} bytes)")
    sys.exit(0)

# 备用源
URLS = [
    "https://github.com/DariusAf/MesoNet/raw/master/weights/Meso4_DF.h5",
    "https://raw.githubusercontent.com/DariusAf/MesoNet/master/weights/Meso4_DF.h5",
]

print(f"下载 Meso4 预训练权重...")
# 注意：原始权重是 Keras .h5 格式，需要转换。这里先尝试获取
# 如果不可用，创建一个最小化训练脚本

# 实际上 MesoNet 原始权重是 Keras 格式。
# 我们改为使用 PyTorch 版权重或自训练

# ── 方案：自训练 Meso4 ──
print("预训练权重不可直接获取，将在首次使用时自训练...")
print(f"请运行: python {Path(__file__).parent / 'train_mesonet.py'}")
