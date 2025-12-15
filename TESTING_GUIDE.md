# 🧪 四维空间智能 - 测试指南
**完整的测试策略和验证方法**
**日期：2025-12-15**

---

## 🎯 **测试目标**

### **验证四维模式的有效性**
```
1. 功能正确性：四维势能计算准确
2. 性能达标：响应时间<5秒
3. 体验提升：用户满意度提高
4. 稳定性：零崩溃、优雅降级
```

---

## 📋 **测试清单**

### **1. 单元测试（Unit Tests）**

#### **测试W轴语义流分析**
```python
import unittest
from src.core.semantic_causal_flow import SemanticFlowAnalyzer, UserStateVector
from src.core.models import Location, POIType

class TestSemanticFlow(unittest.TestCase):
    """测试语义流分析器"""
    
    def setUp(self):
        self.analyzer = SemanticFlowAnalyzer()
        
        # 测试POI
        self.poi_garden = Location(
            id="poi_001",
            name="拙政园",
            type=POIType.SCENIC,
            lat=31.3234,
            lon=120.6298
        )
        
        self.poi_museum = Location(
            id="poi_002",
            name="苏州博物馆",
            type=POIType.MUSEUM,
            lat=31.3250,
            lon=120.6310
        )
        
        self.poi_garden2 = Location(
            id="poi_003",
            name="狮子林",
            type=POIType.SCENIC,
            lat=31.3240,
            lon=120.6305
        )
        
        # 用户状态
        self.user_state = UserStateVector(
            physical_energy=0.7,
            mental_energy=0.8,
            mood=0.9,
            satiety=0.5,
            time_pressure=0.3
        )
    
    def test_semantic_score_range(self):
        """测试语义流得分范围"""
        s_sem, _ = self.analyzer.compute_semantic_score(
            self.poi_garden,
            self.poi_museum,
            self.user_state,
            []
        )
        
        # S_sem ∈ [-1, 1]
        self.assertGreaterEqual(s_sem, -1.0)
        self.assertLessEqual(s_sem, 1.0)
    
    def test_garden_to_museum_positive(self):
        """测试：园林→博物馆，应为正分（体验转换）"""
        s_sem, explanation = self.analyzer.compute_semantic_score(
            self.poi_garden,
            self.poi_museum,
            self.user_state,
            []
        )
        
        # 期望正分（体验转换合理）
        self.assertGreater(s_sem, 0.3, 
            f"园林→博物馆应为正分，实际={s_sem:.2f}")
        self.assertIn("连贯", explanation.lower())
    
    def test_garden_to_garden_negative(self):
        """测试：园林→园林，应为负分（审美疲劳）"""
        s_sem, explanation = self.analyzer.compute_semantic_score(
            self.poi_garden,
            self.poi_garden2,
            self.user_state,
            []
        )
        
        # 期望负分或低分（连续同类型）
        self.assertLess(s_sem, 0.2,
            f"园林→园林应为低分，实际={s_sem:.2f}")
    
    def test_low_energy_adaptation(self):
        """测试：低体力时，高强度活动得分降低"""
        low_energy_state = UserStateVector(
            physical_energy=0.2,  # 低体力
            mental_energy=0.8,
            mood=0.7,
            satiety=0.5,
            time_pressure=0.3
        )
        
        # 创建高强度活动POI（假设）
        poi_intense = Location(
            id="poi_004",
            name="攀岩馆",
            type=POIType.SPORT,
            lat=31.3260,
            lon=120.6320
        )
        
        s_sem, _ = self.analyzer.compute_semantic_score(
            self.poi_garden,
            poi_intense,
            low_energy_state,
            []
        )
        
        # 期望低分（状态不适配）
        self.assertLess(s_sem, 0.5)

if __name__ == '__main__':
    unittest.main()
```

