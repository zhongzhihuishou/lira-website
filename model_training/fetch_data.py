#!/usr/bin/env python3
"""
吨袋数据获取脚本
从绿袋云 API 获取吨袋编码、待分拣信息和投递数据

API 文档:
- 吨袋编码列表：https://www.lvdouge.com/openapi/delivery/sorting/bingbag/list
- 待分拣信息：https://www.lvdouge.com/openapi/delivery/sorting/list
- 投递详情：https://www.lvdouge.com/openapi/delivery/all/list?bagCode={bagCode}

需要配置 token（从 APP 或后台获取）
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import hmac
import base64

class LvDouGeAPI:
    """绿袋云 API 客户端"""
    
    BASE_URL = "https://www.lvdouge.com/openapi"
    
    def __init__(self, token: str = None, app_key: str = None, app_secret: str = None):
        """
        初始化 API 客户端
        
        Args:
            token: 用户 token（从 APP 登录获取）
            app_key: 应用 Key（如有）
            app_secret: 应用密钥（如有）
        """
        self.token = token
        self.app_key = app_key
        self.app_secret = app_secret
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)',
            'Content-Type': 'application/json',
        })
        
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'
            self.session.headers['token'] = token
    
    def _sign_request(self, params: Dict) -> Dict:
        """生成签名（如果需要）"""
        if not self.app_secret:
            return params
        
        # 按 key 排序
        sorted_params = sorted(params.items())
        param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
        param_str += f'&key={self.app_secret}'
        
        # MD5 签名
        sign = hashlib.md5(param_str.encode()).hexdigest().upper()
        params['sign'] = sign
        return params
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """发送 API 请求"""
        url = f"{self.BASE_URL}{endpoint}"
        
        if params:
            params = self._sign_request(params)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get('status') != 200:
                print(f"❌ API 错误：{result.get('msg', 'Unknown error')}")
                return None
            
            return result.get('data', {})
        
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络错误：{e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误：{e}")
            return None
    
    def get_bag_codes(self, page: int = 1, page_size: int = 100) -> Optional[Dict]:
        """
        获取吨袋编码列表
        
        Returns:
            {
                "list": [
                    {
                        "bagCode": "BB20260323001",
                        "deviceCode": "DEV001",
                        "status": 1,
                        "createTime": "2026-03-23 10:00:00"
                    }
                ],
                "total": 1000
            }
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        return self._request('/delivery/sorting/bingbag/list', params)
    
    def get_sorting_tasks(self, page: int = 1, page_size: int = 100) -> Optional[Dict]:
        """
        获取待分拣信息列表
        
        Returns:
            {
                "list": [
                    {
                        "id": 12345,
                        "bagCode": "BB20260323001",
                        "deviceCode": "DEV001",
                        "weight": 1.5,
                        "category": "可回收物",
                        "status": 0,  # 0:待分拣 1:已分拣
                        "createTime": "2026-03-23 10:00:00"
                    }
                ],
                "total": 500
            }
        """
        params = {
            'page': page,
            'page_size': page_size
        }
        return self._request('/delivery/sorting/list', params)
    
    def get_delivery_detail(self, bag_code: str) -> Optional[Dict]:
        """
        获取吨袋投递详情（包含图片）
        
        Args:
            bag_code: 吨袋编码
        
        Returns:
            {
                "bagCode": "BB20260323001",
                "deviceCode": "DEV001",
                "totalWeight": 15.5,
                "deliveries": [
                    {
                        "id": 1001,
                        "weight": 1.5,
                        "category": "可回收物",
                        "categoryCode": "RECYCLE",
                        "imageBefore": "https://...jpg",
                        "imageAfter": "https://...jpg",
                        "throwTime": "2026-03-23 10:00:00"
                    }
                ]
            }
        """
        params = {'bagCode': bag_code}
        return self._request('/delivery/all/list', params)
    
    def download_image(self, url: str, save_path: str) -> bool:
        """下载图片"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"❌ 下载失败 {url}: {e}")
            return False
    
    def fetch_all_data(self, output_dir: str = 'raw_data', max_bags: int = 1000):
        """
        批量获取所有数据
        
        Args:
            output_dir: 输出目录
            max_bags: 最大获取吨袋数
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 开始获取数据，目标：{max_bags} 个吨袋")
        print(f"📁 输出目录：{output_path}")
        
        # 1. 获取吨袋编码列表
        print("\n📦 步骤 1: 获取吨袋编码列表...")
        bag_codes = []
        page = 1
        
        while len(bag_codes) < max_bags:
            result = self.get_bag_codes(page=page, page_size=100)
            if not result or not result.get('list'):
                break
            
            bag_codes.extend([item['bagCode'] for item in result['list']])
            print(f"   第{page}页 - 获取{len(result['list'])}个，累计{len(bag_codes)}个")
            
            if len(result['list']) < 100:
                break
            page += 1
            time.sleep(0.5)  # 避免限流
        
        bag_codes = bag_codes[:max_bags]
        print(f"✅ 共获取 {len(bag_codes)} 个吨袋编码")
        
        # 保存吨袋编码
        with open(output_path / 'bag_codes.json', 'w') as f:
            json.dump(bag_codes, f, ensure_ascii=False, indent=2)
        
        # 2. 获取每个吨袋的投递详情
        print(f"\n📸 步骤 2: 获取投递详情和图片...")
        
        all_deliveries = []
        image_count = 0
        
        for i, bag_code in enumerate(bag_codes, 1):
            if i % 10 == 0:
                print(f"   进度：{i}/{len(bag_codes)}")
            
            detail = self.get_delivery_detail(bag_code)
            if not detail or not detail.get('deliveries'):
                continue
            
            deliveries = detail['deliveries']
            
            for delivery in deliveries:
                # 保存投递记录
                record = {
                    'bagCode': bag_code,
                    'deviceCode': detail.get('deviceCode'),
                    'totalWeight': detail.get('totalWeight'),
                    **delivery
                }
                all_deliveries.append(record)
                
                # 下载图片
                image_dir = output_path / 'images' / bag_code
                image_dir.mkdir(parents=True, exist_ok=True)
                
                for img_type in ['imageBefore', 'imageAfter']:
                    img_url = delivery.get(img_type)
                    if img_url:
                        img_name = f"{delivery['id']}_{img_type}.jpg"
                        img_path = image_dir / img_name
                        
                        if self.download_image(img_url, str(img_path)):
                            image_count += 1
                            delivery[f'{img_type}_path'] = str(img_path)
            
            time.sleep(0.3)  # 避免限流
        
        # 3. 保存投递数据
        with open(output_path / 'deliveries.json', 'w') as f:
            json.dump(all_deliveries, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 数据获取完成！")
        print(f"   📊 投递记录：{len(all_deliveries)} 条")
        print(f"   📷 下载图片：{image_count} 张")
        print(f"   📁 数据位置：{output_path}")
        
        return {
            'bag_codes': len(bag_codes),
            'deliveries': len(all_deliveries),
            'images': image_count
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='吨袋数据获取脚本')
    parser.add_argument('--token', type=str, help='API Token（从 APP 获取）')
    parser.add_argument('--app-key', type=str, help='App Key（可选）')
    parser.add_argument('--app-secret', type=str, help='App Secret（可选）')
    parser.add_argument('--output', type=str, default='raw_data', help='输出目录')
    parser.add_argument('--max-bags', type=int, default=1000, help='最大吨袋数')
    
    args = parser.parse_args()
    
    # 从配置文件读取 token（如果未提供）
    token = args.token
    config_path = Path(__file__).parent / 'config.json'
    
    if not token and config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            token = config.get('token')
    
    if not token:
        print("❌ 错误：缺少 token")
        print("\n获取 token 的方法：")
        print("1. 打开绿袋云 APP")
        print("2. 登录账号")
        print("3. 抓包获取 Authorization header 中的 token")
        print("4. 或者在 config.json 中配置：")
        print('   {"token": "your_token_here"}')
        print("\n用法示例：")
        print("  python fetch_data.py --token YOUR_TOKEN")
        return
    
    # 创建 API 客户端
    api = LvDouGeAPI(
        token=token,
        app_key=args.app_key,
        app_secret=args.app_secret
    )
    
    # 获取数据
    api.fetch_all_data(
        output_dir=args.output,
        max_bags=args.max_bags
    )


if __name__ == '__main__':
    main()
