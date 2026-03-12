# YOLOv8 RK3568 部署教程

**版本：** V1.0  
**创建时间：** 2026-03-12  
**目标：** 在 RK3568 上部署 YOLOv8，实现 20-30 FPS 实时推理

---

## 📋 环境准备

### 硬件要求

| 硬件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **开发板** | RK3568 2GB | RK3568 4GB/8GB |
| **存储** | 16GB eMMC | 32GB eMMC + TF 卡 |
| **电源** | 12V/2A | 12V/5A |
| **散热** | 被动散热 | 金属外壳 + 散热片 |

---

### 软件环境

| 组件 | 版本 | 说明 |
|------|------|------|
| **系统** | Ubuntu 20.04 / Android 11 | 推荐 Ubuntu |
| **Python** | 3.8+ | 深度学习环境 |
| **RKNN-Toolkit2** | v1.6.0+ | 模型转换工具 |
| **ONNX** | 1.13.0+ | 模型中间格式 |
| **YOLOv8** | 8.0+ | Ultralytics |

---

## 🚀 步骤 1：RK3568 系统烧录

### 下载固件

**Ubuntu 20.04 镜像：**
- 友善电子：https://github.com/radxa/radxa-image-builder
- 飞凌嵌入式：官网下载

**烧录工具：**
- RKDevTool（Windows）
- rknpu2（Linux）

### 烧录步骤

```bash
# 1. 下载固件
wget https://github.com/radxa/radxa-image-builder/releases/download/v2.0/rock5b-ubuntu-20.04.img.gz

# 2. 解压
gunzip rock5b-ubuntu-20.04.img.gz

# 3. 烧录（使用 RKDevTool 或 dd 命令）
sudo dd if=rock5b-ubuntu-20.04.img of=/dev/sdX bs=4M conv=fsync

# 4. 插入 TF 卡，启动开发板
```

---

## 🚀 步骤 2：安装依赖

### 系统更新

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv
```

### 创建 Python 虚拟环境

```bash
python3 -m venv rknn-env
source rknn-env/bin/activate
```

### 安装 RKNN-Toolkit2

```bash
# 下载 RKNN-Toolkit2
wget https://github.com/airockchip/rknn-toolkit2/releases/download/v1.6.0/rknn_toolkit2-1.6.0-cp38-cp38-linux_aarch64.whl

# 安装
pip install rknn_toolkit2-1.6.0-cp38-cp38-linux_aarch64.whl
```

### 安装 ONNX 和其他依赖

```bash
pip install onnx==1.13.0
pip install numpy
pip install opencv-python
pip install ultralytics  # YOLOv8
```

---

## 🚀 步骤 3：训练 YOLOv8 模型

### 准备数据集

**回收物数据集结构：**

```
dataset/
├── images/
│   ├── train/
│   │   ├── img001.jpg
│   │   └── ...
│   └── val/
│       └── ...
└── labels/
    ├── train/
    │   ├── img001.txt
    │   └── ...
    └── val/
        └── ...
```

**标签文件示例（img001.txt）：**
```
0 0.5 0.5 0.3 0.4  # class_id x_center y_center width height
1 0.3 0.6 0.2 0.3
2 0.7 0.4 0.25 0.35
```

**类别定义（recycle_data.yaml）：**
```yaml
path: /path/to/dataset
train: images/train
val: images/val

names:
  0: plastic_bottle    # 塑料瓶
  1: paper              # 纸张
  2: metal_can          # 金属罐
  3: glass              # 玻璃
  4: cardboard          # 纸板
```

### 训练模型

```bash
# 使用 YOLOv8n（最小模型，适合 RK3568）
yolo train model=yolov8n.pt data=recycle_data.yaml epochs=100 imgsz=640

# 或使用 YOLOv8s（稍大，精度更高）
yolo train model=yolov8s.pt data=recycle_data.yaml epochs=100 imgsz=640
```

**训练输出：**
```
runs/detect/train/weights/best.pt
```

---

## 🚀 步骤 4：导出 ONNX 模型

```bash
# 导出为 ONNX 格式
yolo export model=runs/detect/train/weights/best.pt format=onnx imgsz=640

# 或使用 Python 脚本
python3 -c "
from ultralytics import YOLO
model = YOLO('runs/detect/train/weights/best.pt')
model.export(format='onnx', imgsz=640)
"
```

**输出文件：** `best.onnx`

---

## 🚀 步骤 5：RKNN 模型转换

### 创建转换脚本

```python
# convert_to_rknn.py
from rknn.api import RKNN

rknn = RKNN()

# 配置
rknn.config(
    target_platform='rk3568',
    optimization_level=3,
    quantization=True  # INT8 量化
)

# 加载 ONNX 模型
rknn.load_onnx(model='best.onnx')

# 构建模型
rknn.build(do_quantization=True, dataset='calib_dataset.txt')

# 导出 RKNN 模型
rknn.export_rknn('yolov8_recycle.rknn')