#### **测试W轴因果流分析**
```python
class TestCausalFlow(unittest.TestCase):
    """测试因果流分析器"""
    
    def setUp(self):
        self.analyzer = CausalFlowAnalyzer()
    
    def test_causal_score_range(self):
        """测试因果流得分范围"""
        c_causal, _ = self.analyzer.compute_causal_score(
            current_poi=self.poi_garden,
            next_poi=self.poi_museum,
            context={'weather': 'sunny'},
            state=mock_state
        )
        
        # C_causal ∈ [0, 1]
        self.assertGreaterEqual(c_causal, 0.0)
        self.assertLessEqual(c_causal, 1.0)
    
    def test_rain_indoor_causal(self):
        """测试：下雨→室内，因果得分高"""
        context = {'weather': 'rain'}
        
        c_causal, explanation = self.analyzer.compute_causal_score(
            current_poi=self.poi_garden,  # 室外
            next_poi=self.poi_museum,     # 室内
            context=context,
            state=mock_state
        )
        
        # 期望高分（因果合理）
        self.assertGreater(c_causal, 0.7)
        self.assertIn("室内", explanation)
```

#### **测试四维势能计算**
```python
class TestInfluenceField(unittest.TestCase):
    """测试影响力场"""
    
    def setUp(self):
        self.field = InfluenceField(
            planner=mock_planner,
            neural_service=mock_neural,
            enable_4d=True
        )
    
    def test_4d_upgrade(self):
        """测试：Φ_4D = Φ_3D + F_wc"""
        phi_4d, factors, w_details = self.field.compute_field(
            option=self.poi_museum,
            time_point=datetime.now(),
            state=mock_state,
            user_profile=mock_profile,
            current_poi=self.poi_garden,
            context={}
        )
        
        # 验证W轴已应用
        self.assertIsNotNone(w_details)
        self.assertIn('F_wc', w_details)
        
        # 重新计算Φ_3D
        phi_3d_factors = [f for f in factors if 'w_axis' not in f.source.lower()]
        phi_3d = sum(f.weighted_value for f in phi_3d_factors) / sum(f.weight for f in phi_3d_factors)
        
        f_wc = w_details['F_wc']
        expected_phi_4d = phi_3d + f_wc
        
        # 验证公式
        self.assertAlmostEqual(phi_4d, expected_phi_4d, places=3)
    
    def test_degradation_when_w_fails(self):
        """测试：W轴失败时降级到三维"""
        # 禁用W轴
        field_3d = InfluenceField(
            planner=mock_planner,
            neural_service=mock_neural,
            enable_4d=False
        )
        
        phi_3d, factors, w_details = field_3d.compute_field(
            option=self.poi_museum,
            time_point=datetime.now(),
            state=mock_state,
            user_profile=mock_profile,
            current_poi=self.poi_garden
        )
        
        # 验证W轴未应用
        self.assertIsNone(w_details)
        
        # Φ应该在[0, 1]范围内
        self.assertGreaterEqual(phi_3d, 0.0)
        self.assertLessEqual(phi_3d, 1.0)
```

---

### **2. 集成测试（Integration Tests）**

#### **测试完整决策空间生成**
```python
class TestThreeDimensionalPlan(unittest.TestCase):
    """测试四维决策空间生成"""
    
    def setUp(self):
        self.plan_4d = ThreeDimensionalPlan(
            progressive_planner=real_planner,
            neural_service=real_neural,
            enable_4d=True
        )
    
    def test_generate_full_space(self):
        """测试：生成完整决策空间"""
        timeline = self.plan_4d.generate_3d_space(
            session_id="test_session",
            initial_state=test_state,
            user_profile=test_profile,
            y_steps=3,
            x_alternatives=4
        )
        
        # 验证Y轴
        self.assertEqual(len(timeline), 3, "应有3个时间点")
        
        # 验证X轴
        for y, node in enumerate(timeline):
            self.assertGreater(len(node.decision_points), 0,
                f"Y={y}应有候选点")
            self.assertLessEqual(len(node.decision_points), 4,
                f"Y={y}候选数不应超过4")
            
            # 验证Z轴
            for dp in node.decision_points:
                self.assertIsNotNone(dp.z, "场强不应为None")
                self.assertGreater(dp.z, 0, "场强应为正")
                
                # 验证W轴（如果启用）
                w_details = self._get_w_details(dp)
                if w_details:
                    self.assertIn('S_sem', w_details)
                    self.assertIn('C_causal', w_details)
    
    def _get_w_details(self, dp):
        """提取W轴详情"""
        for event in dp.dimensional_4_events:
            if event['type'] == 'w_axis_analysis':
                return event['details']
        return None
```

