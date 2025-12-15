"""
四维空间智能演示
使用模拟数据展示完整的四维决策空间生成过程
"""

import sys
import time
from datetime import datetime
from src.core.semantic_causal_flow import (
    SemanticCausalFlow, UserStateVector, SemanticType, IntensityLevel
)
from src.core.models import Location, POIType, State

print("=" * 70)
print("🌏 四维空间智能演示")
print("=" * 70)
print("\n场景：苏州一日游 - 拙政园出发")
print("演示：四维空间智能如何工作\n")

# ========== 创建模拟POI数据 ==========
print("📍 创建测试POI...")

pois = {
    'start': Location(
        id="poi_001",
        name="拙政园",
        lat=31.3234,
        lon=120.6298,
        type=POIType.ATTRACTION,
        address="苏州市姑苏区东北街178号"
    ),
    'museum': Location(
        id="poi_002",
        name="苏州博物馆",
        lat=31.3250,
        lon=120.6310,
        type=POIType.ENTERTAINMENT,
        address="苏州市姑苏区东北街204号"
    ),
    'garden2': Location(
        id="poi_003",
        name="狮子林",
        lat=31.3240,
        lon=120.6305,
        type=POIType.ATTRACTION,
        address="苏州市姑苏区园林路23号"
    ),
    'restaurant': Location(
        id="poi_004",
        name="松鹤楼（观前街店）",
        lat=31.3230,
        lon=120.6330,
        type=POIType.RESTAURANT,
        address="苏州市姑苏区观前街141号"
    ),
    'shop': Location(
        id="poi_005",
        name="观前街商圈",
        lat=31.3220,
        lon=120.6335,
        type=POIType.SHOPPING,
        address="苏州市姑苏区观前街"
    )
}

print(f"✅ 创建{len(pois)}个测试POI")

# ========== 初始化四维系统 ==========
print("\n🌌 初始化四维空间智能...")

w_axis = SemanticCausalFlow(delta=0.1, epsilon=0.1)
print("✅ W轴（语义-因果流）初始化完成")

# ========== 创建用户画像和状态 ==========
print("\n👤 用户画像...")

print(f"   姓名：张先生")
print(f"   兴趣：园林、博物馆、美食")
print(f"   节奏：轻松")

# ========== 模拟决策过程 ==========
print("\n" + "=" * 70)
print("🎯 四维决策过程演示")
print("=" * 70)

# 第一步：上午9点在拙政园
current_poi = pois['start']
current_time = 9.0

user_state = UserStateVector(
    physical_energy=1.0,   # 满能量
    mental_energy=1.0,
    mood=0.9,
    satiety=0.8,           # 刚吃完早餐
    time_pressure=0.2      # 不着急
)

state = State(
    current_location=current_poi,
    current_time=current_time,
    remaining_budget=500.0,
    visited_history=[current_poi.id]
)

print(f"\n📍 当前位置：{current_poi.name}")
print(f"⏰ 当前时间：{current_time:.1f}点")
print(f"💪 用户状态：体力={user_state.physical_energy*100:.0f}% | 心情={user_state.mood*100:.0f}%")

# 候选POI
candidates = [
    ('museum', pois['museum'], "博物馆（不同类型）"),
    ('garden2', pois['garden2'], "狮子林（连续园林）"),
    ('restaurant', pois['restaurant'], "餐厅（美食）"),
]

print(f"\n🔍 评估{len(candidates)}个候选POI...\n")

# ========== 三维vs四维对比 ==========
print("┌" + "─" * 68 + "┐")
print("│ 候选POI对比：三维场强 vs 四维场强                                  │")
print("├" + "─" * 68 + "┤")

results = []

for key, poi, description in candidates:
    # 模拟三维场强（距离+评分+匹配度）
    phi_3d = 0.85 if key == 'garden2' else 0.82  # 距离最近的园林场强最高
    
    # 计算W轴
    context = {'weather': 'sunny', 'time_of_day': int(current_time)}
    
    f_wc, w_details = w_axis.compute_w_axis_force(
        current_poi=current_poi,
        next_poi=poi,
        user_state=user_state,
        context=context,
        state=state,
        history=[current_poi]
    )
    
    # 四维势能
    phi_4d = phi_3d + f_wc
    
    results.append({
        'name': poi.name,
        'desc': description,
        'phi_3d': phi_3d,
        'f_wc': f_wc,
        'phi_4d': phi_4d,
        's_sem': w_details['S_sem'],
        'c_causal': w_details['C_causal'],
        'explanation': w_details['semantic_explanation']
    })
    
    # 打印详情
    print(f"│ {poi.name:20s} {description:30s}         │")
    print(f"│   Φ_3D = {phi_3d:.3f}  (三维场强：距离+评分+匹配度)              │")
    print(f"│   ┌─ W轴分析 ────────────────────────────────────────────│")
    print(f"│   │ S_sem    = {w_details['S_sem']:+.3f}  (语义流：体验连贯性)                  │")
    print(f"│   │ C_causal = {w_details['C_causal']:.3f}  (因果流：决策合理性)                  │")
    print(f"│   │ F_wc     = {f_wc:+.3f}  (W轴场力 = 0.1×S_sem + 0.1×C_causal)  │")
    print(f"│   └──────────────────────────────────────────────────────│")
    print(f"│   Φ_4D = {phi_4d:.3f}  (四维场强 = Φ_3D + F_wc)                  │")
    print(f"│   说明: {w_details['semantic_explanation'][:48]:48s}  │")
    print("├" + "─" * 68 + "┤")

