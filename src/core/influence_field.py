"""
影响力场（Z轴）- 三维决策空间的深度维度

功能：
- 神经网格层：语义理解、模式识别
- 数学内核层：GAODE验证与评分
- 情境因子层：天气、拥挤度、时间窗口

Author: GAODE Team
Date: 2024-12
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np

from .models import Location, UserProfile, State, POIType
from .progressive_planner import ProgressivePlanner
from .neural_net_service import NeuralNetService


@dataclass
class InfluenceFactor:
    """影响因子"""
    name: str
    value: float  # 0-1
    weight: float  # 权重
    source: str  # neural/math/contextual/dimensional_4
    explanation: str = ""
    
    @property
    def weighted_value(self) -> float:
        """加权值"""
        return self.value * self.weight


class NeuralLayer:
    """
    神经网格层（Z轴第1层）
    
    功能：
    - 语义匹配
    - 模式识别  
    - 隐式偏好挖掘
    """
    
    def __init__(self, neural_service: NeuralNetService):
        self.neural = neural_service
    
    def evaluate(self,
                option: Location,
                time_point: datetime,
                state: State,
                profile: UserProfile) -> List[InfluenceFactor]:
        """评估神经网格因子"""
        factors = []
        
        # 1. 语义匹配度
        semantic_score = self._compute_semantic_match(option, profile)
        factors.append(InfluenceFactor(
            name="语义匹配",
            value=semantic_score,
            weight=0.25,
            source="neural",
            explanation=f"与您的意图匹配度{semantic_score:.0%}"
        ))
        
        # 2. 历史模式相似度
        if state.visited:
            pattern_score = self._compute_pattern_similarity(
                option, state.visited
            )
            factors.append(InfluenceFactor(
                name="模式相似度",
                value=pattern_score,
                weight=0.15,
                source="neural",
                explanation=f"与您的历史行为相似{pattern_score:.0%}"
            ))
        
        # 3. 隐式偏好
        implicit_score = self._extract_implicit_preference(option, profile)
        factors.append(InfluenceFactor(
            name="隐式偏好",
            value=implicit_score,
            weight=0.20,
            source="neural",
            explanation="基于深度学习的偏好预测"
        ))
        
        return factors
    
    def _compute_semantic_match(self, option: Location, profile: UserProfile) -> float:
        """计算语义匹配度"""
        # 使用BERT编码
        try:
            poi_embedding = self.neural.bert_encode(
                f"{option.name} {option.type.value}"
            )
            
            # 如果用户有意图嵌入
            if hasattr(profile, 'preferences') and profile.preferences:
                # 简化：基于类型匹配
                pref_types = [p.lower() for p in profile.preferences.keys()]
                if option.type.value.lower() in pref_types:
                    return 0.9
            
            return 0.7  # 默认中等匹配
        except:
            return 0.7
    
    def _compute_pattern_similarity(self,
                                   option: Location,
                                   history: List[Location]) -> float:
        """计算模式相似度"""
        if not history:
            return 0.5
        
        # 统计历史中相同类型的POI数量
        similar_count = sum(1 for h in history if h.type == option.type)
        return min(1.0, similar_count / len(history) * 2)
    
    def _extract_implicit_preference(self,
                                    option: Location,
                                    profile: UserProfile) -> float:
        """提取隐式偏好"""
        # 基于评分偏好
        if hasattr(option, 'rating') and option.rating:
            if option.rating >= 4.5:
                return 0.9
            elif option.rating >= 4.0:
                return 0.75
            else:
                return 0.6
        return 0.7


class MathematicalLayer:
    """
    数学内核层（Z轴第2层）
    
    功能：
    - GAODE四项验证原则
    - 多维度评分
    - 拓扑合理性
    """
    
    def __init__(self, planner: ProgressivePlanner):
        self.planner = planner
    
    def evaluate(self,
                option: Location,
                time_point: datetime,
                state: State,
                profile: UserProfile) -> List[InfluenceFactor]:
        """评估数学内核因子"""
        factors = []
        
        # 1. 验证可信度（四项基本原则）
        try:
            verification = self.planner.verification_engine.verify(
                option, state, None
            )
            
            factors.append(InfluenceFactor(
                name="数据可信度",
                value=verification.overall_trust_score,
                weight=0.30,
                source="math",
                explanation=(
                    f"四项验证通过：多源{verification.cross_validation_score:.0%}、"
                    f"清洗{verification.data_quality_score:.0%}、"
                    f"空间{verification.spatial_score:.0%}、"
                    f"时间{verification.temporal_score:.0%}"
                )
            ))
        except Exception as e:
            # 如果验证失败，给予默认分数
            factors.append(InfluenceFactor(
                name="数据可信度",
                value=0.7,
                weight=0.30,
                source="math",
                explanation="基于默认验证标准"
            ))
        
        # 2. 综合评分
        score = self._compute_综合_score(option, state, profile)
        factors.append(InfluenceFactor(
            name="综合评分",
            value=min(1.0, score),
            weight=0.25,
            source="math",
            explanation=f"GAODE六维评分{score:.2f}"
        ))
        
        # 3. 拓扑合理性
        topo_score = self._compute_topological_score(option, state)
        factors.append(InfluenceFactor(
            name="拓扑合理性",
            value=topo_score,
            weight=0.20,
            source="math",
            explanation="路径优化合理度"
        ))
        
        return factors
    
    def _compute_综合_score(self, option: Location, state: State, profile: UserProfile) -> float:
        """计算综合评分"""
        score = 0.7  # 基础分
        
        # 基于评分
        if hasattr(option, 'rating') and option.rating:
            score += (option.rating / 5.0) * 0.2
        
        # 基于类型匹配
        if hasattr(profile, 'preferences') and profile.preferences:
            if option.type.value in profile.preferences:
                score += 0.1
        
        return min(1.0, score)
    
    def _compute_topological_score(self, option: Location, state: State) -> float:
        """计算拓扑合理性"""
        if not state.current_location:
            return 1.0
        
        # 简化距离计算
        try:
            distance = self._haversine_distance(
                state.current_location.latitude,
                state.current_location.longitude,
                option.latitude,
                option.longitude
            )
            
            # 距离越近，分数越高
            if distance < 2:
                return 1.0
            elif distance < 5:
                return 0.8
            elif distance < 10:
                return 0.6
            else:
                return 0.4
        except:
            return 0.7
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2) -> float:
        """计算两点间距离（km）"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # 地球半径
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