#### **测试多层级展开**
```python
def test_multi_level_expansion(self):
    """测试：多层级展开（用户逐步选择）"""
    # 第一层
    timeline_1 = self.plan_4d.generate_3d_space(
        session_id="multi_test",
        initial_state=state_0,
        user_profile=test_profile,
        y_steps=1,
        x_alternatives=4
    )
    
    self.assertGreater(len(timeline_1[0].decision_points), 0)
    
    # 用户选择第一个
    selected_1 = timeline_1[0].decision_points[0]
    
    # 更新状态
    state_1 = State(
        current_location=selected_1.option,
        current_time=state_0.current_time + 2.0,  # 假设2小时
        remaining_budget=state_0.remaining_budget - selected_1.option.cost,
        visited_history=state_0.visited_history + [selected_1.option.id]
    )
    
    # 第二层
    timeline_2 = self.plan_4d.generate_3d_space(
        session_id="multi_test",
        initial_state=state_1,
        user_profile=test_profile,
        y_steps=1,
        x_alternatives=4
    )
    
    self.assertGreater(len(timeline_2[0].decision_points), 0)
    
    # 验证：第二层的POI不应包含已访问的
    visited_ids = set(state_1.visited_history)
    for dp in timeline_2[0].decision_points:
        self.assertNotIn(dp.option.id, visited_ids,
            "不应推荐已访问的POI")
```

---

### **3. 性能测试（Performance Tests）**

#### **测试响应时间**
```python
import time

class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_single_decision_point_time(self):
        """测试：单个决策点计算时间<200ms"""
        field = InfluenceField(
            planner=real_planner,
            neural_service=real_neural,
            enable_4d=True
        )
        
        start = time.time()
        phi_4d, factors, w_details = field.compute_field(
            option=test_poi,
            time_point=datetime.now(),
            state=test_state,
            user_profile=test_profile,
            current_poi=current_poi,
            context={}
        )
        end = time.time()
        
        elapsed_ms = (end - start) * 1000
        self.assertLess(elapsed_ms, 200,
            f"单点计算应<200ms，实际={elapsed_ms:.1f}ms")
    
    def test_full_space_generation_time(self):
        """测试：完整决策空间生成<5秒"""
        plan_4d = ThreeDimensionalPlan(
            progressive_planner=real_planner,
            neural_service=real_neural,
            enable_4d=True
        )
        
        start = time.time()
        timeline = plan_4d.generate_3d_space(
            session_id="perf_test",
            initial_state=test_state,
            user_profile=test_profile,
            y_steps=5,
            x_alternatives=4
        )
        end = time.time()
        
        elapsed = end - start
        self.assertLess(elapsed, 5.0,
            f"完整空间生成应<5秒，实际={elapsed:.1f}秒")
    
    def test_w_axis_overhead(self):
        """测试：W轴开销<20%"""
        # 三维模式
        field_3d = InfluenceField(enable_4d=False)
        start_3d = time.time()
        for _ in range(100):
            field_3d.compute_field(...)
        time_3d = time.time() - start_3d
        
        # 四维模式
        field_4d = InfluenceField(enable_4d=True)
        start_4d = time.time()
        for _ in range(100):
            field_4d.compute_field(...)
        time_4d = time.time() - start_4d
        
        overhead = (time_4d - time_3d) / time_3d
        self.assertLess(overhead, 0.20,
            f"W轴开销应<20%，实际={overhead*100:.1f}%")
```

