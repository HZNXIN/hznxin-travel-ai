"""
POI深度分析器
不是简单展示拓扑关系，而是深度分析每个推荐
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


# ==================== 数据结构定义 ====================

class ReasonType(Enum):
    """推荐理由类型"""
    CORE_VALUE = "核心价值"      # 景点本身的价值
    USER_MATCH = "用户匹配"      # 与用户偏好的匹配
    SPATIAL_CONVENIENCE = "空间便利"  # 地理位置便利性
    TIME_ADAPTATION = "时间适配"  # 时间安排适配性
    REPUTATION = "口碑验证"      # 评论评分验证


@dataclass
class Reason:
    """推荐理由"""
    type: ReasonType
    content: str
    weight: float  # 权重 [0, 1]
    evidence: Optional[str] = None  # 证据/数据支撑


@dataclass
class MustSeeSpot:
    """必看景观"""
    name: str
    description: str
    importance: int  # 1-5星
    best_time: Optional[str] = None
    photo_tip: Optional[str] = None


@dataclass
class CoreHighlights:
    """核心亮点"""
    architecture: List[str] = field(default_factory=list)  # 建筑艺术
    layout: Dict[str, str] = field(default_factory=dict)   # 布局特色
    history: List[str] = field(default_factory=list)       # 历史文化
    must_see: List[MustSeeSpot] = field(default_factory=list)  # 必看景观
    unique_features: List[str] = field(default_factory=list)  # 独特之处


@dataclass
class PhotoSpot:
    """拍照机位"""
    location: str
    subject: str
    best_time: str
    tips: Optional[str] = None


@dataclass
class VisitStrategy:
    """游玩攻略"""
    best_time: str  # 最佳游览时间
    duration: str   # 建议游玩时长
    route: List[str]  # 推荐路线
    photo_spots: List[PhotoSpot]  # 拍照攻略
    tips: List[str]  # 注意事项


@dataclass
class RelatedPOI:
    """关联POI"""
    poi_id: str
    name: str
    relation_type: str  # 同类型、邻近、互补
    reason: str
    distance: Optional[float] = None


@dataclass
class MatchAnalysis:
    """用户匹配分析"""
    overall_match: float  # 总体匹配度
    reasons: List[str]    # 匹配原因
    strengths: List[str]  # 优势点
    considerations: List[str]  # 需要考虑的点


@dataclass
class POIKnowledge:
    """POI知识图谱"""
    poi_id: str
    name: str
    category: str  # 园林、寺庙、博物馆等
    
    # 核心特色
    core_features: List[str]
    
    # 历史背景
    build_year: Optional[int] = None
    dynasty: Optional[str] = None
    builder: Optional[str] = None
    historical_story: Optional[str] = None
    
    # 文化价值
    cultural_level: str = "一般"  # 顶级、高、中、一般
    heritage_status: Optional[str] = None  # 世界遗产、国家级等
    
    # 核心亮点
    highlights: Optional[CoreHighlights] = None
    
    # 游玩建议
    strategy: Optional[VisitStrategy] = None
    
    # 关联景点
    related: List[RelatedPOI] = field(default_factory=list)


@dataclass
class DeepRecommendation:
    """深度推荐结构"""
    poi_id: str
    poi_name: str
    
    # 1. 为什么推荐
    reasons: List[Reason]
    
    # 2. 核心亮点
    highlights: CoreHighlights
    
    # 3. 游玩攻略
    strategy: VisitStrategy
    
    # 4. 关联推荐
    related: List[RelatedPOI]
    
    # 5. 用户匹配分析
    match_analysis: MatchAnalysis
    
    # 综合评分
    overall_score: float


# ==================== 核心分析器 ====================

class POIDeepAnalyzer:
    """
    POI深度分析器
    
    核心功能：
    1. 生成推荐理由（为什么推荐）
    2. 提炼核心亮点（有什么看点）
    3. 生成游玩攻略（怎么玩最好）
    4. 推荐关联POI（还能去哪）
    5. 分析用户匹配（为什么适合你）
    """
    
    def __init__(self, knowledge_base: Dict[str, POIKnowledge] = None, weather_service=None):
        """
        初始化分析器
        
        Args:
            knowledge_base: POI知识库
            weather_service: 天气服务（可选）
        """
        self.knowledge_base = knowledge_base or self._init_knowledge_base()
        self.weather_service = weather_service
    
    def analyze(self,
                poi,
                verification,
                quality_score,
                user_profile,
                context) -> DeepRecommendation:
        """
        深度分析POI，生成完整推荐
        
        Args:
            poi: POI位置信息
            verification: 验证数据
            quality_score: 质量评分
            user_profile: 用户画像
            context: 规划上下文
            
        Returns:
            深度推荐结构
        """
        # 获取知识
        knowledge = self.knowledge_base.get(poi.name, self._generate_default_knowledge(poi))
        
        # 1. 生成推荐理由
        reasons = self._generate_reasons(poi, verification, quality_score, user_profile, context, knowledge)
        
        # 2. 提炼核心亮点
        highlights = self._extract_highlights(poi, knowledge, verification)
        
        # 3. 生成游玩攻略
        strategy = self._generate_strategy(poi, knowledge, context)
        
        # 4. 推荐关联POI
        related = self._recommend_related(poi, knowledge, context)
        
        # 5. 分析用户匹配
        match_analysis = self._analyze_match(poi, user_profile, knowledge, quality_score)
        
        # 综合评分
        overall_score = self._calculate_overall_score(
            reasons, quality_score, match_analysis
        )
        
        return DeepRecommendation(
            poi_id=poi.id,
            poi_name=poi.name,
            reasons=reasons,
            highlights=highlights,
            strategy=strategy,
            related=related,
            match_analysis=match_analysis,
            overall_score=overall_score
        )
    
    def _generate_reasons(self, poi, verification, quality_score, 
                         user_profile, context, knowledge) -> List[Reason]:
        """生成多维度推荐理由"""
        reasons = []
        
        # 理由1: 核心价值（如果是重要景点）
        if knowledge.cultural_level in ["顶级", "高"]:
            reason = Reason(
                type=ReasonType.CORE_VALUE,
                content=knowledge.core_features[0] if knowledge.core_features else "重要景点",
                weight=0.30,
                evidence=knowledge.heritage_status
            )
            reasons.append(reason)
        
        # 理由2: 用户匹配（如果匹配度高）
        match_score = quality_score.overall if quality_score else 0.5  # ✅ 处理None
        if match_score > 0.7:
            match_desc = self._describe_user_match(poi, user_profile)
            reason = Reason(
                type=ReasonType.USER_MATCH,
                content=f"符合你的'{match_desc}'偏好（{match_score:.0%}匹配）",
                weight=0.25,
                evidence=f"匹配度{match_score:.0%}"
            )
            reasons.append(reason)
        
        # 理由3: 空间便利（距离、交通）
        distance_km = context.get('distance_km', 0)
        travel_time_hours = context.get('travel_time', 0)  # 原始单位是小时
        
        # 转换为分钟并估算（如果没有真实数据）
        if travel_time_hours > 0:
            travel_time_min = travel_time_hours * 60
        elif distance_km > 0:
            # 根据距离估算时间
            if distance_km < 1.0:
                travel_time_min = distance_km / 5 * 60  # 步行速度5km/h
            elif distance_km < 3.0:
                travel_time_min = distance_km / 4 * 60  # 骑行/短距离打车
            else:
                travel_time_min = distance_km / 30 * 60 + 5  # 打车速度30km/h + 5分钟等待
        else:
            travel_time_min = 0
        
        # 确保至少显示1分钟
        if travel_time_min > 0 and travel_time_min < 1:
            travel_time_min = 1
        
        reason = Reason(
            type=ReasonType.SPATIAL_CONVENIENCE,
            content=f"距离{distance_km:.1f}km，{self._get_transport_desc(distance_km)}约{int(travel_time_min)}分钟",
            weight=0.20,
            evidence=f"距离{distance_km:.1f}km"
        )
        reasons.append(reason)
        
        # 理由4: 时间适配（游玩时长）
        visit_time = poi.average_visit_time
        reason = Reason(
            type=ReasonType.TIME_ADAPTATION,
            content=f"建议游玩{visit_time:.1f}小时，与你的行程匹配",
            weight=0.15,
            evidence=f"游玩时长{visit_time:.1f}h"
        )
        reasons.append(reason)
        
        # 理由5: 口碑验证（评论、评分）
        reviews = verification.valid_reviews
        rating = verification.weighted_rating
        reason = Reason(
            type=ReasonType.REPUTATION,
            content=f"{reviews:,}条评论，评分{rating:.1f}/5.0，口碑极佳",
            weight=0.10,
            evidence=f"{reviews}条评论，{rating:.1f}分"
        )
        reasons.append(reason)
        
        # 理由6: 天气影响（如果有天气服务）
        if self.weather_service and context.get('city'):
            weather = self.weather_service.get_weather(context.get('city'))
            if weather:
                weather_impact = self.weather_service.analyze_weather_impact(
                    poi.type.value, weather
                )
                if weather_impact.reasons:
                    reason = Reason(
                        type=ReasonType.TIME_ADAPTATION,  # 复用TIME_ADAPTATION类型
                        content=weather_impact.reasons[0],
                        weight=0.15,
                        evidence=f"天气: {weather.weather}, {weather.temperature}"
                    )
                    reasons.append(reason)
        
        # 按权重排序
        return sorted(reasons, key=lambda r: r.weight, reverse=True)
    
    def _extract_highlights(self, poi, knowledge, verification) -> CoreHighlights:
        """提炼核心亮点"""
        if knowledge.highlights:
            return knowledge.highlights
        
        # 默认亮点（基于POI类型）
        highlights = CoreHighlights()
        
        if poi.type.value == 'attraction':
            highlights.architecture = ["建筑风格独特", "设计精巧"]
            highlights.history = ["历史悠久", "文化底蕴深厚"]
            highlights.unique_features = ["值得一游"]
        
        return highlights
    
    def _generate_strategy(self, poi, knowledge, context) -> VisitStrategy:
        """生成游玩攻略"""
        if knowledge.strategy:
            return knowledge.strategy
        
        # 默认攻略
        return VisitStrategy(
            best_time="上午9-11点（人流较少，光线好）",
            duration=f"{poi.average_visit_time:.1f}小时",
            route=["入口", "主要景观", "出口"],
            photo_spots=[
                PhotoSpot("主要景观处", "标志性建筑", "上午或傍晚", "注意光线角度")
            ],
            tips=[
                "建议提前了解景点历史",
                "注意保护文物",
                "遵守景区规定"
            ]
        )
    
    def _recommend_related(self, poi, knowledge, context) -> List[RelatedPOI]:
        """推荐关联POI"""
        if knowledge.related:
            return knowledge.related
        
        # TODO: 基于距离和类型推荐邻近POI
        return []
    
    def _analyze_match(self, poi, user_profile, knowledge, quality_score) -> MatchAnalysis:
        """分析用户匹配度"""
        match_reasons = []
        strengths = []
        considerations = []
        
        # 分析匹配原因
        if knowledge.cultural_level in ["顶级", "高"]:
            match_reasons.append("文化历史价值顶级")
            strengths.append("深度文化体验")
        
        playability = quality_score.playability if quality_score and hasattr(quality_score, 'playability') else 0.5
        if playability > 0.6:
            match_reasons.append("可玩性强")
            strengths.append("游玩体验丰富")
        
        if poi.average_visit_time < 3.0:
            match_reasons.append("游玩时长适中")
            strengths.append("不会过于疲劳")
        
        # 需要考虑的点
        if poi.ticket_price > 100:
            considerations.append("门票较贵，建议提前购买")
        
        # ✅ 处理None
        overall_match = quality_score.overall if quality_score and hasattr(quality_score, 'overall') else 0.5
        
        return MatchAnalysis(
            overall_match=overall_match,
            reasons=match_reasons,
            strengths=strengths,
            considerations=considerations
        )
    
    def _calculate_overall_score(self, reasons, quality_score, match_analysis) -> float:
        """计算综合评分"""
        # 基于多个因素的加权平均
        reason_score = sum(r.weight for r in reasons[:3]) / 3.0 if reasons else 0.5  # 前3个理由
        # ✅ 处理None
        quality = quality_score.overall if quality_score and hasattr(quality_score, 'overall') else 0.5
        match = match_analysis.overall_match
        
        return (reason_score * 0.3 + quality * 0.4 + match * 0.3)
    
    def _describe_user_match(self, poi, user_profile) -> str:
        """描述用户匹配点"""
        # 简化：基于POI类型匹配用户偏好
        if poi.type.value == 'attraction':
            return "历史文化、观光游览"
        elif poi.type.value == 'restaurant':
            return "美食体验"
        else:
            return "休闲娱乐"
    
    def _get_transport_desc(self, distance_km) -> str:
        """获取交通方式描述"""
        if distance_km < 1.0:
            return "步行"
        elif distance_km < 5.0:
            return "打车"
        elif distance_km < 20.0:
            return "地铁或打车"
        else:
            return "公共交通"
    
    def _generate_default_knowledge(self, poi) -> POIKnowledge:
        """生成默认知识（当知识库中没有时）"""
        return POIKnowledge(
            poi_id=poi.id,
            name=poi.name,
            category=poi.type.value,
            core_features=["值得一游"],
            cultural_level="一般"
        )
    
    def _init_knowledge_base(self) -> Dict[str, POIKnowledge]:
        """初始化知识库（核心景点）"""
        return {
            "拙政园": POIKnowledge(
                poi_id="suzhou_zzy",
                name="拙政园",
                category="江南园林",
                core_features=[
                    "江南园林艺术巅峰之作",
                    "中国四大名园之首",
                    "世界文化遗产"
                ],
                build_year=1509,
                dynasty="明",
                builder="王献臣",
                cultural_level="顶级",
                heritage_status="世界文化遗产（1997年）",
                highlights=CoreHighlights(
                    architecture=[
                        "亭台楼阁布局精巧，移步换景",
                        "借景手法运用极致",
                        "粉墙黛瓦，典型江南风格"
                    ],
                    layout={
                        "东园": "开阔水面为主，远香堂为核心",
                        "中园": "精致山水，曲径通幽",
                        "西园": "层次丰富，见山楼制高点"
                    },
                    history=[
                        "明代正德年间建造（1509年）",
                        "王献臣私园，文徵明参与设计",
                        "世界文化遗产（1997年列入）",
                        "面积5.2公顷，苏州园林之最"
                    ],
                    must_see=[
                        MustSeeSpot("远香堂", "中园主厅，观荷花池", 5, "上午10点", "拍倒影"),
                        MustSeeSpot("见山楼", "西园制高点，俯瞰全园", 5, "晴天", "全景"),
                        MustSeeSpot("小飞虹", "拱形廊桥，经典构图", 4, "任意", "侧面拍"),
                        MustSeeSpot("荷花池", "夏季荷花，冬季残荷", 5, "6-8月", "特写")
                    ],
                    unique_features=[
                        "中国园林建筑的经典范例",
                        "\"虽由人作，宛自天开\"的极致体现"
                    ]
                ),
                strategy=VisitStrategy(
                    best_time="上午9-11点（光线好，人流少）",
                    duration="2-3小时",
                    route=[
                        "入口",
                        "远香堂（20分钟）",
                        "荷花池（15分钟）",
                        "小飞虹（10分钟）",
                        "见山楼（20分钟）",
                        "西园游览（30分钟）",
                        "出口"
                    ],
                    photo_spots=[
                        PhotoSpot("荷花池北侧", "拍远香堂倒影", "上午10点", "使用广角镜头"),
                        PhotoSpot("小飞虹", "拱桥+水景", "任意时间", "侧面45度角"),
                        PhotoSpot("见山楼", "俯拍全园", "晴天", "注意曝光")
                    ],
                    tips=[
                        "周末和节假日人多，建议工作日前往",
                        "夏季荷花盛开（6-8月），冬季可赏残荷雅致",
                        "门票70元，学生半价，提前网购有优惠",
                        "园内禁止使用三脚架和自拍杆",
                        "建议租赁讲解器或请导游，更能体会园林艺术"
                    ]
                ),
                related=[
                    RelatedPOI("suzhou_ly", "留园", "同类型", "与拙政园齐名的江南四大名园之一", 3.5),
                    RelatedPOI("suzhou_museum", "苏州博物馆", "邻近", "贝聿铭设计，步行200米", 0.2),
                    RelatedPOI("suzhou_pjl", "平江路", "邻近", "历史文化街区，步行300米", 0.3)
                ]
            ),
            
            "苏州博物馆": POIKnowledge(
                poi_id="suzhou_museum",
                name="苏州博物馆",
                category="博物馆",
                core_features=[
                    "贝聿铭封笔之作",
                    "现代建筑与传统园林完美融合",
                    "馆藏文物丰富"
                ],
                build_year=2006,
                cultural_level="顶级",
                heritage_status="国家一级博物馆",
                highlights=CoreHighlights(
                    architecture=[
                        "贝聿铭设计，现代主义风格",
                        "粉墙黛瓦，现代诠释江南建筑",
                        "几何造型，光影运用极致"
                    ],
                    layout={
                        "中央大厅": "天光洒落，空间通透",
                        "展览区": "按时代分布，系统展示",
                        "庭院": "山水园林，片石假山"
                    },
                    history=[
                        "2006年开馆，贝聿铭最后作品",
                        "馆藏1.5万件文物",
                        "免费开放，需预约"
                    ],
                    must_see=[
                        MustSeeSpot("片石假山", "贝聿铭设计的现代山水", 5),
                        MustSeeSpot("真珠舍利宝幢", "镇馆之宝", 5),
                        MustSeeSpot("中央大厅", "建筑艺术典范", 4)
                    ]
                ),
                strategy=VisitStrategy(
                    best_time="上午10点开馆后（需提前预约）",
                    duration="1.5-2小时",
                    route=["入口", "中央大厅", "展览区", "庭院", "出口"],
                    photo_spots=[
                        PhotoSpot("中央大厅", "光影效果", "上午", "仰拍天窗"),
                        PhotoSpot("片石假山", "现代山水", "侧光", "黑白效果好")
                    ],
                    tips=[
                        "免费但需提前预约（微信公众号）",
                        "周一闭馆",
                        "禁止使用闪光灯",
                        "建议游览1.5-2小时"
                    ]
                ),
                related=[
                    RelatedPOI("suzhou_zzy", "拙政园", "邻近", "步行200米", 0.2),
                    RelatedPOI("suzhou_pjl", "平江路", "邻近", "步行500米", 0.5)
                ]
            )
        }


def format_deep_recommendation(rec: DeepRecommendation) -> str:
    """格式化深度推荐为可读文本"""
    lines = []
    
    lines.append("=" * 70)
    lines.append(f"📍 推荐景点: {rec.poi_name}")
    lines.append("=" * 70)
    lines.append(f"\n⭐ 综合评分: {rec.overall_score:.1f}/10\n")
    
    # 1. 推荐理由
    lines.append("━" * 70)
    lines.append("💡 为什么推荐这里？")
    lines.append("━" * 70)
    for i, reason in enumerate(rec.reasons, 1):
        lines.append(f"\n{i}. {reason.type.value}")
        lines.append(f"   {reason.content}")
    
    # 2. 核心亮点
    lines.append("\n" + "━" * 70)
    lines.append("✨ 这里有什么？（核心亮点）")
    lines.append("━" * 70)
    
    if rec.highlights.architecture:
        lines.append("\n🏗️ 建筑艺术")
        for item in rec.highlights.architecture:
            lines.append(f"   • {item}")
    
    if rec.highlights.history:
        lines.append("\n📜 历史文化")
        for item in rec.highlights.history:
            lines.append(f"   • {item}")
    
    if rec.highlights.must_see:
        lines.append("\n👁️ 必看景观")
        for spot in rec.highlights.must_see:
            stars = "⭐" * spot.importance
            lines.append(f"   {stars} {spot.name} - {spot.description}")
    
    # 3. 游玩攻略
    lines.append("\n" + "━" * 70)
    lines.append("🎮 怎么玩最好？（游玩攻略）")
    lines.append("━" * 70)
    
    lines.append(f"\n⏰ 最佳时间: {rec.strategy.best_time}")
    lines.append(f"⏱️ 建议时长: {rec.strategy.duration}")
    
    if rec.strategy.route:
        lines.append("\n🚶 推荐路线:")
        lines.append("   " + " → ".join(rec.strategy.route))
    
    if rec.strategy.tips:
        lines.append("\n⚠️ 注意事项:")
        for tip in rec.strategy.tips:
            lines.append(f"   • {tip}")
    
    # 4. 用户匹配
    lines.append("\n" + "━" * 70)
    lines.append("🎯 为什么特别适合你？")
    lines.append("━" * 70)
    
    for strength in rec.match_analysis.strengths:
        lines.append(f"   ✓ {strength}")
    
    lines.append("\n" + "=" * 70)
    
    return "\n".join(lines)
