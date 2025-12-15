"""
神经上下文管理
解决单向拓扑的局限性
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .models import Location, State, PlanningSession, Action, UserProfile, PathHistory


@dataclass
class GlobalContext:
    """
    全局上下文 - 贯穿整个旅程的隐藏状态
    
    解决问题：
    1. 单向性 → 全局影响传播
    2. 短期记忆 → 长程上下文
    3. 局部决策 → 全局优化
    """
    
    # 用户演化状态
    fatigue_level: float = 0.0              # 疲劳度 [0, 1]
    satisfaction_history: List[float] = field(default_factory=list)  # 满意度历史
    preference_evolution: Dict[str, float] = field(default_factory=dict)  # 偏好演化
    
    # 体验累积
    culture_saturation: float = 0.0         # 文化景点饱和度
    nature_saturation: float = 0.0          # 自然景点饱和度
    food_saturation: float = 0.0            # 美食饱和度
    
    # 关键记忆
    memorable_pois: List[Tuple[str, float, str]] = field(default_factory=list)  # (POI名, 评分, 原因)
    regrettable_decisions: List[str] = field(default_factory=list)  # 后悔的选择
    
    # 全局约束演化
    must_visit_remaining: Set[str] = field(default_factory=set)
    avoid_types: Set[str] = field(default_factory=set)
    
    # 情境变化
    weather_adaptation: float = 0.0         # 天气适应度
    crowd_tolerance: float = 1.0            # 拥挤容忍度（递减）
    budget_anxiety: float = 0.0             # 预算焦虑（递增）
    
    def update_after_visit(self, 
                          poi: Location, 
                          satisfaction: float,
                          visit_duration: float):
        """
        访问POI后更新全局上下文
        
        这是关键：每次访问都会影响全局状态
        """
        # 1. 更新疲劳度
        fatigue_gain = visit_duration / 10.0  # 每10小时+1.0疲劳
        self.fatigue_level = min(1.0, self.fatigue_level + fatigue_gain)
        
        # 2. 记录满意度
        self.satisfaction_history.append(satisfaction)
        
        # 3. 更新类型饱和度
        if poi.type.value == 'attraction':
            # 判断是文化还是自然
            if any(kw in poi.name for kw in ['园', '博物馆', '寺', '庙']):
                self.culture_saturation += 0.2
            else:
                self.nature_saturation += 0.2
        elif poi.type.value == 'restaurant':
            self.food_saturation += 0.3
        
        # 4. 记录难忘时刻
        if satisfaction > 0.8:
            self.memorable_pois.append((poi.name, satisfaction, "高满意度"))
        
        # 5. 更新偏好演化
        poi_category = self._categorize_poi(poi)
        if poi_category not in self.preference_evolution:
            self.preference_evolution[poi_category] = 0.0
        
        # 满意则增强偏好，不满意则减弱
        self.preference_evolution[poi_category] += (satisfaction - 0.5) * 0.2
    
    def get_poi_influence(self, poi: Location) -> float:
        """
        计算全局上下文对某个POI的影响
        
        这是全局影响的核心：
        - 之前的经历会影响后续POI的评分
        """
        influence = 0.0
        
        # 1. 疲劳惩罚
        if poi.average_visit_time > 2.0 and self.fatigue_level > 0.6:
            influence -= 0.2  # 累了，不想去耗时长的
        
        # 2. 饱和度惩罚
        if poi.type.value == 'attraction':
            if any(kw in poi.name for kw in ['园', '博物馆']):
                # 文化景点，检查饱和度
                influence -= self.culture_saturation * 0.3
            else:
                influence -= self.nature_saturation * 0.3
        elif poi.type.value == 'restaurant':
            influence -= self.food_saturation * 0.2
        
        # 3. 偏好演化加成
        poi_category = self._categorize_poi(poi)
        if poi_category in self.preference_evolution:
            influence += self.preference_evolution[poi_category]
        
        # 4. 拥挤容忍度
        # 如果之前遇到拥挤且不满意，会降低容忍度
        if self.crowd_tolerance < 0.5:
            # TODO: 根据POI的预测拥挤度调整
            pass
        
        return np.clip(influence, -0.5, 0.5)
    
    def get_rest_need(self) -> float:
        """
        计算休息需求
        
        用于：提升餐厅、咖啡馆等休息场所的评分
        """
        # 基于疲劳度和连续游玩时间
        base_need = self.fatigue_level
        
        # 如果连续多个景点，休息需求更高
        if len(self.satisfaction_history) >= 3:
            recent_visits = self.satisfaction_history[-3:]
            if all(s > 0.6 for s in recent_visits):
                # 连续高强度游玩
                base_need += 0.2
        
        return min(1.0, base_need)
    
    def _categorize_poi(self, poi: Location) -> str:
        """POI分类"""
        if '园' in poi.name or '花园' in poi.name:
            return 'garden'
        elif '博物馆' in poi.name or '馆' in poi.name:
            return 'museum'
        elif '寺' in poi.name or '庙' in poi.name:
            return 'temple'
        elif poi.type.value == 'restaurant':
            return 'food'
        else:
            return 'other'


class ContextualMemory:
    """
    上下文记忆 - 实现"下下步参考上上步"
    
    通过相似度检索历史中的相关经历
    """
    
    def __init__(self):
        self.memory_bank: List[Dict] = []
    
    def store(self, 
             poi: Location, 
             state: State, 
             satisfaction: float,
             context: str):
        """存储一次经历"""
        memory = {
            'poi': poi,
            'state_snapshot': {
                'time': state.current_time,
                'fatigue': 0.0,  # 需要从GlobalContext获取
                'budget': state.remaining_budget
            },
            'satisfaction': satisfaction,
            'context': context,
            'timestamp': datetime.now()
        }
        self.memory_bank.append(memory)
    
    def retrieve_similar(self, 
                        query_poi: Location, 
                        current_state: State,
                        k: int = 3) -> List[Dict]:
        """
        检索相似经历
        
        实现：当要决策时，回忆起类似情况下的经历
        """
        if not self.memory_bank:
            return []
        
        similarities = []
        
        for memory in self.memory_bank:
            # 计算相似度
            sim = self._compute_similarity(
                query_poi, 
                memory['poi'],
                current_state,
                memory['state_snapshot']
            )
            similarities.append((memory, sim))
        
        # 返回最相似的k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [mem for mem, _ in similarities[:k]]
    
    def _compute_similarity(self, 
                           poi1: Location, 
                           poi2: Location,
                           state1: State,
                           state2: Dict) -> float:
        """计算相似度"""
        sim = 0.0
        
        # 1. POI类型相似度
        if poi1.type == poi2.type:
            sim += 0.3
        
        # 2. POI名称语义相似度（简化）
        common_words = set(poi1.name) & set(poi2.name)
        if common_words:
            sim += 0.2
        
        # 3. 状态相似度
        # 时间相似
        time_diff = abs(state1.current_time - state2['time'])
        if time_diff < 2.0:  # 2小时内
            sim += 0.3
        
        # 预算相似
        budget_diff = abs(state1.remaining_budget - state2['budget'])
        if budget_diff < 100:
            sim += 0.2
        
        return sim


class NeuralContextManager:
    """
    神经上下文管理器
    
    整合：
    1. GlobalContext - 全局状态
    2. ContextualMemory - 长程记忆
    3. 影响计算 - 双向传播
    """
    
    def __init__(self):
        self.global_context = GlobalContext()
        self.memory = ContextualMemory()
        
        # 影响网格
        self.influence_grid: Dict[str, Dict[str, float]] = {}
    
    def update_after_decision(self,
                             session: PlanningSession,
                             selected_poi: Location,
                             satisfaction: float):
        """
        用户做出选择后更新
        
        这里实现全局影响传播
        """
        current_state = session.current_state
        
        # 1. 更新全局上下文
        visit_duration = selected_poi.average_visit_time
        self.global_context.update_after_visit(
            selected_poi,
            satisfaction,
            visit_duration
        )
        
        # 2. 存储到记忆
        context_desc = self._describe_context(current_state, self.global_context)
        self.memory.store(
            selected_poi,
            current_state,
            satisfaction,
            context_desc
        )
        
        # 3. 传播影响（如果满意度高）
        if satisfaction > 0.7:
            self._propagate_positive_influence(selected_poi, satisfaction)
    
    def enhance_scoring(self,
                       poi: Location,
                       base_score: float,
                       current_state: State) -> float:
        """
        使用神经上下文增强评分
        
        这是关键接口：
        - 输入：基础评分
        - 输出：上下文增强后的评分
        """
        # 1. 全局上下文影响
        context_influence = self.global_context.get_poi_influence(poi)
        
        # 2. 历史记忆影响
        similar_memories = self.memory.retrieve_similar(poi, current_state, k=2)
        memory_influence = self._compute_memory_influence(similar_memories)
        
        # 3. 休息需求调整
        if poi.type.value == 'restaurant':
            rest_need = self.global_context.get_rest_need()
            if rest_need > 0.6:
                # 很累，餐厅评分提升
                context_influence += 0.2
        
        # 4. 影响网格（横向影响）
        lateral_influence = self.influence_grid.get(poi.id, {}).get('boost', 0.0)
        
        # 综合
        enhanced_score = base_score + (
            0.4 * context_influence +
            0.3 * memory_influence +
            0.3 * lateral_influence
        )
        
        return np.clip(enhanced_score, 0.0, 1.0)
    
    def _propagate_positive_influence(self, poi: Location, satisfaction: float):
        """传播正面影响到相似POI"""
        influence_strength = (satisfaction - 0.7) / 0.3  # [0, 1]
        
        # 简化：通过名称关键词传播影响
        keywords = self._extract_keywords(poi.name)
        
        for keyword in keywords:
            if keyword not in self.influence_grid:
                self.influence_grid[keyword] = {}
            
            self.influence_grid[keyword]['boost'] = influence_strength * 0.2
    
    def _compute_memory_influence(self, memories: List[Dict]) -> float:
        """从记忆中计算影响"""
        if not memories:
            return 0.0
        
        # 加权平均历史满意度
        total_weight = 0.0
        weighted_sum = 0.0
        
        for i, memory in enumerate(memories):
            weight = 1.0 / (i + 1)  # 越相似权重越高
            weighted_sum += weight * (memory['satisfaction'] - 0.5)  # 中心化
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _describe_context(self, state: State, context: GlobalContext) -> str:
        """描述当前情境"""
        desc_parts = []
        
        if context.fatigue_level > 0.6:
            desc_parts.append("疲劳")
        if context.culture_saturation > 0.5:
            desc_parts.append("文化饱和")
        if state.remaining_budget < 200:
            desc_parts.append("预算紧张")
        
        return ", ".join(desc_parts) if desc_parts else "正常"
    
    def _extract_keywords(self, name: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        keyword_dict = {
            '园': 'garden',
            '博物馆': 'museum',
            '馆': 'museum',
            '寺': 'temple',
            '塔': 'tower',
            '楼': 'building',
            '路': 'street',
            '街': 'street'
        }
        
        for key, category in keyword_dict.items():
            if key in name:
                keywords.append(category)
        
        return keywords
    
    def get_context_summary(self) -> Dict:
        """获取上下文摘要（用于调试和展示）"""
        return {
            'fatigue_level': round(self.global_context.fatigue_level, 2),
            'satisfaction_avg': round(
                np.mean(self.global_context.satisfaction_history) 
                if self.global_context.satisfaction_history else 0, 
                2
            ),
            'culture_saturation': round(self.global_context.culture_saturation, 2),
            'memorable_count': len(self.global_context.memorable_pois),
            'memory_count': len(self.memory.memory_bank),
            'preference_evolution': self.global_context.preference_evolution
        }
