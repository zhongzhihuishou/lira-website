# 模型训练模块

## 功能概述

基于 YOLOv8 的工业 AI 视觉模型训练系统，支持：
- 🗑️ 吨袋投递异常检测
- 🏷️ 多品类垃圾识别（10 类）
- 🎯 小目标检测
- ⚖️ 重量预测融合
- 🚨 空投/异常检测

## 📚 文档

- **详细训练指南**: [TRAINING_GUIDE.md](TRAINING_GUIDE.md)
- **API 说明**: 见下方

## 快速开始

### 1. 获取 API Token

从绿袋云 APP 获取 token（抓包获取 Authorization header）

```bash
cd /Users/srz/.openclaw/workspace/model_training

# 复制配置模板
cp config.example.json config.json

# 编辑 config.json，填入 token
vi config.json
```

### 2. 下载数据

```bash
# 获取 1000 个吨袋的投递数据（约 2000-4000 张图片）
python fetch_data.py --max-bags 1000
```

**API 接口：**
- `https://www.lvdouge.com/openapi/delivery/sorting/bingbag/list` - 吨袋编码列表
- `https://www.lvdouge.com/openapi/delivery/sorting/list` - 待分拣信息
- `https://www.lvdouge.com/openapi/delivery/all/list?bagCode=xxx` - 投递详情（含图片）

### 3. 训练模型

```bash
# 完整训练流程（自动准备数据集 + 训练）
python train_yolo.py --data raw_data/deliveries.json --action train

# 自定义参数
python train_yolo.py \
  --data raw_data/deliveries.json \
  --action train \
  --model m \
  --epochs 100 \
  --imgsz 640
```

### 4. 评估与导出

```bash
# 评估
python train_yolo.py --action eval

# 导出为 ONNX
python train_yolo.py --action export
```

## 品类映射

| ID | 品类 | ID | 品类 |
|----|------|----|------|
| 0 | 可回收物 | 5 | 纸张 |
| 1 | 瓶子 | 6 | 厨余 |
| 2 | 织物 | 7 | 有害 |
| 3 | 塑料 | 8 | 其他 |
| 4 | 金属 | 9 | 空袋 |

## 项目结构

```
model_training/
├── README.md                 # 本文件
├── TRAINING_GUIDE.md         # 详细训练指南
├── config.example.json       # 配置模板
├── fetch_data.py             # 数据获取脚本
├── train_yolo.py             # YOLO 训练脚本
├── anomaly_detector.py       # 异常检测器（重量 + 图像）
└── runs/                     # 训练输出
    ├── yolo_dataset/         # YOLO 数据集
    │   ├── data.yaml
    │   ├── images/train/val/test/
    │   └── labels/train/val/test/
    └── detect/
        └── ton_bag_detection/
            └── weights/best.pt
```

## API 接口

训练完成后可通过 Python 调用：

```python
from anomaly_detector import AnomalyDetector

detector = AnomalyDetector(
    model_path='runs/detect/ton_bag_detection/weights/best.pt',
    weight_model='runs/weight_predictor.json',
    rules_path='runs/anomaly_rules.json'
)

result = detector.detect(
    image_path='test.jpg',
    weight=1.5,
    category='可回收物'
)

print(result)
# {
#   'status': 'normal',
#   'risk': 'low',
#   'anomaly_type': '正常',
#   'confidence': 0.96,
#   'weight_info': {...},
#   'image_info': {...}
# }
```

## 状态

- ✅ 数据收集完成（4856 条记录，9712 张图片）
- ✅ 重量统计模型训练完成
- ✅ 异常检测规则定义完成
- ✅ 数据获取脚本完成（fetch_data.py）
- ✅ YOLO 训练脚本完成（train_yolo.py）
- ✅ 训练指南完成（TRAINING_GUIDE.md）
- 🔄 待获取 API Token
- 🔄 待下载真实数据
- 🔄 待训练 YOLO 模型

## 下一步

1. **获取 Token** - 从绿袋云 APP 抓包
2. **下载数据** - 运行 `fetch_data.py`
3. **训练模型** - 运行 `train_yolo.py`
4. **集成 Demo** - 更新 demo/index.html 使用真实模型
5. **部署服务** - 部署为 API 服务
