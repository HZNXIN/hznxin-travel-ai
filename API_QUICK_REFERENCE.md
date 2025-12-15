# 📘 四维空间智能 - API快速参考
**开发者速查手册**
**日期：2025-12-15**

---

## 🎯 **核心类速览**

### **ThreeDimensionalPlan** - 四维决策空间主类

```python
from src.core.three_dimensional_plan import ThreeDimensionalPlan

# 初始化
plan_4d = ThreeDimensionalPlan(
    progressive_planner: ProgressivePlanner,
    neural_service: NeuralNetService,
    spatial_intelligence=None,  # 可选：大模型
    enable_4d: bool = True      # 启用W轴
)
```

#### **主要方法**

**1. generate_3d_space() - 生成决策空间**
```python
timeline = plan_4d.generate_3d_space(
    session_id: str,
    initial_state: State,
    user_profile: UserProfile,
    y_steps: int = 5,           # Y轴时间点数
    x_alternatives: int = 4     # X轴每层候选数
) -> List[TimelineNode]

# 返回值
# timeline = [
#   TimelineNode(
#     y_index=0,
#     time=datetime(...),
#     decision_points=[DecisionPoint(...), ...]
#   ),
#   ...
# ]
```

**2. create_snapshot() - 创建快照**
```python
snapshot = plan_4d.create_snapshot(
    session_id: str,
    timeline: List[TimelineNode],
    selected_y: int,
    selected_x: int,
    reason: str = ""
) -> StaticSnapshot

# 用途：保存用户决策的静态版本
```

**3. apply_dynamic_adjustment() - 动态调整**
```python
adjusted = plan_4d.apply_dynamic_adjustment(
    node: TimelineNode,
    new_time: datetime,
    reason: str
) -> TimelineNode

# 用途：处理突发事件，调整时间
```

---

### **InfluenceField** - 影响力场计算器

```python
from src.core.influence_field import InfluenceField

field = InfluenceField(
    planner: ProgressivePlanner,
    neural_service: NeuralNetService,
    spatial_intelligence=None,
    enable_4d: bool = True
)
```

#### **核心方法**

**compute_field() - 计算场强**
```python
phi_4d, factors, w_details = field.compute_field(
    option: Location,              # 候选POI
    time_point: datetime,          # 时间点
    state: State,                  # 当前状态
    user_profile: UserProfile,     # 用户画像
    current_poi: Location = None,  # 当前POI（启用W轴）
    context: Dict = None           # 上下文（天气、事件等）
) -> Tuple[float, List[InfluenceFactor], Optional[Dict]]

# 返回值
# phi_4d: 四维势能 ∈ [0, 1]
# factors: 影响因子列表（Z轴分解）
# w_details: W轴详情（如果启用）
```

**visualize_field() - 可视化场**
```python
field_matrix = field.visualize_field(
    x_options: List[Location],
    y_timepoints: List[datetime],
    state: State,
    profile: UserProfile
) -> np.ndarray  # 形状: [Y, X]

# 用途：生成场强矩阵，用于可视化
```

---

### **SemanticCausalFlow** - W轴语义-因果流

```python
from src.core.semantic_causal_flow import SemanticCausalFlow

w_axis = SemanticCausalFlow(
    spatial_intelligence=None,  # 大模型（可选）
    delta: float = 0.1,         # 语义权重
    epsilon: float = 0.1        # 因果权重
)
```

#### **核心方法**

**compute_w_axis_force() - 计算W轴关联场力**
```python
f_wc, details = w_axis.compute_w_axis_force(
    current_poi: Location,
    next_poi: Location,
    user_state: UserStateVector,
    context: Dict,
    state: State,
    history: List[Location]
) -> Tuple[float, Dict]

# 返回值
# f_wc: 关联场力 ∈ [-0.2, 0.2]（典型范围）
# details: {
#   'S_sem': float,              # 语义流得分 ∈ [-1, 1]
#   'semantic_explanation': str,
#   'C_causal': float,           # 因果流得分 ∈ [0, 1]
#   'causal_explanation': str,
#   'F_wc': float,
#   'delta': float,
#   'epsilon': float
# }
```

**upgrade_to_4d_potential() - 升级到四维势能**
```python
phi_4d = w_axis.upgrade_to_4d_potential(
    phi_3d: float,
    f_wc: float
) -> float

# Φ_4D = Φ_3D + F_wc
```

