# 吨袋图像模型训练指南

## 📋 完整流程

```
1. 获取 API Token → 2. 下载数据 → 3. 准备数据集 → 4. 训练模型 → 5. 评估导出
```

---

## 🔑 步骤 1: 获取 API Token

### 方法 A: 从绿袋云 APP 获取

1. 安装抓包工具（推荐：Charles / Fiddler / Wireshark）
2. 手机连接抓包代理
3. 打开绿袋云 APP，登录账号
4. 查看请求头中的 `Authorization` 或 `token` 字段
5. 复制 token 值

### 方法 B: 从浏览器获取（如果有 Web 版）

1. 打开浏览器开发者工具（F12）
2. 切换到 Network 标签
3. 登录绿袋云 Web 版
4. 找到 API 请求，复制 token

### 配置 Token

```bash
cd /Users/srz/.openclaw/workspace/model_training

# 复制配置模板
cp config.example.json config.json

# 编辑 config.json，填入 token
vi config.json
```

```json
{
  "api": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

## 📥 步骤 2: 下载数据

```bash
# 获取 1000 个吨袋的投递数据（约 2000-4000 张图片）
python fetch_data.py --max-bags 1000

# 或者使用配置文件中的参数
python fetch_data.py
```

### 输出结构

```
raw_data/
├── bag_codes.json          # 吨袋编码列表
├── deliveries.json         # 投递记录（含图片路径）
└── images/                 # 下载的图片
    ├── BB20260323001/
    │   ├── 1001_imageBefore.jpg
    │   └── 1001_imageAfter.jpg
    └── ...
```

### API 说明

| 接口 | 用途 | 参数 |
|------|------|------|
| `/delivery/sorting/bingbag/list` | 获取吨袋编码列表 | page, page_size |
| `/delivery/sorting/list` | 获取待分拣任务 | page, page_size |
| `/delivery/all/list` | 获取投递详情（含图片） | bagCode |

---

## 📦 步骤 3: 准备 YOLO 数据集

```bash
# 准备数据集（自动划分 train/val/test）
python train_yolo.py --data raw_data/deliveries.json --action prepare
```

### 输出结构

```
runs/yolo_dataset/
├── data.yaml             # YOLO 配置文件
├── dataset_info.json     # 数据集信息
├── images/
│   ├── train/           # 训练集图片
│   ├── val/             # 验证集图片
│   └── test/            # 测试集图片
└── labels/
    ├── train/           # 训练集标签
    ├── val/             # 验证集标签
    └── test/            # 测试集标签
```

### 品类映射

| ID | 品类 | 说明 |
|----|------|------|
| 0 | 可回收物 | 纸张、塑料、金属等 |
| 1 | 瓶子 | 饮料瓶、洗发水瓶等 |
| 2 | 织物 | 衣物、布料等 |
| 3 | 塑料 | 塑料袋、塑料包装等 |
| 4 | 金属 | 易拉罐、金属制品等 |
| 5 | 纸张 | 纸箱、报纸等 |
| 6 | 厨余 | 食物残渣等 |
| 7 | 有害 | 电池、灯管等 |
| 8 | 其他 | 无法分类的垃圾 |
| 9 | 空袋 | 空投异常检测 |

---

## 🚀 步骤 4: 训练模型

```bash
# 完整训练（自动先准备数据集）
python train_yolo.py --data raw_data/deliveries.json --action train

# 自定义参数
python train_yolo.py \
  --data raw_data/deliveries.json \
  --action train \
  --model m \
  --epochs 100 \
  --imgsz 640 \
  --batch 16
```

### 模型大小选择

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|--------|------|------|----------|
| nano (n) | 3.2M | 最快 | 较低 | 边缘设备 |
| small (s) | 11.2M | 快 | 中等 | 实时检测 |
| medium (m) | 25.9M | 中等 | 高 | 推荐✅ |
| large (l) | 43.7M | 慢 | 很高 | 离线分析 |
| xlarge (x) | 68.2M | 最慢 | 最高 | 高精度需求 |

### 训练监控

训练过程中会生成：
- `runs/detect/ton_bag_detection/` - 训练输出目录
- `results.csv` - 训练指标
- `confusion_matrix.png` - 混淆矩阵
- `PR_curve.png` - 精度 - 召回曲线

---

## 📊 步骤 5: 评估模型

```bash
# 在测试集上评估
python train_yolo.py --action eval
```

### 评估指标

- **mAP50**: IOU=0.5 时的平均精度
- **mAP50-95**: IOU 从 0.5 到 0.95 的平均精度
- **Precision**: 查准率
- **Recall**: 召回率

### 目标指标

| 指标 | 目标值 |
|------|--------|
| mAP50 | > 0.90 |
| mAP50-95 | > 0.75 |
| Precision | > 0.85 |
| Recall | > 0.85 |

---

## 📦 步骤 6: 导出模型

```bash
# 导出为 ONNX 格式（推荐）
python train_yolo.py --action export

# 导出为其他格式
python train_yolo.py --action export --format torchscript
python train_yolo.py --action export --format tflite
python train_yolo.py --action export --format openvino
```

### 导出格式对比

| 格式 | 用途 | 部署平台 |
|------|------|----------|
| ONNX | 通用 | 所有平台✅ |
| TorchScript | PyTorch | Python/Cpp |
| TFLite | TensorFlow Lite | 移动端/嵌入式 |
| OpenVINO | Intel | Intel CPU/VPU |

---

## 🔧 常见问题

### Q1: Token 失效怎么办？
重新从 APP 获取 token，更新 config.json

### Q2: 图片下载失败？
检查网络连接，API 可能有限流，增加延时：
```python
time.sleep(1)  # 在 fetch_data.py 中增加延时
```

### Q3: 训练时显存不足？
减小 batch size：
```bash
python train_yolo.py --batch 8  # 或更小
```

### Q4: 精度不够高？
- 增加训练数据量（获取更多吨袋）
- 增加训练轮数（--epochs 200）
- 使用更大的模型（--model l）
- 数据增强（修改 data.yaml）

---

## 📈 性能优化

### 边缘部署（Jetson Orin NX）

```bash
# 导出为 TensorRT
python train_yolo.py --action export --format engine

# 部署测试
python detect.py --model runs/detect/ton_bag_detection/weights/best.engine
```

### 预期性能

| 平台 | FPS | 延迟 |
|------|-----|------|
| Jetson Orin NX (INT8) | 60+ | <17ms |
| RTX 3060 | 100+ | <10ms |
| CPU (i7) | 15-20 | ~50ms |

---

## 📝 下一步

训练完成后：
1. 集成到 anomaly_detector.py
2. 更新 Demo 页面使用真实模型
3. 部署为 API 服务
4. 持续收集数据，定期重新训练

---

**文档版本**: V1.0  
**更新时间**: 2026-03-23
