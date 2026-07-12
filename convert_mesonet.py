"""Mesonet Keras(.h5) → PyTorch(.pth) 权重转换"""
import sys
from pathlib import Path

import h5py
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent / "backend_ai"))
from services.deepfake_detector import Meso4

H5 = Path("backend_ai/models/mesonet/Meso4_DF.h5")
PTH = Path("backend_ai/models/mesonet/meso4_official.pth")


def get_ds(f, path):
    return np.array(f[path])


def convert():
    f = h5py.File(str(H5), "r")
    model = Meso4()
    state = model.state_dict()

    # Keras 层名映射 (编号5-8 对应 Conv1-4, BN5-8)
    for keras_name, py_name, kind in [
        ("conv2d_5", "conv1", "conv"),
        ("conv2d_6", "conv2", "conv"),
        ("conv2d_7", "conv3", "conv"),
        ("conv2d_8", "conv4", "conv"),
        ("batch_normalization_5", "bn1", "bn"),
        ("batch_normalization_6", "bn2", "bn"),
        ("batch_normalization_7", "bn3", "bn"),
        ("batch_normalization_8", "bn4", "bn"),
        ("dense_3", "fc1", "dense"),
        ("dense_4", "fc2", "dense"),
    ]:
        path = f"{keras_name}/{keras_name}"
        key = f"{py_name}"

        if kind == "conv":
            w = get_ds(f, f"{path}/kernel:0")          # (H,W,Cin,Cout) → (Cout,Cin,H,W)
            state[f"{key}.weight"] = torch.from_numpy(np.transpose(w, (3, 2, 0, 1)))
            state[f"{key}.bias"] = torch.from_numpy(get_ds(f, f"{path}/bias:0"))

        elif kind == "bn":
            state[f"{key}.weight"] = torch.from_numpy(get_ds(f, f"{path}/gamma:0"))
            state[f"{key}.bias"] = torch.from_numpy(get_ds(f, f"{path}/beta:0"))
            state[f"{key}.running_mean"] = torch.from_numpy(get_ds(f, f"{path}/moving_mean:0"))
            state[f"{key}.running_var"] = torch.from_numpy(get_ds(f, f"{path}/moving_variance:0"))

        elif kind == "dense":
            w = get_ds(f, f"{path}/kernel:0")           # (in,out) → (out,in)
            state[f"{key}.weight"] = torch.from_numpy(np.transpose(w, (1, 0)))
            state[f"{key}.bias"] = torch.from_numpy(get_ds(f, f"{path}/bias:0"))

        print(f"  {keras_name} → {key}: OK")

    model.load_state_dict(state)
    torch.save(model.state_dict(), str(PTH))
    f.close()

    print(f"\nSaved: {PTH} ({PTH.stat().st_size} bytes)")

    # 验证
    model.eval()
    x = torch.randn(1, 3, 256, 256)
    with torch.no_grad():
        out = model(x).item()
    print(f"Test: {out:.4f}")
    print("OK!")


if __name__ == "__main__":
    convert()