---

### **ProgressivePlanner** - 渐进式规划器

```python
from src.core.progressive_planner import ProgressivePlanner

planner = ProgressivePlanner(
    poi_db,
    verification_engine,
    scoring_engine,
    quality_filter=None,
    deep_analyzer=None,
    neural_net_service=None,
    spatial_core=None
)
```

#### **核心方法**

**get_next_options() - 获取候选节点**
```python
options = planner.get_next_options(
    session: PlanningSession,
    k: int = 10
) -> List[CandidateOption]

# 返回值
# CandidateOption {
#   node: Location,
#   edges: List[Edge],
#   verification: NodeVerification,
#   score: float,
#   match_score: float,
#   quality_score: QualityScore,
#   deep_analysis: DeepRecommendation
# }
```

**user_select() - 用户选择后状态转移**
```python
new_state = planner.user_select(
    session: PlanningSession,
    option: CandidateOption,
    edge: Edge
) -> State

# 功能：更新状态（时间、预算、位置等）
```

---

## 🏗️ **数据结构**

### **DecisionPoint** - 决策点
```python
from src.core.three_dimensional_plan import DecisionPoint

dp = DecisionPoint(
    x: int,                    # X轴索引
    y: int,                    # Y轴索引
    z: float,                  # Z轴场强（或Φ_4D）
    option: Location,          # 对应POI
    time: datetime,            # 时间点
    duration: float,           # 持续时间（小时）
    factors: List[InfluenceFactor] = [],
    status: NodeStatus = NodeStatus.PENDING,
    dimensional_4_events: List[Dict] = []
)

# 访问
print(f"坐标: ({dp.x}, {dp.y})")
print(f"场强: {dp.z:.3f}")
print(f"POI: {dp.option.name}")

# 查看影响因子
for factor in dp.factors:
    print(f"{factor.name}: {factor.value:.2f}")

# 查看W轴详情
for event in dp.dimensional_4_events:
    if event['type'] == 'w_axis_analysis':
        w = event['details']
        print(f"语义流: {w['S_sem']:.2f}")
```

### **UserStateVector** - 用户状态向量
```python
from src.core.semantic_causal_flow import UserStateVector

user_state = UserStateVector(
    physical_energy: float,  # 体力 0-1
    mental_energy: float,    # 精力 0-1
    mood: float,            # 心情 0-1
    satiety: float,         # 饱腹感 0-1
    time_pressure: float    # 时间压力 0-1
)

# 转换为向量
vec = user_state.to_vector()  # np.ndarray[5]
```

### **InfluenceFactor** - 影响因子
```python
from src.core.influence_field import InfluenceFactor

factor = InfluenceFactor(
    name: str,           # 因子名称
    value: float,        # 原始值 ∈ [0, 1]
    weight: float,       # 权重
    source: str,         # 来源（neural/mathematical/contextual）
    explanation: str     # 解释
)

# 计算加权值
weighted = factor.weighted_value  # = value * weight
```

### **TimelineNode** - 时间线节点
```python
from src.core.three_dimensional_plan import TimelineNode

node = TimelineNode(
    y_index: int,
    time: datetime,
    duration: float = 2.0,
    decision_points: List[DecisionPoint] = []
)

# 访问
for dp in node.decision_points:
    print(f"X={dp.x}: {dp.option.name} (z={dp.z:.3f})")
```

---

## 🎯 **常用操作示例**

### **1. 完整流程**
```python
# 初始化
plan_4d = ThreeDimensionalPlan(
    progressive_planner=planner,
    neural_service=neural,
    enable_4d=True
)

# 生成决策空间
timeline = plan_4d.generate_3d_space(
    session_id="session_001",
    initial_state=state,
    user_profile=profile,
    y_steps=5,
    x_alternatives=4
)

# 遍历结果
for y, node in enumerate(timeline):
    print(f"\n时间点 {y}: {node.time.strftime('%H:%M')}")
    for dp in node.decision_points:
        print(f"  [{dp.x}] {dp.option.name}: Φ_4D={dp.z:.3f}")
```

