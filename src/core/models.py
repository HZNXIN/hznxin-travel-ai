"""
核心数据模型
定义系统中所有的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import uuid


class TransportMode(Enum):
    """交通方式枚举"""
    WALK = "walk"
    TAXI = "taxi"
    BUS = "bus"
    SUBWAY = "subway"
    BICYCLE = "bicycle"


class POIType(Enum):
    """POI类型枚举"""
    ATTRACTION = "attraction"
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    TRANSPORT_HUB = "transport_hub"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    STATION = "station"  # 车站、机场等交通起点


@dataclass
class Location:
    """
    位置实体
    代表图中的节点 V
    """
    id: str
    name: str
    lat: float
    lon: float
    type: POIType
    address: str = ""
    city: str = ""  # ✅ 添加city字段
    phone: str = ""
    rating: float = 0.0  # ✅ 添加rating字段（高德API返回）
    opening_hours: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    average_visit_time: float = 2.0  # 小时
    ticket_price: float = 0.0
    
    def is_open(self, time: float) -> bool:
        """
        检查在指定时间是否营业
        
        Args:
            time: 小时数（0-24）
            
        Returns:
            是否营业
        """
        day = datetime.fromtimestamp(time * 3600).strftime('%A')
        if day not in self.opening_hours:
            return True  # 默认全天开放
        
        start, end = self.opening_hours[day]
        hour = time % 24
        return start <= hour <= end
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Location) and self.id == other.id


@dataclass
class Edge:
    """
    边实体
    代表图中的边 E
    包含权重 w = (distance, time, cost)
    """
    id: str
    from_loc: Location
    to_loc: Location
    mode: TransportMode
    distance: float  # km
    time: float  # hours
    cost: float  # RMB
    route_geometry: List[Tuple[float, float]] = field(default_factory=list)
    traffic_condition: Optional[str] = None
    verification: Optional['EdgeVerification'] = None
    
    @property
    def weight(self) -> Tuple[float, float, float]:
        """边的权重向量"""
        return (self.distance, self.time, self.cost)


@dataclass
class EdgeVerification:
    """边的验证数据"""
    route_verified: bool
    estimated_time_range: Tuple[float, float]
    real_time_traffic: Optional[Dict] = None
    safety_score: float = 1.0
    reliability_score: float = 1.0


@dataclass
class State:
    """
    系统状态 σ = (l, t, H, V, budget)
    
    数学定义:
    σ ∈ Σ where Σ is the state space
    """
    current_location: Location
    current_time: float  # 从开始的小时数
    visited_history: Set[str] = field(default_factory=set)
    visit_quality: Dict[str, float] = field(default_factory=dict)
    remaining_budget: float = 10000.0
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.visited_history, list):
            self.visited_history = set(self.visited_history)
    
    def copy(self) -> 'State':
        """深拷贝状态"""
        return State(
            current_location=self.current_location,
            current_time=self.current_time,
            visited_history=self.visited_history.copy(),
            visit_quality=self.visit_quality.copy(),
            remaining_budget=self.remaining_budget
        )
    
    def is_feasible(self, action: 'Action', total_duration: float) -> bool:
        """
        检查动作是否可行
        
        Args:
            action: 待执行的动作
            total_duration: 总持续时间
            
        Returns:
            是否可行
        """
        # 时间约束
        if self.current_time + action.estimated_time > total_duration:
            return False
        
        # 预算约束
        if action.estimated_cost > self.remaining_budget:
            return False
        
        return True


@dataclass
class Action:
    """
    动作 a = (n, m)
    
    数学定义:
    a ∈ A(σ) where A(σ) is the action space at state σ
    """
    target_node: Location
    transport_mode: TransportMode
    selected_edge: Optional[Edge] = None
    estimated_time: float = 0.0
    estimated_cost: float = 0.0


@dataclass
class DataSource:
    """数据源"""
    name: str  # 'gaode', 'ctrip', 'mafengwo', etc.
    rating: float  # 评分
    review_count: int  # 评论数
    last_update: datetime
    weight: float = 0.33  # 权重
    credibility: float = 1.0  # 可信度


@dataclass
class NodeVerification:
    """
    节点验证数据
    实现四项基本原则
    """
    # 原则1: 多源数据交叉验证
    data_sources: List[DataSource] = field(default_factory=list)
    consistency_score: float = 0.0  # Consistency ∈ [0, 1]
    weighted_rating: float = 0.0
    rating_variance: float = 0.0
    
    # 原则2: 数据清洗
    total_reviews: int = 0
    valid_reviews: int = 0
    fake_rate: float = 0.0  # 虚假率
    positive_rate: float = 0.0  # 正面评价率
    negative_rate: float = 0.0  # 负面评价率
    key_positive_words: List[str] = field(default_factory=list)
    key_negative_words: List[str] = field(default_factory=list)
    
    # 原则3: 空间合理性
    spatial_score: float = 0.0  # Spatial_Score ∈ [0, 1]
    distance_from_current: float = 0.0
    detour_rate: float = 0.0  # 绕路率
    connectivity_score: float = 1.0
    
    # 原则4: 时间合理性
    temporal_score: float = 0.0  # Temporal_Score ∈ [0, 1]
    is_open: bool = True
    predicted_crowd_level: float = 0.0  # [0, 1]
    optimal_visit_time: Optional[Tuple[float, float]] = None
    time_sufficient: bool = True
    
    @property
    def overall_trust_score(self) -> float:
        """
        综合可信度评分
        
        Trust = w1·Consistency + w2·(1-FakeRate) + w3·Spatial + w4·Temporal
        """
        return (
            0.25 * self.consistency_score +
            0.25 * (1 - self.fake_rate) +
            0.25 * self.spatial_score +
            0.25 * self.temporal_score
        )


@dataclass
class CandidateOption:
    """
    候选选项
    渐进式展开时返回给用户的选项
    """
    node: Location
    edges: List[Edge]  # 多种到达方式
    verification: NodeVerification
    score: float  # 综合评分
    match_score: float  # 与用户偏好的匹配度
    future_preview: List[Location] = field(default_factory=list)
    
    # 扩展字段（用于深度分析和API响应）
    quality_score: Optional['POIQualityScore'] = None  # 质量评分
    deep_analysis: Optional['DeepRecommendation'] = None  # 深度分析
    edge_score: float = 0.0  # 边评分（距离等）
    total_score: float = 0.0  # 总评分
    
    # 风险等级（用于视觉化）
    risk_level: str = 'info'  # 'info', 'warning', 'critical'
    risk_details: Optional[Dict] = None  # 风险详情
    
    # 🔥 四维空间智能集成字段（新增）
    explanation: Optional[str] = None  # 人性化解释（朋友式语言）
    c_causal: Optional[float] = None  # W轴因果分（0-1）
    region: Optional[str] = None  # 所属区域（如"鼓浪屿"）
    visit_count: Optional[int] = None  # 区域访问次数
    w_axis_details: Optional[Dict] = None  # W轴详细信息
    
    def to_dict(self) -> Dict:
        """转换为字典（用于API返回）"""
        result = {
            'node': {
                'id': self.node.id,
                'name': self.node.name,
                'type': self.node.type.value,
                'location': (self.node.lat, self.node.lon)
            },
            'edges': [
                {
                    'id': edge.id,
                    'mode': edge.mode.value,
                    'distance': edge.distance,
                    'time': edge.time,
                    'cost': edge.cost
                }
                for edge in self.edges
            ],
            'verification': {
                'data_sources': [
                    {
                        'name': ds.name,
                        'rating': ds.rating,
                        'review_count': ds.review_count
                    }
                    for ds in self.verification.data_sources
                ],
                'consistency_score': self.verification.consistency_score,
                'fake_rate': self.verification.fake_rate,
                'spatial_score': self.verification.spatial_score,
                'temporal_score': self.verification.temporal_score,
                'overall_trust': self.verification.overall_trust_score
            },
            'score': self.score,
            'match_score': self.match_score,
            'future_preview': [
                {'id': loc.id, 'name': loc.name}
                for loc in self.future_preview
            ],
            'risk_level': self.risk_level
        }
        
        # 添加风险详情（如果有）
        if self.risk_details:
            result['risk_details'] = self.risk_details
        
        # 🔥 添加四维空间智能字段（如果有）
        if self.explanation:
            result['explanation'] = self.explanation
        if self.c_causal is not None:
            result['c_causal'] = self.c_causal
        if self.region:
            result['region'] = self.region
        if self.visit_count is not None:
            result['visit_count'] = self.visit_count
        if self.w_axis_details:
            result['w_axis_details'] = self.w_axis_details
        
        return result


@dataclass
class UserProfile:
    """
    用户画像
    从用户输入中提取
    """
    # 旅行目的
    purpose: Dict[str, float] = field(default_factory=dict)
    # {'leisure': 0.8, 'culture': 0.6, 'adventure': 0.2, ...}
    
    # 体力强度偏好
    intensity: Dict[str, float] = field(default_factory=dict)
    # {'very_low': 0.0, 'low': 0.8, 'medium': 0.2, 'high': 0.0, 'very_high': 0.0}
    
    # 节奏偏好
    pace: Dict[str, float] = field(default_factory=dict)
    # {'very_slow': 0.0, 'slow': 0.9, 'medium': 0.1, 'fast': 0.0, 'very_fast': 0.0}
    
    # 美食偏好
    food_preference: Dict[str, float] = field(default_factory=dict)
    # {'sichuan': 0.2, 'cantonese': 0.5, 'jiangzhe': 0.9, ...}
    
    # 预算偏好
    budget_level: str = "medium"  # 'low', 'medium', 'high', 'luxury'
    
    # 避免拥挤程度
    avoid_crowd_preference: float = 0.5  # [0, 1]


@dataclass
class PathHistory:
    """路径历史记录"""
    action: Action
    previous_state: State
    new_state: State
    timestamp: datetime = field(default_factory=datetime.now)
    user_feedback: Optional[float] = None  # 用户反馈评分


@dataclass
class PlanningSession:
    """规划会话"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    start_location: Location = None
    destination_city: str = ""
    duration: float = 72.0  # 小时
    budget: float = 5000.0
    
    # 用户画像
    user_profile: Optional[UserProfile] = None
    
    # 硬约束（不可违背的要求）
    hard_constraints: Dict = field(default_factory=dict)
    # 示例: {'return': {'time': datetime, 'location': Location, 'mode': 'train'}}
    
    # 状态
    initial_state: Optional[State] = None  # 初始状态
    current_state: Optional[State] = None  # 当前状态
    
    # 历史
    path_history: List[PathHistory] = field(default_factory=list)  # 路径历史
    history: List[CandidateOption] = field(default_factory=list)  # 选择历史
    
    # 风险确认记录
    risk_acknowledgments: List[Dict] = field(default_factory=list)  # 用户已确认的风险
    
    # 🔥 四维空间智能：区域访问计数（软约束）
    region_visit_counts: Dict[str, int] = field(default_factory=dict)  # 区域访问次数
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)  # 最后活跃时间
    
    def add_history(self, action: Action, old_state: State, new_state: State):
        """添加历史记录"""
        self.path_history.append(
            PathHistory(
                action=action,
                previous_state=old_state,
                new_state=new_state
            )
        )
        self.updated_at = datetime.now()
    
    def get_visited_pois(self) -> List[Location]:
        """获取已访问的POI"""
        return [
            h.action.target_node 
            for h in self.path_history
        ]
