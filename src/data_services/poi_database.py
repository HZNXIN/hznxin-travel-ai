"""
POI数据库
管理POI数据的存储和查询
"""

from typing import List, Dict, Optional
import json
import os
from datetime import datetime

from ..core.models import Location, POIType


class POIDatabase:
    """
    POI数据库
    
    简化实现：使用JSON文件存储
    实际项目应该使用：
    - PostgreSQL + PostGIS（空间数据）
    - MongoDB（文档存储）
    - Elasticsearch（搜索）
    """
    
    def __init__(self, data_dir: str = "data", gaode_client=None):
        """
        初始化数据库
        
        Args:
            data_dir: 数据目录
            gaode_client: 高德API客户端（可选，用于实时搜索）
        """
        self.data_dir = data_dir
        self.gaode_client = gaode_client
        os.makedirs(data_dir, exist_ok=True)
        
        # POI数据文件
        self.poi_file = os.path.join(data_dir, "pois.json")
        
        # 加载数据
        self.pois: Dict[str, Dict] = self._load_pois()
        
        # 城市索引
        self.city_index: Dict[str, List[str]] = {}
        self._build_city_index()
    
    def get_pois_in_city(self, city: str, limit: int = 200, force_refresh: bool = False) -> List[Location]:
        """
        获取城市的所有POI
        
        Args:
            city: 城市名称
            limit: 最大数量
            force_refresh: 是否强制从高德API刷新
            
        Returns:
            POI列表
        """
        # 🔥 如果有高德API客户端且需要刷新，或者本地数据为空，则从API获取
        if self.gaode_client and (force_refresh or city not in self.city_index or len(self.city_index.get(city, [])) < 10):
            print(f"🌐 正在从高德API获取 {city} 的POI数据...")
            self._fetch_and_cache_from_gaode(city)
        
        poi_ids = self.city_index.get(city, [])
        
        locations = []
        for poi_id in poi_ids[:limit]:
            poi_data = self.pois.get(poi_id)
            if poi_data:
                location = self._dict_to_location(poi_data)
                locations.append(location)
        
        return locations
    
    def _fetch_and_cache_from_gaode(self, city: str):
        """
        从高德API获取POI并缓存到本地
        
        Args:
            city: 城市名称
        """
        if not self.gaode_client:
            print("⚠️ 没有高德API客户端，无法获取实时数据")
            return
        
        # 搜索多个类别的POI
        categories = [
            ('景点', '风景名胜|旅游景点'),
            ('餐饮', '餐饮服务'),
            ('购物', '购物服务'),
            ('娱乐', '生活服务'),
        ]
        
        total_count = 0
        
        for cat_name, types in categories:
            try:
                pois = self.gaode_client.search_poi(
                    keywords=cat_name,
                    city=city,
                    types=types,
                    page_size=50
                )
                
                if pois:
                    for poi in pois:
                        # 转换为Location对象
                        location = Location(
                            id=poi['id'],
                            name=poi['name'],
                            lat=poi['location']['lat'],
                            lon=poi['location']['lon'],
                            type=self._map_gaode_type_to_poi_type(poi.get('typecode', '')),
                            address=poi.get('address', ''),
                            phone=poi.get('tel', ''),
                            ticket_price=self._parse_cost(poi.get('cost', '')),
                            average_visit_time=2.0  # 默认2小时
                        )
                        
                        self.save_poi(location)
                        total_count += 1
                    
                    print(f"   ✅ {cat_name}: {len(pois)}个POI")
            
            except Exception as e:
                print(f"   ❌ 获取{cat_name}失败: {e}")
        
        print(f"🎉 从高德API获取并缓存了 {total_count} 个{city}的POI")
    
    def _map_gaode_type_to_poi_type(self, typecode: str) -> POIType:
        """
        将高德POI类型码映射到系统POI类型
        
        Args:
            typecode: 高德类型码（如 110000）
            
        Returns:
            POI类型
        """
        # 高德类型码规则：前2位表示大类
        if not typecode:
            return POIType.ATTRACTION
        
        major_type = typecode[:2]
        
        type_mapping = {
            '06': POIType.SHOPPING,      # 购物服务
            '05': POIType.RESTAURANT,    # 餐饮服务
            '08': POIType.ENTERTAINMENT, # 体育休闲服务
            '09': POIType.ENTERTAINMENT, # 医疗保健服务
            '11': POIType.ATTRACTION,    # 旅游景点
            '14': POIType.TRANSPORT_HUB, # 交通设施服务
        }
        
        return type_mapping.get(major_type, POIType.ATTRACTION)
    
    def _parse_cost(self, cost_str: str) -> float:
        """
        解析费用字符串
        
        Args:
            cost_str: 费用字符串（如 "50元"）
            
        Returns:
            费用数值
        """
        if not cost_str:
            return 0.0
        
        try:
            import re
            numbers = re.findall(r'\d+', cost_str)
            if numbers:
                return float(numbers[0])
        except:
            pass
        
        return 0.0
    
    def get_poi_by_id(self, poi_id: str) -> Optional[Location]:
        """
        根据ID获取POI
        
        Args:
            poi_id: POI ID
            
        Returns:
            Location对象
        """
        poi_data = self.pois.get(poi_id)
        if poi_data:
            return self._dict_to_location(poi_data)
        return None
    
    def save_poi(self, location: Location):
        """
        保存POI
        
        Args:
            location: Location对象
        """
        poi_data = self._location_to_dict(location)
        self.pois[location.id] = poi_data
        
        # 更新城市索引
        city = poi_data.get('city', '')
        if city:
            if city not in self.city_index:
                self.city_index[city] = []
            if location.id not in self.city_index[city]:
                self.city_index[city].append(location.id)
        
        # 持久化
        self._save_pois()
    
    def batch_save_pois(self, locations: List[Location]):
        """批量保存POI"""
        for location in locations:
            self.save_poi(location)
    
    def search_by_type(self, poi_type: POIType, city: Optional[str] = None) -> List[Location]:
        """
        根据类型搜索POI
        
        Args:
            poi_type: POI类型
            city: 城市（可选）
            
        Returns:
            POI列表
        """
        results = []
        
        if city:
            poi_ids = self.city_index.get(city, [])
        else:
            poi_ids = self.pois.keys()
        
        for poi_id in poi_ids:
            poi_data = self.pois.get(poi_id)
            if poi_data and poi_data.get('type') == poi_type.value:
                location = self._dict_to_location(poi_data)
                results.append(location)
        
        return results
    
    def initialize_demo_data(self):
        """
        初始化Demo数据
        
        创建一些测试用的POI
        """
        # 苏州景点 - 扩展到30+个POI
        suzhou_pois = [
            # 姑苏区景点
            {'id': 'suzhou_001', 'name': '拙政园', 'lat': 31.3229, 'lon': 120.6309, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区东北街178号', 'ticket_price': 70.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_002', 'name': '苏州博物馆', 'lat': 31.3241, 'lon': 120.6294, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区东北街204号', 'ticket_price': 0.0, 'average_visit_time': 1.5},
            {'id': 'suzhou_003', 'name': '平江路历史街区', 'lat': 31.3203, 'lon': 120.6328, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区平江路', 'ticket_price': 0.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_004', 'name': '虎丘', 'lat': 31.3282, 'lon': 120.5947, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区虎丘山门内8号', 'ticket_price': 60.0, 'average_visit_time': 2.5},
            {'id': 'suzhou_005', 'name': '留园', 'lat': 31.3157, 'lon': 120.5965, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区留园路338号', 'ticket_price': 55.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_006', 'name': '狮子林', 'lat': 31.3213, 'lon': 120.6298, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区园林路23号', 'ticket_price': 40.0, 'average_visit_time': 1.5},
            {'id': 'suzhou_007', 'name': '盘门景区', 'lat': 31.2969, 'lon': 120.6173, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区东大街49号', 'ticket_price': 40.0, 'average_visit_time': 1.5},
            {'id': 'suzhou_008', 'name': '艺圃', 'lat': 31.3187, 'lon': 120.6205, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区文衙弄5号', 'ticket_price': 10.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_009', 'name': '环秀山庄', 'lat': 31.3136, 'lon': 120.6208, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区景德路262号', 'ticket_price': 15.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_010', 'name': '耦园', 'lat': 31.3234, 'lon': 120.6359, 'type': 'attraction', 'city': '苏州', 'address': '苏州市姑苏区小新桥巷6号', 'ticket_price': 25.0, 'average_visit_time': 1.0},
            
            # 工业园区景点
            {'id': 'suzhou_011', 'name': '金鸡湖景区', 'lat': 31.3189, 'lon': 120.7021, 'type': 'attraction', 'city': '苏州', 'address': '苏州市工业园区金鸡湖', 'ticket_price': 0.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_012', 'name': '诚品书店', 'lat': 31.3162, 'lon': 120.6895, 'type': 'shopping', 'city': '苏州', 'address': '苏州市工业园区月廊街8号', 'ticket_price': 0.0, 'average_visit_time': 1.5},
            {'id': 'suzhou_013', 'name': '东方之门', 'lat': 31.3294, 'lon': 120.6912, 'type': 'attraction', 'city': '苏州', 'address': '苏州市工业园区星港街199号', 'ticket_price': 0.0, 'average_visit_time': 0.5},
            {'id': 'suzhou_014', 'name': '苏州中心', 'lat': 31.3294, 'lon': 120.6863, 'type': 'shopping', 'city': '苏州', 'address': '苏州市工业园区苏雅路388号', 'ticket_price': 0.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_015', 'name': '李公堤', 'lat': 31.3152, 'lon': 120.7135, 'type': 'attraction', 'city': '苏州', 'address': '苏州市工业园区李公堤', 'ticket_price': 0.0, 'average_visit_time': 1.5},
            
            # 吴中区景点
            {'id': 'suzhou_016', 'name': '太湖国家湿地公园', 'lat': 31.1872, 'lon': 120.4312, 'type': 'attraction', 'city': '苏州', 'address': '苏州市吴中区太湖大道', 'ticket_price': 50.0, 'average_visit_time': 3.0},
            {'id': 'suzhou_017', 'name': '木渎古镇', 'lat': 31.2513, 'lon': 120.5243, 'type': 'attraction', 'city': '苏州', 'address': '苏州市吴中区木渎镇', 'ticket_price': 60.0, 'average_visit_time': 2.5},
            {'id': 'suzhou_018', 'name': '穹窿山', 'lat': 31.2812, 'lon': 120.4523, 'type': 'attraction', 'city': '苏州', 'address': '苏州市吴中区穹窿山景区', 'ticket_price': 80.0, 'average_visit_time': 3.0},
            {'id': 'suzhou_019', 'name': '光福古镇', 'lat': 31.2189, 'lon': 120.3456, 'type': 'attraction', 'city': '苏州', 'address': '苏州市吴中区光福镇', 'ticket_price': 0.0, 'average_visit_time': 2.0},
            
            # 餐饮
            {'id': 'suzhou_020', 'name': '得月楼', 'lat': 31.3226, 'lon': 120.6302, 'type': 'restaurant', 'city': '苏州', 'address': '苏州市姑苏区太监弄27号', 'ticket_price': 0.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_021', 'name': '松鹤楼', 'lat': 31.3198, 'lon': 120.6287, 'type': 'restaurant', 'city': '苏州', 'address': '苏州市姑苏区观前街72号', 'ticket_price': 0.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_022', 'name': '协和菜馆', 'lat': 31.3167, 'lon': 120.6243, 'type': 'restaurant', 'city': '苏州', 'address': '苏州市姑苏区凤凰街16号', 'ticket_price': 0.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_023', 'name': '哑巴生煎', 'lat': 31.3189, 'lon': 120.6324, 'type': 'restaurant', 'city': '苏州', 'address': '苏州市姑苏区临顿路', 'ticket_price': 0.0, 'average_visit_time': 0.5},
            
            # 娱乐
            {'id': 'suzhou_024', 'name': '星聚会KTV', 'lat': 31.2956, 'lon': 120.6189, 'type': 'entertainment', 'city': '苏州', 'address': '苏州市姑苏区苏州胥江天街', 'ticket_price': 0.0, 'average_visit_time': 2.0},
            {'id': 'suzhou_025', 'name': '苏州中心影城', 'lat': 31.3289, 'lon': 120.6858, 'type': 'entertainment', 'city': '苏州', 'address': '苏州市工业园区苏雅路388号', 'ticket_price': 0.0, 'average_visit_time': 2.5},
            
            # 高新区景点
            {'id': 'suzhou_026', 'name': '寒山寺', 'lat': 31.3043, 'lon': 120.5634, 'type': 'attraction', 'city': '苏州', 'address': '苏州市高新区枫桥路寒山寺弄24号', 'ticket_price': 20.0, 'average_visit_time': 1.0},
            {'id': 'suzhou_027', 'name': '枫桥景区', 'lat': 31.3056, 'lon': 120.5612, 'type': 'attraction', 'city': '苏州', 'address': '苏州市高新区枫桥路', 'ticket_price': 25.0, 'average_visit_time': 1.5},
            {'id': 'suzhou_028', 'name': '大阳山国家森林公园', 'lat': 31.3892, 'lon': 120.5123, 'type': 'attraction', 'city': '苏州', 'address': '苏州市高新区通安镇', 'ticket_price': 60.0, 'average_visit_time': 3.0},
        ]
        
        # 厦门景点
        xiamen_pois = [
            {
                'id': 'xiamen_001',
                'name': '鼓浪屿',
                'lat': 24.4469,
                'lon': 118.0648,
                'type': 'attraction',
                'city': '厦门',
                'address': '厦门市思明区鼓浪屿',
                'ticket_price': 100.0,
                'average_visit_time': 4.0
            },
            {
                'id': 'xiamen_002',
                'name': '南普陀寺',
                'lat': 24.4411,
                'lon': 118.0883,
                'type': 'attraction',
                'city': '厦门',
                'address': '厦门市思明区思明南路515号',
                'ticket_price': 0.0,
                'average_visit_time': 1.5
            },
            {
                'id': 'xiamen_003',
                'name': '中山路步行街',
                'lat': 24.4486,
                'lon': 118.0829,
                'type': 'shopping',
                'city': '厦门',
                'address': '厦门市思明区中山路',
                'ticket_price': 0.0,
                'average_visit_time': 2.0
            }
        ]
        
        # 保存数据
        all_pois = suzhou_pois + xiamen_pois
        for poi_data in all_pois:
            location = Location(
                id=poi_data['id'],
                name=poi_data['name'],
                lat=poi_data['lat'],
                lon=poi_data['lon'],
                type=POIType(poi_data['type']),
                address=poi_data.get('address', ''),
                ticket_price=poi_data.get('ticket_price', 0.0),
                average_visit_time=poi_data.get('average_visit_time', 2.0)
            )
            self.save_poi(location)
        
        print(f"✅ 初始化了 {len(all_pois)} 个Demo POI")
    
    def _load_pois(self) -> Dict[str, Dict]:
        """加载POI数据"""
        if os.path.exists(self.poi_file):
            try:
                with open(self.poi_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading POIs: {e}")
        return {}
    
    def _save_pois(self):
        """保存POI数据"""
        try:
            with open(self.poi_file, 'w', encoding='utf-8') as f:
                json.dump(self.pois, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving POIs: {e}")
    
    def _build_city_index(self):
        """构建城市索引"""
        self.city_index = {}
        for poi_id, poi_data in self.pois.items():
            city = poi_data.get('city', '')
            if city:
                if city not in self.city_index:
                    self.city_index[city] = []
                self.city_index[city].append(poi_id)
    
    def _dict_to_location(self, poi_data: Dict) -> Location:
        """字典转Location对象"""
        return Location(
            id=poi_data['id'],
            name=poi_data['name'],
            lat=poi_data['lat'],
            lon=poi_data['lon'],
            type=POIType(poi_data['type']),
            address=poi_data.get('address', ''),
            phone=poi_data.get('phone', ''),
            ticket_price=poi_data.get('ticket_price', 0.0),
            average_visit_time=poi_data.get('average_visit_time', 2.0)
        )
    
    def _location_to_dict(self, location: Location) -> Dict:
        """Location对象转字典"""
        return {
            'id': location.id,
            'name': location.name,
            'lat': location.lat,
            'lon': location.lon,
            'type': location.type.value,
            'address': location.address,
            'phone': location.phone,
            'ticket_price': location.ticket_price,
            'average_visit_time': location.average_visit_time,
            'city': self._extract_city_from_address(location.address)
        }
    
    def _extract_city_from_address(self, address: str) -> str:
        """从地址提取城市名"""
        # 简化实现
        cities = ['苏州', '厦门', '深圳', '杭州', '上海', '北京', '广州']
        for city in cities:
            if city in address:
                return city
        return ''
    
    def get_poi_count(self) -> int:
        """获取POI总数"""
        return len(self.pois)