### **2. 获取最佳候选**
```python
# 在第一个时间点找Φ_4D最高的
first_node = timeline[0]
best = max(first_node.decision_points, key=lambda dp: dp.z)

print(f"推荐: {best.option.name}")
print(f"四维势能: {best.z:.3f}")
```

### **3. 分析W轴影响**
```python
def get_w_axis_details(dp: DecisionPoint) -> Optional[Dict]:
    """提取W轴详情"""
    for event in dp.dimensional_4_events:
        if event['type'] == 'w_axis_analysis':
            return event['details']
    return None

# 使用
w = get_w_axis_details(decision_point)
if w:
    print(f"语义流: {w['S_sem']:.2f} - {w['semantic_explanation']}")
    print(f"因果流: {w['C_causal']:.2f} - {w['causal_explanation']}")
    print(f"W轴修正: {w['F_wc']:+.3f}")
```

### **4. 对比三维与四维**
```python
def compare_3d_4d(decision_points: List[DecisionPoint]):
    """对比三维和四维推荐"""
    for dp in decision_points:
        # 提取Φ_3D（需要从factors重新计算）
        phi_3d = sum(f.weighted_value for f in dp.factors if 'w_axis' not in f.source.lower())
        phi_3d /= sum(f.weight for f in dp.factors if 'w_axis' not in f.source.lower())
        
        # Φ_4D已经在dp.z中
        phi_4d = dp.z
        
        print(f"{dp.option.name}:")
        print(f"  Φ_3D = {phi_3d:.3f}")
        print(f"  Φ_4D = {phi_4d:.3f} ({phi_4d-phi_3d:+.3f})")
```

### **5. 自定义W轴权重**
```python
# 创建自定义W轴
custom_w = SemanticCausalFlow(
    delta=0.15,   # 加大语义权重
    epsilon=0.05  # 降低因果权重
)

# 应用到InfluenceField
field.w_axis = custom_w

# 重新计算
phi_4d, factors, w_details = field.compute_field(...)
```

---

## ⚙️ **配置参数**

### **ProgressivePlanner配置**
```python
planner.config = {
    'max_candidates': 10,          # 最多返回候选数
    'max_distance_km': 50,         # 最大距离（km）
    'max_detour_rate': 0.5,        # 最大绕路率
    'min_consistency_score': 0.7,  # 最小一致性分数
    'min_trust_score': 0.6,        # 最小可信度
    'crowd_threshold': 0.7,        # 拥挤度阈值
    'enable_quality_filter': True  # 启用质量过滤
}
```

### **InfluenceField层权重**
```python
# Z轴三层默认权重
layer_weights = {
    'neural': 0.4,       # 神经网格层（用户画像）
    'mathematical': 0.3,  # 数学内核层（距离时间）
    'contextual': 0.3    # 情境因子层（天气拥挤度）
}

# 修改权重（通过子类实现）
class CustomInfluenceField(InfluenceField):
    def compute_field(self, ...):
        # 自定义权重分配
        pass
```

### **W轴权重**
```python
# 默认权重
delta = 0.1    # 语义流权重
epsilon = 0.1  # 因果流权重

# 推荐范围
# delta ∈ [0.05, 0.2]
# epsilon ∈ [0.05, 0.2]

# 经验法则
# - 体验导向用户: delta=0.15, epsilon=0.1
# - 逻辑导向用户: delta=0.1, epsilon=0.15
# - 疲劳状态: delta=0.2, epsilon=0.1
```

---

## 🚨 **常见错误处理**

### **错误1：W轴计算失败**
```python
try:
    phi_4d, factors, w_details = field.compute_field(...)
except Exception as e:
    print(f"W轴失败，降级到三维: {e}")
    # 系统会自动降级，返回phi_3d
```

### **错误2：候选数量为0**
```python
timeline = plan_4d.generate_3d_space(...)
if not timeline or not timeline[0].decision_points:
    print("无可用候选，检查：")
    print("1. POI数据库是否有数据")
    print("2. 过滤条件是否过严")
    print("3. 预算/时间是否充足")
```

### **错误3：UserStateVector缺失**
```python
# 确保State对象有这些属性
if not hasattr(state, 'physical_energy'):
    state.physical_energy = 0.7  # 默认值
if not hasattr(state, 'mental_energy'):
    state.mental_energy = 0.7
# ... 其他属性
```

---

