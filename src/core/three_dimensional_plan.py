"""
三维决策空间：X备选 × Y时间 × Z影响场

核心特性：
- X轴：横向备选方案（用户可选）
- Y轴：纵向时间线（自动推进）
- Z轴：影响力场（隐藏但可解释）
- 动静双态：静态快照 + 动态工作区

预留：第四维度（事件流/因果链）扩展接口

Author: GAODE Team
Date: 2024-12
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import copy
import uuid

from .models import Location, State, UserProfile
from .progressive_planner import ProgressivePlanner
from .neural_net_service import NeuralNetService
from .influence_field import InfluenceField, InfluenceFactor


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"          # 待选择
    SELECTED = "selected"        # 当前选中
    ALTERNATIVE = "alternative"  # 备选方案
    EXECUTED = "executed"        # 已执行
    SKIPPED = "skipped"         # 已跳过
    ADJUSTED = "adjusted"        # 已调整（第四维度）


@dataclass
class DecisionPoint:
    """
    三维决策点
    
    坐标：
    - x: X轴索引（备选方案）
    - y: Y轴索引（时间点）
    - z: Z轴场强（影响力）
    """
    x: int
    y: int
    z: float
    
    option: Location
    time: datetime
    duration: float  # 小时
    
    # Z轴详细信息
    factors: List[InfluenceFactor] = field(default_factory=list)
    
    # 节点状态
    status: NodeStatus = NodeStatus.PENDING
    
    # 动态调整标记
    is_adjusted: bool = False
    original_time: Optional[datetime] = None
    adjustment_reason: str = ""
    
    # 预留：第四维度事件
    dimensional_4_events: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'option': {
                'id': self.option.id,
                'name': self.option.name,
                'type': self.option.type.value,
                'rating': getattr(self.option, 'rating', None)
            },
            'time': self.time.isoformat(),
            'duration': self.duration,
            'status': self.status.value,
            'is_adjusted': self.is_adjusted,
            'factors': [
                {
                    'name': f.name,
                    'value': f.value,
                    'weight': f.weight,
                    'explanation': f.explanation
                }
                for f in self.factors
            ]
        }


@dataclass
class TimelineNode:
    """
    时间线节点（Y轴上的一个点）
    
    包含：
    - 当前选中的方案
    - X轴上的所有备选方案
    """
    y_index: int
    time: datetime
    duration: float
    
    # X轴：备选方案列表
    decision_points: List[DecisionPoint] = field(default_factory=list)
    
    # 当前选中
    selected_x: int = 0
    
    @property
    def selected_point(self) -> Optional[DecisionPoint]:
        """获取当前选中的决策点"""
        if 0 <= self.selected_x < len(self.decision_points):
            return self.decision_points[self.selected_x]
        return None
    
    def switch_to(self, x_index: int) -> bool:
        """横向切换到备选方案"""
        if 0 <= x_index < len(self.decision_points):
            self.selected_x = x_index
            # 更新状态
            for i, point in enumerate(self.decision_points):
                point.status = NodeStatus.SELECTED if i == x_index else NodeStatus.ALTERNATIVE
            return True
        return False
    
    def get_alternatives(self) -> List[DecisionPoint]:
        """获取所有备选（包括选中的）"""
        return self.decision_points


@dataclass
class StaticSnapshot:
    """
    静态快照（已确认的版本）
    
    类似Git的commit
    """
    snapshot_id: str
    created_at: datetime
    nodes: List[TimelineNode]
    user_profile: UserProfile
    
    # 快照元数据
    commit_message: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            'snapshot_id': self.snapshot_id,
            'created_at': self.created_at.isoformat(),
            'commit_message': self.commit_message,
            'confidence': self.confidence,
            'nodes': [
                {
                    'y_index': node.y_index,
                    'time': node.time.isoformat(),
                    'duration': node.duration,
                    'selected': node.selected_point.to_dict() if node.selected_point else None,
                    'alternatives_count': len(node.decision_points)
                }
                for node in self.nodes
            ]
        }


class ThreeDimensionalPlan:
    """
    四维决策空间规划系统 🌌
    
    架构：
    - X轴：横向备选（用户主动选择）
    - Y轴：纵向时间（自动推进）
    - Z轴：影响力场（隐藏计算，可解释）
    - ✨ W轴：语义-因果流（体验连贯性+逻辑自洽性）
    
    双态系统：
    - 静态快照：用户确认的版本（不可变）
    - 动态工作区：实时执行的版本（可变）
    
    数学模型：
    - Φ_4D = Φ_3D + F_wc
    - F_wc = δ·S_sem + ε·C_causal
    """
    
    def __init__(self,
                 progressive_planner: ProgressivePlanner,
                 neural_service: NeuralNetService,
                 spatial_intelligence=None,
                 enable_4d: bool = True):
        """
        Args:
            spatial_intelligence: 大模型（上帝视角），用于W轴因果推理
            enable_4d: 是否启用四维模式（W轴）
        """
        self.planner = progressive_planner
        self.neural = neural_service
        self.spatial_intelligence = spatial_intelligence
        
        # Z轴+W轴：影响力场（四维升级）
        self.influence_field = InfluenceField(
            progressive_planner,
            neural_service,
            spatial_intelligence=spatial_intelligence,
            enable_4d=enable_4d
        )
        
        # Y轴：时间线
        self.timeline: List[TimelineNode] = []
        
        # 静态快照历史
        self.snapshots: List[StaticSnapshot] = []
        
        # 动态工作区
        self.working_timeline: Optional[List[TimelineNode]] = None
        
        # 当前快照
        self.current_snapshot: Optional[StaticSnapshot] = None
        
        # 预留：第四维度处理器
        self.dimensional_4_handler = None  # TODO: 未来扩展
    
    def generate_3d_space(self,
                         session_id: str,
                         initial_state: State,
                         user_profile: UserProfile,
                         y_steps: int = 5,
                         x_alternatives: int = 4) -> List[TimelineNode]:
        """
        生成三维决策空间
        
        Args:
            session_id: 规划会话ID
            initial_state: 初始状态
            user_profile: 用户画像
            y_steps: Y轴节点数（时间点数量）
            x_alternatives: 每个Y节点的X轴备选数
            
        Returns:
            时间线节点列表
        """
        print(f"🌌 生成三维决策空间...")
        print(f"   Y轴: {y_steps}个时间点")
        print(f"   X轴: 每个时间点{x_alternatives}个备选")
        
        self.timeline = []
        current_state = initial_state
        current_time = datetime.now()
        
        for y in range(y_steps):
            # 获取X轴候选
            try:
                candidates = self.planner.get_next_options(
                    session_id=session_id,
                    state=current_state,
                    limit=x_alternatives
                )
            except Exception as e:
                print(f"⚠️ Y={y} 获取候选失败: {e}")
                break
            
            if not candidates:
                print(f"⚠️ Y={y} 无候选方案")
                break
            
            # 创建Y轴节点
            timeline_node = TimelineNode(
                y_index=y,
                time=current_time,
                duration=2.0  # 默认2小时
            )
            
            # 为每个候选计算场强（Z轴 + W轴）
            for x, candidate in enumerate(candidates):
                # 获取当前POI（用于W轴语义-因果分析）
                current_poi = current_state.current_location if hasattr(current_state, 'current_location') else None
                
                # 构造上下文（用于W轴因果推理）
                context = {
                    'weather': 'sunny',  # TODO: 接入实时天气
                    'time_of_day': current_time.hour,
                    'is_weekend': current_time.weekday() >= 5
                }
                
                # 计算影响力场（四维：Z轴 + W轴）
                field_strength, factors, w_details = self.influence_field.compute_field(
                    option=candidate.poi,
                    time_point=current_time,
                    state=current_state,
                    user_profile=user_profile,
                    current_poi=current_poi,  # ✨ 启用W轴
                    context=context
                )
                
                # 创建决策点
                decision_point = DecisionPoint(
                    x=x,
                    y=y,
                    z=field_strength,  # 四维场强（如果W轴启用）
                    option=candidate.poi,
                    time=current_time,
                    duration=getattr(candidate.poi, 'average_visit_time', 2.0) or 2.0,
                    factors=factors,
                    status=NodeStatus.SELECTED if x == 0 else NodeStatus.ALTERNATIVE
                )
                
                # 保存W轴详情（如果有）
                if w_details:
                    decision_point.dimensional_4_events.append({
                        'type': 'w_axis_analysis',
                        'details': w_details
                    })
                
                timeline_node.decision_points.append(decision_point)
            
            # 设置默认选中第一个（场强最高）
            timeline_node.selected_x = 0
            
            self.timeline.append(timeline_node)
            
            # Y轴推进：使用选中的方案更新状态
            selected_poi = timeline_node.selected_point.option
            try:
                current_state = self.planner.apply_action(
                    current_state,
                    selected_poi
                )
            except:
                # 简化状态更新
                current_state.visited.append(selected_poi)
                current_state.current_location = selected_poi
            
            # 时间推进
            current_time += timedelta(hours=timeline_node.duration + 0.5)
            
            print(f"✅ Y={y} 生成完成: {len(timeline_node.decision_points)}个备选")
        
        print(f"🎉 三维空间生成完成！共{len(self.timeline)}个时间节点")
        
        return self.timeline
    
    def commit_snapshot(self,
                       message: str = "") -> StaticSnapshot:
        """
        提交静态快照（用户确认方案）
        
        类似Git commit
        """
        if not self.timeline:
            raise ValueError("时间线为空，无法提交快照")
        
        # 深拷贝（避免后续修改影响快照）
        snapshot_nodes = copy.deepcopy(self.timeline)
        
        # 创建快照
        snapshot = StaticSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            nodes=snapshot_nodes,
            user_profile=None,  # 可选
            commit_message=message or f"用户确认方案 - {len(self.timeline)}个节点",
            confidence=self._calculate_confidence()
        )
        
        # 保存历史
        self.snapshots.append(snapshot)
        self.current_snapshot = snapshot
        
        # 初始化动态工作区（fork from snapshot）
        self.working_timeline = copy.deepcopy(self.timeline)
        
        print(f"✅ 静态快照已提交")
        print(f"   ID: {snapshot.snapshot_id[:8]}...")
        print(f"   节点数: {len(self.timeline)}")
        print(f"   置信度: {snapshot.confidence:.0%}")
        
        return snapshot
    
    def switch_alternative(self,
                          y_index: int,
                          x_index: int) -> bool:
        """
        横向切换备选方案（X轴操作）
        
        用户点击某个节点的备选方案时调用
        """
        if not self.working_timeline:
            print("⚠️ 工作区未初始化，使用主时间线")
            timeline = self.timeline
        else:
            timeline = self.working_timeline
        
        if y_index >= len(timeline):
            print(f"⚠️ Y索引{y_index}越界")
            return False
        
        node = timeline[y_index]
        success = node.switch_to(x_index)
        
        if success:
            print(f"✅ 已切换: Y={y_index}, X={x_index}")
            print(f"   选择: {node.selected_point.option.name}")
            print(f"   场强: {node.selected_point.z:.2f}")
        
        return success
    
    def dynamic_adjust(self,
                      y_start: int,
                      delay_minutes: int,
                      reason: str = "") -> bool:
        """
        动态工作区实时调整
        
        场景：用户延误、突发事件等
        """
        if not self.working_timeline:
            print("⚠️ 工作区未初始化")
            return False
        
        print(f"⚙️ 动态调整: Y>={y_start}, 延迟{delay_minutes}分钟")
        
        adjusted_count = 0
        for node in self.working_timeline[y_start:]:
            if node.selected_point:
                # 保存原始时间
                if not node.selected_point.original_time:
                    node.selected_point.original_time = node.selected_point.time
                
                # 调整时间
                node.time += timedelta(minutes=delay_minutes)
                node.selected_point.time = node.time
                node.selected_point.is_adjusted = True
                node.selected_point.adjustment_reason = reason or "用户延误"
                node.selected_point.status = NodeStatus.ADJUSTED
                
                adjusted_count += 1
        
        print(f"✅ 已调整{adjusted_count}个节点")
        return True
    
    def get_diff(self) -> List[Dict]:
        """
        对比静态快照与动态工作区的差异
        
        Returns:
            差异列表
        """
        if not self.current_snapshot or not self.working_timeline:
            return []
        
        diffs = []
        
        for y_idx in range(min(len(self.current_snapshot.nodes), len(self.working_timeline))):
            static_node = self.current_snapshot.nodes[y_idx]
            working_node = self.working_timeline[y_idx]
            
            static_point = static_node.selected_point
            working_point = working_node.selected_point
            
            if not static_point or not working_point:
                continue
            
            # 检查选项变化
            if static_point.option.id != working_point.option.id:
                diffs.append({
                    'y_index': y_idx,
                    'type': 'option_changed',
                    'from': {
                        'name': static_point.option.name,
                        'x': static_point.x
                    },
                    'to': {
                        'name': working_point.option.name,
                        'x': working_point.x
                    }
                })
            
            # 检查时间调整
            if working_point.is_adjusted:
                diffs.append({
                    'y_index': y_idx,
                    'type': 'time_adjusted',
                    'original': working_point.original_time.isoformat() if working_point.original_time else None,
                    'current': working_point.time.isoformat(),
                    'reason': working_point.adjustment_reason
                })
        
        return diffs
    
    def get_explanation(self, y_index: int, x_index: int) -> Dict:
        """
        获取某个决策点的深度解释（Z轴信息）
        
        用户点击某个选项时，展示Z轴的影响因子
        """
        timeline = self.working_timeline or self.timeline
        
        if y_index >= len(timeline):
            return {'error': 'Y索引越界'}
        
        node = timeline[y_index]
        
        if x_index >= len(node.decision_points):
            return {'error': 'X索引越界'}
        
        point = node.decision_points[x_index]
        
        # 按贡献度排序因子
        sorted_factors = sorted(
            point.factors,
            key=lambda f: f.weighted_value,
            reverse=True
        )
        
        return {
            'option': {
                'name': point.option.name,
                'type': point.option.type.value,
                'rating': getattr(point.option, 'rating', None)
            },
            'time': point.time.isoformat(),
            'duration': point.duration,
            'field_strength': point.z,
            'status': point.status.value,
            'factors': [
                {
                    'name': f.name,
                    'value': f.value,
                    'weight': f.weight,
                    'weighted_value': f.weighted_value,
                    'source': f.source,
                    'explanation': f.explanation
                }
                for f in sorted_factors
            ],
            'is_adjusted': point.is_adjusted,
            'adjustment_reason': point.adjustment_reason if point.is_adjusted else None
        }
    
    def export_current_plan(self) -> Dict:
        """导出当前方案（用于前端展示）"""
        timeline = self.working_timeline or self.timeline
        
        return {
            'timeline': [
                {
                    'y_index': node.y_index,
                    'time': node.time.isoformat(),
                    'duration': node.duration,
                    'selected': node.selected_point.to_dict() if node.selected_point else None,
                    'alternatives': [
                        {
                            'x': point.x,
                            'name': point.option.name,
                            'field_strength': point.z,
                            'is_selected': point.x == node.selected_x
                        }
                        for point in node.decision_points
                    ]
                }
                for node in timeline
            ],
            'has_snapshot': self.current_snapshot is not None,
            'has_changes': len(self.get_diff()) > 0
        }
    
    def _calculate_confidence(self) -> float:
        """计算方案置信度"""
        if not self.timeline:
            return 0.0
        
        # 基于所有选中节点的平均场强
        field_strengths = []
        for node in self.timeline:
            if node.selected_point:
                field_strengths.append(node.selected_point.z)
        
        if not field_strengths:
            return 0.5
        
        return sum(field_strengths) / len(field_strengths)
