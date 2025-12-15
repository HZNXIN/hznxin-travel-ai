"""
天气服务单元测试
验证天气数据获取、异常处理、缓存等功能
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.data_services.weather_service import WeatherService
from src.core.exceptions import WeatherServiceException


class TestWeatherService:
    """天气服务测试类"""
    
    @pytest.fixture
    def mock_gaode_client(self):
        """Mock高德API客户端"""
        return Mock()
    
    @pytest.fixture
    def weather_service(self, mock_gaode_client):
        """创建天气服务实例"""
        return WeatherService(mock_gaode_client)
    
    # ========================================================================
    # 测试正常流程
    # ========================================================================
    
    def test_get_weather_success(self, weather_service, mock_gaode_client, mock_weather_data):
        """测试成功获取天气"""
        mock_gaode_client.get_weather.return_value = mock_weather_data
        
        weather = weather_service.get_weather("苏州")
        
        assert weather is not None
        assert weather.city == "苏州市"
        assert weather.weather == "晴"
        assert weather.temperature == "25℃"
        assert weather.hourly_weather is not None
        assert len(weather.hourly_weather) > 0
    
    def test_weather_cache(self, weather_service, mock_gaode_client, mock_weather_data):
        """测试天气缓存"""
        mock_gaode_client.get_weather.return_value = mock_weather_data
        
        # 第一次调用
        weather1 = weather_service.get_weather("苏州")
        # 第二次调用应该命中缓存
        weather2 = weather_service.get_weather("苏州")
        
        # 应该只调用一次API
        assert mock_gaode_client.get_weather.call_count == 1
        assert weather1 == weather2
    
    def test_weather_cache_with_different_dates(self, weather_service, mock_gaode_client, mock_weather_data):
        """测试不同日期的缓存"""
        mock_gaode_client.get_weather.return_value = mock_weather_data
        
        weather_today = weather_service.get_weather("苏州", date="today")
        weather_tomorrow = weather_service.get_weather("苏州", date="tomorrow")
        
        # 不同日期应该调用两次API
        assert mock_gaode_client.get_weather.call_count == 2
    
    # ========================================================================
    # 测试异常处理
    # ========================================================================
    
    def test_get_weather_no_data(self, weather_service, mock_gaode_client):
        """测试无天气数据异常"""
        mock_gaode_client.get_weather.return_value = None
        
        with pytest.raises(WeatherServiceException) as exc_info:
            weather_service.get_weather("不存在的城市")
        
        assert exc_info.value.code == "WEATHER_NO_DATA"
        assert "不存在的城市" in exc_info.value.message
    
    def test_get_weather_invalid_format(self, weather_service, mock_gaode_client):
        """测试天气数据格式错误"""
        mock_gaode_client.get_weather.return_value = {
            "city": "苏州",
            # 缺少casts字段
        }
        
        with pytest.raises(WeatherServiceException) as exc_info:
            weather_service.get_weather("苏州")
        
        assert exc_info.value.code == "WEATHER_INVALID_FORMAT"
    
    def test_get_weather_api_exception(self, weather_service, mock_gaode_client):
        """测试API调用异常"""
        mock_gaode_client.get_weather.side_effect = Exception("Network error")
        
        with pytest.raises(WeatherServiceException) as exc_info:
            weather_service.get_weather("苏州")
        
        assert exc_info.value.code == "WEATHER_SERVICE_ERROR"
        assert "Network error" in exc_info.value.details.get('error', '')
    
    # ========================================================================
    # 测试天气影响分析
    # ========================================================================
    
    def test_analyze_weather_impact_sunny(self, weather_service, mock_gaode_client, mock_weather_data):
        """测试晴天对景点的影响"""
        mock_gaode_client.get_weather.return_value = mock_weather_data
        weather = weather_service.get_weather("苏州")
        
        impact = weather_service.analyze_weather_impact(
            poi_type="attraction",
            weather=weather
        )
        
        assert impact.score_modifier >= 1.0, "晴天应该加成或保持"
        assert impact.edge_color in ["green", "yellow"]
    
    def test_analyze_weather_impact_rainy_outdoor(self, weather_service):
        """测试雨天对户外景点的影响"""
        # 创建雨天天气
        from src.data_services.weather_service import WeatherInfo, HourlyWeatherInfo
        
        rainy_weather = WeatherInfo(
            city="苏州",
            temperature="20℃",
            weather="小雨",
            wind_direction="东风",
            wind_power="3-4",
            humidity="80%",
            report_time="2025-12-13 12:00:00",
            hourly_weather=[
                HourlyWeatherInfo(
                    hour="10:00-12:00",
                    weather="小雨",
                    temperature="20℃",
                    suitability_score=0.6,
                    outdoor_suitable=False
                )
            ]
        )
        
        impact = weather_service.analyze_weather_impact(
            poi_type="attraction",
            weather=rainy_weather,
            time_period="10:00-12:00",
            poi_location="拙政园"
        )
        
        assert impact.score_modifier < 1.0, "雨天应该降权"
        assert impact.priority_boost < 0, "优先级应该降低"
        assert len(impact.reasons) > 0
        assert any("雨" in r for r in impact.reasons)
    
    def test_analyze_weather_impact_rainy_indoor(self, weather_service):
        """测试雨天对室内场所的影响"""
        from src.data_services.weather_service import WeatherInfo
        
        rainy_weather = WeatherInfo(
            city="苏州",
            temperature="20℃",
            weather="小雨",
            wind_direction="东风",
            wind_power="3-4",
            humidity="80%",
            report_time="2025-12-13 12:00:00"
        )
        
        impact = weather_service.analyze_weather_impact(
            poi_type="shopping",
            weather=rainy_weather
        )
        
        assert impact.score_modifier >= 1.0, "雨天应该加成室内场所"
        assert any("室内" in r for r in impact.reasons)


class TestWeatherInfoDataclass:
    """测试WeatherInfo数据类"""
    
    def test_weather_info_creation(self):
        """测试创建WeatherInfo"""
        from src.data_services.weather_service import WeatherInfo
        
        weather = WeatherInfo(
            city="苏州",
            temperature="25℃",
            weather="晴",
            wind_direction="东南风",
            wind_power="3-4",
            humidity="60%",
            report_time="2025-12-13 12:00:00"
        )
        
        assert weather.city == "苏州"
        assert weather.temperature == "25℃"
        assert weather.weather == "晴"


class TestHourlyWeatherGeneration:
    """测试逐小时天气生成"""
    
    @pytest.fixture
    def weather_service(self):
        mock_client = Mock()
        return WeatherService(mock_client)
    
    def test_generate_hourly_weather(self, weather_service):
        """测试生成逐小时天气"""
        weather_data = {
            "dayweather": "晴",
            "daytemp": "25"
        }
        
        hourly_list = weather_service._generate_hourly_weather(weather_data)
        
        assert len(hourly_list) > 0, "应该生成逐小时天气"
        assert all(hasattr(h, 'hour') for h in hourly_list)
        assert all(hasattr(h, 'weather') for h in hourly_list)
        assert all(hasattr(h, 'temperature') for h in hourly_list)
