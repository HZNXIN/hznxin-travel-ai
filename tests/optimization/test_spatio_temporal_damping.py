"""
测试时空阻尼系数
验证城市功能区逻辑、上下班高峰逻辑、LBS热力图逻辑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.spatio_temporal_damping import SpatioTemporalDamping


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def test_damping_system():
    """测试时空阻尼系统"""
    
    print("\n🌆 " * 35)
    print("  时空阻尼系数测试 - 城市运行规律")
    print("🌆 " * 35)
    
    damping = SpatioTemporalDamping()
    
    # 1. 测试城市功能区逻辑
    print_section("1️⃣  城市功能区逻辑")
    
    test_zones = [
        ("工业园区", 18.0, "夜间工业区"),
        ("金鸡湖CBD", 18.0, "晚高峰CBD"),
        ("金鸡湖CBD", 14.0, "下午CBD"),
        ("观前街商业区", 20.0, "夜间商业区"),
    ]
    
    for zone, hour, desc in test_zones:
        result = damping.calculate_damping(
            from_zone="苏州站",
            to_zone=zone,
            current_hour=hour
        )
        
        color_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴'
        }.get(result.edge_color, '⚪')
        
        print(f"场景: {desc}")
        print(f"  目标: {zone}")
        print(f"  时间: {int(hour)}:00")
        print(f"  L_zone: {result.zone_factor:.2f}")
        print(f"  最终修正: {result.final_modifier:.2f}x")
        print(f"  边颜色: {result.edge_color} {color_emoji}")
        
        if result.reasons:
            print(f"  理由:")
            for reason in result.reasons:
                print(f"    • {reason}")
        
        if result.warnings:
            print(f"  警告:")
            for warning in result.warnings:
                print(f"    ⚠️  {warning}")
        
        print()
    
    # 2. 测试上下班高峰逻辑（潮汐效应）
    print_section("2️⃣  上下班高峰逻辑（潮汐效应）")
    
    rush_hour_tests = [
        # 早高峰
        ("居住区", "金鸡湖CBD", 8.5, "早高峰顺流进CBD"),
        ("金鸡湖CBD", "居住区", 8.5, "早高峰逆流出CBD"),
        # 晚高峰
        ("金鸡湖CBD", "居住区", 18.0, "晚高峰顺流出CBD"),
        ("居住区", "金鸡湖CBD", 18.0, "晚高峰逆流进CBD"),
        # 非高峰
        ("居住区", "金鸡湖CBD", 14.0, "下午时段"),
    ]
    
    print("场景                          | L_flow | 心情值 | 说明")
    print("-" * 70)
    
    for from_z, to_z, hour, desc in rush_hour_tests:
        result = damping.calculate_damping(
            from_zone=from_z,
            to_zone=to_z,
            current_hour=hour
        )
        
        # 心情值需要从flow_factor获取（这里简化显示）
        mood = "😊" if result.flow_factor <= 1.0 else "😣"
        
        print(f"{desc:<30} | {result.flow_factor:>6.2f} | {mood:^6} | ", end="")
        if result.reasons:
            flow_reasons = [r for r in result.reasons if '流' in r]
            if flow_reasons:
                print(flow_reasons[0])
            else:
                print("正常")
        else:
            print("正常")
    
    print()
    
    # 3. 测试LBS热力图逻辑
    print_section("3️⃣  LBS热力图逻辑（区域活力）")
    
    activity_tests = [
        (5, "鬼城（可能闭馆）"),
        (30, "人气偏低"),
        (150, "适中"),
        (400, "人气旺盛"),
        (600, "人流密集（过载）"),
    ]
    
    for active_devices, desc in activity_tests:
        result = damping.calculate_damping(
            from_zone="苏州站",
            to_zone="某景区",
            current_hour=14.0,
            activity_data={'active_devices': active_devices}
        )
        
        print(f"LBS活跃设备数: {active_devices:>4} | L_activity: {result.activity_factor:.2f} | {desc}")
        
        if result.reasons:
            activity_reasons = [r for r in result.reasons if 'LBS' in r or '人气' in r or '人流' in r]
            if activity_reasons:
                print(f"  → {activity_reasons[0]}")
        
        if result.warnings and any('密集' in w for w in result.warnings):
            print(f"  ⚠️  {result.warnings[0]}")
        
        print()
    
    # 4. 综合场景测试
    print_section("4️⃣  综合场景演示")
    
    scenarios = [
        {
            'from': '居住区',
            'to': '工业园区',
            'hour': 19.0,
            'activity': 8,
            'desc': '晚上去工业区（极差场景）'
        },
        {
            'from': '居住区',
            'to': '观前街商业区',
            'hour': 20.0,
            'activity': 350,
            'desc': '晚上去商业街（极佳场景）'
        },
        {
            'from': '居住区',
            'to': '金鸡湖CBD',
            'hour': 18.0,
            'activity': 200,
            'desc': '晚高峰去CBD（拥堵熔断）'
        },
        {
            'from': '金鸡湖CBD',
            'to': '居住区',
            'hour': 8.5,
            'activity': 150,
            'desc': '早高峰逆流（畅通无阻）'
        },
    ]
    
    for scenario in scenarios:
        result = damping.calculate_damping(
            from_zone=scenario['from'],
            to_zone=scenario['to'],
            current_hour=scenario['hour'],
            activity_data={'active_devices': scenario['activity']}
        )
        
        color_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴'
        }.get(result.edge_color, '⚪')
        
        print(f"{'='*70}")
        print(f"场景: {scenario['desc']}")
        print(f"{'='*70}")
        print(f"路径: {scenario['from']} → {scenario['to']}")
        print(f"时间: {int(scenario['hour'])}:00")
        print(f"LBS活跃: {scenario['activity']}台设备")
        print()
        print(f"综合结果:")
        print(f"  L_zone:     {result.zone_factor:.2f}")
        print(f"  L_flow:     {result.flow_factor:.2f}")
        print(f"  L_activity: {result.activity_factor:.2f}")
        print(f"  最终修正:    {result.final_modifier:.2f}x {color_emoji}")
        print()
        
        if result.reasons:
            print(f"分析:")
            for i, reason in enumerate(result.reasons, 1):
                print(f"  {i}. {reason}")
        
        if result.warnings:
            print(f"\n警告:")
            for warning in result.warnings:
                print(f"  🚨 {warning}")
        
        print()
    
    # 5. 机会卡片演示
    print_section("5️⃣  隐藏热点发现（机会卡片）")
    
    opportunity = damping.generate_opportunity_card(
        zone="平江路",
        activity_spike=4.5
    )
    
    if opportunity:
        print("🎁 发现机会！")
        print(f"  类型: {opportunity['type']}")
        print(f"  标题: {opportunity['title']}")
        print(f"  消息: {opportunity['message']}")
        print(f"  可能原因:")
        for sugg in opportunity['suggestions']:
            print(f"    • {sugg}")
        print(f"  建议: {opportunity['recommendation']}")
    
    print()
    
    # 总结
    print("="*70)
    print("  ✅ 时空阻尼系数测试完成")
    print("="*70)
    print()
    print("核心公式: Score_final = Score_base × L_zone × L_flow × L_activity")
    print()
    print("已实现:")
    print("  ✅ 1. 城市功能区逻辑（工业区/CBD/商业区）")
    print("  ✅ 2. 上下班高峰潮汐效应")
    print("  ✅ 3. LBS热力图活力分析")
    print("  ✅ 4. 拥堵熔断机制")
    print("  ✅ 5. 隐藏热点发现")
    print()
    print("🎯 城市运行规律精准建模！")
    print()


if __name__ == "__main__":
    test_damping_system()
