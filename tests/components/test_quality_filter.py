"""
测试POI质量过滤器
展示如何过滤低质量POI，只推荐真正有价值的地点
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.poi_quality_filter import POIQualityFilter, get_poi_quality_explanation
from src.core.models import Location, POIType, NodeVerification, DataSource
from datetime import datetime

def print_section(title):
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

def create_test_verification(review_count, rating, fake_rate=0.1):
    """创建测试验证数据"""
    return NodeVerification(
        data_sources=[
            DataSource('gaode', rating, review_count, datetime.now(), 0.4, 1.0),
            DataSource('ctrip', rating-0.1, int(review_count*0.8), datetime.now(), 0.35, 0.95),
            DataSource('mafengwo', rating+0.1, int(review_count*0.4), datetime.now(), 0.25, 0.90)
        ],
        consistency_score=0.95,
        weighted_rating=rating,
        rating_variance=0.04,
        total_reviews=review_count,
        valid_reviews=int(review_count * (1-fake_rate)),
        fake_rate=fake_rate,
        positive_rate=0.85,
        negative_rate=0.15,
        key_positive_words=['好玩', '值得', '推荐', '美', '有趣'],
        key_negative_words=['人多', '排队'],
        spatial_score=0.80,
        temporal_score=0.85
    )

def main():
    print_section("🔍 POI质量过滤器测试")
    
    quality_filter = POIQualityFilter()
    
    print("核心理念：不是所有POI都值得推荐！")
    print("只推荐具有可玩性、可观性、热度和历史性的优质地点\n")
    
    # 测试案例1: 优质景点 - 拙政园
    print_section("测试1: 优质景点 - 拙政园")
    
    poi1 = Location(
        id="poi_1",
        name="拙政园",
        lat=31.3229,
        lon=120.6309,
        type=POIType.ATTRACTION,
        address="苏州市姑苏区东北街178号",
        average_visit_time=2.5,  # 2.5小时，可玩性高
        ticket_price=70.0  # 有门票，历史景点
    )
    
    verification1 = create_test_verification(
        review_count=23456,  # 评论多
        rating=4.8,          # 评分高
        fake_rate=0.15       # 虚假率正常
    )
    
    quality1 = quality_filter.evaluate_quality(poi1, verification1)
    is_recommended1 = quality_filter.is_worth_recommending(poi1, verification1)
    
    print(f"POI: {poi1.name}")
    print(f"类型: {poi1.type.value}")
    print(f"游玩时长: {poi1.average_visit_time}小时")
    print(f"评论数: {verification1.valid_reviews:,}")
    print(f"评分: {verification1.weighted_rating}")
    print()
    print(f"质量评估:")
    print(f"  可玩性: {quality1.playability:.2f}")
    print(f"  可观性: {quality1.viewability:.2f}")
    print(f"  热度: {quality1.popularity:.2f}")
    print(f"  历史性: {quality1.history:.2f}")
    print(f"  综合质量: {quality1.overall:.2f}")
    print()
    print(f"是否推荐: {'✅ 是' if is_recommended1 else '❌ 否'}")
    if is_recommended1:
        print(f"推荐理由: {get_poi_quality_explanation(quality1)}")
    
    # 测试案例2: 路边小店 - 评论少
    print_section("测试2: 路边小店 - 评论太少")
    
    poi2 = Location(
        id="poi_2",
        name="某路边小餐馆",
        lat=31.32,
        lon=120.63,
        type=POIType.RESTAURANT,
        address="某某路123号",
        average_visit_time=0.8,  # 吃个饭而已
        ticket_price=0.0
    )
    
    verification2 = create_test_verification(
        review_count=25,  # 评论少！
        rating=4.3,
        fake_rate=0.1
    )
    
    quality2 = quality_filter.evaluate_quality(poi2, verification2)
    is_recommended2 = quality_filter.is_worth_recommending(poi2, verification2)
    
    print(f"POI: {poi2.name}")
    print(f"评论数: {verification2.valid_reviews}")
    print(f"评分: {verification2.weighted_rating}")
    print()
    print(f"质量评估:")
    print(f"  可玩性: {quality2.playability:.2f}")
    print(f"  综合质量: {quality2.overall:.2f}")
    print()
    print(f"是否推荐: {'✅ 是' if is_recommended2 else '❌ 否'}")
    if not is_recommended2:
        print(f"❌ 不推荐原因: 评论数太少（{verification2.valid_reviews} < 50），数据不足以判断质量")
    
    # 测试案例3: 差评场所
    print_section("测试3: 差评场所 - 评分低")
    
    poi3 = Location(
        id="poi_3",
        name="某差评景点",
        lat=31.32,
        lon=120.63,
        type=POIType.ATTRACTION,
        address="某某区",
        average_visit_time=1.5,
        ticket_price=50.0
    )
    
    verification3 = create_test_verification(
        review_count=5000,
        rating=3.5,  # 评分低！
        fake_rate=0.2
    )
    
    quality3 = quality_filter.evaluate_quality(poi3, verification3)
    is_recommended3 = quality_filter.is_worth_recommending(poi3, verification3)
    
    print(f"POI: {poi3.name}")
    print(f"评论数: {verification3.valid_reviews:,}")
    print(f"评分: {verification3.weighted_rating} ⭐")
    print()
    print(f"是否推荐: {'✅ 是' if is_recommended3 else '❌ 否'}")
    if not is_recommended3:
        print(f"❌ 不推荐原因: 评分太低（{verification3.weighted_rating} < 4.0），用户体验差")
    
    # 测试案例4: 路过点 - 可玩性低
    print_section("测试4: 路过点 - 可玩性不足")
    
    poi4 = Location(
        id="poi_4",
        name="某公交站",
        lat=31.32,
        lon=120.63,
        type=POIType.TRANSPORT_HUB,
        address="某某路口",
        average_visit_time=0.1,  # 只是路过
        ticket_price=0.0
    )
    
    verification4 = create_test_verification(
        review_count=1000,
        rating=4.2,
        fake_rate=0.1
    )
    
    quality4 = quality_filter.evaluate_quality(poi4, verification4)
    is_recommended4 = quality_filter.is_worth_recommending(poi4, verification4)
    
    print(f"POI: {poi4.name}")
    print(f"类型: {poi4.type.value}")
    print(f"游玩时长: {poi4.average_visit_time}小时")
    print()
    print(f"质量评估:")
    print(f"  可玩性: {quality4.playability:.2f}")
    print(f"  综合质量: {quality4.overall:.2f}")
    print()
    print(f"是否推荐: {'✅ 是' if is_recommended4 else '❌ 否'}")
    if not is_recommended4:
        print(f"❌ 不推荐原因: 可玩性不足（{quality4.playability:.2f} < 0.3），只是交通枢纽")
    
    # 测试案例5: 优质餐厅
    print_section("测试5: 优质餐厅 - 得月楼")
    
    poi5 = Location(
        id="poi_5",
        name="得月楼",
        lat=31.3226,
        lon=120.6302,
        type=POIType.RESTAURANT,
        address="苏州市姑苏区太监弄27号",
        average_visit_time=1.5,
        ticket_price=0.0
    )
    
    verification5 = create_test_verification(
        review_count=8500,  # 评论多
        rating=4.6,         # 评分高
        fake_rate=0.12
    )
    verification5.key_positive_words = ['地道', '苏帮菜', '环境好', '推荐', '美']
    
    quality5 = quality_filter.evaluate_quality(poi5, verification5)
    is_recommended5 = quality_filter.is_worth_recommending(poi5, verification5)
    
    print(f"POI: {poi5.name}")
    print(f"类型: {poi5.type.value}")
    print(f"评论数: {verification5.valid_reviews:,}")
    print(f"评分: {verification5.weighted_rating}")
    print()
    print(f"质量评估:")
    print(f"  可玩性: {quality5.playability:.2f}")
    print(f"  可观性: {quality5.viewability:.2f}")
    print(f"  热度: {quality5.popularity:.2f}")
    print(f"  综合质量: {quality5.overall:.2f}")
    print()
    print(f"是否推荐: {'✅ 是' if is_recommended5 else '❌ 否'}")
    if is_recommended5:
        print(f"推荐理由: {get_poi_quality_explanation(quality5)}")
    
    # 总结
    print_section("📊 测试总结")
    
    test_results = [
        (poi1.name, is_recommended1, "优质景点，各项指标优秀"),
        (poi2.name, is_recommended2, "评论太少，数据不足"),
        (poi3.name, is_recommended3, "评分太低，体验差"),
        (poi4.name, is_recommended4, "可玩性不足，只是路过点"),
        (poi5.name, is_recommended5, "优质餐厅，评论多评分高")
    ]
    
    passed = sum(1 for _, rec, _ in test_results if rec)
    
    print(f"测试结果: {passed}/5 个POI通过质量检查\n")
    
    for name, recommended, reason in test_results:
        status = "✅ 推荐" if recommended else "❌ 过滤"
        print(f"{status} - {name}: {reason}")
    
    print_section("✨ 核心价值")
    
    print("通过质量过滤，系统确保：")
    print()
    print("1️⃣  不推荐评论少的小店")
    print("   - 避免数据不足导致误判")
    print("   - 最低评论数：50条")
    print()
    print("2️⃣  不推荐差评场所")
    print("   - 避免推荐体验差的地方")
    print("   - 最低评分：4.0/5.0")
    print()
    print("3️⃣  不推荐可玩性低的地点")
    print("   - 不推荐只是路过的地方")
    print("   - 最低可玩性：0.3")
    print()
    print("4️⃣  综合评估多个维度")
    print("   - 可玩性：游玩时长、活动丰富度")
    print("   - 可观性：景观价值、拍照价值")
    print("   - 热度：评论数、评分")
    print("   - 历史性：文化价值、历史底蕴")
    print()
    print("🎯 结果: 只推荐真正值得去的优质POI！")
    print()

if __name__ == "__main__":
    main()