## 🔍 **调试技巧**

### **1. 打印决策空间**
```python
def print_decision_space(timeline: List[TimelineNode]):
    """漂亮打印决策空间"""
    for y, node in enumerate(timeline):
        print(f"\n{'='*60}")
        print(f"Y={y} | {node.time.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")
        
        for dp in node.decision_points:
            w = get_w_axis_details(dp)
            print(f"  X={dp.x} | {dp.option.name:30s} | Φ_4D={dp.z:.3f}")
            if w:
                print(f"       语义={w['S_sem']:+.2f} 因果={w['C_causal']:.2f}")
```

### **2. 验证场强范围**
```python
def validate_field_strength(phi: float):
    """验证场强是否在合理范围"""
    if not 0 <= phi <= 1.5:  # 允许超过1（W轴可能为正）
        print(f"⚠️ 场强异常: {phi}")
```

### **3. 追踪W轴影响**
```python
def trace_w_axis_impact(decision_points: List[DecisionPoint]):
    """追踪W轴对排序的影响"""
    # 按Φ_3D排序（估算）
    by_3d = sorted(decision_points, 
                   key=lambda dp: sum(f.weighted_value for f in dp.factors), 
                   reverse=True)
    
    # 按Φ_4D排序
    by_4d = sorted(decision_points, key=lambda dp: dp.z, reverse=True)
    
    if by_3d[0] != by_4d[0]:
        print("⚠️ W轴改变了推荐结果！")
        print(f"三维推荐: {by_3d[0].option.name}")
        print(f"四维推荐: {by_4d[0].option.name}")
```

---

## 📊 **性能优化**

### **1. 批量计算**
```python
# 不推荐：逐个计算
for dp in decision_points:
    phi, factors, w = field.compute_field(dp.option, ...)

# 推荐：准备好数据后批量计算
# （目前API不支持批量，未来可扩展）
```

### **2. 缓存语义相似度**
```python
# 缓存语义流结果
semantic_cache = {}

def cached_semantic_score(poi1, poi2):
    key = (poi1.id, poi2.id)
    if key not in semantic_cache:
        semantic_cache[key] = semantic_analyzer.compute_semantic_score(...)
    return semantic_cache[key]
```

### **3. 异步大模型调用**
```python
import asyncio

async def compute_causal_async(current, next, context, state):
    """异步因果推理"""
    if spatial_intelligence:
        # 异步调用大模型
        result = await spatial_intelligence.reason_async(...)
        return result
    return 0.5  # 默认值
```

---

## 📚 **扩展阅读**

- **深度架构分析**: [FOUR_DIMENSIONAL_ARCHITECTURE_ANALYSIS.md](FOUR_DIMENSIONAL_ARCHITECTURE_ANALYSIS.md)
- **实现指南**: [FOUR_DIMENSIONAL_IMPLEMENTATION_GUIDE.md](FOUR_DIMENSIONAL_IMPLEMENTATION_GUIDE.md)
- **新旧对比**: [BEFORE_VS_AFTER_COMPARISON.md](BEFORE_VS_AFTER_COMPARISON.md)
- **总览**: [FOUR_DIMENSIONAL_README.md](FOUR_DIMENSIONAL_README.md)

---

## 🎯 **速查表**

### **关键公式**
```python
# 四维势能
Φ_4D = Φ_3D + F_wc

# 三维势能
Φ_3D = Σ w_i · factor_i

# W轴关联场力
F_wc = δ·S_sem + ε·C_causal

# 语义流（范围）
S_sem ∈ [-1, 1]

# 因果流（范围）
C_causal ∈ [0, 1]

# 典型权重
δ = ε = 0.1
```

### **数据范围**
```python
# 场强
Φ_3D ∈ [0, 1]
Φ_4D ∈ [-0.2, 1.2]  # 典型范围

# 用户状态
physical_energy ∈ [0, 1]
mental_energy ∈ [0, 1]
mood ∈ [0, 1]
satiety ∈ [0, 1]
time_pressure ∈ [0, 1]

# W轴修正
F_wc ∈ [-0.2, 0.2]  # 典型范围
```

---

**快速开发，从这里开始！🚀**

---

**版本**: v2.0  
**日期**: 2025-12-15  
**作者**: GAODE Team with Cascade AI