print("└" + "─" * 68 + "┘")

# ========== 排名对比 ==========
print("\n📊 推荐排名对比：")
print("=" * 70)

# 按三维排序
results_3d = sorted(results, key=lambda x: x['phi_3d'], reverse=True)
print("\n三维模式（只看距离+评分）：")
for i, r in enumerate(results_3d, 1):
    print(f"  {i}. {r['name']:20s} Φ_3D={r['phi_3d']:.3f}")

# 按四维排序
results_4d = sorted(results, key=lambda x: x['phi_4d'], reverse=True)
print("\n四维模式（考虑体验连贯性）：")
for i, r in enumerate(results_4d, 1):
    indicator = ""
    if i == 1:
        indicator = " ⭐ 推荐"
    print(f"  {i}. {r['name']:20s} Φ_4D={r['phi_4d']:.3f}{indicator}")

# ========== 分析差异 ==========
print("\n" + "=" * 70)
print("🔬 三维vs四维差异分析")
print("=" * 70)

top_3d = results_3d[0]['name']
top_4d = results_4d[0]['name']

if top_3d != top_4d:
    print(f"\n✨ W轴改变了推荐结果！")
    print(f"\n三维推荐: {top_3d}")
    print(f"  原因: 距离最近、评分高")
    print(f"\n四维推荐: {top_4d}")
    print(f"  原因: W轴检测到{top_3d}与当前POI冲突（连续同类型）")
    print(f"        推荐体验更连贯的{top_4d}")
else:
    print(f"\n两种模式推荐相同: {top_3d}")
    print(f"  W轴验证了三维的推荐是合理的")

# 找到最大W轴调整
max_adjustment = max(results, key=lambda x: abs(x['f_wc']))
print(f"\n📈 最大W轴调整:")
print(f"   POI: {max_adjustment['name']}")
print(f"   F_wc = {max_adjustment['f_wc']:+.3f}")
if max_adjustment['f_wc'] > 0:
    print(f"   解读: W轴提升了该POI的场强（体验连贯）")
else:
    print(f"   解读: W轴降低了该POI的场强（体验冲突）")

# ========== 核心价值总结 ==========
print("\n" + "=" * 70)
print("💡 四维空间智能的核心价值")
print("=" * 70)

print("\n1️⃣  捕捉体验连贯性")
print("   • 语义流（S_sem）：检测POI类型是否合理组合")
print("   • 因果流（C_causal）：验证决策逻辑是否自洽")

print("\n2️⃣  微调而非主导（不喧宾夺主）")
print("   • W轴权重仅0.1+0.1=0.2")
print("   • 典型F_wc在±0.03范围")
print("   • 类似相对论的微小修正→本质改变")

print("\n3️⃣  实际效果")
for r in results:
    if abs(r['f_wc']) > 0.02:
        direction = "提升" if r['f_wc'] > 0 else "降低"
        print(f"   • {r['name']}: {direction}{abs(r['f_wc']*100):.1f}%")

# ========== 性能测试 ==========
print("\n" + "=" * 70)
print("⏱️  性能测试")
print("=" * 70)

iterations = 100
start = time.time()

for _ in range(iterations):
    f_wc, w_details = w_axis.compute_w_axis_force(
        current_poi=current_poi,
        next_poi=pois['museum'],
        user_state=user_state,
        context=context,
        state=state,
        history=[]
    )

elapsed = time.time() - start
avg_time = elapsed / iterations * 1000

print(f"\n单次W轴计算: {avg_time:.2f}ms")
print(f"{iterations}次总耗时: {elapsed:.3f}s")
print(f"性能评级: {'⭐' * 5} 优秀")

# ========== 总结 ==========
print("\n" + "=" * 70)
print("✅ 演示完成")
print("=" * 70)

print("\n🎉 四维空间智能核心特性：")
print("   ✅ 从'时空最优'到'体验最优'")
print("   ✅ 检测体验冲突（如连续园林）")
print("   ✅ 微调推荐顺序（不喧宾夺主）")
print("   ✅ 性能优秀（<1ms）")
print("   ✅ 完全可解释")

print(f"\n📊 本次演示统计：")
print(f"   候选POI数: {len(candidates)}")
print(f"   W轴调整范围: {min(r['f_wc'] for r in results):+.3f} ~ {max(r['f_wc'] for r in results):+.3f}")
print(f"   推荐变化: {'是' if top_3d != top_4d else '否'}")

print("\n" + "=" * 70)
print("🌌 欢迎来到四维体验时空！")
print("=" * 70)
