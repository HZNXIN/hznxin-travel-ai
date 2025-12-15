"""
API路由
定义所有API端点
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from typing import List

from .models import *
from .session_manager import SessionManager
from ..core.models import Location, POIType
from ..core.progressive_planner import ProgressivePlanner
from ..core.verification_engine import VerificationEngine
from ..core.scoring_engine import ScoringEngine
from ..core.poi_quality_filter import POIQualityFilter
from ..core.poi_deep_analyzer import POIDeepAnalyzer
from ..data_services.gaode_api_client import GaodeAPIClient
from ..data_services.multi_source_collector import MultiSourceCollector
from ..data_services.poi_database import POIDatabase
from config import GAODE_API_KEY


# 创建路由器
router = APIRouter()

# 全局实例（实际应用中应该使用依赖注入）
gaode_client = GaodeAPIClient(GAODE_API_KEY)
poi_db = POIDatabase()

# 初始化POI数据（如果数据库为空）
if len(poi_db.pois) == 0:
    print("📍 POI数据库为空，正在初始化Demo数据...")
    poi_db.initialize_demo_data()
    print(f"✅ 已加载 {len(poi_db.pois)} 个POI")

collector = MultiSourceCollector(gaode_client)
verification_engine = VerificationEngine(collector, None, gaode_client)  # neural_net_service=None
scoring_engine = ScoringEngine()
quality_filter = POIQualityFilter()
deep_analyzer = POIDeepAnalyzer()
planner = ProgressivePlanner(
    poi_db=poi_db,
    verification_engine=verification_engine,
    scoring_engine=scoring_engine,
    quality_filter=quality_filter,
    deep_analyzer=deep_analyzer
)
session_manager = SessionManager(planner)


def convert_to_location_response(loc: Location) -> LocationResponse:
    """转换Location到LocationResponse"""
    return LocationResponse(
        id=loc.id,
        name=loc.name,
        lat=loc.lat,
        lon=loc.lon,
        type=loc.type.value,
        address=loc.address,
        average_visit_time=loc.average_visit_time,
        ticket_price=loc.ticket_price
    )


def convert_to_verification_response(verification) -> VerificationResponse:
    """转换NodeVerification到VerificationResponse"""
    return VerificationResponse(
        consistency_score=verification.consistency_score,
        weighted_rating=verification.weighted_rating,
        total_reviews=verification.total_reviews,
        valid_reviews=verification.valid_reviews,
        fake_rate=verification.fake_rate,
        positive_rate=verification.positive_rate,
        negative_rate=verification.negative_rate,
        key_positive_words=verification.key_positive_words,
        key_negative_words=verification.key_negative_words,
        spatial_score=verification.spatial_score,
        temporal_score=verification.temporal_score
    )


def convert_to_quality_score_response(quality) -> QualityScoreResponse:
    """转换POIQualityScore到QualityScoreResponse"""
    return QualityScoreResponse(
        playability=quality.playability,
        viewability=quality.viewability,
        popularity=quality.popularity,
        history=quality.history,
        overall=quality.overall
    )


def convert_to_deep_analysis_response(deep) -> DeepAnalysisResponse:
    """转换DeepRecommendation到DeepAnalysisResponse"""
    return DeepAnalysisResponse(
        reasons=[
            ReasonResponse(
                type=r.type.value,
                content=r.content,
                weight=r.weight,
                evidence=r.evidence
            ) for r in deep.reasons
        ],
        highlights=CoreHighlightsResponse(
            architecture=deep.highlights.architecture,
            layout=deep.highlights.layout,
            history=deep.highlights.history,
            must_see=[
                MustSeeSpotResponse(
                    name=spot.name,
                    description=spot.description,
                    importance=spot.importance,
                    best_time=spot.best_time,
                    photo_tip=spot.photo_tip
                ) for spot in deep.highlights.must_see
            ],
            unique_features=deep.highlights.unique_features
        ),
        strategy=VisitStrategyResponse(
            best_time=deep.strategy.best_time,
            duration=deep.strategy.duration,
            route=deep.strategy.route,
            photo_spots=[
                PhotoSpotResponse(
                    location=ps.location,
                    subject=ps.subject,
                    best_time=ps.best_time,
                    tips=ps.tips
                ) for ps in deep.strategy.photo_spots
            ],
            tips=deep.strategy.tips
        ),
        related=[
            RelatedPOIResponse(
                poi_id=rel.poi_id,
                name=rel.name,
                relation_type=rel.relation_type,
                reason=rel.reason,
                distance=rel.distance
            ) for rel in deep.related
        ],
        match_analysis=MatchAnalysisResponse(
            overall_match=deep.match_analysis.overall_match,
            reasons=deep.match_analysis.reasons,
            strengths=deep.match_analysis.strengths,
            considerations=deep.match_analysis.considerations
        ),
        overall_score=deep.overall_score
    )


def convert_to_session_state_response(state, initial_budget: float = None) -> SessionStateResponse:
    """转换State到SessionStateResponse"""
    # 计算总花费：初始预算 - 剩余预算
    total_cost = 0.0
    if initial_budget is not None:
        total_cost = initial_budget - state.remaining_budget
    
    return SessionStateResponse(
        current_location=convert_to_location_response(state.current_location),
        current_time=state.current_time,
        total_cost=total_cost,  # 计算出的总花费
        visited_count=len(state.visited_history),  # 使用 visited_history (Set)
        remaining_budget=state.remaining_budget  # 使用 remaining_budget
    )


# ==================== API端点 ====================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat()
    )


@router.post("/session/init", response_model=InitSessionResponse)
async def init_session(request: InitSessionRequest):
    """
    初始化会话
    
    创建新的旅行规划会话
    """
    try:
        # 地理编码获取起始位置
        geo_result = gaode_client.geocode(request.starting_location)
        if not geo_result:
            raise HTTPException(status_code=400, detail=f"无法识别地址: {request.starting_location}")
        
        # geocode 返回 (lon, lat) 元组
        lon, lat = geo_result
        
        # 创建起始位置对象
        starting_location = Location(
            id=f"start_{request.user_id}",
            name=request.starting_location,  # 使用用户输入的地址作为名称
            lat=lat,
            lon=lon,
            type=POIType.STATION,  # 起点标记为交通站
            address=request.starting_location,
            average_visit_time=0.0,
            ticket_price=0.0
        )
        
        # 创建会话
        session = session_manager.create_session(
            user_id=request.user_id,
            starting_location=starting_location,
            purpose=request.purpose,
            pace=request.pace,
            intensity=request.intensity,
            time_budget=request.time_budget,
            money_budget=request.money_budget
        )
        
        return InitSessionResponse(
            session_id=session.session_id,
            message=f"会话创建成功！起始位置: {starting_location.name}",
            initial_state=convert_to_session_state_response(session.initial_state, session.budget),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@router.get("/session/{session_id}/options", response_model=GetOptionsResponse)
async def get_options(session_id: str, top_k: int = 5):
    """
    获取候选选项
    
    基于当前状态，返回推荐的下一步候选POI
    """
    try:
        # 获取会话
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
        
        # 获取候选选项
        options = planner.get_next_options(session, k=top_k)
        
        # 转换为响应格式
        option_responses = []
        for i, option in enumerate(options):
            option_responses.append(CandidateOptionResponse(
                index=i,
                node=convert_to_location_response(option.node),
                verification=convert_to_verification_response(option.verification),
                quality_score=convert_to_quality_score_response(option.quality_score),
                deep_analysis=convert_to_deep_analysis_response(option.deep_analysis),
                edge_score=option.edge_score,
                total_score=option.total_score,
                rank=i + 1
            ))
        
        return GetOptionsResponse(
            session_id=session_id,
            current_state=convert_to_session_state_response(session.current_state, session.budget),
            options=option_responses,
            total_options=len(option_responses),
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取选项失败: {str(e)}")


@router.post("/session/{session_id}/select", response_model=SelectOptionResponse)
async def select_option(session_id: str, request: SelectOptionRequest):
    """
    选择选项
    
    用户选择一个候选选项，系统更新会话状态
    """
    try:
        # 获取会话
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在或已过期")
        
        # 获取候选选项
        options = planner.get_next_options(session)
        
        # 检查索引
        if request.option_index < 0 or request.option_index >= len(options):
            raise HTTPException(status_code=400, detail=f"无效的选项索引: {request.option_index}")
        
        # 获取选择的选项
        selected_option = options[request.option_index]
        
        # 更新会话状态
        new_state = planner.select_option(session, selected_option)
        
        # 更新会话
        session_manager.update_session(session)
        
        return SelectOptionResponse(
            session_id=session_id,
            selected_option=CandidateOptionResponse(
                index=request.option_index,
                node=convert_to_location_response(selected_option.node),
                verification=convert_to_verification_response(selected_option.verification),
                quality_score=convert_to_quality_score_response(selected_option.quality_score),
                deep_analysis=convert_to_deep_analysis_response(selected_option.deep_analysis),
                edge_score=selected_option.edge_score,
                total_score=selected_option.total_score,
                rank=request.option_index + 1
            ),
            new_state=convert_to_session_state_response(new_state, session.budget),
            message=f"已选择: {selected_option.node.name}",
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"选择选项失败: {str(e)}")


@router.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """获取会话信息"""
    info = session_manager.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")
    return info


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    session_manager.delete_session(session_id)
    return {"message": "会话已删除", "session_id": session_id}


@router.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    return {
        "active_sessions": session_manager.get_active_session_count(),
        "poi_count": poi_db.get_poi_count(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/cleanup")
async def cleanup_sessions(background_tasks: BackgroundTasks):
    """清理过期会话（后台任务）"""
    background_tasks.add_task(session_manager.cleanup_expired_sessions)
    return {"message": "清理任务已启动"}
