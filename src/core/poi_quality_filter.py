"""
POI质量过滤器
确保推荐的POI具有足够的价值：可玩性、可观性、热度、历史性
不能仅凭距离就推荐，必须保证质量
"""

from typing import Dict, List
from dataclasses import dataclass

from .models import Location, POIType, NodeVerification


@dataclass
class POIQualityScore:
    """POI质量评分"""
    playability: float  # 可玩性 [0, 1]
    viewability: float  # 可观性 [0, 1]
    popularity: float   # 热度 [0, 1]
    history: float      # 历史性 [0, 1]
    overall: float      # 综合质量 [0, 1]
    
    def is_qualified(self, min_score: float = 0.5) -> bool:
        """是否达到推荐标准"""
        return self.overall >= min_score


class POIQualityFilter:
    """
    POI质量过滤器
    
    核心理念：不是所有POI都值得推荐
    只推荐真正有价值的地点
    """
    
    def __init__(self):
        # 质量阈值配置
        self.config = {
            'min_overall_score': 0.5,      # 最低综合分数
            'min_review_count': 50,        # 最低评论数
            'min_rating': 4.0,             # 最低评分
            'min_playability': 0.3,        # 最低可玩性
            'weights': {
                'playability': 0.30,       # 可玩性权重
                'viewability': 0.25,       # 可观性权重
                'popularity': 0.25,        # 热度权重
                'history': 0.20            # 历史性权重
            }
        }
    
    def evaluate_quality(self, 
                        poi: Location, 
                        verification: NodeVerification) -> POIQualityScore:
        """
        评估POI质量
        
        Args:
            poi: POI节点
            verification: 验证数据
            
        Returns:
            质量评分
        """
        # 1. 可玩性评估
        playability = self._evaluate_playability(poi, verification)
        
        # 2. 可观性评估
        viewability = self._evaluate_viewability(poi, verification)
        
        # 3. 热度评估
        popularity = self._evaluate_popularity(poi, verification)
        
        # 4. 历史性评估
        history = self._evaluate_history(poi, verification)
        
        # 5. 综合评分
        weights = self.config['weights']
        overall = (
            weights['playability'] * playability +
            weights['viewability'] * viewability +
            weights['popularity'] * popularity +
            weights['history'] * history
        )
        
        return POIQualityScore(
            playability=playability,
            viewability=viewability,
            popularity=popularity,
            history=history,
            overall=overall
        )
    
    def is_worth_recommending(self, 
                             poi: Location,
                             verification: NodeVerification) -> bool:
        """
        判断POI是否值得推荐
        
        核心逻辑：
        1. 必须有足够的评论数（不推荐冷门小店）
        2. 必须有足够的评分（不推荐差评场所）
        3. 必须有一定的可玩性（不推荐路过性场所）
        4. 综合质量必须达标
        
        Args:
            poi: POI节点
            verification: 验证数据
            
        Returns:
            是否值得推荐
        """
        # 1. 评论数检查
        if verification.valid_reviews < self.config['min_review_count']:
            return False
        
        # 2. 评分检查
        if verification.weighted_rating < self.config['min_rating']:
            return False
        
        # 3. 质量评估
        quality = self.evaluate_quality(poi, verification)
        
        # 4. 可玩性基本要求
        if quality.playability < self.config['min_playability']:
            return False
        
        # 5. 综合质量检查
        if not quality.is_qualified(self.config['min_overall_score']):
            return False
        
        return True
    
    def _evaluate_playability(self, 
                             poi: Location, 
                             verification: NodeVerification) -> float:
        """
        评估可玩性
        
        考虑因素:
        - 建议游玩时长（越长可玩性越高）
        - POI类型（景点 > 商场 > 路过点）
        - 活动丰富度
        """
        score = 0.0
        
        # 1. 基于游玩时长
        visit_time = poi.average_visit_time
        if visit_time >= 3.0:
            score += 0.5  # 3小时以上，高可玩性
        elif visit_time >= 1.5:
            score += 0.3  # 1.5-3小时，中等
        elif visit_time >= 0.5:
            score += 0.15  # 0.5-1.5小时，较低
        else:
            score += 0.05  # 小于0.5小时，几乎无可玩性
        
        # 2. 基于POI类型
        type_scores = {
            'attraction': 0.4,      # 景点
            'restaurant': 0.2,      # 餐厅（主要功能是吃）
            'hotel': 0.1,          # 酒店（主要功能是住）
            'shopping': 0.3,       # 商场
            'entertainment': 0.35,  # 娱乐场所
            'transport_hub': 0.0   # 交通枢纽（无可玩性）
        }
        score += type_scores.get(poi.type.value, 0.2)
        
        # 3. 基于评论中的关键词
        positive_keywords = verification.key_positive_words
        playability_keywords = ['好玩', '有趣', '值得', '推荐', '精彩', '丰富']
        matched = sum(1 for kw in playability_keywords if kw in str(positive_keywords))
        score += min(matched * 0.05, 0.1)
        
        return min(score, 1.0)
    
    def _evaluate_viewability(self,
                             poi: Location,
                             verification: NodeVerification) -> float:
        """
        评估可观性
        
        考虑因素:
        - 是否有景观价值
        - 建筑美学
        - 拍照打卡价值
        """
        score = 0.0
        
        # 1. 基于类型
        type_scores = {
            'attraction': 0.6,      # 景点通常有观赏价值
            'restaurant': 0.3,      # 部分餐厅环境好
            'hotel': 0.2,
            'shopping': 0.25,
            'entertainment': 0.3,
            'transport_hub': 0.1
        }
        score += type_scores.get(poi.type.value, 0.2)
        
        # 2. 基于评论关键词
        positive_keywords = verification.key_positive_words
        view_keywords = ['美', '漂亮', '风景', '景色', '拍照', '打卡', '壮观']
        matched = sum(1 for kw in view_keywords if kw in str(positive_keywords))
        score += min(matched * 0.08, 0.2)
        
        # 3. 基于评分（高评分通常意味着体验好，包括视觉）
        if verification.weighted_rating >= 4.8:
            score += 0.2
        elif verification.weighted_rating >= 4.5:
            score += 0.15
        elif verification.weighted_rating >= 4.0:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_popularity(self,
                            poi: Location,
                            verification: NodeVerification) -> float:
        """
        评估热度
        
        考虑因素:
        - 评论数量
        - 评分高低
        - 数据源数量
        """
        score = 0.0
        
        # 1. 基于评论数（对数缩放）
        import math
        review_count = verification.valid_reviews
        if review_count > 0:
            # log10(10000) = 4, 1万条评论 → 1.0分
            score += min(math.log10(review_count) / 4.0, 0.4)
        
        # 2. 基于评分
        rating = verification.weighted_rating
        if rating >= 4.8:
            score += 0.3
        elif rating >= 4.5:
            score += 0.25
        elif rating >= 4.0:
            score += 0.15
        else:
            score += 0.05
        
        # 3. 基于数据源数量（越多说明越知名）
        source_count = len(verification.data_sources)
        score += min(source_count * 0.1, 0.3)
        
        return min(score, 1.0)
    
    def _evaluate_history(self,
                         poi: Location,
                         verification: NodeVerification) -> float:
        """
        评估历史性
        
        考虑因素:
        - 是否是历史景点
        - 文化价值
        - 名气
        """
        score = 0.0
        
        # 1. 基于名称关键词
        name = poi.name.lower()
        history_keywords = [
            '园', '寺', '庙', '塔', '古', '故居', '博物馆', '纪念馆',
            '遗址', '文化', '历史', '传统', '老街', '古镇'
        ]
        if any(kw in name for kw in history_keywords):
            score += 0.4
        
        # 2. 基于地址关键词
        address = poi.address.lower()
        if any(kw in address for kw in ['老城', '古城', '历史街区']):
            score += 0.2
        
        # 3. 基于评论关键词
        positive_keywords = verification.key_positive_words
        history_review_keywords = ['历史', '文化', '古老', '传统', '底蕴']
        matched = sum(1 for kw in history_review_keywords if kw in str(positive_keywords))
        score += min(matched * 0.1, 0.2)
        
        # 4. 基于票价（历史景点通常有门票）
        if poi.ticket_price > 0:
            score += 0.2
        
        return min(score, 1.0)
    
    def rank_by_quality(self, 
                       candidates: List[tuple]) -> List[tuple]:
        """
        按质量对候选POI排序
        
        Args:
            candidates: [(poi, verification), ...]
            
        Returns:
            排序后的列表，高质量POI在前
        """
        def get_quality_score(item):
            poi, verification = item
            quality = self.evaluate_quality(poi, verification)
            return quality.overall
        
        return sorted(candidates, key=get_quality_score, reverse=True)
    
    def filter_low_quality(self,
                          candidates: List[tuple]) -> List[tuple]:
        """
        过滤掉低质量POI
        
        Args:
            candidates: [(poi, verification), ...]
            
        Returns:
            过滤后的高质量POI列表
        """
        filtered = []
        
        for poi, verification in candidates:
            if self.is_worth_recommending(poi, verification):
                filtered.append((poi, verification))
        
        return filtered


def get_poi_quality_explanation(quality: POIQualityScore) -> str:
    """
    获取质量评分的解释
    
    用于向用户展示为什么推荐这个POI
    """
    explanation = []
    
    if quality.playability >= 0.6:
        explanation.append("可玩性高（游玩时间长、活动丰富）")
    if quality.viewability >= 0.6:
        explanation.append("观赏价值高（风景优美、适合拍照）")
    if quality.popularity >= 0.6:
        explanation.append("热门景点（评论多、评分高）")
    if quality.history >= 0.6:
        explanation.append("历史文化价值（有历史底蕴）")
    
    if not explanation:
        explanation.append("综合体验良好")
    
    return "、".join(explanation)
