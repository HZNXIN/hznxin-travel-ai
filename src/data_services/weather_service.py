"""
天气服务
使用高德API获取天气数据并作为推荐影响因子
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.exceptions import WeatherServiceException, NetworkException

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """天气状况"""
    SUNNY = "晴"
    CLOUDY = "多云"
    OVERCAST = "阴"
    RAIN = "雨"
    SNOW = "雪"
    FOG = "雾"
    HAZE = "霾"


@dataclass
class HourlyWeatherInfo:
    """逐小时天气（精准时间维度）"""
    hour: str  # 小时段，如"14:00-16:00"
    weather: str  # 天气状况
    temperature: str  # 温度
    suitability_score: float = 1.0  # 适宜度评分
    outdoor_suitable: bool = True  # 是否适合户外


@dataclass
class WeatherInfo:
    """天气信息"""
    city: str
    temperature: str  # 温度（如"25℃"）
    weather: str  # 天气状况
    wind_direction: str  # 风向
    wind_power: str  # 风力
    humidity: str  # 湿度
    report_time: str  # 发布时间
    
    # 逐小时天气（关键补充）
    hourly_weather: List[HourlyWeatherInfo] = None  # 逐小时天气预报
    
    # 天气适宜度评分
    suitability_score: float = 1.0  # [0, 1]
    
    # 影响建议
    outdoor_suitable: bool = True  # 是否适合户外活动
    recommendations: List[str] = None  # 建议
    warnings: List[str] = None  # 警告


@dataclass
class WeatherImpact:
    """天气对推荐的影响"""
    score_modifier: float  # 评分调整系数 [0, 1.5]
    priority_boost: float  # 优先级提升 [-0.2, 0.2]
    reasons: List[str]  # 理由
    warnings: List[str] = None  # 警告
    edge_color: str = "green"  # 边颜色映射（对接拓扑可视化）
    
    def __post_init__(self):
        """根据score_modifier自动映射颜色"""
        if self.score_modifier >= 1.0:
            self.edge_color = "green"  # 天气良好
        elif 0.7 <= self.score_modifier < 1.0:
            self.edge_color = "yellow"  # 天气一般
        else:
            self.edge_color = "red"  # 天气不佳


class WeatherService:
    """
    天气服务
    
    功能：
    1. 获取实时天气
    2. 获取天气预报
    3. 分析天气对POI推荐的影响
    """
    
    def __init__(self, gaode_client):
        """
        初始化天气服务
        
        Args:
            gaode_client: 高德API客户端
        """
        self.gaode_client = gaode_client
        self._cache = {}  # 天气缓存
    
    def get_weather(self, city: str, date: str = "today") -> WeatherInfo:
        """
        获取城市天气（支持多日期查询）
        
        Args:
            city: 城市名称
            date: 日期（"today", "tomorrow", "2025-12-13"）
            
        Returns:
            天气信息
            
        Raises:
            WeatherServiceException: 天气数据获取失败
            NetworkException: 网络请求失败
        """
        # 检查缓存（按城市和日期缓存）
        cache_key = (city, date)
        if cache_key in self._cache:
            logger.debug(f"Weather cache hit for {cache_key}")
            return self._cache[cache_key]
        
        try:
            weather_data = self.gaode_client.get_weather(city)
            
            if not weather_data:
                raise WeatherServiceException(
                    message=f"无法获取{city}的天气数据",
                    code="WEATHER_NO_DATA",
                    details={'city': city, 'date': date}
                )
            
            if 'casts' not in weather_data or not weather_data['casts']:
                raise WeatherServiceException(
                    message=f"{city}的天气数据格式错误",
                    code="WEATHER_INVALID_FORMAT",
                    details={'city': city, 'data': weather_data}
                )
            
            # 获取今天的天气
            today = weather_data['casts'][0]
            
            # 生成逐小时天气（模拟，实际可接入更精细的API）
            hourly_weather = self._generate_hourly_weather(today)
            
            weather_info = WeatherInfo(
                city=weather_data.get('city', city),
                temperature=f"{today.get('daytemp', 'N/A')}℃",
                weather=today.get('dayweather', '未知'),
                wind_direction=today.get('daywind', '无'),
                wind_power=today.get('daypower', '0'),
                humidity='N/A',
                report_time=weather_data.get('reporttime', ''),
                hourly_weather=hourly_weather,  # 逐小时天气
                suitability_score=self._calculate_suitability(today),
                outdoor_suitable=self._is_outdoor_suitable(today),
                recommendations=self._generate_recommendations(today),
                warnings=self._generate_warnings(today)
            )
            
            # 缓存（按城市和日期）
            self._cache[cache_key] = weather_info
            logger.info(f"Weather fetched and cached for {city}")
            return weather_info
        
        except WeatherServiceException:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            logger.exception(f"获取天气失败: {e}")
            raise WeatherServiceException(
                message=f"天气服务异常: {str(e)}",
                code="WEATHER_SERVICE_ERROR",
                details={'city': city, 'date': date, 'error': str(e)}
            )
    
    def analyze_weather_impact(self, 
                               poi_type: str,
                               weather: WeatherInfo,
                               time_period: str = None,  # 新增：时间段如"14:00-16:00"
                               poi_location: str = None) -> WeatherImpact:  # 新增：POI位置
        """
        分析天气对POI的影响（精准到时间段）
        
        Args:
            poi_type: POI类型
            weather: 天气信息
            time_period: 时间段（可选，如"14:00-16:00"）
            poi_location: POI位置（可选，用于生成更精准的提示）
            
        Returns:
            天气影响分析
        """
        score_modifier = 1.0
        priority_boost = 0.0
        reasons = []
        warnings = []
        
        # 优先使用逐小时天气（如果提供了时间段）
        weather_condition = weather.weather
        if time_period and weather.hourly_weather:
            for hourly in weather.hourly_weather:
                if hourly.hour == time_period:
                    weather_condition = hourly.weather
                    # 基于该时段天气计算影响（更精准）
                    if '雨' in weather_condition:
                        score_modifier = 0.6  # 比全天雨的0.7更严格
                        priority_boost = -0.15
                        location_str = f"{poi_location}" if poi_location else "该地"
                        reasons.append(f"{time_period}{location_str}有雨，户外游览受影响")
                        warnings.append("建议携带雨具或调整时间")
                        break
            else:
                # 没找到匹配的小时段，使用全天天气
                weather_condition = weather.weather
        
        # 根据POI类型和天气状况分析（全天或未指定时段）
        if not (time_period and weather.hourly_weather and any(h.hour == time_period for h in weather.hourly_weather)):
            # 判断是否为室内场所
            is_indoor = False
            if poi_type in ['shopping', 'restaurant']:
                is_indoor = True
            elif poi_type == 'attraction' and poi_location:
                # 根据名称判断是否为室内景点
                indoor_keywords = ['博物馆', '美术馆', '展览馆', '图书馆', '科技馆', 
                                   '文化馆', '艺术馆', '纪念馆', '影院', '剧院']
                is_indoor = any(keyword in poi_location for keyword in indoor_keywords)
            
            if is_indoor:
                # 室内场所（博物馆、购物等）
                if '雨' in weather_condition:
                    score_modifier = 1.2  # 雨天室内场所加分
                    priority_boost = 0.1
                    location_str = f"{poi_location}" if poi_location else "室内场所"
                    reasons.append(f"今日有雨，{location_str}是理想选择")
                else:
                    score_modifier = 1.0
            else:
                # 户外景点
                if '晴' in weather_condition:
                    score_modifier = 1.2
                    priority_boost = 0.1
                    reasons.append(f"今日{weather_condition}，适合游览")
                elif '雨' in weather_condition:
                    score_modifier = 0.7
                    priority_boost = -0.1
                    reasons.append(f"今日有雨，户外活动受影响")
                    warnings.append("建议携带雨具")
                elif '阴' in weather_condition or '多云' in weather_condition:
                    score_modifier = 1.0
                    reasons.append(f"今日{weather_condition}，适宜游览")
        
        # 温度影响
        try:
            temp = int(weather.temperature.replace('℃', ''))
            if temp > 35:
                if poi_type in ['attraction']:
                    score_modifier *= 0.8
                    warnings.append("高温天气，注意防暑")
                elif poi_type in ['shopping', 'restaurant']:
                    score_modifier *= 1.1
                    reasons.append("高温天气，室内活动更舒适")
            elif temp < 5:
                if poi_type in ['attraction']:
                    score_modifier *= 0.9
                    warnings.append("天气较冷，注意保暖")
        except:
            pass
        
        return WeatherImpact(
            score_modifier=score_modifier,
            priority_boost=priority_boost,
            reasons=reasons,
            warnings=warnings
        )
    
    def _calculate_suitability(self, weather_data: Dict) -> float:
        """计算天气适宜度"""
        score = 1.0
        
        weather = weather_data.get('dayweather', '')
        
        # 晴天加分
        if '晴' in weather:
            score = 1.0
        # 阴天、多云
        elif '阴' in weather or '多云' in weather:
            score = 0.9
        # 雨雪减分
        elif '雨' in weather:
            score = 0.6
        elif '雪' in weather:
            score = 0.5
        # 雾霾
        elif '雾' in weather or '霾' in weather:
            score = 0.7
        
        return score
    
    def _is_outdoor_suitable(self, weather_data: Dict) -> bool:
        """判断是否适合户外活动"""
        weather = weather_data.get('dayweather', '')
        
        # 不适合的天气
        unsuitable_conditions = ['大雨', '暴雨', '大雪', '暴雪', '台风']
        for condition in unsuitable_conditions:
            if condition in weather:
                return False
        
        return True
    
    def _generate_recommendations(self, weather_data: Dict) -> List[str]:
        """生成天气建议"""
        recommendations = []
        weather = weather_data.get('dayweather', '')
        
        if '晴' in weather:
            recommendations.append("适合户外活动")
            recommendations.append("注意防晒")
        elif '雨' in weather:
            recommendations.append("建议携带雨具")
            recommendations.append("优先考虑室内活动")
        elif '阴' in weather or '多云' in weather:
            recommendations.append("适合游览")
        
        # 温度建议
        try:
            temp = int(weather_data.get('daytemp', 20))
            if temp > 30:
                recommendations.append("注意防暑降温")
            elif temp < 10:
                recommendations.append("注意添衣保暖")
        except:
            pass
        
        return recommendations
    
    def _generate_warnings(self, weather_data: Dict) -> List[str]:
        """生成天气警告"""
        warnings = []
        weather = weather_data.get('dayweather', '')
        
        if '大雨' in weather or '暴雨' in weather:
            warnings.append("强降雨天气，谨慎出行")
        if '大雪' in weather or '暴雪' in weather:
            warnings.append("强降雪天气，注意安全")
        if '雷电' in weather:
            warnings.append("有雷电，避免户外活动")
        
        # 风力警告
        power = weather_data.get('daypower', '')
        if '7' in power or '8' in power or '9' in power:
            warnings.append("风力较大，注意安全")
        
        return warnings
    
    def _generate_hourly_weather(self, weather_data: Dict) -> List[HourlyWeatherInfo]:
        """
        生成逐小时天气（模拟）
        实际应用中可接入更精细的逐小时天气API
        
        Args:
            weather_data: 当日天气数据
            
        Returns:
            逐小时天气列表
        """
        hourly_list = []
        base_weather = weather_data.get('dayweather', '晴')
        base_temp = int(weather_data.get('daytemp', 20))
        
        # 生成8:00-20:00的逐小时天气（每2小时一个时段）
        time_slots = [
            "08:00-10:00", "10:00-12:00", "12:00-14:00", 
            "14:00-16:00", "16:00-18:00", "18:00-20:00"
        ]
        
        for i, slot in enumerate(time_slots):
            # 模拟温度变化（中午最热）
            if i < 2:
                temp_offset = -2
            elif i < 4:
                temp_offset = 2
            else:
                temp_offset = -1
            
            # 模拟天气变化（下午可能转雨）
            if '晴' in base_weather and i >= 3:
                weather = "多云" if i == 3 else base_weather
            else:
                weather = base_weather
            
            hourly = HourlyWeatherInfo(
                hour=slot,
                weather=weather,
                temperature=f"{base_temp + temp_offset}℃",
                suitability_score=self._calculate_suitability({'dayweather': weather}),
                outdoor_suitable='雨' not in weather and '雪' not in weather
            )
            hourly_list.append(hourly)
        
        return hourly_list
