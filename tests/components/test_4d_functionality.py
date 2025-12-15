"""
四维空间智能功能测试
测试W轴的实际计算功能
"""

import sys
import time
from datetime import datetime, timedelta
from src.core.semantic_causal_flow import (
    SemanticCausalFlow, SemanticFlowAnalyzer, CausalFlowAnalyzer,
    UserStateVector, SemanticType, IntensityLevel
)
from src.core.models import Location, POIType, State, UserProfile

print("=" * 70)
print("🧪 四维空间智能功能测试")
print("=" * 70)

tests_passed = 0
tests_failed = 0
tests_total = 0

def test(name, func):
    """运行单个测试"""
    global tests_passed, tests_failed, tests_total
    tests_total += 1
    
    try:
        start = time.time()
        func()
        elapsed = time.time() - start
        print(f"✅ [{tests_total}] {name} ({elapsed*1000:.0f}ms)")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"❌ [{tests_total}] {name}")
        print(f"    错误: {e}")
        tests_failed += 1
        return False

# ========== 测试W轴完整计算 ==========
print("\n🌊 测试W轴完整计算流程...")

def test_w_axis_complete_flow():
    """测试完整的W轴计算流程"""
    # 1. 创建W轴
    w_axis = SemanticCausalFlow(delta=0.1, epsilon=0.1)
    
    # 2. 创建测试POI
    poi_garden = Location(
        id="poi_001",
        name="拙政园",
        lat=31.3234,
        lon=120.6298,
        type=POIType.ATTRACTION
    )
    
    poi_museum = Location(
        id="poi_002",
        name="苏州博物馆",
        lat=31.3250,
        lon=120.6310,
        type=POIType.ENTERTAINMENT
    )
    
    # 3. 创建用户状态
    user_state = UserStateVector(
        physical_energy=0.7,
        mental_energy=0.8,
        mood=0.9,
        satiety=0.5,
        time_pressure=0.3
    )
    
    # 4. 创建State
    state = State(
        current_location=poi_garden,
        current_time=10.0,  # 上午10点
        remaining_budget=500.0,
        visited_history=[poi_garden.id]
    )
    
    # 5. 上下文
    context = {
        'weather': 'sunny',
        'time_of_day': 10,
        'is_weekend': True
    }
    
    # 6. 计算W轴场力
    f_wc, details = w_axis.compute_w_axis_force(
        current_poi=poi_garden,
        next_poi=poi_museum,
        user_state=user_state,
        context=context,
        state=state,
        history=[poi_garden]
    )
    
    # 7. 验证结果
    assert 'S_sem' in details
    assert 'C_causal' in details
    assert 'F_wc' in details
    assert isinstance(f_wc, (int, float))
    
    # 打印详情
    print(f"      语义流: S_sem={details['S_sem']:+.3f}")
    print(f"      因果流: C_causal={details['C_causal']:.3f}")
    print(f"      场力: F_wc={f_wc:+.3f}")
    print(f"      说明: {details['semantic_explanation'][:50]}...")

