"""
多源数据采集器
从多个数据源收集POI信息和评论
"""

from typing import List, Dict, Optional
from datetime import datetime
import random

from ..core.models import Location


class MultiSourceCollector:
    """
    多源数据采集器
    
    数据源:
    1. 高德地图
    2. 携程（模拟）
    3. 马蜂窝（模拟）
    4. 大众点评（模拟）
    5. 小红书（模拟）
    
    注: 实际项目中应该使用真实API或爬虫
        这里为了Demo，部分数据源使用模拟数据
    """
    
    def __init__(self, gaode_client):
        """
        初始化采集器
        
        Args:
            gaode_client: 高德API客户端
        """
        self.gaode = gaode_client
        
        # 数据源权重配置
        self.source_weights = {
            'gaode': 0.40,
            'ctrip': 0.25,
            'mafengwo': 0.15,
            'dianping': 0.15,
            'xiaohongshu': 0.05
        }
        
        # 数据源可信度
        self.source_credibility = {
            'gaode': 1.0,
            'ctrip': 0.95,
            'mafengwo': 0.90,
            'dianping': 0.90,
            'xiaohongshu': 0.85
        }
    
    def collect_multi_source(self, node: Location) -> Dict[str, Dict]:
        """
        从多个数据源收集POI数据
        
        Args:
            node: POI节点
            
        Returns:
            数据源字典 {source_name: data}
        """
        results = {}
        
        # 1. 高德地图（优先级最高）
        try:
            gaode_data = self._collect_from_gaode(node)
            if gaode_data:
                results['gaode'] = {
                    **gaode_data,
                    'weight': self.source_weights['gaode'],
                    'credibility': self.source_credibility['gaode']
                }
        except Exception as e:
            print(f"⚠️ 高德数据采集失败: {e}")
        
        # 2. 携程（模拟）
        try:
            ctrip_data = self._collect_from_ctrip_mock(node)
            if ctrip_data:
                results['ctrip'] = {
                    **ctrip_data,
                    'weight': self.source_weights['ctrip'],
                    'credibility': self.source_credibility['ctrip']
                }
        except Exception as e:
            print(f"⚠️ 携程数据采集失败: {e}")
        
        # 3. 马蜂窝（模拟）
        try:
            mafengwo_data = self._collect_from_mafengwo_mock(node)
            if mafengwo_data:
                results['mafengwo'] = {
                    **mafengwo_data,
                    'weight': self.source_weights['mafengwo'],
                    'credibility': self.source_credibility['mafengwo']
                }
        except Exception as e:
            print(f"⚠️ 马蜂窝数据采集失败: {e}")
        
        # 4. 大众点评（模拟，仅餐厅）
        if node.type.value == 'restaurant':
            try:
                dianping_data = self._collect_from_dianping_mock(node)
                if dianping_data:
                    results['dianping'] = {
                        **dianping_data,
                        'weight': self.source_weights['dianping'],
                        'credibility': self.source_credibility['dianping']
                    }
            except Exception as e:
                print(f"⚠️ 大众点评数据采集失败: {e}")
        
        # 确保至少有一个数据源
        if not results:
            print(f"⚠️ 所有数据源采集失败，使用默认数据")
            results['default'] = {
                'rating': 4.0,
                'review_count': 100,
                'source': 'default',
                'last_update': datetime.now(),
                'weight': 1.0,
                'credibility': 0.5
            }
        
        return results
    
    def collect_reviews(self, node: Location, limit: int = 100) -> List[Dict]:
        """
        收集评论
        
        Args:
            node: POI节点
            limit: 最大评论数
            
        Returns:
            评论列表
        """
        reviews = []
        
        # 从各个数据源收集评论
        reviews.extend(self._collect_gaode_reviews_mock(node, limit // 3))
        reviews.extend(self._collect_ctrip_reviews_mock(node, limit // 3))
        reviews.extend(self._collect_other_reviews_mock(node, limit // 3))
        
        return reviews[:limit]
    
    def _collect_from_gaode(self, node: Location) -> Optional[Dict]:
        """
        从高德地图收集数据
        
        实际项目中应该调用高德API获取POI详情
        这里简化处理
        """
        try:
            # 这里应该调用 gaode.get_poi_detail(node.id)
            # 简化：返回基础数据
            return {
                'rating': 4.5 + random.random() * 0.5,
                'review_count': random.randint(1000, 50000),
                'source': 'gaode',
                'last_update': datetime.now()
            }
        except Exception as e:
            print(f"Error collecting from Gaode: {e}")
            return None
    
    def _collect_from_ctrip_mock(self, node: Location) -> Optional[Dict]:
        """
        从携程收集数据（模拟）
        
        实际项目中应该：
        1. 使用携程API（如果有）
        2. 或者爬取携程网站数据
        """
        # 模拟数据，评分会有小的波动
        base_rating = 4.5
        variation = random.uniform(-0.3, 0.3)
        
        return {
            'rating': base_rating + variation,
            'review_count': random.randint(800, 20000),
            'source': 'ctrip',
            'last_update': datetime.now()
        }
    
    def _collect_from_mafengwo_mock(self, node: Location) -> Optional[Dict]:
        """从马蜂窝收集数据（模拟）"""
        base_rating = 4.5
        variation = random.uniform(-0.2, 0.4)
        
        return {
            'rating': base_rating + variation,
            'review_count': random.randint(500, 10000),
            'source': 'mafengwo',
            'last_update': datetime.now()
        }
    
    def _collect_from_dianping_mock(self, node: Location) -> Optional[Dict]:
        """从大众点评收集数据（模拟）"""
        base_rating = 4.3
        variation = random.uniform(-0.2, 0.3)
        
        return {
            'rating': base_rating + variation,
            'review_count': random.randint(500, 15000),
            'source': 'dianping',
            'last_update': datetime.now()
        }
    
    def _collect_gaode_reviews_mock(self, node: Location, limit: int) -> List[Dict]:
        """收集高德评论（模拟）"""
        reviews = []
        
        positive_templates = [
            "服务很好，环境不错",
            "值得推荐，体验很棒",
            "性价比高，下次还会来",
            "景色优美，令人难忘",
            "非常满意，超出预期"
        ]
        
        negative_templates = [
            "人太多了，排队很久",
            "价格有点贵",
            "环境一般，有待改善",
            "服务态度需要提升"
        ]
        
        for i in range(limit):
            is_positive = random.random() > 0.15  # 85%正面
            
            if is_positive:
                text = random.choice(positive_templates)
                rating = random.uniform(4.0, 5.0)
            else:
                text = random.choice(negative_templates)
                rating = random.uniform(2.0, 3.5)
            
            reviews.append({
                'text': text,
                'rating': rating,
                'source': 'gaode',
                'timestamp': datetime.now(),
                'user_id': f"user_{random.randint(1000, 9999)}"
            })
        
        return reviews
    
    def _collect_ctrip_reviews_mock(self, node: Location, limit: int) -> List[Dict]:
        """收集携程评论（模拟）"""
        reviews = []
        
        templates = [
            "位置便利，交通方便",
            "设施齐全，服务周到",
            "环境优雅，值得一去",
            "整体满意，推荐给大家"
        ]
        
        for i in range(limit):
            reviews.append({
                'text': random.choice(templates),
                'rating': random.uniform(4.0, 5.0),
                'source': 'ctrip',
                'timestamp': datetime.now(),
                'user_id': f"user_{random.randint(1000, 9999)}"
            })
        
        return reviews
    
    def _collect_other_reviews_mock(self, node: Location, limit: int) -> List[Dict]:
        """收集其他来源评论（模拟）"""
        reviews = []
        
        # 模拟一些虚假评论（用于测试检测算法）
        fake_templates = [
            "超级好超级好超级好",  # 重复词汇
            "老板人很好老板人很好",  # 重复句式
            "五星好评五星好评五星好评"  # 明显刷单
        ]
        
        normal_templates = [
            "总体还不错，值得一去",
            "体验良好，环境舒适",
            "服务到位，很满意"
        ]
        
        for i in range(limit):
            # 10%概率是虚假评论
            is_fake = random.random() < 0.1
            
            if is_fake:
                text = random.choice(fake_templates)
            else:
                text = random.choice(normal_templates)
            
            reviews.append({
                'text': text,
                'rating': random.uniform(4.0, 5.0),
                'source': 'other',
                'timestamp': datetime.now(),
                'user_id': f"user_{random.randint(1000, 9999)}"
            })
        
        return reviews
