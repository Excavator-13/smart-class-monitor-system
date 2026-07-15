"""换脸检测器 — 集成 MesoNet CNN + 多特征融合"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Meso4 网络 ────────────────────────────────────────

class Meso4(nn.Module):
    """输入 256x256x3 → 4层卷积 + 全连接 → 输出 1 (0=real, 1=fake)"""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 8, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(8)
        self.conv2 = nn.Conv2d(8, 8, 5, padding=2)
        self.bn2 = nn.BatchNorm2d(8)
        self.conv3 = nn.Conv2d(8, 16, 5, padding=2)
        self.bn3 = nn.BatchNorm2d(16)
        self.conv4 = nn.Conv2d(16, 16, 5, padding=2)
        self.bn4 = nn.BatchNorm2d(16)
        self.dropout = nn.Dropout(0.5)
        # conv4输出 16x8x8=1024 → fc1: 1024→16 → fc2: 16→1
        self.fc1 = nn.Linear(1024, 16)
        self.fc2 = nn.Linear(16, 1)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                if m.out_features == 1:
                    nn.init.normal_(m.weight, 0, 0.01)
                    nn.init.constant_(m.bias, 0)
                else:
                    nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.bn3(self.conv3(x)))
        x = F.max_pool2d(x, 2)
        x = F.relu(self.bn4(self.conv4(x)))
        x = F.max_pool2d(x, 4)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        return x


# ── DeepfakeDetector ──────────────────────────────────

class DeepfakeDetector:
    """换脸检测: CNN 主检测 + 拉普拉斯 + FFT 辅助"""

    INPUT_SIZE = 256

    def __init__(self, weights_path: str | None = None):
        from backend_ai.utils import resolve_device
        self.device = torch.device(resolve_device())
        self.model = Meso4().to(self.device)
        self.model.eval()
        self._cnn_loaded = False

        # 尝试加载预训练权重
        if weights_path:
            self._load_weights(weights_path)
        else:
            default = Path(__file__).parent.parent / "models" / "mesonet" / "meso4_weights.pth"
            if default.exists():
                self._load_weights(str(default))

    def _load_weights(self, path: str):
        try:
            state = torch.load(path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self._cnn_loaded = True
            print(f"[DeepfakeDetector] CNN 权重已加载")
        except Exception as e:
            print(f"[DeepfakeDetector] 权重加载失败: {e}")

    def _preprocess(self, face_img: np.ndarray) -> torch.Tensor | None:
        try:
            img = cv2.resize(face_img, (self.INPUT_SIZE, self.INPUT_SIZE))
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406])
            std = np.array([0.229, 0.224, 0.225])
            img = (img - mean) / std
            img = np.transpose(img, (2, 0, 1))
            return torch.from_numpy(img).unsqueeze(0).float().to(self.device)
        except Exception:
            return None

    def predict(self, face_roi: np.ndarray) -> dict[str, Any]:
        """综合预测（CNN 为主，规则为辅）"""
        if face_roi is None or face_roi.size == 0:
            return {"is_fake": False, "confidence": 0.0, "method": "none"}

        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi

        # 规则特征
        lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # CNN 预测
        cnn_score = 0.5
        if self._cnn_loaded:
            with torch.no_grad():
                tensor = self._preprocess(face_roi)
                if tensor is not None:
                    cnn_score = float(self.model(tensor).item())

        # 融合判定
        if self._cnn_loaded and (cnn_score > 0.7 or cnn_score < 0.3):
            # CNN 置信度高时以 CNN 为准
            is_fake = cnn_score > 0.5
            confidence = cnn_score if is_fake else 1.0 - cnn_score
            method = "cnn"
        elif lap_var < 5.0:
            is_fake = True
            confidence = 1.0 - lap_var / 10.0
            method = "laplacian"
        else:
            # 结合两者
            rule_fake = lap_var < 10.0
            confidence = 0.6 if rule_fake else 0.4
            is_fake = rule_fake if not self._cnn_loaded else cnn_score > 0.5
            method = "combined" if self._cnn_loaded else "rule"

        return {
            "is_fake": is_fake,
            "confidence": round(confidence, 4),
            "verdict": "FAKE" if is_fake else "REAL",
            "method": method,
            "cnn_score": round(cnn_score, 4),
            "laplacian_var": round(lap_var, 1),
        }

    @property
    def loaded(self) -> bool:
        return self._cnn_loaded

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self._cnn_loaded,
            "model": "Meso4",
            "input_size": self.INPUT_SIZE,
            "device": str(self.device),
        }

    # ── 自训练功能 ────────────────────────────────────

    def train_quick(
        self,
        real_images: list[np.ndarray],
        fake_images: list[np.ndarray],
        epochs: int = 20,
        save_path: str | None = None,
    ) -> dict[str, float]:
        """
        快速训练（用于微调/演示）

        Args:
            real_images: 真人脸图片列表 (BGR)
            fake_images: AI脸图片列表 (BGR)
            epochs: 训练轮数
            save_path: 保存权重路径
        """
        if len(real_images) == 0 or len(fake_images) == 0:
            print("[MesoNet] 训练数据不足")
            return {"accuracy": 0.0}

        # 构建数据集
        X_real, X_fake = [], []
        for img in real_images:
            t = self._preprocess(img)
            if t is not None:
                X_real.append(t)
        for img in fake_images:
            t = self._preprocess(img)
            if t is not None:
                X_fake.append(t)

        if len(X_real) < 1 or len(X_fake) < 1:
            print("[MesoNet] 预处理后图片不足")
            return {"accuracy": 0.0}

        # 数据增强（增强真人样本）
        augmented_real = []
        for t in X_real:
            augmented_real.append(t)
            augmented_real.append(torch.flip(t, [3]))          # 水平翻转
            augmented_real.append(t + torch.randn_like(t) * 0.02)  # 加噪
            augmented_real.append(t * (0.8 + torch.rand(1).item() * 0.4))  # 亮度变化
        aug_y_real = torch.zeros(len(augmented_real), 1).to(self.device)

        augmented_fake = []
        for t in X_fake:
            augmented_fake.append(t)
            augmented_fake.append(torch.flip(t, [3]))
        aug_y_fake = torch.ones(len(augmented_fake), 1).to(self.device)

        augmented = torch.cat(augmented_real + augmented_fake, dim=0).float()
        aug_y = torch.cat([aug_y_real, aug_y_fake], dim=0)

        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        criterion = nn.BCELoss()

        for epoch in range(epochs):
            optimizer.zero_grad()
            output = self.model(augmented)
            loss = criterion(output, aug_y)
            loss.backward()
            optimizer.step()

            if (epoch + 1) % 5 == 0:
                pred = (output > 0.5).float()
                acc = (pred == aug_y).float().mean().item()
                print(f"  Epoch {epoch+1}/{epochs} | loss={loss.item():.4f} | acc={acc:.2%}")

        self.model.eval()
        self._cnn_loaded = True

        # 保存
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            torch.save(self.model.state_dict(), save_path)
            print(f"  Weights saved: {save_path}")

        with torch.no_grad():
            final_output = self.model(augmented)
            final_pred = (final_output > 0.5).float()
            final_acc = (final_pred == aug_y).float().mean().item()

        return {"accuracy": round(final_acc, 4), "samples": len(X_real) + len(X_fake)}