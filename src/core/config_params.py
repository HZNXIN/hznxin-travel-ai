"""
系统配置参数集中管理
便于调优和AB测试
"""

from typing import Dict


class SystemConfig:
    """系统全局配置"""
    
    # ========== ProgressivePlanner 配置 ==========
    PLANNER_CONFIG = {
        'max_candidates': 10,          # 最多返回候选数
        'max_distance_km': 50.0,       # 最大距离（km）
        'max_detour_rate': 0.5,        # 最大绕路率
        'min_consistency_score': 0.7,  # 最小一致性分数
        'min_trust_score': 0.6,        # 最小可信度
        'crowd_threshold': 0.7,        # 拥挤度阈值
        'enable_quality_filter': True, # 启用质量过滤
        'enable_temporal_filter': False, # 启用时间过滤（营业时间检查）
    }
    
    # ========== ScoringEngine 权重配置 ==========
    SCORING_WEIGHTS = {
        'match': 0.25,       # 偏好匹配权重
        'trust': 0.20,       # 可信度权重
        'quality': 0.20,     # 质量权重
        'efficiency': 0.15,  # 效率权重
        'novelty': 0.10,     # 新颖性权重
        'crowd': 0.10        # 避免拥挤权重
    }
    
    # ========== POIQualityFilter 配置 ==========
    QUALITY_FILTER_CONFIG = {
        'min_overall_score': 0.5,      # 最低综合分数
        'min_review_count': 50,        # 最低评论数
        'min_rating': 4.0,             # 最低评分
        'min_playability': 0.3,        # 最低可玩性
        'weights': {
            'playability': 0.30,       # 可玩性权重
            'viewability': 0.25,       # 可观性权重
            'popularity': 0.25,        # 热度权重
            'history': 0.20            # 历史性权重
        }
    }
    
    # ========== VerificationEngine 配置 ==========
    VERIFICATION_CONFIG = {
        'consistency_threshold': 0.8,   # 一致性阈值
        'fake_threshold': 0.3,          # 虚假评论阈值
        'min_reviews': 10,              # 最少评论数
        'crowd_threshold': 0.7,         # 拥挤度阈值
    }
    
    # ========== MultiSourceCollector 权重 ==========
    SOURCE_WEIGHTS = {
        'gaode': 0.40,          # 高德权重最高（官方数据）
        'ctrip': 0.25,          # 携程
        'mafengwo': 0.15,       # 马蜂窝
        'dianping': 0.15,       # 大众点评
        'xiaohongshu': 0.05     # 小红书
    }
    
    SOURCE_CREDIBILITY = {
        'gaode': 1.0,           # 高德可信度最高
        'ctrip': 0.95,
        'mafengwo': 0.90,
        'dianping': 0.90,
        'xiaohongshu': 0.85
    }
    
    # ========== 交通方式参数 ==========
    TRANSPORT_CONFIG = {
        'walk': {
            'speed_kmh': 4.0,           # 步行速度
            'max_distance_km': 2.0,     # 最大步行距离
            'cost_per_km': 0.0          # 免费
        },
        'taxi': {
            'speed_kmh': 30.0,          # 平均速度（市区）
            'base_fare': 13.0,          # 起步价
            'price_per_km': 2.5,        # 每公里价格
            'distance_factor': 1.3      # 实际距离 = 直线距离 × 1.3
        },
        'bus': {
            'speed_kmh': 15.0,          # 平均速度
            'wait_time_h': 0.3,         # 等待时间
            'fare': 2.0,                # 票价
            'min_distance_km': 1.0,     # 最小推荐距离
            'max_distance_km': 20.0,    # 最大推荐距离
            'distance_factor': 1.4      # 实际距离系数
        },
        'subway': {
            'speed_kmh': 35.0,          # 平均速度
            'wait_time_h': 0.25,        # 等待+换乘时间
            'base_fare': 2.0,           # 起步价
            'price_per_10km': 1.0,      # 每10km加价
            'max_fare': 8.0,            # 最高票价
            'min_distance_km': 3.0,     # 最小推荐距离
            'max_distance_km': 30.0,    # 最大推荐距离
            'distance_factor': 1.2      # 实际距离系数
        }
    }
    
    # ========== 空间智能核心配置 ==========
    SPATIAL_INTELLIGENCE_CONFIG = {
        'budget_warning_threshold': 100,    # 预算警告阈值
        'budget_critical_threshold': 50,    # 预算危险阈值
        'time_warning_threshold': 1.0,      # 时间警告阈值（小时）
        'time_critical_threshold': 0.5,     # 时间危险阈值（小时）
        'return_buffer_time': 0.5           # 回程缓冲时间（小时）
    }
    
    # ========== 神经网络服务配置 ==========
    NEURAL_NET_CONFIG = {
        'enabled': False,                   # 是否启用真实模型
        'mock_mode': True,                  # Mock模式
        'bert_model_path': None,            # BERT模型路径
        'gan_model_path': None,             # GAN模型路径
        'gnn_model_path': None,             # GNN模型路径
        'lstm_model_path': None,            # LSTM模型路径
    }
    
    # ========== 缓存配置 ==========
    CACHE_CONFIG = {
        'poi_cache_ttl': 3600,              # POI缓存过期时间（秒）
        'route_cache_ttl': 1800,            # 路径缓存过期时间（秒）
        'weather_cache_ttl': 1800,          # 天气缓存过期时间（秒）
        'max_cache_size': 1000              # 最大缓存条目数
    }
    
    @classmethod
    def get_planner_config(cls) -> Dict:
        """获取规划器配置"""
        return cls.PLANNER_CONFIG.copy()
    
    @classmethod
    def get_scoring_weights(cls) -> Dict:
        """获取评分权重"""
        return cls.SCORING_WEIGHTS.copy()
    
    @classmethod
    def get_quality_filter_config(cls) -> Dict:
        """获取质量过滤配置"""
        return cls.QUALITY_FILTER_CONFIG.copy()
    
    @classmethod
    def get_transport_config(cls, mode: str = None) -> Dict:
        """获取交通配置"""
        if mode:
            return cls.TRANSPORT_CONFIG.get(mode, {}).copy()
        return cls.TRANSPORT_CONFIG.copy()
    
    @classmethod
    def update_planner_config(cls, **kwargs):
        """更新规划器配置"""
        cls.PLANNER_CONFIG.update(kwargs)
    
    @classmethod
    def update_scoring_weights(cls, **kwargs):
        """更新评分权重"""
        cls.SCORING_WEIGHTS.update(kwargs)
    
    @classmethod
    def reset_to_defaults(cls):
        """重置为默认值"""
        # 可以重新初始化所有配置
        pass


