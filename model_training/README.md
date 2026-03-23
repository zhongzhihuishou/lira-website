# 模型训练模块

## 功能概述

基于 YOLOv8 的工业 AI 视觉模型训练系统，支持：
- 吨袋投递异常检测
- 多品类垃圾识别
- 小目标检测
- 重量预测融合

## 快速开始

### 1. 环境准备

```bash
cd /Users/srz/.openclaw/workspace/training_data
python -m venv venv
source venv/bin/activate
pip install ultralytics pandas numpy matplotlib scikit-learn
```

### 2. 数据准备

```bash
# 下载投递数据（已有）
python download_data.py

# 数据集已位于：
# - training_data/yolo_dataset_weighted/
# - training_data/runs/weight_predictor.json
# - training_data/runs/anomaly_rules.json
```

### 3. 训练模型

```bash
# 训练重量异常检测模型
python weight_anomaly_detect.py --train

# 训练 YOLO 视觉模型
python train_yolo.py --data yolo_dataset_weighted/data.yaml --epochs 100
```

### 4. 评估模型

```bash
# 运行评估
python evaluate.py --model runs/detect/best.pt

# 生成测试报告
python generate_report.py
```

## 模型输出

- `runs/detect/best.pt` - 训练完成的 YOLO 模型
- `runs/weight_predictor.json` - 重量统计模型
- `runs/anomaly_rules.json` - 异常检测规则
- `results/` - 评估报告和可视化

## API 接口

训练完成后可通过 API 调用：

```python
from anomaly_detector import AnomalyDetector

detector = AnomalyDetector(
    model_path='runs/detect/best.pt',
    weight_model='runs/weight_predictor.json',
    rules_path='runs/anomaly_rules.json'
)

result = detector.detect(image_path='test.jpg', weight=1.5)
print(result)
# {'status': 'normal', 'risk': 'low', 'confidence': 0.96}
```

## 状态

- ✅ 数据收集完成（4856 条记录，9712 张图片）
- ✅ 重量统计模型训练完成
- ✅ 异常检测规则定义完成
- 🔄 YOLO 视觉模型待训练
- 🔄 Demo 页面待部署
