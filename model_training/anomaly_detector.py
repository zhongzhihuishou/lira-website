#!/usr/bin/env python3
"""
吨袋投递异常检测器
整合图像识别 + 重量分析的异常检测系统
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AnomalyType(Enum):
    EMPTY_DUMP = "空投异常"
    UNDER_WEIGHT = "重量不足"
    OVER_WEIGHT = "重量异常"
    CATEGORY_MISMATCH = "品类重量不符"
    NORMAL = "正常"

@dataclass
class DetectionResult:
    status: str
    risk: RiskLevel
    anomaly_type: AnomalyType
    confidence: float
    details: Dict
    weight_info: Dict
    image_info: Dict

class AnomalyDetector:
    def __init__(self, 
                 weight_model_path: str = None,
                 rules_path: str = None,
                 yolo_model_path: str = None):
        self.weight_model = self._load_weight_model(weight_model_path)
        self.rules = self._load_rules(rules_path)
        self.yolo_model = None
        if yolo_model_path:
            self._load_yolo_model(yolo_model_path)
    
    def _load_weight_model(self, path: str) -> Dict:
        """加载重量统计模型"""
        if not path or not Path(path).exists():
            return self._default_weight_model()
        
        with open(path, 'r') as f:
            return json.load(f)
    
    def _default_weight_model(self) -> Dict:
        """默认重量统计（基于历史数据）"""
        return {
            "categories": {
                "可回收物": {"mean": 1.78, "std": 2.80, "count": 1673},
                "瓶子": {"mean": 0.85, "std": 1.68, "count": 1344},
                "织物": {"mean": 3.75, "std": 8.98, "count": 621},
                "塑料": {"mean": 1.20, "std": 2.10, "count": 890},
                "金属": {"mean": 2.50, "std": 3.20, "count": 456},
                "纸张": {"mean": 1.90, "std": 2.50, "count": 723}
            },
            "global_stats": {
                "mean": 1.85,
                "std": 3.50,
                "total_samples": 5707
            }
        }
    
    def _load_rules(self, path: str) -> Dict:
        """加载异常检测规则"""
        if not path or not Path(path).exists():
            return self._default_rules()
        
        with open(path, 'r') as f:
            return json.load(f)
    
    def _default_rules(self) -> Dict:
        """默认异常检测规则"""
        return {
            "empty_dump_threshold": 0.05,  # 空投阈值 (kg)
            "under_weight_sigma": 2.0,     # 重量不足标准差
            "over_weight_sigma": 2.0,      # 重量异常标准差
            "category_ranges": {
                "可回收物": {"min": 0.1, "max": 10.0},
                "瓶子": {"min": 0.05, "max": 5.0},
                "织物": {"min": 0.5, "max": 20.0},
                "塑料": {"min": 0.1, "max": 8.0},
                "金属": {"min": 0.2, "max": 15.0},
                "纸张": {"min": 0.1, "max": 10.0}
            }
        }
    
    def _load_yolo_model(self, path: str):
        """加载 YOLO 模型"""
        try:
            from ultralytics import YOLO
            self.yolo_model = YOLO(path)
        except ImportError:
            print("Warning: ultralytics not installed, image detection disabled")
    
    def detect(self, 
               image_path: Optional[str] = None,
               weight: Optional[float] = None,
               category: Optional[str] = None,
               device_id: Optional[str] = None,
               timestamp: Optional[str] = None) -> DetectionResult:
        """
        执行异常检测
        
        Args:
            image_path: 投递图片路径（可选）
            weight: 投递重量 (kg)
            category: 垃圾品类
            device_id: 设备编号
            timestamp: 时间戳
        
        Returns:
            DetectionResult: 检测结果
        """
        # 图像分析（如果有 YOLO 模型）
        image_info = {"analyzed": False, "objects": [], "confidence": 0.0}
        if self.yolo_model and image_path:
            image_info = self._analyze_image(image_path)
        
        # 重量分析
        weight_info = self._analyze_weight(weight, category)
        
        # 规则匹配
        anomaly_type, risk, confidence, details = self._apply_rules(
            weight=weight,
            category=category,
            weight_info=weight_info,
            image_info=image_info
        )
        
        return DetectionResult(
            status="normal" if anomaly_type == AnomalyType.NORMAL else "anomaly",
            risk=risk,
            anomaly_type=anomaly_type,
            confidence=confidence,
            details=details,
            weight_info=weight_info,
            image_info=image_info
        )
    
    def _analyze_image(self, image_path: str) -> Dict:
        """分析投递图片"""
        if not self.yolo_model:
            return {"analyzed": False, "objects": [], "confidence": 0.0}
        
        results = self.yolo_model(image_path)
        objects = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    objects.append({
                        "class": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })
        
        return {
            "analyzed": True,
            "objects": objects,
            "confidence": np.mean([o["confidence"] for o in objects]) if objects else 0.0
        }
    
    def _analyze_weight(self, weight: float, category: str) -> Dict:
        """分析重量数据"""
        if weight is None:
            return {"analyzed": False, "z_score": None, "percentile": None}
        
        stats = self.weight_model["categories"].get(category)
        if not stats:
            stats = self.weight_model["global_stats"]
        
        mean = stats["mean"]
        std = stats["std"]
        z_score = (weight - mean) / std if std > 0 else 0
        percentile = 0.5 * (1 + np.erf(z_score / np.sqrt(2)))
        
        return {
            "analyzed": True,
            "weight": weight,
            "expected_mean": mean,
            "expected_std": std,
            "z_score": round(z_score, 3),
            "percentile": round(percentile, 3)
        }
    
    def _apply_rules(self, 
                     weight: float,
                     category: str,
                     weight_info: Dict,
                     image_info: Dict) -> Tuple[AnomalyType, RiskLevel, float, Dict]:
        """应用异常检测规则"""
        details = {"rules_applied": [], "violations": []}
        
        # 规则 1: 空投检测
        if weight is not None and weight < self.rules["empty_dump_threshold"]:
            details["rules_applied"].append("empty_dump_check")
            details["violations"].append(f"重量 {weight}kg < 阈值 {self.rules['empty_dump_threshold']}kg")
            return (
                AnomalyType.EMPTY_DUMP,
                RiskLevel.HIGH,
                0.95,
                details
            )
        
        # 规则 2: 重量不足检测
        if weight_info.get("z_score") is not None and weight_info["z_score"] < -self.rules["under_weight_sigma"]:
            details["rules_applied"].append("under_weight_check")
            details["violations"].append(f"Z-Score {weight_info['z_score']} < -{self.rules['under_weight_sigma']}")
            return (
                AnomalyType.UNDER_WEIGHT,
                RiskLevel.MEDIUM,
                0.85,
                details
            )
        
        # 规则 3: 重量异常检测
        if weight_info.get("z_score") is not None and weight_info["z_score"] > self.rules["over_weight_sigma"]:
            details["rules_applied"].append("over_weight_check")
            details["violations"].append(f"Z-Score {weight_info['z_score']} > {self.rules['over_weight_sigma']}")
            return (
                AnomalyType.OVER_WEIGHT,
                RiskLevel.MEDIUM,
                0.85,
                details
            )
        
        # 规则 4: 品类重量不符
        if category and weight is not None:
            cat_range = self.rules["category_ranges"].get(category)
            if cat_range:
                if weight < cat_range["min"] or weight > cat_range["max"]:
                    details["rules_applied"].append("category_range_check")
                    details["violations"].append(f"重量 {weight}kg 超出 {category} 正常范围 [{cat_range['min']}, {cat_range['max']}]")
                    return (
                        AnomalyType.CATEGORY_MISMATCH,
                        RiskLevel.LOW,
                        0.75,
                        details
                    )
        
        # 正常
        details["rules_applied"].append("all_checks_passed")
        return (
            AnomalyType.NORMAL,
            RiskLevel.LOW,
            0.98,
            details
        )
    
    def batch_detect(self, records: List[Dict]) -> List[DetectionResult]:
        """批量检测"""
        return [self.detect(**record) for record in records]
    
    def generate_report(self, results: List[DetectionResult]) -> Dict:
        """生成检测报告"""
        total = len(results)
        anomalies = sum(1 for r in results if r.status == "anomaly")
        
        risk_counts = {level.value: 0 for level in RiskLevel}
        type_counts = {t.value: 0 for t in AnomalyType}
        
        for r in results:
            risk_counts[r.risk.value] += 1
            type_counts[r.anomaly_type.value] += 1
        
        return {
            "total_records": total,
            "anomaly_count": anomalies,
            "anomaly_rate": round(anomalies / total * 100, 2) if total > 0 else 0,
            "risk_distribution": risk_counts,
            "anomaly_types": type_counts,
            "avg_confidence": round(np.mean([r.confidence for r in results]), 3)
        }


# 测试
if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # 测试用例
    test_cases = [
        {"weight": 0.02, "category": "可回收物"},  # 空投
        {"weight": 15.5, "category": "瓶子"},       # 重量异常
        {"weight": 1.5, "category": "可回收物"},    # 正常
        {"weight": 0.3, "category": "织物"},       # 重量不足
    ]
    
    print("=" * 60)
    print("吨袋投递异常检测系统 - 测试结果")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        result = detector.detect(**case)
        print(f"\n测试 {i}: 重量={case['weight']}kg, 品类={case['category']}")
        print(f"  状态：{result.status}")
        print(f"  风险：{result.risk.value}")
        print(f"  类型：{result.anomaly_type.value}")
        print(f"  置信度：{result.confidence}")