class ContextualLayer:
    """
    情境因子层（Z轴第3层）
    
    功能：
    - 时间适配
    - 天气影响
    - 拥挤度预测
    - 预算合理性
    """
    
    def evaluate(self,
                option: Location,
                time_point: datetime,
                state: State,
                profile: UserProfile) -> List[InfluenceFactor]:
        """评估情境因子"""
        factors = []
        
        # 1. 时间适配度
        time_score = self._evaluate_time_fitness(option, time_point)
        factors.append(InfluenceFactor(
            name="时间适配",
            value=time_score,
            weight=0.15,
            source="contextual",
            explanation=f"{time_point.strftime('%H:%M')}适合游览"
        ))
        
        # 2. 天气影响
        weather_score = self._evaluate_weather(option, time_point)
        factors.append(InfluenceFactor(
            name="天气适宜度",
            value=weather_score,
            weight=0.10,
            source="contextual",
            explanation="天气条件适宜"
        ))
        
        # 3. 拥挤度预测
        crowd_score = 1.0 - self._predict_crowd(option, time_point)
        factors.append(InfluenceFactor(
            name="人流舒适度",
            value=crowd_score,
            weight=0.15,
            source="contextual",
            explanation=f"预测拥挤度{(1-crowd_score)*100:.0f}%"
        ))
        
        # 4. 预算合理性
        budget_score = self._evaluate_budget_fit(option, state)
        factors.append(InfluenceFactor(
            name="预算合理性",
            value=budget_score,
            weight=0.10,
            source="contextual",
            explanation="符合预算范围"
        ))
        
        return factors
    
    def _evaluate_time_fitness(self, option: Location, time: datetime) -> float:
        """评估时间适配度"""
        hour = time.hour
        
        # 不同POI类型的最佳时间
        optimal_hours = {
            POIType.ATTRACTION: (9, 17),
            POIType.RESTAURANT: (11, 20),
            POIType.SHOPPING: (10, 21),
            POIType.HOTEL: (15, 23)
        }
        
        if option.type in optimal_hours:
            start, end = optimal_hours[option.type]
            if start <= hour <= end:
                return 1.0
            else:
                return 0.5
        
        return 0.8
    
    def _evaluate_weather(self, option: Location, time: datetime) -> float:
        """评估天气影响"""
        # TODO: 接入真实天气API
        # 简化：假设好天气
        return 0.85
    
    def _predict_crowd(self, option: Location, time: datetime) -> float:
        """预测拥挤度"""
        hour = time.hour
        day_of_week = time.weekday()
        
        # 周末高峰
        if day_of_week >= 5:  # 周六周日
            if 10 <= hour <= 16:
                return 0.8
            else:
                return 0.5
        else:
            if 12 <= hour <= 14:
                return 0.6
            else:
                return 0.3
    
    def _evaluate_budget_fit(self, option: Location, state: State) -> float:
        """评估预算合理性"""
        if not hasattr(state, 'budget_remaining'):
            return 0.8
        
        if state.budget_remaining < 50:
            return 0.4
        elif state.budget_remaining < 200:
            return 0.7
        else:
            return 1.0


