"""
验证引擎
实现四项基本原则的验证逻辑
"""

from typing import List, Dict, Optional
import numpy as np
from datetime import datetime

from .models import (
    Location, State, PlanningSession, NodeVerification,
    DataSource
)


class VerificationEngine:
    """
    验证引擎 - 实现四项基本原则
    
    原则1: 多源数据交叉验证
    原则2: 大数据清洗
    原则3: 空间合理性验证
    原则4: 时间合理性验证
    """
    
    def __init__(self,
                 multi_source_collector,
                 neural_net_service,
                 gaode_api_client):
        """
        初始化验证引擎
        
        Args:
            multi_source_collector: 多源数据采集器
            neural_net_service: 神经网络服务
            gaode_api_client: 高德API客户端
        """
        self.collector = multi_source_collector
        self.nn_service = neural_net_service
        self.gaode_api = gaode_api_client
        
        # 配置
        self.config = {
            'consistency_threshold': 0.8,
            'fake_threshold': 0.3,
            'min_reviews': 10,
            'crowd_threshold': 0.7,
        }
    
    def verify(self,
              node: Location,
              state: State,
              session: PlanningSession) -> NodeVerification:
        """
        完整验证流程
        
        执行四项基本原则的验证
        
        Args:
            node: 待验证的节点
            state: 当前状态
            session: 规划会话
            
        Returns:
            验证结果
        """
        # 原则1: 多源数据交叉验证
        multi_source_result = self._multi_source_verification(node)
        
        # 原则2: 大数据清洗
        cleaned_result = self._data_cleaning(node, multi_source_result)
        
        # 原则3: 空间合理性验证
        spatial_result = self._spatial_verification(node, state)
        
        # 原则4: 时间合理性验证
        temporal_result = self._temporal_verification(node, state, session)
        
        # 构建验证数据
        verification = NodeVerification(
            # 原则1
            data_sources=multi_source_result['sources'],
            consistency_score=multi_source_result['consistency'],
            weighted_rating=multi_source_result['weighted_rating'],
            rating_variance=multi_source_result['variance'],
            
            # 原则2
            total_reviews=cleaned_result['total_reviews'],
            valid_reviews=cleaned_result['valid_reviews'],
            fake_rate=cleaned_result['fake_rate'],
            positive_rate=cleaned_result['positive_rate'],
            negative_rate=cleaned_result['negative_rate'],
            key_positive_words=cleaned_result['key_positive'],
            key_negative_words=cleaned_result['key_negative'],
            
            # 原则3
            spatial_score=spatial_result['score'],
            distance_from_current=spatial_result['distance'],
            detour_rate=spatial_result['detour_rate'],
            connectivity_score=spatial_result['connectivity'],
            
            # 原则4
            temporal_score=temporal_result['score'],
            is_open=temporal_result['is_open'],
            predicted_crowd_level=temporal_result['crowd_level'],
            optimal_visit_time=temporal_result['optimal_time'],
            time_sufficient=temporal_result['time_sufficient']
        )
        
        return verification
    
    def _multi_source_verification(self, node: Location) -> Dict:
        """
        原则1: 多源数据交叉验证
        
        数学模型:
        - Consistency = 1 - σ/μ
        - Weighted_Rating = Σ(wᵢ × rᵢ × trustᵢ)
        
        算法:
        1. 从多个数据源收集数据（高德、携程、马蜂窝等）
        2. 计算评分一致性
        3. 加权融合
        
        Args:
            node: POI节点
            
        Returns:
            验证结果字典
        """
        try:
            # 1. 收集多源数据
            sources_data = self.collector.collect_multi_source(node)
            
            # 构建数据源列表
            sources = []
            ratings = []
            
            for source_name, data in sources_data.items():
                if data and 'rating' in data:
                    ds = DataSource(
                        name=source_name,
                        rating=data['rating'],
                        review_count=data.get('review_count', 0),
                        last_update=datetime.now(),
                        weight=data.get('weight', 0.33),
                        credibility=data.get('credibility', 1.0)
                    )
                    sources.append(ds)
                    ratings.append(data['rating'])
            
            if not ratings:
                # 没有数据源，返回默认值
                return self._default_multi_source_result()
            
            # 2. 计算一致性
            ratings_array = np.array(ratings)
            mu = np.mean(ratings_array)
            sigma = np.std(ratings_array)
            
            # Consistency = 1 - σ/μ
            consistency = 1 - (sigma / mu if mu > 0 else 1.0)
            consistency = max(0.0, min(1.0, consistency))  # 限制在[0, 1]
            
            # 3. 加权融合
            weighted_rating = sum(
                ds.rating * ds.weight * ds.credibility 
                for ds in sources
            )
            total_weight = sum(ds.weight for ds in sources)
            if total_weight > 0:
                weighted_rating /= total_weight
            
            return {
                'sources': sources,
                'consistency': consistency,
                'weighted_rating': weighted_rating,
                'mu': mu,
                'sigma': sigma,
                'variance': sigma ** 2
            }
            
        except Exception as e:
            print(f"Multi-source verification error: {e}")
            return self._default_multi_source_result()
    
    def _data_cleaning(self,
                      node: Location,
                      multi_source_result: Dict) -> Dict:
        """
        原则2: 大数据清洗
        
        算法:
        1. 收集所有评论
        2. 使用神经网络检测虚假评论
        3. 过滤虚假评论
        4. 情感分析提取正负面
        
        Args:
            node: POI节点
            multi_source_result: 多源验证结果
            
        Returns:
            清洗结果字典
        """
        try:
            # 1. 收集评论
            all_reviews = self.collector.collect_reviews(node)
            
            if not all_reviews or len(all_reviews) < self.config['min_reviews']:
                return self._default_cleaning_result()
            
            # 2. 检测虚假评论（神经网络）
            if self.nn_service:
                fake_scores = []
                for review in all_reviews:
                    try:
                        score = self.nn_service.detect_fake(review['text'])
                        fake_scores.append(score)
                    except:
                        fake_scores.append(0.0)  # 默认认为真实
            else:
                fake_scores = [0.0] * len(all_reviews)
            
            # 3. 过滤虚假评论
            threshold = self.config['fake_threshold']
            valid_reviews = [
                review for review, score in zip(all_reviews, fake_scores)
                if score <= threshold
            ]
            
            fake_rate = 1 - len(valid_reviews) / len(all_reviews)
            
            # 4. 情感分析
            if self.nn_service and valid_reviews:
                sentiments = []
                for review in valid_reviews:
                    try:
                        sentiment = self.nn_service.sentiment_analysis(
                            review['text']
                        )
                        sentiments.append(sentiment)
                    except:
                        sentiments.append(0.5)  # 默认中性
                
                positive_count = sum(1 for s in sentiments if s > 0.6)
                negative_count = sum(1 for s in sentiments if s < 0.4)
                
                positive_rate = positive_count / len(sentiments)
                negative_rate = negative_count / len(sentiments)
            else:
                positive_rate = 0.7  # 默认值
                negative_rate = 0.1
            
            # 5. 提取关键词（TODO: 使用NLP）
            key_positive = ['服务好', '环境好', '值得']
            key_negative = ['人多', '排队', '贵']
            
            return {
                'total_reviews': len(all_reviews),
                'valid_reviews': len(valid_reviews),
                'fake_rate': fake_rate,
                'positive_rate': positive_rate,
                'negative_rate': negative_rate,
                'key_positive': key_positive,
                'key_negative': key_negative
            }
            
        except Exception as e:
            print(f"Data cleaning error: {e}")
            return self._default_cleaning_result()
    
    def _spatial_verification(self,
                             node: Location,
                             state: State) -> Dict:
        """
        原则3: 空间合理性验证
        
        数学模型:
        Spatial_Score = w1·D + w2·T + w3·C
        其中:
            D = 1 - (actual_dist / direct_dist - 1)  # 绕路程度
            T = 1 - (actual_time / optimal_time - 1) # 时间效率
            C = connectivity_score                    # 连通性
        
        算法:
        1. 计算直线距离
        2. 调用高德API获取实际路径
        3. 计算绕路率
        4. 使用GNN评估空间关系（可选）
        
        Args:
            node: POI节点
            state: 当前状态
            
        Returns:
            空间验证结果
        """
        current = state.current_location
        
        try:
            # 1. 计算直线距离
            direct_dist = self._haversine(current, node)
            
            # 2. 获取实际路径（调用高德API）
            # TODO: 实际调用高德API
            actual_dist = direct_dist * 1.3  # 简化：直线距离 * 1.3
            
            # 3. 计算绕路率
            detour_rate = (actual_dist / direct_dist - 1) if direct_dist > 0 else 0
            detour_rate = max(0.0, detour_rate)
            
            # 4. 绕路分数（绕路越少分数越高）
            D = 1 - min(detour_rate, 1.0)
            
            # 5. 连通性评分（简化：假设都连通）
            connectivity = 1.0
            
            # 6. GNN空间关系评分（可选）
            if self.nn_service:
                try:
                    gnn_score = self.nn_service.gnn_spatial(current, node)
                except:
                    gnn_score = 0.8
            else:
                gnn_score = 0.8
            
            # 7. 综合评分
            score = 0.4 * D + 0.3 * connectivity + 0.3 * gnn_score
            score = max(0.0, min(1.0, score))
            
            return {
                'score': score,
                'distance': direct_dist,
                'actual_distance': actual_dist,
                'detour_rate': detour_rate,
                'connectivity': connectivity,
                'gnn_score': gnn_score
            }
            
        except Exception as e:
            print(f"Spatial verification error: {e}")
            return {
                'score': 0.7,
                'distance': 5.0,
                'actual_distance': 6.5,
                'detour_rate': 0.3,
                'connectivity': 1.0,
                'gnn_score': 0.8
            }
    
    def _temporal_verification(self,
                              node: Location,
                              state: State,
                              session: PlanningSession) -> Dict:
        """
        原则4: 时间合理性验证
        
        数学模型:
        Temporal_Score = w1·O + w2·C + w3·R
        其中:
            O = 1 if is_open else 0           # 营业时间
            C = 1 - crowd_level                # 不拥挤
            R = remaining_time / required_time # 时间充足
        
        算法:
        1. 检查营业时间
        2. LSTM预测拥挤度
        3. 计算时间充足性
        
        Args:
            node: POI节点
            state: 当前状态
            session: 规划会话
            
        Returns:
            时间验证结果
        """
        try:
            # 1. 检查营业时间
            arrival_time = state.current_time
            is_open = node.is_open(arrival_time)
            O = 1.0 if is_open else 0.0
            
            # 2. 预测拥挤度（LSTM）
            if self.nn_service:
                try:
                    crowd_level = self.nn_service.lstm_predict_crowd(
                        node, arrival_time
                    )
                except:
                    crowd_level = 0.4  # 默认中等拥挤
            else:
                crowd_level = 0.4
            
            C = 1 - crowd_level
            
            # 3. 时间充足性
            remaining = session.duration - state.current_time
            required = node.average_visit_time + 1.0  # 加上交通时间
            
            time_sufficient = remaining >= required
            R = min(remaining / required, 1.0) if required > 0 else 0.0
            
            # 4. 综合评分
            score = 0.3 * O + 0.4 * C + 0.3 * R
            score = max(0.0, min(1.0, score))
            
            # 5. 最佳访问时间（TODO: 基于历史数据）
            optimal_time = (9.0, 11.0)  # 默认9-11点
            
            return {
                'score': score,
                'is_open': is_open,
                'crowd_level': crowd_level,
                'time_sufficient': time_sufficient,
                'remaining_time': remaining,
                'required_time': required,
                'optimal_time': optimal_time
            }
            
        except Exception as e:
            print(f"Temporal verification error: {e}")
            return {
                'score': 0.7,
                'is_open': True,
                'crowd_level': 0.5,
                'time_sufficient': True,
                'remaining_time': 10.0,
                'required_time': 2.0,
                'optimal_time': (9.0, 11.0)
            }
    
    def _haversine(self, loc1: Location, loc2: Location) -> float:
        """计算球面距离（Haversine公式）"""
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
    
    def _default_multi_source_result(self) -> Dict:
        """默认多源验证结果"""
        return {
            'sources': [],
            'consistency': 0.7,
            'weighted_rating': 4.0,
            'mu': 4.0,
            'sigma': 0.3,
            'variance': 0.09
        }
    
    def _default_cleaning_result(self) -> Dict:
        """默认数据清洗结果"""
        return {
            'total_reviews': 0,
            'valid_reviews': 0,
            'fake_rate': 0.0,
            'positive_rate': 0.7,
            'negative_rate': 0.1,
            'key_positive': [],
            'key_negative': []
        }
