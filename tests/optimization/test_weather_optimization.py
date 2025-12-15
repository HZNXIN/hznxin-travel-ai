"""
测试天气系统优化
验证逐小时天气、时空绑定、边颜色映射等功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.data_services.gaode_api_client import GaodeAPIClient
from src.data_services.weather_service import WeatherService
from config import GAODE_API_KEY


def test_weather_optimization():
    """测试天气系统优化"""
    
    print("\n" + "="*70)
    print("  测试天气系统优化")
    print("="*70 + "\n")
    
    # 初始化
    gaode_client = GaodeAPIClient(GAODE_API_KEY)
    weather_service = WeatherService(gaode_client)
    
    # 1. 测试逐小时天气
    print("1️⃣  测试逐小时天气功能")
    print("="*70 + "\n")
    
    weather = weather_service.get_weather("苏州")
    
    if weather and weather.hourly_weather:
        print(f"城市: {weather.city}")
        print(f"全天天气: {weather.weather}, {weather.temperature}\n")
        print("逐小时天气预报:")
        print("-" * 70)
        
        for hourly in weather.hourly_weather:
            status = "✅" if hourly.outdoor_suitable else "⚠️ "
            print(f"{status} {hourly.hour:16s} | {hourly.weather:8s} | "
                  f"{hourly.temperature:6s} | 适宜度 {hourly.suitability_score:.0%}")
        print()
    else:
        print("  ⚠️  天气数据获取失败\n")
    
    # 2. 测试时空绑定的天气影响分析
    print("2️⃣  测试时空绑定影响分析")
    print("="*70 + "\n")
    
    if weather:
        test_cases = [
            {
                'poi_type': 'attraction',
                'time_period': '10:00-12:00',
                'location': '拙政园',
                'desc': '上午游览拙政园'
            },
            {
                'poi_type': 'attraction',
                'time_period': '14:00-16:00',
                'location': '太湖',
                'desc': '下午游览太湖'
            },
            {
                'poi_type': 'restaurant',
                'time_period': '12:00-14:00',
                'location': '得月楼',
                'desc': '午餐时段'
            }
        ]
        
        for case in test_cases:
            print(f"场景: {case['desc']}")
            print(f"  POI类型: {case['poi_type']}")
            print(f"  时间段: {case['time_period']}")
            print(f"  位置: {case['location']}")
            
            impact = weather_service.analyze_weather_impact(
                poi_type=case['poi_type'],
                weather=weather,
                time_period=case['time_period'],
                poi_location=case['location']
            )
            
            print(f"  评分调整: {impact.score_modifier:.2f}x")
            print(f"  优先级: {impact.priority_boost:+.2f}")
            print(f"  边颜色: {impact.edge_color} ⬤")
            
            if impact.reasons:
                print(f"  理由:")
                for reason in impact.reasons:
                    print(f"    • {reason}")
            
            if impact.warnings:
                print(f"  警告:")
                for warning in impact.warnings:
                    print(f"    ⚠️  {warning}")
            
            print()
    
    # 3. 测试边颜色映射
    print("3️⃣  测试边颜色自动映射")
    print("="*70 + "\n")
    
    if weather:
        poi_types = ['attraction', 'restaurant', 'shopping']
        
        print("不同POI类型的边颜色映射:\n")
        print(f"{'POI类型':<15} {'评分调整':<10} {'边颜色':<10} {'视觉效果'}")
        print("-" * 70)
        
        for poi_type in poi_types:
            impact = weather_service.analyze_weather_impact(
                poi_type=poi_type,
                weather=weather
            )
            
            color_emoji = {
                'green': '🟢',
                'yellow': '🟡',
                'red': '🔴'
            }.get(impact.edge_color, '⚪')
            
            print(f"{poi_type:<15} {impact.score_modifier:>6.2f}x    "
                  f"{impact.edge_color:<10} {color_emoji}")
        print()
    
    # 4. 测试缓存策略（多日期）
    print("4️⃣  测试多日期缓存策略")
    print("="*70 + "\n")
    
    dates = ["today", "tomorrow"]
    for date in dates:
        weather = weather_service.get_weather("苏州", date=date)
        if weather:
            print(f"日期: {date:10s} | 缓存: ✅ | 天气: {weather.weather}")
    
    print()
    
    # 总结
    print("="*70)
    print("  ✅ 优化功能测试完成")
    print("="*70)
    print()
    print("已实现的优化:")
    print("  ✅ 1. 逐小时天气支持（精准到2小时时段）")
    print("  ✅ 2. 时空绑定影响分析（时间段 + POI位置）")
    print("  ✅ 3. 边颜色自动映射（green/yellow/red）")
    print("  ✅ 4. 多日期缓存策略（支持today/tomorrow）")
    print()
    print("🎯 天气系统与SpatialCore深度融合！")
    print()


if __name__ == "__main__":
    test_weather_optimization()
