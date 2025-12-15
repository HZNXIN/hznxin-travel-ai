"""
空间智能核心 (SpatialIntelligenceCore)

核心理念：监控、分析、建议，而非控制、计划、强制
用户是主人，AI是顾问
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime

from .models import Location, State, PlanningSession, POIType


@dataclass
class ConstraintStatus:
    """约束状态（描述性，非指令性）"""
    time_usage: Dict = field(default_factory=dict)
    budget_usage: Dict = field(default_factory=dict)
    spatial_coverage: Dict = field(default_factory=dict)
    variety: Dict = field(default_factory=dict)


@dataclass
class ImpactAnalysis:
    """影响分析（信息性，非命令性）"""
    spatial_impact: Dict = field(default_factory=dict)
    time_impact: Dict = field(default_factory=dict)
    budget_impact: Dict = field(default_factory=dict)
    reachability_impact: Dict = field(default_factory=dict)
    
    def to_user_message(self) -> str:
        """转换为用户友好的描述"""
        messages = []
        
        if self.spatial_impact:
            messages.append(f"📍 空间：{self.spatial_impact.get('description', '')}")
        
        if self.time_impact:
            messages.append(f"⏱️  时间：{self.time_impact.get('time_status', '')}")
        
        if self.budget_impact:
            messages.append(f"💰 预算：{self.budget_impact.get('budget_status', '')}")
        
        if self.reachability_impact:
            messages.append(f"🎯 后续：{self.reachability_impact.get('description', '')}")
        
        return "\n".join(messages)


class SpatialNetwork:
    """
    空间网络模型
    
    理解城市的空间关系，不制定路线
    """
    
    def __init__(self):
        self.nodes: Dict[str, Location] = {}
        self.edges: Dict[Tuple[str, str], Dict] = {}
        self.clusters: Dict[str, List[Location]] = {}
    
    def add_node(self, poi: Location):
        """添加POI节点"""
        self.nodes[poi.id] = poi
    
    def add_edge(self, from_id: str, to_id: str, distance: float, time: float):
        """添加边（两POI之间的关系）"""
        self.edges[(from_id, to_id)] = {
            'distance': distance,
            'time': time
        }
    
    def get_distance(self, from_id: str, to_id: str) -> float:
        """获取距离"""
        if (from_id, to_id) in self.edges:
            return self.edges[(from_id, to_id)]['distance']
        return float('inf')
    
    def get_travel_time(self, from_id: str, to_id: str) -> float:
        """获取旅行时间"""
        if (from_id, to_id) in self.edges:
            return self.edges[(from_id, to_id)]['time']
        return float('inf')
    
    def get_cluster(self, poi: Location) -> Optional[str]:
        """获取POI所属的簇"""
        for cluster_name, pois in self.clusters.items():
            if poi in pois:
                return cluster_name
        return None


class ConstraintMonitor:
    """
    约束监控器
    
    不强制执行，只提醒用户当前状态
    """
    
    def monitor(self, 
               current_state: State,
               session: PlanningSession) -> ConstraintStatus:
        """
        监控约束状态
        
        返回：当前各项约束的使用情况（描述性）
        不返回：你应该怎么做（指令性）
        """
        status = ConstraintStatus()
        
        # 1. 时间使用
        time_used = current_state.current_time
        time_total = session.duration
        time_remaining = time_total - time_used
        usage_rate = time_used / time_total if time_total > 0 else 0
        
        status.time_usage = {
            'used': time_used,
            'total': time_total,
            'remaining': time_remaining,
            'usage_rate': usage_rate,
            'status': self._describe_usage(usage_rate),
            'description': f"已用{time_used:.1f}h / {time_total:.1f}h (进度{usage_rate*100:.0f}%)"
        }
        
        # 2. 预算使用
        budget_spent = session.budget - current_state.remaining_budget
        budget_total = session.budget
        budget_remaining = current_state.remaining_budget
        budget_rate = budget_spent / budget_total if budget_total > 0 else 0
        
        status.budget_usage = {
            'spent': budget_spent,
            'total': budget_total,
            'remaining': budget_remaining,
            'usage_rate': budget_rate,
            'status': self._describe_usage(budget_rate),
            'description': f"已用¥{budget_spent:.0f} / ¥{budget_total:.0f} (进度{budget_rate*100:.0f}%)"
        }
        
        # 3. 空间覆盖（访问了哪些地方）
        visited_count = len(current_state.visited_history)
        
        status.spatial_coverage = {
            'visited_count': visited_count,
            'visited_ids': list(current_state.visited_history),
            'description': f"已游览{visited_count}个地点"
        }
        
        # 4. 体验多样性（暂时简化）
        status.variety = {
            'description': f"多样性评估（基于历史）"
        }
        
        return status
    
    def _describe_usage(self, rate: float) -> Dict:
        """描述使用率（客观描述）"""
        if rate < 0.3:
            return {'level': 'low', 'description': '充裕', 'emoji': '😊'}
        elif rate < 0.7:
            return {'level': 'medium', 'description': '正常', 'emoji': '👍'}
        elif rate < 0.9:
            return {'level': 'high', 'description': '紧张', 'emoji': '⚠️'}
        else:
            return {'level': 'critical', 'description': '即将耗尽', 'emoji': '🚨'}


class ForesightEngine:
    """
    前瞻引擎
    
    "如果你选A，会发生什么"
    而不是"你应该选A"
    """
    
    def __init__(self, spatial_network: SpatialNetwork):
        self.network = spatial_network
    
    def analyze_choice_impact(self,
                             candidate: Location,
                             current_state: State,
                             session: PlanningSession) -> ImpactAnalysis:
        """
        分析选择的全局影响
        
        返回：客观的影响分析，不是主观的建议
        """
        analysis = ImpactAnalysis()
        
        # 1. 空间影响
        analysis.spatial_impact = self._analyze_spatial(candidate, current_state)
        
        # 2. 时间影响
        analysis.time_impact = self._analyze_time(candidate, current_state, session)
        
        # 3. 预算影响
        analysis.budget_impact = self._analyze_budget(candidate, current_state, session)
        
        # 4. 可达性影响
        analysis.reachability_impact = self._analyze_reachability(
            candidate, current_state, session
        )
        
        return analysis
    
    def _analyze_spatial(self, candidate: Location, state: State) -> Dict:
        """分析空间影响"""
        current_loc = state.current_location
        
        # 计算距离
        distance = self._haversine_distance(
            current_loc.lat, current_loc.lon,
            candidate.lat, candidate.lon
        )
        
        # 简化描述
        if distance < 1.0:
            distance_desc = f"很近（{distance:.1f}km），步行可达"
        elif distance < 5.0:
            distance_desc = f"中等距离（{distance:.1f}km），建议打车"
        else:
            distance_desc = f"较远（{distance:.1f}km），需要交通工具"
        
        return {
            'distance_km': distance,
            'description': distance_desc
        }
    
    def _analyze_time(self, 
                     candidate: Location,
                     state: State,
                     session: PlanningSession) -> Dict:
        """分析时间影响"""
        
        # 估算旅行时间
        distance = self._haversine_distance(
            state.current_location.lat, state.current_location.lon,
            candidate.lat, candidate.lon
        )
        travel_time = self._estimate_travel_time(distance)
        
        # 预计游览时间
        visit_time = candidate.average_visit_time
        
        # 总耗时
        total_time = travel_time + visit_time
        
        # 新的总时间
        new_total_time = state.current_time + total_time
        remaining_time = session.duration - new_total_time
        
        # 客观描述（不是建议）
        if remaining_time < 1.0:
            time_status = f"耗时{total_time:.1f}h，之后仅剩{remaining_time:.1f}h"
        elif remaining_time < 2.0:
            time_status = f"耗时{total_time:.1f}h，之后还能游览1个短景点"
        else:
            estimated_pois = int(remaining_time / 2.0)
            time_status = f"耗时{total_time:.1f}h，之后大约能游览{estimated_pois}个景点"
        
        return {
            'travel_time': travel_time,
            'visit_time': visit_time,
            'total_time_cost': total_time,
            'remaining_after': remaining_time,
            'time_status': time_status
        }
    
    def _analyze_budget(self,
                       candidate: Location,
                       state: State,
                       session: PlanningSession) -> Dict:
        """分析预算影响"""
        
        # 门票费用
        ticket_cost = candidate.ticket_price
        
        # 估算交通费用（简化）
        distance = self._haversine_distance(
            state.current_location.lat, state.current_location.lon,
            candidate.lat, candidate.lon
        )
        transport_cost = distance * 3  # 假设每公里3元
        
        total_cost = ticket_cost + transport_cost
        
        # 新预算状态
        new_remaining = state.remaining_budget - total_cost
        
        # 客观描述
        if new_remaining < 50:
            budget_status = f"花费¥{total_cost:.0f}，之后预算紧张（剩¥{new_remaining:.0f}）"
        elif new_remaining < 200:
            budget_status = f"花费¥{total_cost:.0f}，之后预算有限（剩¥{new_remaining:.0f}）"
        else:
            budget_status = f"花费¥{total_cost:.0f}，之后预算充裕（剩¥{new_remaining:.0f}）"
        
        return {
            'ticket_cost': ticket_cost,
            'transport_cost': transport_cost,
            'total_cost': total_cost,
            'remaining_after': new_remaining,
            'budget_status': budget_status
        }
    
    def _analyze_reachability(self,
                             candidate: Location,
                             state: State,
                             session: PlanningSession) -> Dict:
        """
        分析可达性影响
        
        选了A之后，还能去哪？（客观分析）
        """
        # 简化实现：返回基本信息
        return {
            'description': "可达性分析（基于剩余时间和预算）",
            'note': "这只是预测，实际取决于你的选择"
        }
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """计算两点距离（km）"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # 地球半径（km）
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _estimate_travel_time(self, distance_km: float) -> float:
        """估算旅行时间（小时）"""
        if distance_km < 1.0:
            return distance_km / 5  # 步行速度5km/h
        else:
            return distance_km / 20 + 0.1  # 打车速度20km/h + 等待时间


