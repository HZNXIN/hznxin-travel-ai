"""
神经网络服务 - 提供AI能力支持

当前为Mock实现，返回合理的默认值
未来可接入真实的神经网络模型（BERT、GAN、GNN、LSTM等）
"""

from typing import List, Dict, Optional, Tuple
import random
from datetime import datetime

from .models import Location, UserProfile


class NeuralNetService:
    """
    神经网络服务
    
    提供AI能力：
    1. 用户画像提取（BERT）
    2. 虚假评论检测（GAN）
    3. 空间关系建模（GNN）
    4. 拥挤度预测（LSTM）
    5. 情感分析（NLP）
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化神经网络服务
        
        Args:
            config: 配置参数（模型路径、API密钥等）
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        
        # 模型状态
        self.models_loaded = False
        
        print(f"🧠 NeuralNetService初始化 (enabled={self.enabled})")
    
    def extract_user_profile(self, 
                            user_input: str,
                            history: List[Dict]) -> UserProfile:
        """
        从用户输入提取用户画像
        
        使用BERT理解用户意图和偏好
        
        Args:
            user_input: 用户输入的自然语言
            history: 历史行为数据
            
        Returns:
            用户画像
        """
        if not self.enabled:
            return self._default_user_profile(user_input)
        
        # TODO: 接入真实BERT模型
        # profile = self.bert_model.predict(user_input)
        
        return self._default_user_profile(user_input)
    
    def detect_fake(self, review_text: str) -> float:
        """
        检测评论是否为虚假评论
        
        使用GAN模型检测
        
        Args:
            review_text: 评论文本
            
        Returns:
            虚假概率 [0, 1]，越高越可能是虚假评论
        """
        if not self.enabled:
            # Mock实现：随机返回较低的虚假率
            return random.uniform(0.0, 0.15)
        
        # TODO: 接入真实GAN模型
        # fake_prob = self.gan_model.predict(review_text)
        
        return random.uniform(0.0, 0.15)
    
    def sentiment_analysis(self, text: str) -> float:
        """
        情感分析
        
        Args:
            text: 文本内容
            
        Returns:
            情感分数 [0, 1]
            0 = 非常负面，0.5 = 中性，1 = 非常正面
        """
        if not self.enabled:
            # Mock实现：偏向正面
            return random.uniform(0.6, 0.9)
        
        # TODO: 接入真实情感分析模型
        # sentiment = self.sentiment_model.predict(text)
        
        return random.uniform(0.6, 0.9)
    
    def gnn_spatial(self, 
                   from_loc: Location,
                   to_loc: Location) -> float:
        """
        GNN空间关系评分
        
        使用图神经网络评估两个POI之间的空间关系合理性
        
        Args:
            from_loc: 起点
            to_loc: 终点
            
        Returns:
            空间关系评分 [0, 1]
        """
        if not self.enabled:
            # Mock实现：基于距离的简单评分
            distance = self._haversine_distance(from_loc, to_loc)
            if distance < 2.0:
                return 0.95
            elif distance < 5.0:
                return 0.85
            elif distance < 10.0:
                return 0.75
            else:
                return 0.65
        
        # TODO: 接入真实GNN模型
        # score = self.gnn_model.predict(from_loc, to_loc)
        
        distance = self._haversine_distance(from_loc, to_loc)
        return max(0.5, 1.0 - distance / 20.0)
    
    def lstm_predict_crowd(self,
                          poi: Location,
                          time: float) -> float:
        """
        LSTM预测拥挤度
        
        基于历史数据预测某个时间点的拥挤程度
        
        Args:
            poi: POI位置
            time: 时间（小时）
            
        Returns:
            拥挤度 [0, 1]
        """
        if not self.enabled:
            # Mock实现：基于时间的简单估算
            hour = int(time % 24)
            
            # 景点拥挤度模式
            if poi.type.value == 'attraction':
                if 9 <= hour < 11:  # 早上人少
                    return random.uniform(0.2, 0.4)
                elif 11 <= hour < 15:  # 中午高峰
                    return random.uniform(0.6, 0.8)
                elif 15 <= hour < 18:  # 下午较多
                    return random.uniform(0.4, 0.6)
                else:  # 其他时间少
                    return random.uniform(0.1, 0.3)
            
            # 餐厅拥挤度模式
            elif poi.type.value == 'restaurant':
                if 11 <= hour < 13 or 17 <= hour < 19:  # 用餐高峰
                    return random.uniform(0.7, 0.9)
                else:
                    return random.uniform(0.2, 0.4)
            
            # 其他类型
            return random.uniform(0.3, 0.5)
        
        # TODO: 接入真实LSTM模型
        # crowd = self.lstm_model.predict(poi, time)
        
        return random.uniform(0.3, 0.6)
    
    def _default_user_profile(self, user_input: str) -> UserProfile:
        """
        根据用户输入生成默认画像
        
        简单关键词匹配
        """
        user_input_lower = user_input.lower()
        
        # 旅行目的
        purpose = {}
        if any(kw in user_input_lower for kw in ['文化', '历史', '博物馆', '园林']):
            purpose['culture'] = 0.8
        if any(kw in user_input_lower for kw in ['休闲', '放松', '度假']):
            purpose['leisure'] = 0.7
        if any(kw in user_input_lower for kw in ['美食', '吃', '餐厅']):
            purpose['food'] = 0.8
        if any(kw in user_input_lower for kw in ['购物', '买']):
            purpose['shopping'] = 0.7
        if any(kw in user_input_lower for kw in ['冒险', '刺激', '探险']):
            purpose['adventure'] = 0.8
        
        # 如果没有匹配到任何关键词，默认为休闲+文化
        if not purpose:
            purpose = {'leisure': 0.6, 'culture': 0.5}
        
        # 体力强度（默认中等）
        intensity = {'low': 0.5, 'medium': 0.4, 'high': 0.1}
        if any(kw in user_input_lower for kw in ['轻松', '慢', '悠闲']):
            intensity = {'low': 0.8, 'medium': 0.2, 'high': 0.0}
        elif any(kw in user_input_lower for kw in ['暴走', '深度', '多']):
            intensity = {'low': 0.0, 'medium': 0.3, 'high': 0.7}
        
        # 节奏
        pace = {'slow': 0.6, 'medium': 0.3, 'fast': 0.1}
        if any(kw in user_input_lower for kw in ['慢', '悠闲']):
            pace = {'slow': 0.9, 'medium': 0.1, 'fast': 0.0}
        elif any(kw in user_input_lower for kw in ['快', '紧凑', '多去']):
            pace = {'slow': 0.0, 'medium': 0.3, 'fast': 0.7}
        
        # 预算等级
        budget_level = 'medium'
        if any(kw in user_input_lower for kw in ['穷游', '省钱', '便宜']):
            budget_level = 'low'
        elif any(kw in user_input_lower for kw in ['奢华', '高端', '豪华']):
            budget_level = 'luxury'
        
        # 避免拥挤偏好
        avoid_crowd = 0.5
        if any(kw in user_input_lower for kw in ['人少', '安静', '避开']):
            avoid_crowd = 0.9
        
        return UserProfile(
            purpose=purpose,
            intensity=intensity,
            pace=pace,
            food_preference={},
            budget_level=budget_level,
            avoid_crowd_preference=avoid_crowd
        )
    
    def _haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """计算两点间距离（km）"""
        import math
        
        R = 6371  # 地球半径（km）
        
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def enable_models(self):
        """启用真实模型"""
        self.enabled = True
        self.models_loaded = True
        print("✅ 神经网络模型已启用")
    
    def disable_models(self):
        """禁用模型，使用Mock"""
        self.enabled = False
        print("⚠️ 神经网络模型已禁用，使用Mock实现")