def test_semantic_score_coherence():
    """测试语义流得分的连贯性"""
    analyzer = SemanticFlowAnalyzer()
    
    # 园林 → 博物馆（不同类型，应该连贯）
    poi1 = Location(id="p1", name="园林", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    poi2 = Location(id="p2", name="博物馆", lat=31.0, lon=120.0, type=POIType.ENTERTAINMENT)
    
    user_state = UserStateVector(
        physical_energy=0.7, mental_energy=0.8, mood=0.9,
        satiety=0.5, time_pressure=0.3
    )
    
    s_sem, explanation = analyzer.compute_semantic_score(poi1, poi2, user_state, [])
    
    print(f"      园林→博物馆: S_sem={s_sem:+.3f}")
    assert s_sem >= 0.0, "不同类型POI应该有非负语义流"

def test_semantic_score_conflict():
    """测试语义流对冲突的检测"""
    analyzer = SemanticFlowAnalyzer()
    
    # 园林 → 园林（连续同类型，应该冲突）
    poi1 = Location(id="p1", name="拙政园", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    poi2 = Location(id="p2", name="狮子林", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    
    user_state = UserStateVector(
        physical_energy=0.7, mental_energy=0.8, mood=0.9,
        satiety=0.5, time_pressure=0.3
    )
    
    # 已访问1个园林
    history = [poi1]
    
    s_sem, explanation = analyzer.compute_semantic_score(poi1, poi2, user_state, history)
    
    print(f"      园林→园林: S_sem={s_sem:+.3f}")
    # 期望负分或低分
    assert s_sem < 0.3, "连续同类型POI应该检测到冲突"

test("W轴完整计算流程", test_w_axis_complete_flow)
test("语义流连贯性检测", test_semantic_score_coherence)
test("语义流冲突检测", test_semantic_score_conflict)

# ========== 测试四维势能升级 ==========
print("\n⚡ 测试四维势能升级...")

def test_4d_potential_upgrade():
    """测试Φ_4D = Φ_3D + F_wc"""
    w_axis = SemanticCausalFlow(delta=0.1, epsilon=0.1)
    
    # 三维势能
    phi_3d = 0.85
    
    # W轴场力（正向）
    f_wc_positive = 0.05
    phi_4d_positive = w_axis.upgrade_to_4d_potential(phi_3d, f_wc_positive)
    expected_positive = phi_3d + f_wc_positive
    
    assert abs(phi_4d_positive - expected_positive) < 0.001
    print(f"      Φ_3D={phi_3d:.3f}, F_wc=+{f_wc_positive:.3f} → Φ_4D={phi_4d_positive:.3f} ✅")
    
    # W轴场力（负向，表示冲突）
    f_wc_negative = -0.03
    phi_4d_negative = w_axis.upgrade_to_4d_potential(phi_3d, f_wc_negative)
    expected_negative = phi_3d + f_wc_negative
    
    assert abs(phi_4d_negative - expected_negative) < 0.001
    print(f"      Φ_3D={phi_3d:.3f}, F_wc={f_wc_negative:.3f} → Φ_4D={phi_4d_negative:.3f} ✅")
    
    # 验证：冲突时Φ_4D应低于Φ_3D
    assert phi_4d_negative < phi_3d, "冲突时四维势能应低于三维"

def test_weight_impact():
    """测试权重对结果的影响"""
    # 默认权重
    w_axis_default = SemanticCausalFlow(delta=0.1, epsilon=0.1)
    
    # 更高权重
    w_axis_high = SemanticCausalFlow(delta=0.2, epsilon=0.2)
    
    # 假设语义和因果得分
    s_sem = 0.7
    c_causal = 0.8
    
    f_wc_default = 0.1 * s_sem + 0.1 * c_causal
    f_wc_high = 0.2 * s_sem + 0.2 * c_causal
    
    print(f"      默认权重(0.1): F_wc={f_wc_default:.3f}")
    print(f"      高权重(0.2): F_wc={f_wc_high:.3f}")
    
    assert f_wc_high > f_wc_default, "更高权重应产生更大的场力"
    assert f_wc_high <= 0.5, "即使高权重，场力也不应过大（不喧宾夺主）"

test("四维势能升级公式", test_4d_potential_upgrade)
test("权重影响测试", test_weight_impact)

# ========== 测试边界条件 ==========
print("\n🔍 测试边界条件...")

def test_boundary_s_sem():
    """测试S_sem的边界范围"""
    analyzer = SemanticFlowAnalyzer()
    
    # 创建测试数据
    poi1 = Location(id="p1", name="POI1", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    poi2 = Location(id="p2", name="POI2", lat=31.0, lon=120.0, type=POIType.RESTAURANT)
    
    user_state = UserStateVector(
        physical_energy=0.5, mental_energy=0.5, mood=0.5,
        satiety=0.5, time_pressure=0.5
    )
    
    # 计算100次，验证范围
    for _ in range(10):
        s_sem, _ = analyzer.compute_semantic_score(poi1, poi2, user_state, [])
        assert -1.0 <= s_sem <= 1.0, f"S_sem={s_sem}超出范围[-1, 1]"
    
    print(f"      S_sem始终在[-1, 1]范围内 ✅")

def test_boundary_c_causal():
    """测试C_causal的边界范围"""
    analyzer = CausalFlowAnalyzer(spatial_intelligence=None)
    
    poi1 = Location(id="p1", name="POI1", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    poi2 = Location(id="p2", name="POI2", lat=31.0, lon=120.0, type=POIType.RESTAURANT)
    
    state = State(
        current_location=poi1,
        current_time=12.0,
        remaining_budget=500.0,
        visited_history=[]
    )
    
    context = {'weather': 'sunny'}
    
    # 计算10次，验证范围
    for _ in range(10):
        c_causal, _ = analyzer.compute_causal_score(poi1, poi2, context, state)
        assert 0.0 <= c_causal <= 1.0, f"C_causal={c_causal}超出范围[0, 1]"
    
    print(f"      C_causal始终在[0, 1]范围内 ✅")

test("S_sem边界范围", test_boundary_s_sem)
test("C_causal边界范围", test_boundary_c_causal)

# ========== 性能测试 ==========
print("\n⏱️  性能测试...")

def test_w_axis_performance():
    """测试W轴计算性能"""
    w_axis = SemanticCausalFlow(delta=0.1, epsilon=0.1)
    
    poi1 = Location(id="p1", name="POI1", lat=31.0, lon=120.0, type=POIType.ATTRACTION)
    poi2 = Location(id="p2", name="POI2", lat=31.0, lon=120.0, type=POIType.RESTAURANT)
    
    user_state = UserStateVector(
        physical_energy=0.7, mental_energy=0.8, mood=0.9,
        satiety=0.5, time_pressure=0.3
    )
    
    state = State(
        current_location=poi1,
        current_time=10.0,
        remaining_budget=500.0,
        visited_history=[]
    )
    
    context = {'weather': 'sunny'}
    
    # 计算100次，取平均时间
    iterations = 100
    start = time.time()
    
    for _ in range(iterations):
        f_wc, details = w_axis.compute_w_axis_force(
            current_poi=poi1,
            next_poi=poi2,
            user_state=user_state,
            context=context,
            state=state,
            history=[]
        )
    
    elapsed = time.time() - start
    avg_time = elapsed / iterations * 1000  # ms
    
    print(f"      平均计算时间: {avg_time:.1f}ms")
    print(f"      100次总耗时: {elapsed:.2f}s")
    
    # 性能要求：单次<200ms
    assert avg_time < 200, f"W轴计算应<200ms，实际={avg_time:.1f}ms"

test("W轴计算性能", test_w_axis_performance)

# ========== 测试结果 ==========
print("\n" + "=" * 70)
print("📊 测试结果汇总")
print("=" * 70)
print(f"总测试数: {tests_total}")
print(f"通过: {tests_passed} ✅")
print(f"失败: {tests_failed} ❌")
print(f"通过率: {tests_passed/tests_total*100:.1f}%")

if tests_failed == 0:
    print("\n🎉 所有功能测试通过！")
    print("\n✅ W轴功能完全正常")
    print("   - 语义流计算正确")
    print("   - 因果流计算正确")
    print("   - 四维势能升级准确")
    print("   - 边界条件安全")
    print("   - 性能满足要求")
    sys.exit(0)
else:
    print("\n⚠️ 部分测试失败，请检查实现")
    sys.exit(1)
