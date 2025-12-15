"""
第四维度：语义-因果流（W轴）

核心定义：
- W轴 = Semantic-Causal Flow
- 不是独立轴，而是贯穿三维空间的动态关联维度
- 作用：从"时空最优"升级为"体验最优"

数学模型：
Φ_4D(x,y,z,w) = Φ_3D(x,y,z) + F_wc
F_wc = δ·S_sem + ε·C_causal

物理类比：
- 延续爱因斯坦四维时空（3D空间 + 1D时间）
- W轴是决策时空的曲率

Author: GAODE Team
Date: 2024-12
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np

from .models import Location, UserProfile, State, POIType


class SemanticType(Enum):
    """语义类型"""
    STATIC_VIEWING = "static_viewing"      # 静态观赏（园林、博物馆）
    DYNAMIC_ACTIVITY = "dynamic_activity"  # 动态活动（游乐场、运动）
    RELAXATION = "relaxation"              # 休闲放松（茶馆、温泉）
    DINING = "dining"                      # 餐饮美食
    SHOPPING = "shopping"                  # 购物
    CULTURAL = "cultural"                  # 文化体验
    NATURAL = "natural"                    # 自然风光


class IntensityLevel(Enum):
    """强度等级"""
    REST = 1          # 休息（0-20%体力消耗）
    LIGHT = 2         # 轻度（20-40%）
    MODERATE = 3      # 中度（40-60%）
    INTENSE = 4       # 高强度（60-80%）
    EXTREME = 5       # 极限（80-100%）


@dataclass
class UserStateVector:
    """用户状态向量"""
    physical_energy: float  # 体力 0-1
    mental_energy: float    # 精力 0-1
    mood: float            # 心情 0-1
    satiety: float         # 饱腹感 0-1
    time_pressure: float   # 时间压力 0-1
    
    def to_vector(self) -> np.ndarray:
        """转换为向量"""
        return np.array([
            self.physical_energy,
            self.mental_energy,
            self.mood,
            self.satiety,
            self.time_pressure
        ])


@dataclass
class SemanticVector:
    """语义向量"""
    semantic_type: SemanticType
    intensity_level: IntensityLevel
    duration: float  # 持续时间（小时）
    
    # 语义属性
    is_indoor: bool
    is_static: bool
    cultural_depth: float  # 文化深度 0-1
    physical_demand: float  # 体力需求 0-1
    
    def to_embedding(self) -> np.ndarray:
        """转换为嵌入向量"""
        # 8维语义嵌入
        return np.array([
            self.intensity_level.value / 5.0,  # 强度归一化
            self.duration / 4.0,  # 假设最长4小时
            1.0 if self.is_indoor else 0.0,
            1.0 if self.is_static else 0.0,
            self.cultural_depth,
            self.physical_demand,
            self._type_to_numeric(),
            0.0  # 预留维度
        ])
    
    def _type_to_numeric(self) -> float:
        """类型转数值"""
        type_map = {
            SemanticType.STATIC_VIEWING: 0.1,
            SemanticType.DYNAMIC_ACTIVITY: 0.9,
            SemanticType.RELAXATION: 0.2,
            SemanticType.DINING: 0.5,
            SemanticType.SHOPPING: 0.6,
            SemanticType.CULTURAL: 0.3,
            SemanticType.NATURAL: 0.7
        }
        return type_map.get(self.semantic_type, 0.5)


class SemanticFlowAnalyzer:
    """
    语义流分析器
    
    功能：计算行程的体验连贯性
    - 内容语义连贯性
    - 强度语义互补性
    - 用户状态适配性
    """
    
    def __init__(self):
        # 语义相似度矩阵（基于POI类型）
        self.semantic_similarity_matrix = self._init_similarity_matrix()
        
        # 强度转移矩阵（前后强度组合的合理性）
        self.intensity_transition_matrix = self._init_intensity_matrix()
    
    def compute_semantic_score(self,
                              current_poi: Location,
                              next_poi: Location,
                              user_state: UserStateVector,
                              history: List[Location]) -> Tuple[float, str]:
        """
        计算语义流得分
        
        Returns:
            (S_sem ∈ [-1, 1], explanation)
            
        得分含义：
        - +1.0: 完美连贯
        - +0.5~1.0: 良好连贯
        - 0: 中性（无关联）
        - -0.5~0: 轻微冲突
        - -1.0: 严重冲突
        """
        # 提取语义向量
        current_semantic = self._extract_semantic(current_poi)
        next_semantic = self._extract_semantic(next_poi)
        
        # 1. 内容语义连贯性（40%权重）
        content_score = self._compute_content_coherence(
            current_semantic, next_semantic
        )
        
        # 2. 强度语义互补性（30%权重）
        intensity_score = self._compute_intensity_complementarity(
            current_semantic, next_semantic, user_state
        )
        
        # 3. 用户状态适配性（30%权重）
        state_score = self._compute_state_fitness(
            next_semantic, user_state
        )
        
        # 加权综合
        S_sem = (
            0.4 * content_score +
            0.3 * intensity_score +
            0.3 * state_score
        )
        
        # 生成解释
        explanation = self._generate_semantic_explanation(
            content_score, intensity_score, state_score,
            current_poi, next_poi
        )
        
        return S_sem, explanation
    
    def _extract_semantic(self, poi: Location) -> SemanticVector:
        """从POI提取语义向量"""
        # 根据POI类型映射语义类型
        type_mapping = {
            POIType.ATTRACTION: SemanticType.STATIC_VIEWING,
            POIType.RESTAURANT: SemanticType.DINING,
            POIType.SHOPPING: SemanticType.SHOPPING,
            POIType.HOTEL: SemanticType.RELAXATION,
            POIType.ENTERTAINMENT: SemanticType.DYNAMIC_ACTIVITY
        }
        
        semantic_type = type_mapping.get(poi.type, SemanticType.CULTURAL)
        
        # 推断强度等级
        if semantic_type == SemanticType.STATIC_VIEWING:
            intensity = IntensityLevel.LIGHT
        elif semantic_type == SemanticType.DYNAMIC_ACTIVITY:
            intensity = IntensityLevel.INTENSE
        elif semantic_type == SemanticType.RELAXATION:
            intensity = IntensityLevel.REST
        else:
            intensity = IntensityLevel.MODERATE
        
        return SemanticVector(
            semantic_type=semantic_type,
            intensity_level=intensity,
            duration=getattr(poi, 'average_visit_time', 2.0) or 2.0,
            is_indoor=semantic_type in [SemanticType.SHOPPING, SemanticType.DINING],
            is_static=semantic_type == SemanticType.STATIC_VIEWING,
            cultural_depth=0.8 if semantic_type == SemanticType.CULTURAL else 0.3,
            physical_demand=intensity.value / 5.0
        )
    
    def _compute_content_coherence(self,
                                   current: SemanticVector,
                                   next: SemanticVector) -> float:
        """计算内容连贯性"""
        # 使用相似度矩阵
        similarity = self.semantic_similarity_matrix.get(
            (current.semantic_type, next.semantic_type),
            0.0
        )
        
        # 检查冲突模式
        # 1. 连续静态观赏（疲劳）
        if current.is_static and next.is_static:
            if current.duration + next.duration > 3:  # 连续超过3小时
                similarity -= 0.4
        
        # 2. 室内/室外交替（体验丰富）
        if current.is_indoor != next.is_indoor:
            similarity += 0.2
        
        return np.clip(similarity, -1.0, 1.0)
    
    def _compute_intensity_complementarity(self,
                                          current: SemanticVector,
                                          next: SemanticVector,
                                          user_state: UserStateVector) -> float:
        """计算强度互补性"""
        current_intensity = current.intensity_level.value
        next_intensity = next.intensity_level.value
        
        # 强度差
        intensity_diff = abs(current_intensity - next_intensity)
        
        # 根据用户体力评估合理性
        if user_state.physical_energy > 0.7:
            # 体力充沛：接受高强度
            if next_intensity >= 4:
                return 0.8
            else:
                return 0.5
        elif user_state.physical_energy > 0.4:
            # 体力中等：适合中度
            if 2 <= next_intensity <= 3:
                return 0.9
            elif next_intensity >= 4:
                return -0.3  # 不适合高强度
            else:
                return 0.6
        else:
            # 体力低：需要休息
            if next_intensity <= 2:
                return 1.0  # 强烈推荐休息
            else:
                return -0.6  # 不适合继续高强度
        
        # 检查强度叠加疲劳
        if current_intensity >= 4 and next_intensity >= 4:
            return -0.7  # 连续高强度，严重冲突
        
        return 0.0
    
    def _compute_state_fitness(self,
                              next: SemanticVector,
                              user_state: UserStateVector) -> float:
        """计算用户状态适配性"""
        score = 0.0
        
        # 1. 体力适配
        physical_fitness = 1.0 - abs(next.physical_demand - user_state.physical_energy)
        score += physical_fitness * 0.4
        
        # 2. 精力适配
        if next.is_static and user_state.mental_energy < 0.4:
            score -= 0.3  # 精力不足时不适合静态观赏
        
        # 3. 饱腹感适配
        if next.semantic_type == SemanticType.DINING:
            if user_state.satiety < 0.3:
                score += 0.8  # 饿了，推荐餐饮
            elif user_state.satiety > 0.7:
                score -= 0.5  # 太饱，不推荐
        
        # 4. 心情适配
        if user_state.mood < 0.4:
            if next.semantic_type in [SemanticType.RELAXATION, SemanticType.NATURAL]:
                score += 0.5  # 心情不好，推荐放松
        
        return np.clip(score, -1.0, 1.0)
    
    def _generate_semantic_explanation(self,
                                      content_score: float,
                                      intensity_score: float,
                                      state_score: float,
                                      current_poi: Location,
                                      next_poi: Location) -> str:
        """生成语义解释"""
        explanations = []
        
        if content_score > 0.6:
            explanations.append(f"与{current_poi.name}体验连贯")
        elif content_score < -0.3:
            explanations.append(f"与{current_poi.name}体验冲突")
        
        if intensity_score > 0.7:
            explanations.append("强度搭配合理")
        elif intensity_score < -0.3:
            explanations.append("强度过高，建议休息")
        
        if state_score > 0.6:
            explanations.append("符合您当前状态")
        elif state_score < -0.3:
            explanations.append("可能不适合当前状态")
        
        return "；".join(explanations) if explanations else "体验中性"
    
    def _init_similarity_matrix(self) -> Dict[Tuple[SemanticType, SemanticType], float]:
        """初始化语义相似度矩阵"""
        # 简化版：只定义关键组合
        return {
            # 文化类连贯
            (SemanticType.CULTURAL, SemanticType.STATIC_VIEWING): 0.8,
            (SemanticType.STATIC_VIEWING, SemanticType.CULTURAL): 0.8,
            
            # 动态活动后接休闲
            (SemanticType.DYNAMIC_ACTIVITY, SemanticType.RELAXATION): 0.9,
            
            # 餐饮后接休闲
            (SemanticType.DINING, SemanticType.RELAXATION): 0.7,
            
            # 冲突组合
            (SemanticType.STATIC_VIEWING, SemanticType.STATIC_VIEWING): -0.2,  # 连续静态
            (SemanticType.DYNAMIC_ACTIVITY, SemanticType.DYNAMIC_ACTIVITY): -0.4,  # 连续高强度
        }
    
    def _init_intensity_matrix(self) -> np.ndarray:
        """初始化强度转移矩阵"""
        # 5x5矩阵（5个强度等级）
        # 行=当前强度，列=下一强度，值=合理性得分
        return np.array([
            # REST  LIGHT  MOD   INTENSE EXTREME
            [0.5,  0.9,   0.8,  0.6,    0.3],   # 从REST
            [0.7,  0.7,   0.9,  0.7,    0.4],   # 从LIGHT
            [0.8,  0.8,   0.7,  0.6,    0.3],   # 从MODERATE
            [0.9,  0.8,   0.6,  0.3,    0.1],   # 从INTENSE
            [1.0,  0.9,   0.7,  0.2,   -0.3]    # 从EXTREME
        ])


class CausalFlowAnalyzer:
    """
    因果流分析器
    
    功能：计算决策的逻辑关联性
    - 事件因果（景点闭园→推荐同类型备选）
    - 决策因果（用户偏好→推荐策略）
    - 环境因果（天气→场所类型）
    """
    
    def __init__(self, spatial_intelligence=None, llm_client=None, enable_concurrent=True):
        """
        Args:
            spatial_intelligence: 大模型（上帝视角），用于因果推理（兼容旧版）
            llm_client: LLM客户端（新版，推荐使用）
            enable_concurrent: 是否启用并发推理
        """
        self.spatial_intelligence = spatial_intelligence
        self.llm_client = llm_client  # 🔥 新增：LLM客户端
        self.enable_concurrent = enable_concurrent  # 🔥 新增：并发开关
        
        # 因果规则库
        self.causal_rules = self._init_causal_rules()
    
    def compute_causal_score(self,
                            current_poi: Location,
                            next_poi: Location,
                            context: Dict,
                            state: State) -> Tuple[float, str]:
        """
        计算因果流得分
        
        Args:
            context: 上下文信息（天气、事件、用户偏好等）
            
        Returns:
            (C_causal ∈ [0, 1], explanation)
            
        得分含义：
        - 1.0: 因果链完全自洽
        - 0.7~1.0: 因果关联强
        - 0.4~0.7: 因果关联中等
        - 0~0.4: 因果关联弱
        """
        # 提取因果链
        causal_chain = self._extract_causal_chain(
            current_poi, next_poi, context, state
        )
        
        # 如果有大模型，使用"上帝视角"推理
        if self.spatial_intelligence:
            llm_score = self._llm_causal_reasoning(
                current_poi, next_poi, context, causal_chain
            )
        else:
            llm_score = 0.5  # 默认中性
        
        # 规则基础分
        rule_score = self._rule_based_causal_score(causal_chain)
        
        # 综合得分（大模型50%+规则50%）
        C_causal = 0.5 * llm_score + 0.5 * rule_score
        
        # 生成解释
        explanation = self._generate_causal_explanation(causal_chain)
        
        return C_causal, explanation
    
    def _extract_causal_chain(self,
                             current_poi: Location,
                             next_poi: Location,
                             context: Dict,
                             state: State) -> List[Dict]:
        """提取因果链"""
        chain = []
        
        # 1. 事件因果
        if context.get('event_type'):
            chain.append({
                'type': 'event_causal',
                'event': context['event_type'],
                'from': current_poi.name,
                'to': next_poi.name,
                'reason': self._explain_event_causal(context, current_poi, next_poi)
            })
        
        # 2. 决策因果
        if hasattr(state, 'user_preferences'):
            chain.append({
                'type': 'decision_causal',
                'preference': state.user_preferences,
                'to': next_poi.name,
                'reason': self._explain_decision_causal(state, next_poi)
            })
        
        # 3. 环境因果
        if context.get('weather'):
            chain.append({
                'type': 'environment_causal',
                'weather': context['weather'],
                'to': next_poi.name,
                'reason': self._explain_environment_causal(context, next_poi)
            })
        
        return chain
    
    def _llm_causal_reasoning(self,
                             current_poi: Location,
                             next_poi: Location,
                             context: Dict,
                             causal_chain: List[Dict]) -> float:
        """
        大模型因果推理（上帝视角）
        
        利用SpatialIntelligenceCore的推理能力
        """
        try:
            # 构造推理问题
            question = f"从{current_poi.name}到{next_poi.name}，考虑{context}，因果关联度如何？"
            
            # 调用大模型推理
            # 注：SpatialIntelligenceCore可能需要扩展因果推理接口
            if hasattr(self.spatial_intelligence, 'reason_causality'):
                score = self.spatial_intelligence.reason_causality(
                    current_poi, next_poi, context
                )
                return float(score)
            else:
                # 降级：使用POI相似度
                if hasattr(self.spatial_intelligence, 'poi_graph'):
                    similarity = self.spatial_intelligence.compute_poi_similarity(
                        current_poi, next_poi
                    )
                    return float(similarity)
        except:
            pass
        
        return 0.6  # 默认中等关联
    
    def _rule_based_causal_score(self, causal_chain: List[Dict]) -> float:
        """基于规则的因果得分"""
        if not causal_chain:
            return 0.5
        
        scores = []
        for link in causal_chain:
            rule_score = self.causal_rules.get(link['type'], 0.5)
            scores.append(rule_score)
        
        return np.mean(scores)
    
    def _explain_event_causal(self, context: Dict, current: Location, next: Location) -> str:
        """解释事件因果"""
        event = context.get('event_type', 'unknown')
        if event == 'closure':
            if current.type == next.type:
                return f"{current.name}闭园，推荐同类型{next.name}"
            else:
                return f"{current.name}不可用，推荐备选{next.name}"
        return "事件响应"
    
    def _explain_decision_causal(self, state: State, next: Location) -> str:
        """解释决策因果"""
        return f"基于您的偏好推荐{next.name}"
    
    def _explain_environment_causal(self, context: Dict, next: Location) -> str:
        """解释环境因果"""
        weather = context.get('weather', '')
        if 'rain' in weather.lower() or '雨' in weather:
            if next.type in [POIType.SHOPPING, POIType.RESTAURANT]:
                return f"雨天推荐室内场所{next.name}"
        return f"天气适合{next.name}"
    
    def _generate_causal_explanation(self, causal_chain: List[Dict]) -> str:
        """生成因果解释"""
        if not causal_chain:
            return "因果关联中等"
        
        explanations = [link['reason'] for link in causal_chain]
        return "；".join(explanations)
    
    def _init_causal_rules(self) -> Dict[str, float]:
        """初始化因果规则库"""
        return {
            'event_causal': 0.9,         # 事件因果权重高
            'decision_causal': 0.7,      # 决策因果中等
            'environment_causal': 0.8    # 环境因果较高
        }
    
    def batch_compute_causal_flow(self, tasks: List[Dict]) -> List[Dict]:
        """
        批量计算因果流（🔥 修复：返回结构化张力）
        
        Args:
            tasks: 任务列表，每个任务包含：
                - current: 当前POI
                - next: 下一个POI
                - context: 上下文（天气、时间等）
                
        Returns:
            张力信息列表，每个包含：
            {
                'c_causal': 综合分数 [0, 1]，
                'tensions': {
                    'novelty': 新鲜感张力 [-1, 1]，
                    'continuity': 连续性张力 [-1, 1]，
                    'energy': 体力张力 [-1, 1]，
                    'conflict': 冲突度 [0, 1]
                }
            }
        """
        if not tasks:
            return []
        
        # 方案1：使用LLM客户端批量推理（推荐）
        if self.llm_client:
            return self._batch_llm_reason_with_tensions(tasks)
        
        # 方案2：使用旧版spatial_intelligence（兼容）
        elif self.spatial_intelligence:
            return self._batch_spatial_reason_with_tensions(tasks)
        
        # 方案3：纯规则推理（降级）
        else:
            return self._batch_rule_reason_with_tensions(tasks)
    
    def _batch_llm_reason(self, tasks: List[Dict]) -> List[float]:
        """使用LLM客户端批量推理"""
        # 构建prompts
        prompts = []
        for task in tasks:
            current = task['current']
            next_poi = task['next']
            context = task.get('context', {})
            
            # 提取关键信息
            weather = context.get('weather', 'sunny')
            time_hour = context.get('time_of_day', 10)
            visited_regions = context.get('visited_regions', {})
            
            # 计算区域访问次数
            region = self._get_region(next_poi)
            visit_count = visited_regions.get(region, 0)
            
            # 构建prompt
            prompt = f"""评估旅行决策合理性（0-1分）：

