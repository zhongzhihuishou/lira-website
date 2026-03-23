#!/usr/bin/env python3
"""
YOLOv8 吨袋投递图像训练脚本

基于获取的投递图片训练异常检测模型：
- 空投检测（重量<0.05kg）
- 品类识别（可回收物/瓶子/织物等）
- 投递动作识别

依赖:
pip install ultralytics pandas numpy matplotlib scikit-learn
"""

import json
import yaml
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import random

# YOLOv8
try:
    from ultralytics import YOLO
except ImportError:
    print("❌ 请安装 ultralytics: pip install ultralytics")
    exit(1)


class YOLOTrainer:
    """YOLO 训练器"""
    
    # 品类映射
    CATEGORY_MAP = {
        '可回收物': 0,
        '瓶子': 1,
        '织物': 2,
        '塑料': 3,
        '金属': 4,
        '纸张': 5,
        '厨余': 6,
        '有害': 7,
        '其他': 8,
        '空袋': 9,  # 空投异常
    }
    
    def __init__(self, data_dir: str = 'raw_data', output_dir: str = 'runs'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据集目录
        self.dataset_dir = self.output_dir / 'yolo_dataset'
        self.images_dir = self.dataset_dir / 'images'
        self.labels_dir = self.dataset_dir / 'labels'
        
        for split in ['train', 'val', 'test']:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)
    
    def prepare_dataset(self, deliveries_file: str, split_ratio: Tuple[float, float, float] = (0.7, 0.2, 0.1)):
        """
        准备 YOLO 数据集
        
        Args:
            deliveries_file: 投递数据 JSON 文件
            split_ratio: 训练/验证/测试 比例
        """
        print("📦 准备 YOLO 数据集...")
        
        # 加载投递数据
        with open(deliveries_file) as f:
            deliveries = json.load(f)
        
        print(f"   加载投递记录：{len(deliveries)} 条")
        
        # 统计品类分布
        category_dist = Counter([d.get('category', '未知') for d in deliveries])
        print(f"   品类分布：{dict(category_dist)}")
        
        # 过滤有效数据（有图片且有品类）
        valid_deliveries = []
        for d in deliveries:
            if d.get('category') and (d.get('imageBefore_path') or d.get('imageAfter_path')):
                valid_deliveries.append(d)
        
        print(f"   有效记录：{len(valid_deliveries)} 条")
        
        # 随机打乱
        random.shuffle(valid_deliveries)
        
        # 划分数据集
        n = len(valid_deliveries)
        train_end = int(n * split_ratio[0])
        val_end = int(n * (split_ratio[0] + split_ratio[1]))
        
        splits = {
            'train': valid_deliveries[:train_end],
            'val': valid_deliveries[train_end:val_end],
            'test': valid_deliveries[val_end:]
        }
        
        # 处理每个分割
        dataset_info = {'train': [], 'val': [], 'test': []}
        
        for split_name, split_data in splits.items():
            print(f"\n   处理 {split_name} 集 ({len(split_data)} 条)...")
            
            for i, delivery in enumerate(split_data):
                # 复制图片
                img_paths = []
                for img_type in ['imageBefore_path', 'imageAfter_path']:
                    img_path = delivery.get(img_type)
                    if img_path and Path(img_path).exists():
                        # 复制到数据集目录
                        img_name = f"{delivery['bagCode']}_{delivery['id']}_{img_type}.jpg"
                        dst_path = self.images_dir / split_name / img_name
                        shutil.copy2(img_path, dst_path)
                        img_paths.append((dst_path, img_type))
                
                # 创建标签文件
                if img_paths:
                    label_data = self._create_label(delivery)
                    
                    for img_path, img_type in img_paths:
                        label_name = img_path.stem + '.txt'
                        label_path = self.labels_dir / split_name / label_name
                        
                        with open(label_path, 'w') as f:
                            for label in label_data:
                                f.write(f"{label['class']} {label['x']} {label['y']} {label['w']} {label['h']}\n")
                        
                        dataset_info[split_name].append({
                            'image': str(img_path),
                            'label': str(label_path),
                            'category': delivery.get('category'),
                            'weight': delivery.get('weight')
                        })
        
        # 保存数据集信息
        with open(self.dataset_dir / 'dataset_info.json', 'w') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        
        # 创建 data.yaml
        self._create_data_yaml()
        
        print(f"\n✅ 数据集准备完成！")
        print(f"   📁 数据集目录：{self.dataset_dir}")
        print(f"   📊 Train: {len(dataset_info['train'])} 张")
        print(f"   📊 Val: {len(dataset_info['val'])} 张")
        print(f"   📊 Test: {len(dataset_info['test'])} 张")
        
        return dataset_info
    
    def _create_label(self, delivery: Dict) -> List[Dict]:
        """
        创建 YOLO 格式标签
        
        返回：[{class: int, x: float, y: float, w: float, h: float}, ...]
        """
        labels = []
        
        # 品类标签（整图分类）
        category = delivery.get('category', '其他')
        class_id = self.CATEGORY_MAP.get(category, 8)  # 默认"其他"
        
        # 对于整图分类，使用整个图像作为目标
        # YOLO 格式：class x_center y_center width height (归一化 0-1)
        labels.append({
            'class': class_id,
            'x': 0.5,
            'y': 0.5,
            'w': 1.0,
            'h': 1.0
        })
        
        # 空投检测（重量<0.05kg）
        weight = delivery.get('weight', 0)
        if weight < 0.05:
            labels.append({
                'class': self.CATEGORY_MAP['空袋'],
                'x': 0.5,
                'y': 0.5,
                'w': 1.0,
                'h': 1.0
            })
        
        return labels
    
    def _create_data_yaml(self):
        """创建 YOLO data.yaml 配置文件"""
        data = {
            'path': str(self.dataset_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            
            'nc': len(self.CATEGORY_MAP),
            'names': list(self.CATEGORY_MAP.keys())
        }
        
        yaml_path = self.dataset_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True)
        
        print(f"   📄 已创建：{yaml_path}")
    
    def train(self, model_size: str = 'm', epochs: int = 100, imgsz: int = 640, batch: int = 16):
        """
        训练模型
        
        Args:
            model_size: n/s/m/l/x
            epochs: 训练轮数
            imgsz: 输入图像尺寸
            batch: 批次大小
        """
        print(f"\n🚀 开始训练 YOLOv8{model_size}...")
        print(f"   Epochs: {epochs}")
        print(f"   Image Size: {imgsz}")
        print(f"   Batch Size: {batch}")
        
        # 加载预训练模型
        model = YOLO(f'yolov8{model_size}.pt')
        
        # 训练
        results = model.train(
            data=str(self.dataset_dir / 'data.yaml'),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=0,  # GPU，如果没有 GPU 会自动使用 CPU
            workers=8,
            optimizer='auto',
            patience=50,  # 早停
            save=True,
            project=str(self.output_dir / 'detect'),
            name='ton_bag_detection',
            exist_ok=True
        )
        
        print(f"\n✅ 训练完成！")
        print(f"   📁 模型保存：{self.output_dir / 'detect' / 'ton_bag_detection'}")
        
        return results
    
    def evaluate(self, model_path: str = None):
        """
        评估模型
        
        Args:
            model_path: 模型路径（默认使用最新训练的模型）
        """
        if not model_path:
            model_path = self.output_dir / 'detect' / 'ton_bag_detection' / 'weights' / 'best.pt'
        
        print(f"\n📊 评估模型：{model_path}")
        
        model = YOLO(str(model_path))
        
        # 在测试集上评估
        metrics = model.val(
            data=str(self.dataset_dir / 'data.yaml'),
            split='test',
            device=0
        )
        
        print(f"\n📈 评估结果:")
        print(f"   mAP50: {metrics.box.map50:.4f}")
        print(f"   mAP50-95: {metrics.box.map:.4f}")
        print(f"   Precision: {metrics.box.mp:.4f}")
        print(f"   Recall: {metrics.box.mr:.4f}")
        
        return metrics
    
    def export(self, model_path: str = None, format: str = 'onnx'):
        """
        导出模型
        
        Args:
            model_path: 模型路径
            format: 导出格式 (onnx/torchscript/openvino/tflite)
        """
        if not model_path:
            model_path = self.output_dir / 'detect' / 'ton_bag_detection' / 'weights' / 'best.pt'
        
        print(f"\n📦 导出模型：{model_path} -> {format}")
        
        model = YOLO(str(model_path))
        
        export_path = model.export(
            format=format,
            dynamic=True
        )
        
        print(f"   ✅ 导出完成：{export_path}")
        return export_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLOv8 吨袋检测训练')
    parser.add_argument('--data', type=str, default='raw_data/deliveries.json', help='投递数据文件')
    parser.add_argument('--output', type=str, default='runs', help='输出目录')
    parser.add_argument('--model', type=str, default='m', choices=['n', 's', 'm', 'l', 'x'], help='模型大小')
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--imgsz', type=int, default=640, help='图像尺寸')
    parser.add_argument('--batch', type=int, default=16, help='批次大小')
    parser.add_argument('--action', type=str, default='train', choices=['prepare', 'train', 'eval', 'export'], help='操作类型')
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = YOLOTrainer(data_dir='raw_data', output_dir=args.output)
    
    if args.action == 'prepare':
        trainer.prepare_dataset(args.data)
    
    elif args.action == 'train':
        # 先准备数据集
        if not (Path(trainer.dataset_dir) / 'data.yaml').exists():
            trainer.prepare_dataset(args.data)
        
        # 训练
        trainer.train(
            model_size=args.model,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch
        )
    
    elif args.action == 'eval':
        trainer.evaluate()
    
    elif args.action == 'export':
        trainer.export(format='onnx')


if __name__ == '__main__':
    main()