@dataclass
class RiskAnalysis:
    """风险分析结果"""
    impact: ImpactAnalysis
    risk_level: str  # 'info', 'warning', 'critical'
    risk_type: Optional[str] = None  # 'budget', 'time', 'return'
    constraint_violations: List[Dict] = field(default_factory=list)


class SpatialIntelligenceCore:
    """
    空间智能核心
    
    核心理念：
    - 监控全局状态
    - 分析选择影响
    - 提供客观信息
    - 用户做决定
    """
    
    def __init__(self, llm_client=None):
        self.spatial_network = SpatialNetwork()
        self.constraint_monitor = ConstraintMonitor()
        self.foresight_engine = ForesightEngine(self.spatial_network)
        self.llm_client = llm_client  # 可选的LLM客户端
    
    def initialize(self, pois: List[Location]):
        """
        初始化空间网络
        
        理解城市结构，不制定路线
        """
        # 添加所有POI节点
        for poi in pois:
            self.spatial_network.add_node(poi)
        
        # 构建边（简化：计算两两距离）
        for poi1 in pois:
            for poi2 in pois:
                if poi1.id != poi2.id:
                    distance = self._calculate_distance(poi1, poi2)
                    time = self._estimate_time(distance)
                    self.spatial_network.add_edge(
                        poi1.id, poi2.id, distance, time
                    )
        
        # 识别簇（简化：按类型分组）
        self._identify_clusters(pois)
    
    def get_global_status(self,
                         current_state: State,
                         session: PlanningSession) -> Dict:
        """
        获取全局状态
        
        返回当前的全局概览（信息性）
        """
        status = self.constraint_monitor.monitor(current_state, session)
        
        return {
            'time': status.time_usage,
            'budget': status.budget_usage,
            'coverage': status.spatial_coverage,
            'variety': status.variety,
            'summary': self._generate_summary(status)
        }
    
    def analyze_candidates(self,
                          candidates: List[Location],
                          current_state: State,
                          session: PlanningSession) -> List[Dict]:
        """
        分析所有候选的全局影响
        
        不是排序，只是提供信息
        """
        analyses = []
        
        for candidate in candidates:
            impact = self.foresight_engine.analyze_choice_impact(
                candidate, current_state, session
            )
            
            analyses.append({
                'poi': candidate,
                'impact': impact,
                'user_message': impact.to_user_message()
            })
        
        return analyses
    
    def _calculate_distance(self, poi1: Location, poi2: Location) -> float:
        """计算距离"""
        return self.foresight_engine._haversine_distance(
            poi1.lat, poi1.lon, poi2.lat, poi2.lon
        )
    
    def _estimate_time(self, distance: float) -> float:
        """估算时间"""
        return self.foresight_engine._estimate_travel_time(distance)
    
    def _identify_clusters(self, pois: List[Location]):
        """识别POI簇（简化：按类型）"""
        clusters = {}
        
        for poi in pois:
            poi_type = poi.type.value
            if poi_type not in clusters:
                clusters[poi_type] = []
            clusters[poi_type].append(poi)
        
        self.spatial_network.clusters = clusters
    
    def _generate_summary(self, status: ConstraintStatus) -> str:
        """生成摘要"""
        parts = []
        
        # 时间摘要
        time_desc = status.time_usage.get('description', '')
        parts.append(time_desc)
        
        # 预算摘要
        budget_desc = status.budget_usage.get('description', '')
        parts.append(budget_desc)
        
        # 空间摘要
        spatial_desc = status.spatial_coverage.get('description', '')
        parts.append(spatial_desc)
        
        return " | ".join(parts)
    
    def analyze_with_risk_level(self,
                                candidate: Location,
                                current_state: State,
                                session: PlanningSession) -> RiskAnalysis:
        """
        分析选择 + 风险等级评估
        
        这是集成的核心方法！
        """
        # 1. 基础影响分析
        impact = self.foresight_engine.analyze_choice_impact(
            candidate, current_state, session
        )
        
        # 2. 硬约束检查
        violations = self._check_hard_constraints(
            candidate, current_state, session, impact
        )
        
        # 3. 确定风险等级
        risk_level, risk_type = self._determine_risk_level(
            impact, violations, current_state, session
        )
        
        return RiskAnalysis(
            impact=impact,
            risk_level=risk_level,
            risk_type=risk_type,
            constraint_violations=violations
        )
    
    def _check_hard_constraints(self,
                                candidate: Location,
                                state: State,
                                session: PlanningSession,
                                impact: ImpactAnalysis) -> List[Dict]:
        """检查硬约束"""
        violations = []
        
        # 检查回程约束
        if 'return' in session.hard_constraints:
            return_constraint = session.hard_constraints['return']
            
            # 计算是否会错过回程
            finish_time = state.current_time + impact.time_impact.get('total_time_cost', 0)
            
            # 返程位置
            return_location = return_constraint.get('location')
            if return_location:
                # 计算返程时间
                return_travel_time = self._estimate_time(
                    self._calculate_distance(candidate, return_location)
                )
                
                arrive_time = finish_time + return_travel_time
                
                # 检查是否超过截止时间
                deadline_hour = return_constraint.get('time')  # datetime对象或小时数
                
                if isinstance(deadline_hour, (int, float)):
                    deadline = deadline_hour
                else:
                    # 如果是datetime，转换为小时数
                    deadline = deadline_hour.hour if hasattr(deadline_hour, 'hour') else 18.0
                
                buffer = 0.5  # 30分钟缓冲
                
                if arrive_time + buffer > deadline:
                    violations.append({
                        'type': 'return',
                        'severity': 'critical',
                        'details': {
                            'finish_time': f"{int(finish_time)}:{int((finish_time % 1) * 60):02d}",
                            'return_travel_time': return_travel_time,
                            'arrive_time': f"{int(arrive_time)}:{int((arrive_time % 1) * 60):02d}",
                            'deadline': f"{int(deadline)}:{int((deadline % 1) * 60):02d}",
                            'late_by': arrive_time - deadline,
                            'consequence': f"错过{return_constraint.get('mode', '回程')}"
                        }
                    })
        
        return violations
    
    def _determine_risk_level(self,
                             impact: ImpactAnalysis,
                             violations: List[Dict],
                             state: State,
                             session: PlanningSession) -> tuple:
        """确定风险等级"""
        
        # 检查严重违反（硬约束）
        if any(v.get('severity') == 'critical' for v in violations):
            return ('critical', violations[0]['type'])
        
        # 检查预算警告
        remaining = impact.budget_impact.get('remaining_after', 999)
        if remaining < 50:
            return ('critical', 'budget')
        elif remaining < 100:
            return ('warning', 'budget')
        
        # 检查时间警告
        remaining_time = impact.time_impact.get('remaining_after', 999)
        if remaining_time < 0.5:
            return ('critical', 'time')
        elif remaining_time < 1.0:
            return ('warning', 'time')
        
        # 正常
        return ('info', None)