---

### **4. A/B测试（A/B Tests）**

#### **对比三维与四维推荐质量**
```python
class TestABComparison(unittest.TestCase):
    """A/B测试：三维 vs 四维"""
    
    def setUp(self):
        self.test_scenarios = self._load_test_scenarios()
        # 场景列表，包含：
        # - 用户画像
        # - 初始状态
        # - 已访问历史
    
    def test_recommendation_diversity(self):
        """测试：推荐多样性（四维应更好）"""
        results_3d = []
        results_4d = []
        
        for scenario in self.test_scenarios:
            # 三维模式
            plan_3d = ThreeDimensionalPlan(enable_4d=False)
            timeline_3d = plan_3d.generate_3d_space(...)
            diversity_3d = self._calc_diversity(timeline_3d)
            results_3d.append(diversity_3d)
            
            # 四维模式
            plan_4d = ThreeDimensionalPlan(enable_4d=True)
            timeline_4d = plan_4d.generate_3d_space(...)
            diversity_4d = self._calc_diversity(timeline_4d)
            results_4d.append(diversity_4d)
        
        # 统计比较
        avg_3d = sum(results_3d) / len(results_3d)
        avg_4d = sum(results_4d) / len(results_4d)
        
        print(f"平均多样性：3D={avg_3d:.2f}, 4D={avg_4d:.2f}")
        
        # 期望四维更多样
        self.assertGreater(avg_4d, avg_3d,
            "四维模式应提供更多样的推荐")
    
    def _calc_diversity(self, timeline):
        """计算推荐多样性（POI类型数量）"""
        poi_types = set()
        for node in timeline:
            for dp in node.decision_points:
                poi_types.add(dp.option.type)
        return len(poi_types)
    
    def test_coherence_detection(self):
        """测试：体验连贯性检测（四维应捕捉冲突）"""
        # 构造"连续园林"场景
        scenario = {
            'history': [
                Location(name="拙政园", type=POIType.SCENIC),
                Location(name="狮子林", type=POIType.SCENIC)
            ],
            'current': Location(name="留园", type=POIType.SCENIC)
        }
        
        # 三维模式：可能仍推荐园林（因为距离近）
        plan_3d = ThreeDimensionalPlan(enable_4d=False)
        timeline_3d = plan_3d.generate_3d_space(...)
        top_3d = timeline_3d[0].decision_points[0]
        
        # 四维模式：应降低园林推荐（因为S_sem<0）
        plan_4d = ThreeDimensionalPlan(enable_4d=True)
        timeline_4d = plan_4d.generate_3d_space(...)
        top_4d = timeline_4d[0].decision_points[0]
        
        # 期望四维推荐非园林类型
        print(f"3D推荐：{top_3d.option.name} ({top_3d.option.type})")
        print(f"4D推荐：{top_4d.option.name} ({top_4d.option.type})")
        
        # 如果历史都是园林，4D应推荐其他类型
        if top_3d.option.type == POIType.SCENIC:
            self.assertNotEqual(top_4d.option.type, POIType.SCENIC,
                "四维应避免连续同类型推荐")
```

---

### **5. 用户验收测试（UAT）**

