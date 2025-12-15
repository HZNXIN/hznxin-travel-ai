"""
时空阻尼系数 (Spatio-Temporal Damping Factor)
作为局部影响因子引入算法，精准反映城市运行规律
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ZoneType(Enum):
    """城市功能区类型"""
    INDUSTRIAL = "工业区"
    CBD = "商务区"
    RESIDENTIAL = "居住区"
    COMMERCIAL = "商业区"
    SCENIC = "景区"
    TRANSPORTATION = "交通枢纽"
    UNKNOWN = "未知"


class TrafficFlow(Enum):
    """交通潮汐方向"""
    WITH_FLOW = "顺流"  # 跟着早晚高峰方向走
    AGAINST_FLOW = "逆流"  # 逆着早晚高峰方向走
    NEUTRAL = "中性"  # 非高峰或无明显方向


@dataclass
class ZoneFactor:
    """区域因子"""
    zone_type: ZoneType
    score_modifier: float  # 评分调整系数
    cost_multiplier: float  # 通行成本倍数
    reasons: list
    warnings: list = None


@dataclass
class FlowFactor:
    """潮汐因子"""
    flow_type: TrafficFlow
    cost_multiplier: float  # 通行成本倍数
    mood_modifier: float  # 心情值调整
    reasons: list


@dataclass
class ActivityFactor:
    """活力因子（基于LBS热力图）"""
    activity_level: str  # 'ghost', 'low', 'medium', 'high', 'overload'
    score_modifier: float
    crowd_warning: bool
    reasons: list


@dataclass
class DampingResult:
    """时空阻尼结果"""
    zone_factor: float  # L_zone
    flow_factor: float  # L_flow
    activity_factor: float  # L_activity
    final_modifier: float  # 最终修正系数
    edge_color: str  # 边颜色（red/yellow/green）
    reasons: list
    warnings: list


class SpatioTemporalDamping:
    """
    时空阻尼系数计算器
    
    核心理念：
    城市不是平权的，不同区域在不同时间段的通过代价和游玩价值完全不同
    
    公式：Score_final = Score_base × L_zone × L_flow × L_activity
    """
    
    def __init__(self):
        """初始化"""
        # CBD区域定义（示例，实际应从高德AOI数据获取）
        self.cbd_areas = {
            '苏州': ['工业园区', '金鸡湖', '圆融广场'],
            '上海': ['陆家嘴', '人民广场', '南京西路'],
            '北京': ['国贸', '金融街', '中关村']
        }
        
        # 工业区关键词
        self.industrial_keywords = ['工业园', '开发区', '物流园', '厂区']
        
        # 商业区关键词
        self.commercial_keywords = ['商场', '步行街', '商业街', '购物中心']
    
    def calculate_damping(self,
                         from_zone: str,
                         to_zone: str,
                         current_hour: float,
                         activity_data: Optional[Dict] = None) -> DampingResult:
        """
        计算时空阻尼系数
        
        Args:
            from_zone: 起点区域
            to_zone: 目标区域
            current_hour: 当前小时（0-24）
            activity_data: LBS活跃度数据（可选）
            
        Returns:
            阻尼结果
        """
        # 1. 计算区域因子 L_zone
        zone_factor_result = self._calculate_zone_factor(to_zone, current_hour)
        
        # 2. 计算潮汐因子 L_flow
        flow_factor_result = self._calculate_flow_factor(
            from_zone, to_zone, current_hour
        )
        
        # 3. 计算活力因子 L_activity
        activity_factor_result = self._calculate_activity_factor(
            to_zone, activity_data
        )
        
        # 4. 综合计算
        final_modifier = (
            zone_factor_result.score_modifier *
            flow_factor_result.cost_multiplier *
            activity_factor_result.score_modifier
        )
        
        # 5. 确定边颜色
        edge_color = self._determine_edge_color(final_modifier)
        
        # 6. 汇总原因和警告
        reasons = []
        reasons.extend(zone_factor_result.reasons)
        reasons.extend(flow_factor_result.reasons)
        reasons.extend(activity_factor_result.reasons)
        
        warnings = []
        if zone_factor_result.warnings:
            warnings.extend(zone_factor_result.warnings)
        if activity_factor_result.crowd_warning:
            warnings.append("目标区域人流密集，请注意")
        
        return DampingResult(
            zone_factor=zone_factor_result.score_modifier,
            flow_factor=flow_factor_result.cost_multiplier,
            activity_factor=activity_factor_result.score_modifier,
            final_modifier=final_modifier,
            edge_color=edge_color,
            reasons=reasons,
            warnings=warnings
        )
    
    def _calculate_zone_factor(self, zone: str, hour: float) -> ZoneFactor:
        """计算区域因子"""
        zone_type = self._identify_zone_type(zone)
        
        # 工业区逻辑
        if zone_type == ZoneType.INDUSTRIAL:
            if 18.0 <= hour <= 24.0 or 0.0 <= hour <= 7.0:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=0.4,
                    cost_multiplier=1.5,
                    reasons=[f"{zone}为工业区，夜间交通不便"],
                    warnings=["工业区夜间打车困难，建议避开"]
                )
            else:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=0.7,
                    cost_multiplier=1.5,
                    reasons=[f"{zone}为工业区，大货车多"],
                    warnings=["工业区路况复杂"]
                )
        
        # CBD逻辑（拥堵熔断）
        elif zone_type == ZoneType.CBD:
            if 17.0 <= hour <= 19.0:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=0.3,
                    cost_multiplier=2.5,
                    reasons=[f"{zone}为CBD，晚高峰严重拥堵"],
                    warnings=["晚高峰拥堵熔断，强烈建议避开"]
                )
            elif 7.5 <= hour <= 9.5:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=0.4,
                    cost_multiplier=2.0,
                    reasons=[f"{zone}为CBD，早高峰拥堵"],
                    warnings=["早高峰拥堵，建议避开"]
                )
            elif 10.0 <= hour <= 16.0:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=1.0,
                    cost_multiplier=1.0,
                    reasons=[f"{zone}为CBD，工作时段交通便利"]
                )
            else:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=0.9,
                    cost_multiplier=1.1,
                    reasons=[f"{zone}为CBD"]
                )
        
        # 商业区逻辑
        elif zone_type == ZoneType.COMMERCIAL:
            if 18.0 <= hour <= 22.0:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=1.2,
                    cost_multiplier=1.0,
                    reasons=[f"{zone}为商业区，夜间热闹氛围好"]
                )
            else:
                return ZoneFactor(
                    zone_type=zone_type,
                    score_modifier=1.0,
                    cost_multiplier=1.0,
                    reasons=[f"{zone}为商业区"]
                )
        
        # 默认
        else:
            return ZoneFactor(
                zone_type=zone_type,
                score_modifier=1.0,
                cost_multiplier=1.0,
                reasons=[]
            )
    
    def _calculate_flow_factor(self, from_zone: str, to_zone: str, hour: float) -> FlowFactor:
        """计算潮汐因子"""
        from_type = self._identify_zone_type(from_zone)
        to_type = self._identify_zone_type(to_zone)
        
        # 早高峰 (07:30 - 09:30)
        if 7.5 <= hour <= 9.5:
            if from_type == ZoneType.RESIDENTIAL and to_type == ZoneType.CBD:
                return FlowFactor(
                    flow_type=TrafficFlow.WITH_FLOW,
                    cost_multiplier=2.0,
                    mood_modifier=-0.3,
                    reasons=["早高峰顺流前往CBD，严重拥堵"]
                )
            elif from_type == ZoneType.CBD and to_type == ZoneType.RESIDENTIAL:
                return FlowFactor(
                    flow_type=TrafficFlow.AGAINST_FLOW,
                    cost_multiplier=0.8,
                    mood_modifier=0.2,
                    reasons=["早高峰逆流出CBD，道路畅通"]
                )
        
        # 晚高峰 (17:00 - 19:30)
        elif 17.0 <= hour <= 19.5:
            if from_type == ZoneType.CBD and to_type == ZoneType.RESIDENTIAL:
                return FlowFactor(
                    flow_type=TrafficFlow.WITH_FLOW,
                    cost_multiplier=2.0,
                    mood_modifier=-0.3,
                    reasons=["晚高峰顺流出CBD，严重拥堵"]
                )
            elif from_type == ZoneType.RESIDENTIAL and to_type == ZoneType.CBD:
                return FlowFactor(
                    flow_type=TrafficFlow.AGAINST_FLOW,
                    cost_multiplier=0.8,
                    mood_modifier=0.2,
                    reasons=["晚高峰逆流进CBD，道路畅通（看夜景好时机）"]
                )
        
        # 非高峰时段
        return FlowFactor(
            flow_type=TrafficFlow.NEUTRAL,
            cost_multiplier=1.0,
            mood_modifier=0.0,
            reasons=[]
        )
    
    def _calculate_activity_factor(self, zone: str, activity_data: Optional[Dict]) -> ActivityFactor:
        """计算活力因子（基于LBS热力图）"""
        if not activity_data:
            return ActivityFactor(
                activity_level='medium',
                score_modifier=1.0,
                crowd_warning=False,
                reasons=[]
            )
        
        active_devices = activity_data.get('active_devices', 100)
        
        # 鬼城预警
        if active_devices < 10:
            return ActivityFactor(
                activity_level='ghost',
                score_modifier=0.1,
                crowd_warning=False,
                reasons=["LBS数据显示区域活跃度异常低，可能闭馆或装修"]
            )
        
        # 低活跃
        elif active_devices < 50:
            return ActivityFactor(
                activity_level='low',
                score_modifier=0.7,
                crowd_warning=False,
                reasons=["区域人气偏低"]
            )
        
        # 适中
        elif active_devices < 200:
            return ActivityFactor(
                activity_level='medium',
                score_modifier=1.0,
                crowd_warning=False,
                reasons=[]
            )
        
        # 高活跃
        elif active_devices < 500:
            return ActivityFactor(
                activity_level='high',
                score_modifier=1.1,
                crowd_warning=False,
                reasons=["检测到区域人气旺盛"]
            )
        
        # 过载（人挤人）
        else:
            return ActivityFactor(
                activity_level='overload',
                score_modifier=0.6,
                crowd_warning=True,
                reasons=["LBS显示人流密集，可能人挤人"]
            )
    
    def _identify_zone_type(self, zone: str) -> ZoneType:
        """识别区域类型"""
        # 工业区
        for keyword in self.industrial_keywords:
            if keyword in zone:
                return ZoneType.INDUSTRIAL
        
        # 商业区
        for keyword in self.commercial_keywords:
            if keyword in zone:
                return ZoneType.COMMERCIAL
        
        # CBD
        for city, areas in self.cbd_areas.items():
            for area in areas:
                if area in zone:
                    return ZoneType.CBD
        
        # 默认
        return ZoneType.UNKNOWN
    
    def _determine_edge_color(self, modifier: float) -> str:
        """根据修正系数确定边颜色"""
        if modifier >= 1.0:
            return "green"
        elif modifier >= 0.6:
            return "yellow"
        else:
            return "red"
    
    def generate_opportunity_card(self, zone: str, activity_spike: float) -> Optional[Dict]:
        """
        生成机会卡片（发现隐形热点）
        
        Args:
            zone: 区域名称
            activity_spike: 活跃度激增倍数
            
        Returns:
            机会卡片数据
        """
        if activity_spike > 3.0:
            return {
                'type': 'opportunity',
                'title': '发现隐藏热点',
                'message': f"检测到{zone}附近人群聚集激增{activity_spike:.1f}倍",
                'suggestions': [
                    "可能是临时夜市",
                    "可能有明星活动",
                    "可能有灯会表演"
                ],
                'recommendation': f"建议前往{zone}探索"
            }
        return None
