"""
初始化POI数据库
添加一些测试用的POI数据
"""

from src.data_services.poi_database import POIDatabase

def main():
    print("🚀 开始初始化POI数据库...")
    
    # 创建数据库实例
    poi_db = POIDatabase()
    
    # 初始化Demo数据
    poi_db.initialize_demo_data()
    
    # 统计
    print(f"\n📊 数据库统计:")
    print(f"  总POI数: {len(poi_db.pois)}")
    
    # 按城市统计
    for city, poi_ids in poi_db.city_index.items():
        print(f"  {city}: {len(poi_ids)} 个POI")
    
    print(f"\n✅ POI数据库初始化完成！")
    print(f"数据文件: {poi_db.poi_file}")

if __name__ == "__main__":
    main()