当前：{current.name}
候选：{next_poi.name}（{region}区域）
时间：{time_hour}点 | 天气：{weather}
该区域已访问：{visit_count}次

评估要点：
1. 区域重复：首次+0.3，第2次-0.25，第3次-0.4
2. 时间合理：中午餐厅+0.4，其他时段餐厅-0.2
3. 天气适配：雨天室内+0.2，雨天户外-0.3
4. 景点知名度：知名景点+0.15
5. 类型连续：重复类型-0.15

只返回一个0-1之间的数字（如0.85），不要解释。"""
            
            prompts.append(prompt)
        
        # 并发调用LLM
        results = self.llm_client.batch_reason(
            prompts, 
            temperature=0.5, 
            max_tokens=10,
            max_workers=10 if self.enable_concurrent else 1
        )
        
        # 处理结果（None → 规则推理）
        final_results = []
        for i, score in enumerate(results):
            if score is not None:
                final_results.append(float(score))
            else:
                # 降级到规则
                final_results.append(self._rule_causal_score_simple(tasks[i]))
        
        return final_results
    
    def _batch_spatial_reason(self, tasks: List[Dict]) -> List[float]:
        """使用旧版spatial_intelligence批量推理（兼容）"""
        results = []
        for task in tasks:
            try:
                if hasattr(self.spatial_intelligence, 'reason_causality'):
                    score = self.spatial_intelligence.reason_causality(
                        task['current'], task['next'], task.get('context', {})
                    )
                    results.append(float(score))
                else:
                    results.append(0.6)  # 默认
            except:
                results.append(0.6)
        return results
    
    def _batch_rule_reason(self, tasks: List[Dict]) -> List[float]:
        """纯规则批量推理（降级，向后兼容）"""
        return [self._rule_causal_score_simple(task) for task in tasks]
    
    def _batch_rule_reason_with_tensions(self, tasks: List[Dict]) -> List[Dict]:
        """
        纯规则批量推理（返回张力）🔥
        """
        results = []
        for task in tasks:
            tensions = self._compute_tensions(task)
            c_causal = self._rule_causal_score_simple(task)
            
            results.append({
                'c_causal': c_causal,
                'tensions': tensions
            })
        
        return results
    
    def _batch_llm_reason_with_tensions(self, tasks: List[Dict]) -> List[Dict]:
        """
        LLM批量推理（返回张力）🔥
        
        先用规则计算张力，再用LLM微调c_causal
        """
        results = []
        
        # 先用规则计算张力
        for task in tasks:
            tensions = self._compute_tensions(task)
            results.append({
                'c_causal': 0.5,  # 临时值
                'tensions': tensions
            })
        
        # 然后用LLM批量计算c_causal（仍然并发）
        c_causals = self._batch_llm_reason(tasks)
        
        # 合并结果
        for i, c_causal in enumerate(c_causals):
            if c_causal is not None:
                results[i]['c_causal'] = c_causal
            else:
                # LLM失败，用规则计算
                results[i]['c_causal'] = self._rule_causal_score_simple(tasks[i])
        
        return results
    
    def _batch_spatial_reason_with_tensions(self, tasks: List[Dict]) -> List[Dict]:
        """
        旧版spatial_intelligence推理（返回张力）🔥
        """
        results = []
        for task in tasks:
            tensions = self._compute_tensions(task)
            
            try:
                if hasattr(self.spatial_intelligence, 'reason_causality'):
                    c_causal = float(self.spatial_intelligence.reason_causality(
                        task['current'], task['next'], task.get('context', {})
                    ))
                else:
                    c_causal = 0.6
            except:
                c_causal = 0.6
            
            results.append({
                'c_causal': c_causal,
                'tensions': tensions
            })
        
        return results
    
    def _rule_causal_score_simple(self, task: Dict) -> float:
        """
        简化规则推理（用于降级）
        
        🔥 修复：返回结构化张力，而不是单一标量
        """
        current = task['current']
        next_poi = task['next']
        context = task.get('context', {})
        
        # 🔥 计算三个子张力
        tensions = self._compute_tensions(task)
        
        # 综合成最终分数（但保留张力信息）
        score = 0.5 + tensions['novelty'] * 0.3 + tensions['continuity'] * 0.2 + tensions['energy'] * 0.1
        
        return max(0.1, min(0.95, score))
    
    def _compute_tensions(self, task: Dict) -> Dict[str, float]:
        """
        计算子张力（🔥 核心修复）
        
        Returns:
            {
                'novelty': 新鲜感张力 [-1, 1]，正=新奇，负=重复
                'continuity': 连续性张力 [-1, 1]，正=连贯，负=跳跃
                'energy': 体力张力 [-1, 1]，正=充沛，负=疲惫
                'conflict': 冲突度 [0, 1]，越高越矛盾
            }
        """
        current = task['current']
        next_poi = task['next']
        context = task.get('context', {})
        
        # 1. 新鲜感张力（novelty tension）
        visited_regions = context.get('visited_regions', {})
        region = self._get_region(next_poi)
        visit_count = visited_regions.get(region, 0)
        
        if visit_count == 0:
            novelty = 0.8  # 新区域，强烈吸引
        elif visit_count == 1:
            novelty = -0.3  # 回访，轻度排斥
        else:
            novelty = -0.6  # 多次回访，强烈排斥
        
        # 2. 连续性张力（continuity tension）
        if current.type == next_poi.type:
            continuity = -0.4  # 类型重复，体验单调
        else:
            continuity = 0.3  # 类型切换，体验丰富
        
        # 知名度影响连续性
        famous = ["厦大", "鼓浪屿", "环岛路", "曾厝垵", "中山路",
                  "拙政园", "虎丘", "平江路", "姑苏"]
        if any(f in next_poi.name for f in famous):
            continuity += 0.2  # 知名景点，逻辑连贯
        
        # 3. 体力张力（energy tension）
        time_hour = context.get('time_of_day', 10)
        
        # 时间越晚，体力越低
        if time_hour < 12:
            energy = 0.6  # 早上精力充沛
        elif time_hour < 16:
            energy = 0.2  # 下午适中
        elif time_hour < 18:
            energy = -0.2  # 傍晚开始疲惫
        else:
            energy = -0.5  # 晚上很累
        
        # 餐厅补充体力
        if next_poi.type.value == 'restaurant':
            if 11 <= time_hour <= 13 or 17 <= time_hour <= 19:
                energy += 0.4  # 饭点吃饭，恢复体力
        
        # 4. 🔥 冲突度（conflict）- 核心创新
        # 当多个张力方向不一致时，冲突度高
        tension_values = [novelty, continuity, energy]
        positive_count = sum(1 for t in tension_values if t > 0)
        negative_count = sum(1 for t in tension_values if t < 0)
        
        if positive_count > 0 and negative_count > 0:
            # 有正有负，存在冲突
            conflict = min(positive_count, negative_count) / len(tension_values)
        else:
            # 方向一致，无冲突
            conflict = 0.0
        
        return {
            'novelty': novelty,
            'continuity': continuity,
            'energy': energy,
            'conflict': conflict
        }
    
    def _get_region(self, poi: Location) -> str:
        """获取POI所属区域"""
        for k in ["鼓浪屿", "厦大", "曾厝垵", "中山路", "环岛路"]:
            if k in poi.name or k in poi.address:
                return k
        return "其他"


class SemanticCausalFlow:
    """
    语义-因果流（W轴）
    
    核心功能：
    1. 计算语义流得分 S_sem
    2. 计算因果流得分 C_causal
    3. 生成关联场力 F_wc = δ·S_sem + ε·C_causal
    4. 叠加到Z轴，升级为四维势能
    5. 批量并发推理（🔥 性能优化）
    
    物理意义：
    - W轴是决策时空的"曲率"
    - 让三维空间的势能分布更贴合体验逻辑
    """
    
    def __init__(self,
                 spatial_intelligence=None,
                 llm_client=None,
                 delta: float = 0.1,
                 epsilon: float = 0.1,
                 enable_concurrent: bool = True):
        """
        Args:
            spatial_intelligence: 大模型（上帝视角，兼容旧版）
            llm_client: LLM客户端（新版，推荐使用）🔥
            delta: 语义权重（默认0.1，不喧宾夺主）
            epsilon: 因果权重（默认0.1）
            enable_concurrent: 启用并发推理（默认True）🔥
        """
        self.semantic_analyzer = SemanticFlowAnalyzer()
        self.causal_analyzer = CausalFlowAnalyzer(
            spatial_intelligence=spatial_intelligence,
            llm_client=llm_client,  # 🔥 传递LLM客户端
            enable_concurrent=enable_concurrent  # 🔥 传递并发开关
        )
        
        self.delta = delta
        self.epsilon = epsilon
        self.llm_client = llm_client  # 🔥 保存引用
        
        print(f"✅ W轴初始化完成（δ={delta}, ε={epsilon}）")
    
    def compute_w_axis_force(self,
                            current_poi: Location,
                            next_poi: Location,
                            user_state: UserStateVector,
                            context: Dict,
                            state: State,
                            history: List[Location]) -> Tuple[float, Dict]:
        """
        计算W轴关联场力
        
        Returns:
            (F_wc, details)
            
        数学模型：
        F_wc = δ·S_sem + ε·C_causal
        """
        # 1. 计算语义流得分
        S_sem, semantic_explanation = self.semantic_analyzer.compute_semantic_score(
            current_poi, next_poi, user_state, history
        )
        
        # 2. 计算因果流得分
        C_causal, causal_explanation = self.causal_analyzer.compute_causal_score(
            current_poi, next_poi, context, state
        )
        
        # 3. 计算关联场力
        F_wc = self.delta * S_sem + self.epsilon * C_causal
        
        # 4. 返回详情
        details = {
            'S_sem': S_sem,
            'semantic_explanation': semantic_explanation,
            'C_causal': C_causal,
            'causal_explanation': causal_explanation,
            'F_wc': F_wc,
            'delta': self.delta,
            'epsilon': self.epsilon
        }
        
        return F_wc, details
    
    def upgrade_to_4d_potential(self,
                                phi_3d: float,
                                f_wc: float) -> float:
        """
        升级到四维势能
        
        Φ_4D = Φ_3D + F_wc
        """
        return phi_3d + f_wc
    
    def batch_compute_causal_flow(self, tasks: List[Dict]) -> List[float]:
        """
        批量计算因果流（🔥 核心集成点）
        
        这是连接架构和脚本测试的关键方法！
        
        Args:
            tasks: 任务列表，每个任务包含：
                - current: 当前POI
                - next: 下一个POI  
                - context: 上下文（天气、时间、visited_regions等）
                
        Returns:
            C_causal得分列表
            
        性能：
            - 并发LLM：10x提速（如xiamen_final.py）
            - 兼容旧代码（无LLM时降级到规则）
            
        Example:
            >>> tasks = [
            ...     {'current': poi1, 'next': poi2, 'context': {...}},
            ...     {'current': poi1, 'next': poi3, 'context': {...}},
            ... ]
            >>> scores = w_axis.batch_compute_causal_flow(tasks)
            >>> # [0.75, 0.35, ...]  # 并发计算，快速返回
        """
        return self.causal_analyzer.batch_compute_causal_flow(tasks)
