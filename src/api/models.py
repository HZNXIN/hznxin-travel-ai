"""
API请求/响应模型
定义所有API的数据结构
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 请求模型 ====================

class InitSessionRequest(BaseModel):
    """初始化会话请求"""
    user_id: str = Field(..., description="用户ID")
    starting_location: str = Field(..., description="起始位置（地点名或地址）")
    purpose: Optional[str] = Field(None, description="旅行目的（如'历史文化'、'美食探索'）")
    pace: Optional[str] = Field("medium", description="旅行节奏（slow/medium/fast）")
    intensity: Optional[str] = Field("medium", description="体力强度（low/medium/high）")
    time_budget: Optional[float] = Field(None, description="时间预算（小时）")
    money_budget: Optional[float] = Field(None, description="金钱预算（元）")


class SelectOptionRequest(BaseModel):
    """选择选项请求"""
    session_id: str = Field(..., description="会话ID")
    option_index: int = Field(..., description="选择的选项索引（从0开始）")


# ==================== 响应模型 ====================

class LocationResponse(BaseModel):
    """位置响应"""
    id: str
    name: str
    lat: float
    lon: float
    type: str
    address: str
    average_visit_time: float
    ticket_price: float


class DataSourceResponse(BaseModel):
    """数据源响应"""
    source: str
    rating: float
    reviews: int
    last_update: str
    weight: float
    credibility: float


class VerificationResponse(BaseModel):
    """验证数据响应"""
    consistency_score: float
    weighted_rating: float
    total_reviews: int
    valid_reviews: int
    fake_rate: float
    positive_rate: float
    negative_rate: float
    key_positive_words: List[str]
    key_negative_words: List[str]
    spatial_score: float
    temporal_score: float


class QualityScoreResponse(BaseModel):
    """质量评分响应"""
    playability: float
    viewability: float
    popularity: float
    history: float
    overall: float


class ReasonResponse(BaseModel):
    """推荐理由响应"""
    type: str
    content: str
    weight: float
    evidence: Optional[str] = None


class MustSeeSpotResponse(BaseModel):
    """必看景观响应"""
    name: str
    description: str
    importance: int
    best_time: Optional[str] = None
    photo_tip: Optional[str] = None


class CoreHighlightsResponse(BaseModel):
    """核心亮点响应"""
    architecture: List[str]
    layout: Dict[str, str]
    history: List[str]
    must_see: List[MustSeeSpotResponse]
    unique_features: List[str]


class PhotoSpotResponse(BaseModel):
    """拍照机位响应"""
    location: str
    subject: str
    best_time: str
    tips: Optional[str] = None


class VisitStrategyResponse(BaseModel):
    """游玩攻略响应"""
    best_time: str
    duration: str
    route: List[str]
    photo_spots: List[PhotoSpotResponse]
    tips: List[str]


class RelatedPOIResponse(BaseModel):
    """关联POI响应"""
    poi_id: str
    name: str
    relation_type: str
    reason: str
    distance: Optional[float] = None


class MatchAnalysisResponse(BaseModel):
    """用户匹配分析响应"""
    overall_match: float
    reasons: List[str]
    strengths: List[str]
    considerations: List[str]


class DeepAnalysisResponse(BaseModel):
    """深度分析响应"""
    reasons: List[ReasonResponse]
    highlights: CoreHighlightsResponse
    strategy: VisitStrategyResponse
    related: List[RelatedPOIResponse]
    match_analysis: MatchAnalysisResponse
    overall_score: float


class CandidateOptionResponse(BaseModel):
    """候选选项响应"""
    index: int
    node: LocationResponse
    verification: VerificationResponse
    quality_score: QualityScoreResponse
    deep_analysis: DeepAnalysisResponse
    edge_score: float
    total_score: float
    rank: int


class SessionStateResponse(BaseModel):
    """会话状态响应"""
    current_location: LocationResponse
    current_time: float
    total_cost: float
    visited_count: int
    remaining_budget: Optional[float]


class InitSessionResponse(BaseModel):
    """初始化会话响应"""
    session_id: str
    message: str
    initial_state: SessionStateResponse
    timestamp: str


class GetOptionsResponse(BaseModel):
    """获取候选选项响应"""
    session_id: str
    current_state: SessionStateResponse
    options: List[CandidateOptionResponse]
    total_options: int
    timestamp: str


class SelectOptionResponse(BaseModel):
    """选择选项响应"""
    session_id: str
    selected_option: CandidateOptionResponse
    new_state: SessionStateResponse
    message: str
    timestamp: str


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    message: str
    timestamp: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    timestamp: str
