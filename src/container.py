"""
依赖注入容器
统一管理所有服务的依赖关系，便于测试和维护
"""

from dependency_injector import containers, providers
from config import settings

from src.data_services.poi_database import POIDatabase
from src.data_services.gaode_api_client import GaodeAPIClient
from src.data_services.weather_service import WeatherService
from src.core.spatio_temporal_damping import SpatioTemporalDamping


class Container(containers.DeclarativeContainer):
    """
    应用依赖注入容器
    
    使用依赖注入模式管理所有服务实例，提供：
    - 统一的依赖管理
    - 易于测试（可替换mock对象）
    - 配置外部化
    - 单例模式支持
    """
    
    # ========================================================================
    # 配置
    # ========================================================================
    config = providers.Configuration()
    
    # ========================================================================
    # 数据服务层
    # ========================================================================
    
    gaode_client = providers.Singleton(
        GaodeAPIClient,
        api_key=config.gaode_api_key
    )
    
    poi_database = providers.Singleton(
        POIDatabase,
        data_dir=config.data_dir
    )
    
    weather_service = providers.Singleton(
        WeatherService,
        gaode_client=gaode_client
    )
    
    # ========================================================================
    # 核心服务层
    # ========================================================================
    
    damping_service = providers.Singleton(
        SpatioTemporalDamping
    )
    
    # LLM客户端将在需要时添加
    # llm_client = providers.Singleton(
    #     create_llm_client,
    #     provider=config.llm_provider,
    #     api_key=config.llm_api_key,
    #     model=config.llm_model,
    #     api_base=config.llm_api_base
    # )
    
    # SpatialIntelligenceCore将在需要时添加
    # spatial_core = providers.Singleton(
    #     SpatialIntelligenceCore,
    #     llm_client=llm_client
    # )
    
    # ProgressivePlanner将在需要时添加
    # planner = providers.Singleton(
    #     ProgressivePlanner,
    #     poi_db=poi_database,
    #     spatial_core=spatial_core,
    #     weather_service=weather_service,
    #     damping_service=damping_service
    # )


def create_container() -> Container:
    """
    创建并配置容器
    
    Returns:
        配置好的依赖注入容器
    """
    container = Container()
    container.config.from_dict({
        'gaode_api_key': settings.gaode_api_key,
        'data_dir': settings.data_dir,
        'llm_provider': settings.llm_provider,
        'llm_api_key': settings.llm_api_key,
        'llm_model': settings.llm_model,
        'llm_api_base': settings.llm_api_base,
    })
    return container