#### **真实场景测试**
```python
def test_real_scenario_suzhou_tour():
    """真实场景：苏州一日游"""
    
    # 用户画像
    profile = UserProfile(
        purpose="文化体验",
        pace="轻松",
        budget_level="medium",
        interests=["园林", "博物馆", "古建筑"],
        avoid_crowd_preference=0.7
    )
    
    # 初始状态（早上9点，拙政园门口）
    state_0 = State(
        current_location=Location(
            id="poi_start",
            name="拙政园",
            lat=31.3234,
            lon=120.6298,
            type=POIType.SCENIC
        ),
        current_time=9.0,
        remaining_budget=500.0,
        visited_history=["poi_start"],
        physical_energy=1.0,
        mental_energy=1.0,
        mood=0.9,
        satiety=0.8
    )
    
    # 生成决策空间
    plan_4d = ThreeDimensionalPlan(
        progressive_planner=real_planner,
        neural_service=real_neural,
        enable_4d=True
    )
    
    timeline = plan_4d.generate_3d_space(
        session_id="suzhou_tour",
        initial_state=state_0,
        user_profile=profile,
        y_steps=5,
        x_alternatives=4
    )
    
    # 验证结果
    print("\n===== 苏州一日游决策空间 =====")
    for y, node in enumerate(timeline):
        print(f"\n时间点 {y}: {node.time.strftime('%H:%M')}")
        for x, dp in enumerate(node.decision_points):
            w = get_w_axis_details(dp)
            print(f"  [{x}] {dp.option.name} (Φ_4D={dp.z:.3f})")
            if w:
                print(f"      语义={w['S_sem']:+.2f}, 因果={w['C_causal']:.2f}")
    
    # 用户验收标准
    # 1. 推荐数量充足
    assert all(len(node.decision_points) >= 3 for node in timeline), \
        "每个时间点应至少3个候选"
    
    # 2. 推荐多样性
    poi_types = set()
    for node in timeline:
        for dp in node.decision_points:
            poi_types.add(dp.option.type)
    assert len(poi_types) >= 3, "应包含至少3种POI类型"
    
    # 3. 体验连贯性（第二个时间点不应都是园林）
    second_node = timeline[1]
    garden_count = sum(1 for dp in second_node.decision_points 
                       if dp.option.type == POIType.SCENIC)
    assert garden_count < len(second_node.decision_points), \
        "第二时间点不应全是园林（体验转换）"
    
    print("\n✅ 真实场景测试通过！")
```

---

## 📊 **测试报告模板**

### **单元测试报告**
```
测试日期：2025-12-15
测试人员：[姓名]
测试环境：Python 3.10, Windows 10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试模块：SemanticFlowAnalyzer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试用例                        结果    耗时
─────────────────────────────────────
test_semantic_score_range       ✅      12ms
test_garden_to_museum_positive  ✅      15ms
test_garden_to_garden_negative  ✅      14ms
test_low_energy_adaptation      ✅      13ms
─────────────────────────────────────
总计                            4/4     54ms

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试模块：InfluenceField
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
测试用例                        结果    耗时
─────────────────────────────────────
test_4d_upgrade                 ✅      180ms
test_degradation_when_w_fails   ✅      120ms
─────────────────────────────────────
总计                            2/2     300ms

总体结果：6/6 通过 ✅
```

### **性能测试报告**
```
测试场景：完整决策空间生成
配置：Y=5, X=4 (20个决策点)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
指标                 目标      实际      状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
单点计算时间          <200ms    185ms     ✅
完整空间生成          <5秒      3.8秒     ✅
W轴开销              <20%      15%       ✅
内存占用              <500MB    320MB     ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

性能评级：优秀 ⭐⭐⭐⭐⭐
```

### **A/B测试报告**
```
测试场景：50个真实用户场景
对比：三维模式 vs 四维模式

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
指标                 三维      四维      提升
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
推荐多样性            3.2       4.5       +41%
体验连贯性            6.5       8.2       +26%
用户满意度            7.1       8.7       +23%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

结论：四维模式显著优于三维模式 ✅
```

---

## 🔧 **持续集成（CI）配置**

### **GitHub Actions示例**
```yaml
name: 4D Planning Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src/core
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## ✅ **测试检查清单**

### **发布前必测**
```
□ 所有单元测试通过 (>95%覆盖率)
□ 集成测试通过
□ 性能测试达标 (<5秒)
□ A/B测试显示改进
□ 真实场景测试通过
□ 无内存泄漏
□ 优雅降级验证
□ 边界条件测试
□ 错误处理验证
□ 文档更新完整
```

---

**完整测试，确保质量！🧪**

---

**版本**: v2.0  
**日期**: 2025-12-15  
**作者**: GAODE Team with Cascade AI