class InfluenceField:
    """
    影响力场（Z轴） + 语义-因果流（W轴）
    
    核心思想：
    - Z轴是连续的"场"，不是离散的选项
    - 场强决定X-Y平面上每个决策点的推荐度
    - 场源来自三层：神经网格、数学内核、情境因子
    
    ✨ 四维升级：
    - W轴（语义-因果流）贯穿三维空间
    - 作为"体验修正项"叠加到Z轴
    - Φ_4D = Φ_3D + F_wc
    """
    
    def __init__(self,
                 planner: ProgressivePlanner,
                 neural_service: NeuralNetService,
                 spatial_intelligence=None,
                 enable_4d: bool = True):
        """
        Args:
            spatial_intelligence: 大模型（上帝视角），用于W轴因果推理
            enable_4d: 是否启用四维模式
        """
        self.planner = planner
        self.neural = neural_service
        self.spatial_intelligence = spatial_intelligence
        
        # Z轴三层
        self.layers = {
            'neural': NeuralLayer(neural_service),
            'mathematical': MathematicalLayer(planner),
            'contextual': ContextualLayer()
        }
        
        # W轴：语义-因果流（第四维度）
        if enable_4d:
            try:
                from .semantic_causal_flow import SemanticCausalFlow
                self.w_axis = SemanticCausalFlow(
                    spatial_intelligence=spatial_intelligence,
                    delta=0.1,  # 语义权重
                    epsilon=0.1  # 因果权重
                )
                self.enable_4d = True
                print("   ✅ W轴（语义-因果流）已启用")
            except Exception as e:
                print(f"   ⚠️ W轴初始化失败: {e}")
                self.w_axis = None
                self.enable_4d = False
        else:
            self.w_axis = None
            self.enable_4d = False
    
    def compute_field(self,
                     option: Location,
                     time_point: datetime,
                     state: State,
                     user_profile: UserProfile,
                     current_poi: Optional[Location] = None,
                     context: Optional[Dict] = None) -> Tuple[float, List[InfluenceFactor], Optional[Dict]]:
        """
        计算(x, y)点的场强
        
        ✨ 四维升级：
        - Φ_3D: 三维势能（Z轴三层）
        - Φ_4D = Φ_3D + F_wc（叠加W轴关联场力）
        
        Returns:
            (总场强, 影响因子列表, W轴详情)
        """
        factors = []
        
        # ========== Z轴：三维场强计算 ==========
        
        # Z层1：神经网格层
        try:
            neural_factors = self.layers['neural'].evaluate(
                option, time_point, state, user_profile
            )
            factors.extend(neural_factors)
        except Exception as e:
            print(f"⚠️ 神经网格层评估失败: {e}")
        
        # Z层2：数学内核层
        try:
            math_factors = self.layers['mathematical'].evaluate(
                option, time_point, state, user_profile
            )
            factors.extend(math_factors)
        except Exception as e:
            print(f"⚠️ 数学内核层评估失败: {e}")
        
        # Z层3：情境因子层
        try:
            context_factors = self.layers['contextual'].evaluate(
                option, time_point, state, user_profile
            )
            factors.extend(context_factors)
        except Exception as e:
            print(f"⚠️ 情境因子层评估失败: {e}")
        
        # 计算三维场强（加权和）
        if not factors:
            phi_3d = 0.5  # 默认值
        else:
            total_field_strength = sum(f.weighted_value for f in factors)
            max_possible = sum(f.weight for f in factors)
            if max_possible > 0:
                phi_3d = total_field_strength / max_possible
            else:
                phi_3d = 0.5
        
        # ========== W轴：语义-因果流叠加 ==========
        
        w_details = None
        if self.enable_4d and self.w_axis and current_poi:
            try:
                from .semantic_causal_flow import UserStateVector
                
                # 构造用户状态向量
                user_state_vec = UserStateVector(
                    physical_energy=getattr(state, 'physical_energy', 0.7),
                    mental_energy=getattr(state, 'mental_energy', 0.7),
                    mood=getattr(state, 'mood', 0.7),
                    satiety=getattr(state, 'satiety', 0.5),
                    time_pressure=getattr(state, 'time_pressure', 0.3)
                )
                
                # 计算W轴关联场力
                f_wc, w_details = self.w_axis.compute_w_axis_force(
                    current_poi=current_poi,
                    next_poi=option,
                    user_state=user_state_vec,
                    context=context or {},
                    state=state,
                    history=getattr(state, 'visited', [])
                )
                
                # 升级到四维势能
                phi_4d = self.w_axis.upgrade_to_4d_potential(phi_3d, f_wc)
                
                # 添加W轴因子（用于展示）
                factors.append(InfluenceFactor(
                    name="W轴-语义连贯",
                    value=w_details['S_sem'],
                    weight=self.w_axis.delta,
                    source="w_axis_semantic",
                    explanation=w_details['semantic_explanation']
                ))
                
                factors.append(InfluenceFactor(
                    name="W轴-因果自洽",
                    value=w_details['C_causal'],
                    weight=self.w_axis.epsilon,
                    source="w_axis_causal",
                    explanation=w_details['causal_explanation']
                ))
                
                return phi_4d, factors, w_details
                
            except Exception as e:
                print(f"⚠️ W轴计算失败，降级到三维: {e}")
        
        # 三维模式（无W轴）
        return phi_3d, factors, w_details
    
    def visualize_field(self,
                       x_options: List[Location],
                       y_timepoints: List[datetime],
                       state: State,
                       profile: UserProfile) -> np.ndarray:
        """
        可视化影响力场
        
        Returns:
            场强矩阵 [Y, X]
        """
        Y, X = len(y_timepoints), len(x_options)
        field_matrix = np.zeros((Y, X))
        
        for y_idx, time in enumerate(y_timepoints):
            for x_idx, option in enumerate(x_options):
                field_strength, _, _ = self.compute_field(
                    option, time, state, profile
                )
                field_matrix[y_idx, x_idx] = field_strength
        
        return field_matrix