# ========== 预设配置方案 ==========

class ConfigPresets:
    """配置预设方案"""
    
    @staticmethod
    def get_conservative_config():
        """保守配置 - 更严格的过滤"""
        return {
            'max_distance_km': 30.0,
            'min_trust_score': 0.7,
            'enable_quality_filter': True,
            'min_review_count': 100,
            'min_rating': 4.3
        }
    
    @staticmethod
    def get_aggressive_config():
        """激进配置 - 更多候选"""
        return {
            'max_distance_km': 100.0,
            'min_trust_score': 0.5,
            'enable_quality_filter': False,
            'min_review_count': 10,
            'min_rating': 3.5
        }
    
    @staticmethod
    def get_balanced_config():
        """平衡配置 - 默认推荐"""
        return SystemConfig.PLANNER_CONFIG.copy()
    
    @staticmethod
    def get_quality_first_config():
        """质量优先配置"""
        return {
            'max_distance_km': 50.0,
            'min_trust_score': 0.8,
            'enable_quality_filter': True,
            'min_review_count': 200,
            'min_rating': 4.5,
            'scoring_weights': {
                'quality': 0.35,    # 提高质量权重
                'trust': 0.25,
                'match': 0.20,
                'efficiency': 0.10,
                'novelty': 0.05,
                'crowd': 0.05
            }
        }
    
    @staticmethod
    def get_efficiency_first_config():
        """效率优先配置"""
        return {
            'max_distance_km': 20.0,
            'scoring_weights': {
                'efficiency': 0.35,  # 提高效率权重
                'match': 0.25,
                'quality': 0.20,
                'trust': 0.10,
                'novelty': 0.05,
                'crowd': 0.05
            }
        }