# 性能评估
perf = rknn.eval_perf()
print(perf)
```

### 准备校准数据集

**calib_dataset.txt：**
```
dataset/images/train/img001.jpg
dataset/images/train/img002.jpg
dataset/images/train/img003.jpg
...
```

（约 100-200 张代表性图片）

### 执行转换

```bash
python3 convert_to_rknn.py
```

**输出文件：** `yolov8_recycle.rknn`

---

## 🚀 步骤 6：RKNN 推理部署

### 创建推理脚本

```python
# inference.py
import cv2
import numpy as np
from rknn.api import RKNN
import time

class YOLOv8RKNN:
    def __init__(self, model_path):
        self.rknn = RKNN()
        self.rknn.load_rknn(model_path)
        self.rknn.init_runtime()
        
        self.input_size = 640
        self.conf_thres = 0.5
        self.iou_thres = 0.45
        self.classes = ['plastic_bottle', 'paper', 'metal_can', 'glass', 'cardboard']
    
    def preprocess(self, image):
        # 调整大小
        img = cv2.resize(image, (self.input_size, self.input_size))
        # 归一化
        img = img.astype(np.float32) / 255.0
        # HWC to CHW
        img = np.transpose(img, (2, 0, 1))
        # 添加 batch 维度
        img = np.expand_dims(img, axis=0)
        return img
    
    def postprocess(self, outputs):
        # 解析 YOLOv8 输出
        # 非极大值抑制（NMS）
        # 返回检测结果
        pass
    
    def detect(self, image):
        # 预处理
        input_data = self.preprocess(image)
        
        # 推理
        outputs = self.rknn.inference(inputs=[input_data])
        
        # 后处理
        results = self.postprocess(outputs)
        
        return results

# 测试
if __name__ == '__main__':
    detector = YOLOv8RKNN('yolov8_recycle.rknn')
    
    # 摄像头或图片
    cap = cv2.VideoCapture(0)
    
    fps_list = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        start = time.time()
        results = detector.detect(frame)
        end = time.time()
        
        fps = 1.0 / (end - start)
        fps_list.append(fps)
        
        # 显示结果
        cv2.putText(frame, f'FPS: {fps:.1f}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('YOLOv8 RK3568', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f'Average FPS: {np.mean(fps_list):.1f}')
```

---

## 🚀 步骤 7：性能优化

### 优化技巧

**1. 模型量化**
```python
# INT8 量化（已在上文配置）
rknn.config(quantization=True)
```

**2. 输入尺寸调整**
```python
# 640x640 → 精度最高，速度较慢
# 416x416 → 速度更快，精度略降
# 320x320 → 最快，精度最低
```

**3. 多线程推理**
```python
# 使用 RKNN 多核支持
rknn.config(core_mask=RKNN.NPU_CORE_0_1_2)
```

**4. 内存优化**
```python
# 减少 batch size
# 使用 float16
```

---

## 📊 预期性能

| 模型 | 输入尺寸 | FPS | 准确率 | 功耗 |
|------|----------|-----|--------|------|
| **YOLOv8n** | 640x640 | 25-30 | 95%+ | 3-4W |
| **YOLOv8n** | 416x416 | 35-40 | 93%+ | 3-4W |
| **YOLOv8n** | 320x320 | 45-50 | 90%+ | 3-4W |
| **YOLOv8s** | 640x640 | 15-20 | 96%+ | 4-5W |

**推荐配置：** YOLOv8n @ 640x640（平衡性能与精度）

---

## 🔧 常见问题

### Q1: 模型转换失败

**解决：**
- 检查 ONNX 模型是否有效
- 确保 RKNN-Toolkit2 版本匹配
- 校准数据集质量

### Q2: 推理速度慢

**解决：**
- 使用 INT8 量化
- 减小输入尺寸
- 启用多核 NPU

### Q3: 内存不足

**解决：**
- 使用更小模型（YOLOv8n）
- 减小输入尺寸
- 关闭其他进程

### Q4: 准确率低

**解决：**
- 增加训练数据
- 调整置信度阈值
- 使用更大模型（YOLOv8s）

---

## 📁 项目结构

```
rk3568-yolov8/
├── dataset/                    # 数据集
│   ├── images/
│   └── labels/
├── models/                     # 模型文件
│   ├── yolov8n.pt
│   ├── best.onnx
│   └── yolov8_recycle.rknn
├── scripts/
│   ├── convert_to_rknn.py
│   └── inference.py
├── calib_dataset.txt          # 校准数据集
├── recycle_data.yaml          # 数据集配置
└── README.md
```

---

## 🎯 下一步

1. **采购 RK3568 开发板** — 参考《RK3568 硬件选型指南.md》
2. **准备数据集** — 收集回收物图片（至少 500 张）
3. **训练模型** — 使用 YOLOv8n
4. **转换部署** — ONNX → RKNN → RK3568
5. **性能测试** — 实测 FPS 和准确率

---

**文档版本：** V1.0  
**最后更新：** 2026-03-12  
**创建人：** 总经理 AI
