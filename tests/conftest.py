"""
测试配置
提供通用的fixtures和测试工具
"""

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.models import Location, POIType
from src.container import Container


@pytest.fixture(scope="session")
def test_container():
    """测试用依赖容器"""
    container = Container()
    container.config.from_dict({
        'gaode_api_key': 'test_key',
        'data_dir': 'tests/data',
        'llm_provider': 'mock',
        'llm_api_key': 'test_llm_key',
        'llm_model': 'test_model',
        'llm_api_base': 'http://localhost'
    })
    return container


@pytest.fixture
def sample_location():
    """示例POI"""
    return Location(
        id="test_poi_1",
        name="测试景点",
        lat=31.3,
        lon=120.6,
        type=POIType.ATTRACTION,
        address="苏州市姑苏区测试路1号",
        average_visit_time=2.0,
        ticket_price=50.0
    )


@pytest.fixture
def sample_locations():
    """多个示例POI"""
    return [
        Location(
            id="poi_1",
            name="拙政园",
            lat=31.324,
            lon=120.630,
            type=POIType.ATTRACTION,
            address="苏州市姑苏区东北街178号",
            average_visit_time=2.5,
            ticket_price=80.0
        ),
        Location(
            id="poi_2",
            name="观前街",
            lat=31.312,
            lon=120.623,
            type=POIType.COMMERCIAL,
            address="苏州市姑苏区观前街",
            average_visit_time=1.5,
            ticket_price=0.0
        ),
        Location(
            id="poi_3",
            name="金鸡湖",
            lat=31.308,
            lon=120.706,
            type=POIType.SCENIC,
            address="苏州市工业园区金鸡湖",
            average_visit_time=3.0,
            ticket_price=0.0
        )
    ]


@pytest.fixture
def mock_weather_data():
    """Mock天气数据"""
    return {
        "city": "苏州市",
        "casts": [{
            "dayweather": "晴",
            "daytemp": "25",
            "daywind": "东南风",
            "daypower": "3-4",
            "nightweather": "晴",
            "nighttemp": "15"
        }],
        "reporttime": "2025-12-13 12:00:00"
    }
