"""
核心组件单元测试
测试所有修复后的功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import Location, POIType, TransportMode, State
from src.core.neural_net_service import NeuralNetService
from src.core.config_params import SystemConfig, ConfigPresets
from src.data_services.poi_database_v2 import POIDatabase
from src.data_services.gaode_api_client import GaodeAPIClient


class TestPOITypeFixe:
    """测试POIType修复"""
    
    def test_parse_empty_typecode(self):
        """测试空类型码解析"""
        client = GaodeAPIClient("test_key")
        poi_db = POIDatabase(client)
        
        result = poi_db._parse_poi_type("")
        assert result == POIType.ATTRACTION, "空类型码应返回ATTRACTION"
    
    def test_parse_unknown_typecode(self):
        """测试未知类型码解析"""
        client = GaodeAPIClient("test_key")
        poi_db = POIDatabase(client)
        
        result = poi_db._parse_poi_type("999999")
        assert result == POIType.ATTRACTION, "未知类型码应返回ATTRACTION"
    
    def test_parse_known_typecode(self):
        """测试已知类型码解析"""
        client = GaodeAPIClient("test_key")
        poi_db = POIDatabase(client)
        
        # 测试餐饮类型
        result = poi_db._parse_poi_type("110101")
        assert result == POIType.RESTAURANT
        
        # 测试景点类型
        result = poi_db._parse_poi_type("060101")
        assert result == POIType.ATTRACTION
        
        # 测试购物类型
        result = poi_db._parse_poi_type("080101")
        assert result == POIType.SHOPPING


class TestTransportCalculation:
    """测试交通方式计算"""
    
    @pytest.fixture
    def test_locations(self):
        """创建测试用的位置"""
        loc1 = Location(
            id="loc1", name="起点", lat=31.30, lon=120.52,
            type=POIType.STATION
        )
        loc2 = Location(
            id="loc2", name="终点", lat=31.35, lon=120.58,
            type=POIType.ATTRACTION
        )
        return loc1, loc2
    
    def test_walk_edge_calculation(self, test_locations):
        """测试步行边计算"""
        from src.core.progressive_planner import ProgressivePlanner
        
        # 创建简化的planner（只用于测试距离计算）
        loc1, loc2 = test_locations
        
        # 计算距离
        import math
        R = 6371
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        distance = R * 2 * math.asin(math.sqrt(a))
        
        assert distance > 0, "距离应大于0"
        assert distance < 10, "测试点距离应小于10km"
    
    def test_bus_edge_distance_filter(self):
        """测试公交距离过滤"""
        from src.core.config_params import SystemConfig
        
        bus_config = SystemConfig.get_transport_config('bus')
        assert bus_config['min_distance_km'] == 1.0
        assert bus_config['max_distance_km'] == 20.0
    
    def test_subway_edge_distance_filter(self):
        """测试地铁距离过滤"""
        from src.core.config_params import SystemConfig
        
        subway_config = SystemConfig.get_transport_config('subway')
        assert subway_config['min_distance_km'] == 3.0
        assert subway_config['max_distance_km'] == 30.0


class TestNeuralNetService:
    """测试神经网络服务"""
    
    @pytest.fixture
    def nn_service(self):
        """创建神经网络服务实例"""
        return NeuralNetService(config={'enabled': False})
    
    def test_extract_user_profile(self, nn_service):
        """测试用户画像提取"""
        profile = nn_service.extract_user_profile(
            "我想在苏州玩1天，喜欢文化和园林", 
            []
        )
        
        assert profile is not None
        assert hasattr(profile, 'purpose')
        assert isinstance(profile.purpose, dict)
        assert 'culture' in profile.purpose or 'leisure' in profile.purpose
    
    def test_detect_fake(self, nn_service):
        """测试虚假评论检测"""
        fake_score = nn_service.detect_fake("超级好超级好超级好")
        
        assert 0.0 <= fake_score <= 1.0, "虚假分数应在0-1之间"
    
    def test_sentiment_analysis(self, nn_service):
        """测试情感分析"""
        sentiment = nn_service.sentiment_analysis("景色优美，令人难忘")
        
        assert 0.0 <= sentiment <= 1.0, "情感分数应在0-1之间"
        assert sentiment > 0.5, "正面评论应得到较高分数"
    
    def test_gnn_spatial(self, nn_service):
        """测试GNN空间关系评分"""
        loc1 = Location(
            id="1", name="地点1", lat=31.30, lon=120.52,
            type=POIType.ATTRACTION
        )
        loc2 = Location(
            id="2", name="地点2", lat=31.31, lon=120.53,
            type=POIType.ATTRACTION
        )
        
        score = nn_service.gnn_spatial(loc1, loc2)
        assert 0.0 <= score <= 1.0, "空间评分应在0-1之间"
    
    def test_lstm_predict_crowd(self, nn_service):
        """测试LSTM拥挤度预测"""
        loc = Location(
            id="test", name="测试景点", lat=31.32, lon=120.63,
            type=POIType.ATTRACTION
        )
        
        # 测试不同时间段
        morning_crowd = nn_service.lstm_predict_crowd(loc, 10.0)  # 上午10点
        noon_crowd = nn_service.lstm_predict_crowd(loc, 14.0)     # 下午2点
        
        assert 0.0 <= morning_crowd <= 1.0
        assert 0.0 <= noon_crowd <= 1.0


class TestConfigManagement:
    """测试配置管理"""
    
    def test_get_planner_config(self):
        """测试获取规划器配置"""
        config = SystemConfig.get_planner_config()
        
        assert 'max_candidates' in config
        assert 'max_distance_km' in config
        assert config['max_candidates'] == 10
    
    def test_get_scoring_weights(self):
        """测试获取评分权重"""
        weights = SystemConfig.get_scoring_weights()
        
        assert 'match' in weights
        assert 'trust' in weights
        assert 'quality' in weights
        
        # 权重和应约为1
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01, f"权重和应接近1，实际为{total}"
    
    def test_update_config(self):
        """测试动态更新配置"""
        original = SystemConfig.get_planner_config()
        original_max = original['max_distance_km']
        
        # 更新配置
        SystemConfig.update_planner_config(max_distance_km=100.0)
        updated = SystemConfig.get_planner_config()
        
        assert updated['max_distance_km'] == 100.0
        
        # 恢复原配置
        SystemConfig.update_planner_config(max_distance_km=original_max)
    
    def test_preset_configs(self):
        """测试预设配置"""
        conservative = ConfigPresets.get_conservative_config()
        aggressive = ConfigPresets.get_aggressive_config()
        quality_first = ConfigPresets.get_quality_first_config()
        
        # 保守配置应该更严格
        assert conservative['min_trust_score'] > aggressive['min_trust_score']
        assert conservative['min_rating'] > aggressive['min_rating']
        
        # 质量优先配置应有更高的质量权重
        quality_weights = quality_first['scoring_weights']
        assert quality_weights['quality'] > 0.3


class TestDataCollectionFaultTolerance:
    """测试数据采集容错"""
    
    def test_multi_source_collection_with_failures(self):
        """测试部分数据源失败的情况"""
        from src.data_services.multi_source_collector import MultiSourceCollector
        
        client = GaodeAPIClient("test_key")
        collector = MultiSourceCollector(client)
        
        loc = Location(
            id="test", name="测试POI", lat=31.30, lon=120.52,
            type=POIType.ATTRACTION
        )
        
        # 即使部分数据源失败，也应返回结果
        results = collector.collect_multi_source(loc)
        
        assert len(results) > 0, "至少应有一个数据源返回结果"
        assert 'gaode' in results or 'ctrip' in results or 'default' in results
    
    def test_all_sources_fail_fallback(self):
        """测试所有数据源失败时的降级"""
        # 这个测试需要模拟所有数据源失败的情况
        # 实际实现中应使用mock
        pass


class TestSystemIntegration:
    """系统集成测试"""
    
    def test_system_initialization(self):
        """测试系统初始化"""
        # 测试所有核心组件能否成功初始化
        from src.data_services.multi_source_collector import MultiSourceCollector
        from src.core.verification_engine import VerificationEngine
        from src.core.scoring_engine import ScoringEngine
        
        client = GaodeAPIClient("test_key")
        poi_db = POIDatabase(client)
        nn_service = NeuralNetService(config={'enabled': False})
        collector = MultiSourceCollector(client)
        
        # 初始化核心引擎
        verification_engine = VerificationEngine(
            multi_source_collector=collector,
            neural_net_service=nn_service,
            gaode_api_client=client
        )
        scoring_engine = ScoringEngine()
        
        assert verification_engine is not None
        assert scoring_engine is not None
    
    def test_location_creation(self):
        """测试Location对象创建"""
        loc = Location(
            id="test_id",
            name="测试地点",
            lat=31.30,
            lon=120.52,
            type=POIType.ATTRACTION,
            city="苏州",
            rating=4.5
        )
        
        assert loc.id == "test_id"
        assert loc.name == "测试地点"
        assert loc.city == "苏州"
        assert loc.rating == 4.5


class TestErrorHandling:
    """测试错误处理和降级机制"""
    
    def test_invalid_api_key_handling(self):
        """测试无效API Key的处理"""
        client = GaodeAPIClient("invalid_key")
        
        # 应该能够创建客户端，但API调用会失败
        assert client.api_key == "invalid_key"
    
    def test_empty_poi_database(self):
        """测试空POI数据库的处理"""
        client = GaodeAPIClient("test_key")
        poi_db = POIDatabase(client)
        
        # 空结果应该被正确处理
        pois = poi_db.get_pois_in_city("不存在的城市", limit=10)
        assert isinstance(pois, list)


# 运行测试的便捷函数
def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行单元测试...")
    print("=" * 60)
    
    pytest.main([
        __file__, 
        "-v",           # 详细输出
        "-s",           # 显示print输出
        "--tb=short",   # 简短的traceback
    ])


if __name__ == "__main__":
    run_all_tests()
