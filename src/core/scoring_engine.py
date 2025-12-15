"""
评分引擎
计算节点的综合评分和匹配度
"""

from typing import List, Dict
import math

from .models import (
    Location, Edge, NodeVerification, UserProfile, State
)


class ScoringEngine:
    """
    评分引擎
    
    核心功能:
    1. 计算节点综合评分
    2. 计算用户偏好匹配度
    3. 考虑多个维度（验证、匹配、效率）
    
    数学模型:
    Score(v, σ, u) = Σᵢ wᵢ · fᵢ(v, σ, u)
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化评分引擎
        
        Args:
            config: 配置参数
        """
        self.config = config or self._default_config()
    
    def compute_score(self,
                     node: Location,
                     edges: List[Edge],
                     verification: NodeVerification,
                     profile: UserProfile,
                     state: State) -> float:
        """
        计算节点综合评分
        
        数学模型:
        Score = Σᵢ wᵢ · fᵢ
        
        其中因子包括:
        f1 = Match(node, profile)        # 偏好匹配
        f2 = Trust(verification)         # 可信度
        f3 = Quality(node)               # 质量
        f4 = Efficiency(edges)           # 效率
        f5 = Novelty(node, history)      # 新颖性
        f6 = 1 - Crowd(node)             # 避免拥挤
        
        Args:
            node: POI节点
            edges: 可达边列表
            verification: 验证数据
            profile: 用户画像
            state: 当前状态
            
        Returns:
            综合评分 ∈ [0, 1]
        """
        # 获取权重配置
        weights = self.config['score_weights']
        
        # f1: 偏好匹配度
        match_score = self.compute_match_score(node, profile)
        
        # f2: 可信度（四项原则）
        trust_score = verification.overall_trust_score
        
        # f3: 质量分数（评分）
        quality_score = self._compute_quality_score(verification)
        
        # f4: 效率分数（距离、时间）
        efficiency_score = self._compute_efficiency_score(edges, state)
        
        # f5: 新颖性（未访问过的更高）
        novelty_score = self._compute_novelty_score(node, state)
        
        # f6: 避免拥挤
        crowd_score = 1 - verification.predicted_crowd_level
        
        # 综合评分
        score = (
            weights['match'] * match_score +
            weights['trust'] * trust_score +
            weights['quality'] * quality_score +
            weights['efficiency'] * efficiency_score +
            weights['novelty'] * novelty_score +
            weights['crowd'] * crowd_score
        )
        
        # 归一化到 [0, 1]
        score = max(0.0, min(1.0, score))
        
        return score
    
    def compute_match_score(self,
                           node: Location,
                           profile: UserProfile) -> float:
        """
        计算用户偏好匹配度
        
        算法:
        1. 根据POI类型匹配用户目的
        2. 考虑体力消耗与用户体力偏好
        3. 考虑节奏与用户节奏偏好
        
        Args:
            node: POI节点
            profile: 用户画像
            
        Returns:
            匹配度 ∈ [0, 1]
        """
        scores = []
        
        # 1. 类型匹配
        type_match = self._match_poi_type_to_purpose(node, profile.purpose)
        scores.append(type_match)
        
        # 2. 体力匹配
        intensity_match = self._match_intensity(node, profile.intensity)
        scores.append(intensity_match)
        
        # 3. 节奏匹配
        pace_match = self._match_pace(node, profile.pace)
        scores.append(pace_match)
        
        # 4. 美食匹配（如果是餐厅）
        if node.type.value == 'restaurant' and profile.food_preference:
            food_match = self._match_food(node, profile.food_preference)
            scores.append(food_match)
        
        # 平均匹配度
        return sum(scores) / len(scores) if scores else 0.5
    
    def _match_poi_type_to_purpose(self,
                                    node: Location,
                                    purpose: Dict[str, float]) -> float:
        """
        POI类型与旅行目的匹配
        
        映射规则:
        - attraction → culture, leisure, adventure
        - restaurant → leisure, food
        - hotel → rest
        - shopping → shopping, leisure
        """
        type_to_purpose = {
            'attraction': ['culture', 'leisure', 'adventure', 'photography'],
            'restaurant': ['leisure', 'food'],
            'hotel': ['rest'],
            'shopping': ['shopping', 'leisure'],
            'entertainment': ['leisure', 'adventure']
        }
        
        mapped_purposes = type_to_purpose.get(node.type.value, ['leisure'])
        
        # 计算匹配分数
        scores = [purpose.get(p, 0.0) for p in mapped_purposes]
        return max(scores) if scores else 0.5
    
    def _match_intensity(self,
                        node: Location,
                        intensity_pref: Dict[str, float]) -> float:
        """
        体力消耗匹配
        
        估算POI的体力消耗，与用户偏好匹配
        """
        # 简化：基于访问时间估算体力消耗
        visit_time = node.average_visit_time
        
        if visit_time < 1.0:
            poi_intensity = 'very_low'
        elif visit_time < 2.0:
            poi_intensity = 'low'
        elif visit_time < 3.0:
            poi_intensity = 'medium'
        elif visit_time < 4.0:
            poi_intensity = 'high'
        else:
            poi_intensity = 'very_high'
        
        return intensity_pref.get(poi_intensity, 0.5)
    
    def _match_pace(self,
                   node: Location,
                   pace_pref: Dict[str, float]) -> float:
        """
        节奏匹配
        
        景点节奏与用户偏好匹配
        """
        # 简化：景点默认慢节奏，娱乐场所快节奏
        if node.type.value in ['attraction', 'restaurant']:
            poi_pace = 'slow'
        elif node.type.value == 'entertainment':
            poi_pace = 'fast'
        else:
            poi_pace = 'medium'
        
        return pace_pref.get(poi_pace, 0.5)
    
    def _match_food(self,
                   node: Location,
                   food_pref: Dict[str, float]) -> float:
        """
        美食匹配
        
        TODO: 需要POI的菜系标签
        """
        # 简化：返回默认值
        return 0.7
    
    def _compute_quality_score(self,
                               verification: NodeVerification) -> float:
        """
        质量分数
        
        基于清洗后的评分和评价率
        """
        # 评分归一化（假设满分5分）
        rating_score = verification.weighted_rating / 5.0
        
        # 正面评价率
        positive_score = verification.positive_rate
        
        # 综合
        return 0.6 * rating_score + 0.4 * positive_score
    
    def _compute_efficiency_score(self,
                                  edges: List[Edge],
                                  state: State) -> float:
        """
        效率分数
        
        考虑距离和时间成本
        
        算法:
        选择最佳边（时间最短）
        Efficiency = 1 / (1 + time)
        """
        if not edges:
            return 0.5
        
        # 选择时间最短的边
        best_edge = min(edges, key=lambda e: e.time)
        
        # 效率分数（时间越短分数越高）
        # 使用衰减函数
        efficiency = math.exp(-best_edge.time / 2.0)
        
        return efficiency
    
    def _compute_novelty_score(self,
                              node: Location,
                              state: State) -> float:
        """
        新颖性分数
        
        未访问过的节点新颖性更高
        """
        if node.id in state.visited_history:
            return 0.0  # 已访问过
        else:
            return 1.0  # 未访问
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            'score_weights': {
                'match': 0.25,       # 偏好匹配
                'trust': 0.20,       # 可信度
                'quality': 0.20,     # 质量
                'efficiency': 0.15,  # 效率
                'novelty': 0.10,     # 新颖性
                'crowd': 0.10        # 避免拥挤
            }
        }
