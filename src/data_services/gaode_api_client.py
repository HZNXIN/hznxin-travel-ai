"""
高德开放平台API客户端
封装高德地图API的调用
"""

import requests
from typing import List, Dict, Optional, Tuple
import hashlib
import time
from dataclasses import dataclass


@dataclass
class RouteResult:
    """路径结果"""
    distance: float  # 距离（米）
    duration: float  # 时间（秒）
    route: List[Tuple[float, float]]  # 路径坐标点
    strategy: str
    traffic_lights: int = 0
    tolls: float = 0.0


class GaodeAPIClient:
    """
    高德开放平台API客户端
    
    主要功能:
    1. 路径规划（步行、驾车、公交、骑行）
    2. POI搜索
    3. 地理编码/逆地理编码
    4. 天气查询
    5. 距离测量
    
    文档: https://lbs.amap.com/api/webservice/summary
    """
    
    def __init__(self, api_key: str, private_key: Optional[str] = None):
        """
        初始化API客户端
        
        Args:
            api_key: 高德开放平台API Key
            private_key: 私钥（用于签名，可选）
        """
        self.api_key = api_key
        self.private_key = private_key
        self.base_url = "https://restapi.amap.com/v3"
        self.base_url_v4 = "https://restapi.amap.com/v4"
        
        # 请求统计
        self.request_count = 0
        self.last_request_time = 0
        
        # 配置
        self.config = {
            'timeout': 10,  # 超时时间（秒）
            'max_retries': 3,  # 最大重试次数
            'rate_limit': 0.1  # 限流间隔（秒）
        }
    
    def get_route_walking(self,
                         origin: Tuple[float, float],
                         destination: Tuple[float, float]) -> Optional[RouteResult]:
        """
        步行路径规划
        
        API: /v3/direction/walking
        
        Args:
            origin: 起点 (lon, lat)
            destination: 终点 (lon, lat)
            
        Returns:
            路径结果
        """
        url = f"{self.base_url}/direction/walking"
        
        params = {
            'key': self.api_key,
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}"
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'route' in response:
                route_data = response['route']
                paths = route_data.get('paths', [])
                
                if paths:
                    path = paths[0]
                    
                    # 解析路径
                    route_coords = self._parse_route_coordinates(path)
                    
                    return RouteResult(
                        distance=float(path.get('distance', 0)),
                        duration=float(path.get('duration', 0)),
                        route=route_coords,
                        strategy='walking'
                    )
            
            return None
            
        except Exception as e:
            print(f"Error in get_route_walking: {e}")
            return None
    
    def get_route_driving(self,
                         origin: Tuple[float, float],
                         destination: Tuple[float, float],
                         strategy: int = 0) -> Optional[RouteResult]:
        """
        驾车路径规划
        
        API: /v3/direction/driving
        
        Args:
            origin: 起点 (lon, lat)
            destination: 终点 (lon, lat)
            strategy: 路径策略
                0: 速度优先（默认）
                1: 费用优先（避免收费）
                2: 距离优先
                3: 不走高速
                
        Returns:
            路径结果
        """
        url = f"{self.base_url}/direction/driving"
        
        params = {
            'key': self.api_key,
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'strategy': strategy,
            'extensions': 'all'  # 返回详细信息
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'route' in response:
                route_data = response['route']
                paths = route_data.get('paths', [])
                
                if paths:
                    path = paths[0]
                    
                    # 解析路径
                    route_coords = self._parse_route_coordinates(path)
                    
                    return RouteResult(
                        distance=float(path.get('distance', 0)),
                        duration=float(path.get('duration', 0)),
                        route=route_coords,
                        strategy=f"driving_{strategy}",
                        traffic_lights=int(path.get('traffic_lights', 0)),
                        tolls=float(path.get('tolls', 0))
                    )
            
            return None
            
        except Exception as e:
            print(f"Error in get_route_driving: {e}")
            return None
    
    def get_route_transit(self,
                         origin: Tuple[float, float],
                         destination: Tuple[float, float],
                         city: str,
                         strategy: int = 0) -> Optional[List[Dict]]:
        """
        公交路径规划
        
        API: /v3/direction/transit/integrated
        
        Args:
            origin: 起点 (lon, lat)
            destination: 终点 (lon, lat)
            city: 城市名称或citycode
            strategy: 路径策略
                0: 最快捷（默认）
                1: 最经济
                2: 最少换乘
                3: 最少步行
                
        Returns:
            公交方案列表
        """
        url = f"{self.base_url}/direction/transit/integrated"
        
        params = {
            'key': self.api_key,
            'origin': f"{origin[0]},{origin[1]}",
            'destination': f"{destination[0]},{destination[1]}",
            'city': city,
            'strategy': strategy
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'route' in response:
                route_data = response['route']
                transits = route_data.get('transits', [])
                
                results = []
                for transit in transits[:3]:  # 最多返回3个方案
                    results.append({
                        'distance': float(transit.get('distance', 0)),
                        'duration': float(transit.get('duration', 0)),
                        'walking_distance': float(transit.get('walking_distance', 0)),
                        'cost': float(transit.get('cost', 0)),
                        'segments': transit.get('segments', [])
                    })
                
                return results
            
            return None
            
        except Exception as e:
            print(f"Error in get_route_transit: {e}")
            return None
    
    def search_poi(self,
                  keywords: str,
                  city: str,
                  types: Optional[str] = None,
                  page: int = 1,
                  page_size: int = 20) -> Optional[List[Dict]]:
        """
        POI搜索
        
        API: /v3/place/text
        
        Args:
            keywords: 搜索关键词
            city: 城市名称或citycode
            types: POI类型（可选）
            page: 页码
            page_size: 每页数量
            
        Returns:
            POI列表
        """
        url = f"{self.base_url}/place/text"
        
        params = {
            'key': self.api_key,
            'keywords': keywords,
            'city': city,
            'page': page,
            'offset': page_size,
            'extensions': 'all'
        }
        
        if types:
            params['types'] = types
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'pois' in response:
                pois = response['pois']
                
                results = []
                for poi in pois:
                    location = poi.get('location', '').split(',')
                    
                    # 安全解析rating
                    rating = 0.0
                    biz_ext = poi.get('biz_ext', {})
                    if biz_ext and 'rating' in biz_ext:
                        try:
                            rating_val = biz_ext['rating']
                            if isinstance(rating_val, (int, float)):
                                rating = float(rating_val)
                            elif isinstance(rating_val, str) and rating_val:
                                rating = float(rating_val)
                        except:
                            rating = 0.0
                    
                    results.append({
                        'id': poi.get('id'),
                        'name': poi.get('name'),
                        'type': poi.get('type'),
                        'typecode': poi.get('typecode'),
                        'address': poi.get('address'),
                        'location': {
                            'lon': float(location[0]) if len(location) > 0 else 0,
                            'lat': float(location[1]) if len(location) > 1 else 0
                        },
                        'tel': poi.get('tel', ''),
                        'rating': rating,
                        'cost': poi.get('biz_ext', {}).get('cost', '') if biz_ext else ''
                    })
                
                return results
            
            return None
            
        except Exception as e:
            print(f"Error in search_poi: {e}")
            return None
    
    def search_poi_around(self,
                         location: Tuple[float, float],
                         keywords: str,
                         radius: int = 1000,
                         types: Optional[str] = None) -> Optional[List[Dict]]:
        """
        周边POI搜索
        
        API: /v3/place/around
        
        Args:
            location: 中心点 (lon, lat)
            keywords: 搜索关键词
            radius: 搜索半径（米）
            types: POI类型
            
        Returns:
            POI列表
        """
        url = f"{self.base_url}/place/around"
        
        params = {
            'key': self.api_key,
            'location': f"{location[0]},{location[1]}",
            'keywords': keywords,
            'radius': radius,
            'extensions': 'all'
        }
        
        if types:
            params['types'] = types
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'pois' in response:
                return self._parse_pois(response['pois'])
            
            return None
            
        except Exception as e:
            print(f"Error in search_poi_around: {e}")
            return None
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Tuple[float, float]]:
        """
        地理编码（地址 → 坐标）
        
        API: /v3/geocode/geo
        
        Args:
            address: 地址
            city: 城市（可选）
            
        Returns:
            坐标 (lon, lat)
        """
        url = f"{self.base_url}/geocode/geo"
        
        params = {
            'key': self.api_key,
            'address': address
        }
        
        if city:
            params['city'] = city
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'geocodes' in response:
                geocodes = response['geocodes']
                if geocodes:
                    location = geocodes[0].get('location', '').split(',')
                    if len(location) == 2:
                        return (float(location[0]), float(location[1]))
            
            return None
            
        except Exception as e:
            print(f"Error in geocode: {e}")
            return None
    
    def regeocode(self, location: Tuple[float, float]) -> Optional[Dict]:
        """
        逆地理编码（坐标 → 地址）
        
        API: /v3/geocode/regeo
        
        Args:
            location: 坐标 (lon, lat)
            
        Returns:
            地址信息
        """
        url = f"{self.base_url}/geocode/regeo"
        
        params = {
            'key': self.api_key,
            'location': f"{location[0]},{location[1]}",
            'extensions': 'all'
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'regeocode' in response:
                regeocode = response['regeocode']
                return {
                    'formatted_address': regeocode.get('formatted_address', ''),
                    'province': regeocode.get('addressComponent', {}).get('province', ''),
                    'city': regeocode.get('addressComponent', {}).get('city', ''),
                    'district': regeocode.get('addressComponent', {}).get('district', ''),
                    'pois': regeocode.get('pois', [])
                }
            
            return None
            
        except Exception as e:
            print(f"Error in regeocode: {e}")
            return None
    
    def get_weather(self, city: str) -> Optional[Dict]:
        """
        天气查询
        
        API: /v3/weather/weatherInfo
        
        Args:
            city: 城市名称或citycode
            
        Returns:
            天气信息
        """
        url = f"{self.base_url}/weather/weatherInfo"
        
        params = {
            'key': self.api_key,
            'city': city,
            'extensions': 'all'  # 获取未来3天预报
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'forecasts' in response:
                forecasts = response['forecasts']
                if forecasts:
                    forecast = forecasts[0]
                    return {
                        'city': forecast.get('city'),
                        'province': forecast.get('province'),
                        'reporttime': forecast.get('reporttime'),
                        'casts': forecast.get('casts', [])  # 未来天气
                    }
            
            return None
            
        except Exception as e:
            print(f"Error in get_weather: {e}")
            return None
    
    def get_distance(self,
                    origins: List[Tuple[float, float]],
                    destination: Tuple[float, float],
                    type_: int = 1) -> Optional[List[float]]:
        """
        距离测量
        
        API: /v3/distance
        
        Args:
            origins: 起点列表
            destination: 终点
            type_: 路径类型
                0: 直线距离
                1: 驾车距离（默认）
                3: 步行距离
                
        Returns:
            距离列表（米）
        """
        url = f"{self.base_url}/distance"
        
        origins_str = '|'.join([f"{o[0]},{o[1]}" for o in origins])
        
        params = {
            'key': self.api_key,
            'origins': origins_str,
            'destination': f"{destination[0]},{destination[1]}",
            'type': type_
        }
        
        try:
            response = self._make_request(url, params)
            
            if response['status'] == '1' and 'results' in response:
                results = response['results']
                return [float(r.get('distance', 0)) for r in results]
            
            return None
            
        except Exception as e:
            print(f"Error in get_distance: {e}")
            return None
    
    def _make_request(self, url: str, params: Dict) -> Dict:
        """
        发起HTTP请求
        
        包含:
        - 限流控制
        - 重试逻辑
        - 签名（如果有私钥）
        """
        # 限流
        self._rate_limit()
        
        # 签名（如果需要）
        if self.private_key:
            params = self._sign_params(params)
        
        # 发起请求
        for retry in range(self.config['max_retries']):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.config['timeout']
                )
                response.raise_for_status()
                
                self.request_count += 1
                return response.json()
                
            except requests.RequestException as e:
                if retry == self.config['max_retries'] - 1:
                    raise
                time.sleep(1 * (retry + 1))  # 指数退避
        
        return {}
    
    def _rate_limit(self):
        """限流控制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.config['rate_limit']:
            time.sleep(self.config['rate_limit'] - elapsed)
        
        self.last_request_time = time.time()
    
    def _sign_params(self, params: Dict) -> Dict:
        """参数签名（如果需要）"""
        # 排序参数
        sorted_params = sorted(params.items())
        
        # 拼接字符串
        param_str = '&'.join([f"{k}={v}" for k, v in sorted_params])
        param_str += self.private_key
        
        # MD5签名
        signature = hashlib.md5(param_str.encode()).hexdigest()
        
        params['sig'] = signature
        return params
    
    def _parse_route_coordinates(self, path: Dict) -> List[Tuple[float, float]]:
        """解析路径坐标"""
        coords = []
        
        steps = path.get('steps', [])
        for step in steps:
            polyline = step.get('polyline', '')
            if polyline:
                points = polyline.split(';')
                for point in points:
                    lon_lat = point.split(',')
                    if len(lon_lat) == 2:
                        coords.append((float(lon_lat[0]), float(lon_lat[1])))
        
        return coords
    
    def _parse_pois(self, pois: List[Dict]) -> List[Dict]:
        """解析POI列表"""
        results = []
        
        for poi in pois:
            location = poi.get('location', '').split(',')
            
            results.append({
                'id': poi.get('id'),
                'name': poi.get('name'),
                'type': poi.get('type'),
                'address': poi.get('address'),
                'location': {
                    'lon': float(location[0]) if len(location) > 0 else 0,
                    'lat': float(location[1]) if len(location) > 1 else 0
                },
                'tel': poi.get('tel', ''),
                'rating': float(poi.get('biz_ext', {}).get('rating', 0)) if poi.get('biz_ext') else 0
            })
        
        return results
    
    def get_route(self, 
                  origin: str, 
                  destination: str, 
                  mode: str = "walking") -> Optional[Dict]:
        """
        通用路径规划接口（用于API服务器）
        
        Args:
            origin: 起点 "lon,lat"
            destination: 终点 "lon,lat"
            mode: 出行方式 "walking"/"driving"/"transit"
            
        Returns:
            包含distance和duration的字典，如果失败返回None
        """
        try:
            # 解析坐标
            origin_parts = origin.split(',')
            dest_parts = destination.split(',')
            
            origin_tuple = (float(origin_parts[0]), float(origin_parts[1]))
            dest_tuple = (float(dest_parts[0]), float(dest_parts[1]))
            
            # 根据模式调用对应方法
            if mode == "walking":
                result = self.get_route_walking(origin_tuple, dest_tuple)
            elif mode == "driving":
                result = self.get_route_driving(origin_tuple, dest_tuple)
            else:
                result = self.get_route_walking(origin_tuple, dest_tuple)
            
            if result:
                return {
                    'distance': result.distance,  # 米
                    'duration': result.duration,  # 秒
                    'route': result.route
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error in get_route: {e}")
            return None
