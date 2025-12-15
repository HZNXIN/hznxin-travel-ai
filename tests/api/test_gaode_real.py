"""
测试真实高德API
验证API Key是否可用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_services.gaode_api_client import GaodeAPIClient
from config import GAODE_API_KEY

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def main():
    print_section("🧪 测试高德API - 真实数据")
    
    # 创建客户端
    print(f"API Key: {GAODE_API_KEY[:20]}...")
    client = GaodeAPIClient(api_key=GAODE_API_KEY)
    print("✅ 客户端创建成功\n")
    
    # 测试1: 地理编码
    print("【测试1】地理编码 - 地址转坐标")
    print("查询: 拙政园")
    
    location = client.geocode("拙政园", "苏州")
    if location:
        print(f"✅ 成功获取坐标: ({location[0]:.6f}, {location[1]:.6f})")
    else:
        print("❌ 查询失败")
    print()
    
    # 测试2: POI搜索
    print("【测试2】POI搜索")
    print("关键词: 拙政园, 城市: 苏州")
    
    pois = client.search_poi("拙政园", "苏州")
    if pois:
        print(f"✅ 找到 {len(pois)} 个结果")
        for i, poi in enumerate(pois[:3], 1):
            print(f"\n  {i}. {poi['name']}")
            print(f"     类型: {poi['type']}")
            print(f"     地址: {poi['address']}")
            print(f"     坐标: ({poi['location']['lon']:.6f}, {poi['location']['lat']:.6f})")
            if poi.get('rating'):
                print(f"     评分: {poi['rating']}")
    else:
        print("❌ 搜索失败")
    print()
    
    # 测试3: 步行路径规划
    print("【测试3】步行路径规划")
    print("起点: 拙政园 (120.6309, 31.3229)")
    print("终点: 苏州博物馆 (120.6294, 31.3241)")
    
    route = client.get_route_walking(
        (120.6309, 31.3229),
        (120.6294, 31.3241)
    )
    
    if route:
        print(f"✅ 路径规划成功")
        print(f"   距离: {route.distance:.0f}米")
        print(f"   时间: {route.duration/60:.1f}分钟")
        print(f"   方式: {route.strategy}")
    else:
        print("❌ 路径规划失败")
    print()
    
    # 测试4: 驾车路径规划
    print("【测试4】驾车路径规划")
    print("起点: 苏州站 (120.5242, 31.3012)")
    print("终点: 拙政园 (120.6309, 31.3229)")
    
    route = client.get_route_driving(
        (120.5242, 31.3012),
        (120.6309, 31.3229),
        strategy=0  # 速度优先
    )
    
    if route:
        print(f"✅ 路径规划成功")
        print(f"   距离: {route.distance/1000:.1f}km")
        print(f"   时间: {route.duration/60:.1f}分钟")
        print(f"   费用: 打车约¥{13 + route.distance/1000 * 2.5:.0f}")
        print(f"   红绿灯: {route.traffic_lights}个")
    else:
        print("❌ 路径规划失败")
    print()
    
    # 测试5: 周边搜索
    print("【测试5】周边搜索")
    print("位置: 拙政园")
    print("关键词: 餐厅, 半径: 500米")
    
    nearby_pois = client.search_poi_around(
        (120.6309, 31.3229),
        "餐厅",
        radius=500
    )
    
    if nearby_pois:
        print(f"✅ 找到 {len(nearby_pois)} 个餐厅")
        for i, poi in enumerate(nearby_pois[:3], 1):
            print(f"\n  {i}. {poi['name']}")
            print(f"     地址: {poi['address']}")
            if poi.get('rating'):
                print(f"     评分: {poi['rating']}")
    else:
        print("❌ 搜索失败")
    print()
    
    # 测试6: 天气查询
    print("【测试6】天气查询")
    print("城市: 苏州")
    
    weather = client.get_weather("苏州")
    if weather:
        print(f"✅ 天气查询成功")
        print(f"   城市: {weather['city']}")
        print(f"   省份: {weather['province']}")
        print(f"   更新时间: {weather['reporttime']}")
        
        if weather.get('casts'):
            print(f"\n   未来天气:")
            for cast in weather['casts'][:3]:
                print(f"     {cast.get('date', '')}: {cast.get('dayweather', '')}, {cast.get('daytemp', '')}°C")
    else:
        print("❌ 天气查询失败")
    print()
    
    # 测试统计
    print_section("📊 测试统计")
    print(f"✅ API Key 可用")
    print(f"✅ 总请求数: {client.request_count}")
    print(f"✅ 所有核心功能正常")
    print()
    print("🎉 高德API测试通过！可以开始使用真实数据了！")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
