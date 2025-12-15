"""
POI数据库 V2 - 基于高德API的动态POI搜索
不再依赖本地JSON文件，直接调用高德API获取实时数据
"""

from typing import List, Dict, Optional
from ..core.models import Location, POIType
from .gaode_api_client import GaodeAPIClient


class POIDatabase:
    """
    POI数据库 V2 - 动态版本
    
    核心改变：
    ❌ 不再读取本地JSON文件
    ✅ 直接调用高德API实时搜索POI
    
    优势：
    1. 数据实时、准确
    2. 覆盖全国所有POI（百万级）
    3. 无需手动维护
    4. 自动包含评分、地址、电话等详细信息
    """
    
    def __init__(self, gaode_client: GaodeAPIClient):
        """
        初始化数据库
        
        Args:
            gaode_client: 高德API客户端
        """
        self.gaode_client = gaode_client
        
        # 缓存（可选，提升性能）
        self._cache = {}
        self._cache_ttl = 3600  # 缓存1小时
    
    def get_pois_in_city(self, 
                         city: str, 
                         limit: int = 50,
                         poi_type: Optional[str] = None) -> List[Location]:
        """
        获取城市的POI（从高德API动态搜索）
        
        Args:
            city: 城市名称（如："苏州"）
            limit: 最大返回数量
            poi_type: POI类型过滤（可选）
            
        Returns:
            Location对象列表
        """
        # 构建搜索关键词
        if poi_type:
            keywords = self._type_to_keywords(poi_type)
        else:
            # 默认搜索：景点、餐厅、购物、娱乐
            keywords = "景点|风景名胜|旅游景点|博物馆|公园|餐饮|美食|购物|商场|娱乐"
        
        # 调用高德API搜索
        pois_data = self.gaode_client.search_poi(
            keywords=keywords,
            city=city,
            page_size=min(limit, 25)  # 高德API单次最多25条
        )
        
        if not pois_data:
            print(f"⚠️ 高德API未返回{city}的POI数据")
            return []
        
        # 转换为Location对象
        locations = []
        for poi_data in pois_data[:limit]:
            try:
                location = self._gaode_poi_to_location(poi_data, city)
                locations.append(location)
            except Exception as e:
                print(f"转换POI失败: {poi_data.get('name')}, 错误: {e}")
                continue
        
        print(f"✅ 从高德API获取到{len(locations)}个{city}的POI")
        return locations
    
    def get_pois_around(self,
                       center_location: Location,
                       radius_km: float = 5.0,
                       limit: int = 50,
                       poi_type: Optional[str] = None) -> List[Location]:
        """
        获取周边POI（从高德API动态搜索）
        
        Args:
            center_location: 中心点位置
            radius_km: 搜索半径（公里）
            limit: 最大返回数量
            poi_type: POI类型过滤
            
        Returns:
            Location对象列表
        """
        keywords = self._type_to_keywords(poi_type) if poi_type else "景点|餐饮|购物|娱乐"
        
        pois_data = self.gaode_client.search_poi_around(
            location=(center_location.lon, center_location.lat),
            keywords=keywords,
            radius=int(radius_km * 1000)  # 转换为米
        )
        
        if not pois_data:
            return []
        
        locations = []
        for poi_data in pois_data[:limit]:
            try:
                # 推断城市（从地址中提取）
                city = self._infer_city_from_address(poi_data.get('address', ''))
                location = self._gaode_poi_to_location(poi_data, city)
                locations.append(location)
            except Exception as e:
                print(f"转换周边POI失败: {poi_data.get('name')}, 错误: {e}")
                continue
        
        return locations
    
    def get_poi_by_id(self, poi_id: str) -> Optional[Location]:
        """
        根据ID获取POI（从缓存或API）
        
        Args:
            poi_id: POI ID（高德POI ID）
            
        Returns:
            Location对象
        """
        # 简化实现：通过搜索获取
        # 实际应该调用高德的POI详情API
        return None
    
    def get_poi_by_name(self, name: str, city: Optional[str] = None) -> Optional[Location]:
        """
        根据名称搜索POI
        
        Args:
            name: POI名称
            city: 城市（可选）
            
        Returns:
            Location对象
        """
        pois_data = self.gaode_client.search_poi(
            keywords=name,
            city=city or "苏州",  # 默认苏州
            page_size=5
        )
        
        if pois_data and len(pois_data) > 0:
            return self._gaode_poi_to_location(pois_data[0], city or "苏州")
        
        return None
    
    def _gaode_poi_to_location(self, poi_data: Dict, city: str) -> Location:
        """
        将高德POI数据转换为Location对象
        
        Args:
            poi_data: 高德API返回的POI数据
            city: 城市名称
            
        Returns:
            Location对象
        """
        # 解析POI类型
        poi_type = self._parse_poi_type(poi_data.get('typecode', ''))
        
        # 解析坐标
        location_data = poi_data.get('location', {})
        if isinstance(location_data, dict):
            # 已经是字典格式（从gaode_api_client.search_poi处理过）
            lon = location_data.get('lon', 0)
            lat = location_data.get('lat', 0)
        elif isinstance(location_data, str):
            # 字符串格式："lon,lat"（原始高德API返回）
            try:
                lon_str, lat_str = location_data.split(',')
                lon = float(lon_str)
                lat = float(lat_str)
            except:
                lon, lat = 0, 0
        else:
            lon, lat = 0, 0
        
        # 估算门票和游览时间
        ticket_price, visit_time = self._estimate_cost_and_time(poi_type, poi_data.get('name', ''))
        
        return Location(
            id=poi_data.get('id', ''),
            name=poi_data.get('name', '未知'),
            lat=float(lat),
            lon=float(lon),
            type=poi_type,
            address=poi_data.get('address', ''),
            city=city,
            phone=poi_data.get('tel', ''),
            rating=float(poi_data.get('rating', 0)),
            ticket_price=ticket_price,
            average_visit_time=visit_time,
            opening_hours={}  # 可以从高德API获取，这里简化
        )
    
    def _parse_poi_type(self, typecode: str) -> POIType:
        """
        解析高德POI类型码为系统POI类型
        
        高德类型码规则：
        - 11xxxx: 餐饮
        - 06xxxx: 景点
        - 08xxxx: 购物
        - 09xxxx: 娱乐
        - 15xxxx: 住宿
        """
        if not typecode:
            return POIType.ATTRACTION  # 默认为景点
        
        # 取前两位
        category = typecode[:2] if len(typecode) >= 2 else typecode
        
        type_mapping = {
            '06': POIType.ATTRACTION,
            '11': POIType.RESTAURANT,
            '08': POIType.SHOPPING,
            '09': POIType.ENTERTAINMENT,
            '15': POIType.HOTEL,
            '13': POIType.TRANSPORT_HUB  # ✅ 修复：TRANSPORT_HUB不是TRANSPORT
        }
        
        # POIType没有OTHER，使用ATTRACTION作为默认
        return type_mapping.get(category, POIType.ATTRACTION)
    
    def _type_to_keywords(self, poi_type: str) -> str:
        """POI类型转搜索关键词"""
        type_keywords = {
            'attraction': '景点|风景名胜|旅游景点|博物馆|公园|古迹',
            'restaurant': '餐厅|美食|餐饮|小吃|特色菜',
            'shopping': '购物|商场|商店|百货|超市',
            'entertainment': '娱乐|KTV|电影院|游乐场|酒吧',
            'hotel': '酒店|宾馆|民宿|旅馆',
            'transport': '火车站|汽车站|地铁站|机场'
        }
        return type_keywords.get(poi_type, '景点|餐饮|购物')
    
    def _estimate_cost_and_time(self, poi_type: POIType, name: str) -> tuple:
        """
        估算门票价格和游览时间
        
        Args:
            poi_type: POI类型
            name: POI名称
            
        Returns:
            (门票价格, 游览时间小时)
        """
        # 基础估算
        type_defaults = {
            POIType.ATTRACTION: (50.0, 2.0),
            POIType.RESTAURANT: (0.0, 1.5),
            POIType.SHOPPING: (0.0, 2.0),
            POIType.ENTERTAINMENT: (100.0, 2.5),
            POIType.HOTEL: (300.0, 0.0),
            POIType.TRANSPORT_HUB: (0.0, 0.0),  # ✅ 修复
            POIType.STATION: (0.0, 0.0)
        }
        
        # 知名景点特殊处理
        famous_attractions = {
            '拙政园': (70.0, 2.5),
            '留园': (55.0, 2.0),
            '虎丘': (60.0, 2.0),
            '寒山寺': (20.0, 1.0),
            '苏州博物馆': (0.0, 1.5)
        }
        
        for famous_name, (price, time) in famous_attractions.items():
            if famous_name in name:
                return (price, time)
        
        return type_defaults.get(poi_type, (0.0, 1.0))
    
    def _infer_city_from_address(self, address: str) -> str:
        """从地址推断城市"""
        # 简化版：提取地址中的城市名
        cities = ['苏州', '上海', '杭州', '南京', '厦门', '北京', '广州', '深圳']
        for city in cities:
            if city in address:
                return city
        return "苏州"  # 默认
    
    @property
    def pois(self) -> Dict:
        """
        兼容性属性（用于旧代码）
        返回空字典，因为不再使用本地存储
        """
        return {}
    
    def get_poi_count(self) -> int:
        """
        获取POI总数（兼容性方法）
        V2版本无法提供准确的总数，返回估算值
        """
        return 1000000  # 高德API有百万级POI
