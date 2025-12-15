# 渐进式旅行规划系统 - 数学基础

## 📐 第一部分：形式化定义

### 1.1 基本定义

**定义 1.1 (旅行规划问题)**
```
给定三元组 I = (S, D, T)，其中：
  S ∈ Location    起点（确定）
  D ∈ Location    终点（确定）
  T ∈ ℝ⁺          持续时间（确定）

目标：通过渐进式决策生成路径 P
```

**定义 1.2 (状态空间)**
```
状态 σ = (l, t, H, V)，其中：
  l ∈ Location    当前位置
  t ∈ ℝ⁺          当前时间
  H ⊆ Location    历史访问节点集
  V : Location → [0,1]  访问质量评分

状态空间 Σ = {σ | σ 满足约束条件}
```

**定义 1.3 (动作空间)**
```
动作 a = (n, m)，其中：
  n ∈ Location    目标节点
  m ∈ Mode        交通方式 = {步行, 打车, 公交, 地铁, ...}

动作空间 A(σ) = {a | a 在状态 σ 下可行}
```

**定义 1.4 (状态转移函数)**
```
δ : Σ × A → Σ

δ(σ, a) = σ' = (l', t', H', V')，其中：
  l' = a.n
  t' = t + travel_time(σ.l, a.n, a.m)
  H' = H ∪ {a.n}
  V' = V[a.n ← visit_quality(a.n, t')]
```

---

## 📊 第二部分：图论模型

### 2.1 动态拓扑图

**定义 2.1 (渐进式有向图)**
```
G(σ) = (V(σ), E(σ), w)

V(σ) = {v | v ∈ Reachable(σ.l, σ.t, T - σ.t)}
  仅包含从当前状态可达的节点

E(σ) = {(σ.l, v, m) | v ∈ V(σ), m ∈ Mode}
  当前节点到所有可达节点的边

w : E → ℝ³
  边权重 w(e) = (distance, time, cost)
```

**性质 2.1 (图的动态性)**
```
∀σ, σ' ∈ Σ : σ ≠ σ' ⟹ G(σ) ≠ G(σ')

证明：状态不同导致可达节点集不同，因此图结构不同。
```

### 2.2 可达性分析

**定理 2.1 (时空可达性)**
```
节点 v 在状态 σ 下可达，当且仅当：

Reachable(v, σ) ⟺ 
  ∃m ∈ Mode : 
    travel_time(σ.l, v, m) + visit_time(v) ≤ T - σ.t
    ∧ spatial_feasible(σ.l, v)
    ∧ temporal_feasible(v, σ.t + travel_time(σ.l, v, m))
```

**定义 2.2 (空间可行性)**
```
spatial_feasible(l₁, l₂) ⟺ 
  distance(l₁, l₂) ≤ θ_dist
  ∧ ∃path : l₁ →* l₂  (连通性)
  
其中 θ_dist 是最大合理距离阈值
```

**定义 2.3 (时间可行性)**
```
temporal_feasible(v, t) ⟺
  t ∈ opening_hours(v)
  ∧ crowd_level(v, t) ≤ θ_crowd
  
其中 θ_crowd 是可接受拥挤度阈值
```

---

## 🔢 第三部分：四项基本原则的数学化

### 3.1 多源数据交叉验证

**定义 3.1 (数据源)**
```
数据源集合 DS = {ds₁, ds₂, ..., dsₙ}
每个数据源对节点 v 的评估 R(v, dsᵢ) ∈ [0, 5]
```

**定义 3.2 (一致性度量)**
```
Consistency(v) = 1 - (σᴿ / μᴿ)

其中：
  μᴿ = (1/n) Σᵢ R(v, dsᵢ)      均值
  σᴿ = √[(1/n) Σᵢ (R(v, dsᵢ) - μᴿ)²]  标准差
```

**定理 3.1 (一致性阈值)**
```
数据可信 ⟺ Consistency(v) ≥ θ_consistency

通常取 θ_consistency = 0.8 (即标准差 < 0.2μ)
```

**定义 3.3 (加权融合)**
```
R_final(v) = Σᵢ wᵢ · R(v, dsᵢ) · Trust(dsᵢ)

其中：
  wᵢ = 数据源权重 (Σᵢ wᵢ = 1)
  Trust(dsᵢ) = 数据源可信度 ∈ [0, 1]
```

### 3.2 数据清洗模型

**定义 3.4 (评论集)**
```
Reviews(v) = {r₁, r₂, ..., rₘ}
每条评论 rᵢ = (text, rating, timestamp, user)
```

**定义 3.5 (虚假检测函数)**
```
Fake : Review → [0, 1]

Fake(r) = P(r 是虚假评论 | features(r))

features(r) = [
  text_similarity(r, others),  // 与其他评论的相似度
  temporal_pattern(r),         // 时间模式异常
  user_credibility(r.user),    // 用户可信度
  sentiment_extremity(r)       // 情感极端程度
]
```

**定理 3.2 (清洗准则)**
```
保留评论 r ⟺ Fake(r) ≤ θ_fake

其中 θ_fake 通常取 0.3
```

**定义 3.6 (清洗后评分)**
```
R_cleaned(v) = Σᵢ rating(rᵢ) / |Reviews_valid(v)|

其中 Reviews_valid(v) = {r ∈ Reviews(v) | Fake(r) ≤ θ_fake}
```

### 3.3 空间合理性验证

**定义 3.7 (路径函数)**
```
Path(l₁, l₂, m) = sequence of waypoints

返回从 l₁ 到 l₂ 使用方式 m 的路径
```

**定义 3.8 (空间合理性分数)**
```
Spatial_Score(l₁, l₂) = w₁·D + w₂·T + w₃·C

其中：
  D = 1 - (actual_dist / direct_dist)  // 绕路程度
  T = 1 - (actual_time / optimal_time) // 时间效率
  C = connectivity_score(l₁, l₂)       // 连通性

  w₁ + w₂ + w₃ = 1
```

**定理 3.3 (空间合理性)**
```
空间合理 ⟺ 
  Spatial_Score(l₁, l₂) ≥ θ_spatial
  ∧ actual_dist / direct_dist ≤ 1.5  (绕路率 < 50%)
```

### 3.4 时间合理性验证

**定义 3.9 (时间窗口)**
```
TimeWindow(v) = [opening_time, closing_time]
```

**定义 3.10 (拥挤度预测)**
```
Crowd(v, t) : Location × Time → [0, 1]

使用 LSTM 预测：
  Crowd(v, t) = LSTM(历史数据(v), t)
```

**定义 3.11 (时间合理性分数)**
```
Temporal_Score(v, t) = w₁·O + w₂·C + w₃·R

其中：
  O = 1 if t ∈ TimeWindow(v) else 0  // 营业时间
  C = 1 - Crowd(v, t)                 // 不拥挤
  R = remaining_time(t, T) / visit_time(v)  // 时间充足

  w₁ + w₂ + w₃ = 1
```

**定理 3.4 (时间合理性)**
```
时间合理 ⟺ 
  Temporal_Score(v, t) ≥ θ_temporal
  ∧ t ∈ TimeWindow(v)
  ∧ Crowd(v, t) ≤ θ_crowd
```

---

## 🎯 第四部分：决策优化模型

### 4.1 候选节点生成

**算法 4.1 (候选节点计算)**
```
Candidates(σ) = {v ∈ Location | 
  Reachable(v, σ)
  ∧ Spatial_Score(σ.l, v) ≥ θ_spatial
  ∧ Temporal_Score(v, σ.t) ≥ θ_temporal
  ∧ Consistency(v) ≥ θ_consistency
}
```

### 4.2 边的计算

**算法 4.2 (边集计算)**
```
Edges(σ, v) = {(σ.l, v, m) | 
  m ∈ Mode
  ∧ travel_time(σ.l, v, m) ≤ T - σ.t
  ∧ feasible(σ.l, v, m)
}
```

### 4.3 综合评分

**定义 4.1 (节点综合评分)**
```
Score(v, σ, u) = Σᵢ wᵢ · fᵢ(v, σ, u)

其中 u 是用户画像，评分因子：
  f₁ = Match(v.type, u.preference)     // 偏好匹配
  f₂ = R_cleaned(v)                    // 清洗后评分
  f₃ = Spatial_Score(σ.l, v)           // 空间合理性
  f₄ = Temporal_Score(v, σ.t)          // 时间合理性
  f₅ = Consistency(v)                  // 数据一致性
  f₆ = 1 - popularity(v, σ.t)          // 避免拥挤
  f₇ = Novelty(v, σ.H)                 // 新颖性

权重 wᵢ 由用户偏好决定
```

### 4.4 排序与推荐

**算法 4.3 (推荐排序)**
```
Recommend(σ, u, k):
  C ← Candidates(σ)
  S ← [(v, Score(v, σ, u)) for v in C]
  S_sorted ← sort(S, key=lambda x: x[1], reverse=True)
  return S_sorted[:k]  // 返回 top-k
```

---

## 🧠 第五部分：神经网络模型

### 5.1 用户画像网络

**模型架构**
```
Input: x = (自然语言描述, 历史行为)
  ↓
BERT Encoding: h = BERT(x)
  ↓
Multi-Head Attention: a = Attention(h, h, h)
  ↓
Preference Heads:
  purpose = softmax(W_p · a)      // 旅行目的
  intensity = softmax(W_i · a)    // 体力强度
  pace = softmax(W_t · a)         // 节奏偏好
  food = softmax(W_f · a)         // 美食偏好

Output: u = (purpose, intensity, pace, food)
```

**损失函数**
```
L = Σ CrossEntropy(yᵢ, ŷᵢ) + λ·||W||²

其中 λ 是正则化系数
```

### 5.2 评论真实性检测网络

**模型架构**
```
Input: review text
  ↓
BERT Encoding: e = BERT(text)
  ↓
Discriminator:
  h₁ = ReLU(W₁·e + b₁)
  h₂ = ReLU(W₂·h₁ + b₂)
  p = sigmoid(W₃·h₂ + b₃)

Output: p ∈ [0,1]  (虚假概率)
```

**对抗训练**
```
Generator G: 生成虚假评论
Discriminator D: 判别真假

min_G max_D V(D,G) = E[log D(x)] + E[log(1-D(G(z)))]
```

### 5.3 空间关系图神经网络

**模型架构**
```
Graph: G = (V, E)
Node features: X ∈ ℝⁿˣᵈ
Adjacency: A ∈ ℝⁿˣⁿ

GCN Layer:
  H⁽ˡ⁺¹⁾ = σ(D̃⁻¹/²ÃD̃⁻¹/²H⁽ˡ⁾W⁽ˡ⁾)

其中：
  Ã = A + I  (加自环)
  D̃ᵢᵢ = Σⱼ Ãᵢⱼ  (度矩阵)

多层 GCN:
  H⁽⁰⁾ = X
  H⁽ˡ⁺¹⁾ = GCN(H⁽ˡ⁾, A)

Output: 空间关系 embedding
```

### 5.4 时序预测网络

**LSTM 模型**
```
Input: historical data (人流, 天气, 节假日)
  xₜ ∈ ℝᵈ

LSTM Cell:
  fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)      // 遗忘门
  iₜ = σ(Wi·[hₜ₋₁, xₜ] + bi)      // 输入门
  C̃ₜ = tanh(Wc·[hₜ₋₁, xₜ] + bc)  // 候选状态
  Cₜ = fₜ ⊙ Cₜ₋₁ + iₜ ⊙ C̃ₜ        // 单元状态
  oₜ = σ(Wo·[hₜ₋₁, xₜ] + bo)      // 输出门
  hₜ = oₜ ⊙ tanh(Cₜ)              // 隐状态

Output: ŷₜ = Wy·hₜ + by  (未来拥挤度预测)
```

**损失函数**
```
L = (1/T) Σₜ (yₜ - ŷₜ)² + λ·||W||²

MSE + L2 正则化
```

---

## 🎲 第六部分：复杂度分析

### 6.1 时间复杂度

**候选节点计算**
```
T_candidates = O(|V| · log|V|)

其中 |V| 是所有 POI 数量（城市级别 ~10⁴）
```

**边计算**
```
T_edges = O(|Candidates| · |Mode|)
        = O(k · m)

其中 k = |Candidates| ≈ 10-20
     m = |Mode| ≈ 3-5
```

**总时间复杂度（每步）**
```
T_total = O(|V| log|V| + k·m + k·log k)
        ≈ O(|V| log|V|)

对于 |V| = 10⁴：T ≈ 10⁴ · 13 ≈ 1.3×10⁵ ops
在现代 CPU 上 < 10ms
```

### 6.2 空间复杂度

**状态存储**
```
S_state = O(|H| + |V|)  (历史节点 + 访问评分)
```

**图存储（当前层）**
```
S_graph = O(k + k·m)  (节点 + 边)
```

**总空间复杂度**
```
S_total = O(|H| + k·m)
        ≈ O(n)  (n 是决策步数)

线性空间复杂度
```

---

## 📈 第七部分：收敛性与最优性

### 7.1 目标函数

**定义 7.1 (用户满意度)**
```
Satisfaction(P) = Σᵥ∈P [Score(v, σᵥ, u) · duration(v)]

其中 P 是最终路径，σᵥ 是访问 v 时的状态
```

**定义 7.2 (效率)**
```
Efficiency(P) = useful_time / total_time

useful_time = Σᵥ visit_time(v)
total_time = Σₑ travel_time(e) + Σᵥ visit_time(v)
```

**定义 7.3 (综合目标)**
```
Objective(P) = α·Satisfaction(P) + β·Efficiency(P) - γ·Risk(P)

其中 α, β, γ 是权重参数
```

### 7.2 贪心策略的局部最优性

**定理 7.1 (局部最优)**
```
渐进式贪心策略在每步选择 argmax Score(v) 时，
保证局部最优性，但不保证全局最优。

证明：
  每步选择最大化当前 Score，
  但未来状态依赖于当前选择，
  因此无法保证全局最优。
```

**引理 7.1 (近似比)**
```
设 OPT 是全局最优解，GREEDY 是贪心解，则：

Satisfaction(GREEDY) ≥ (1 - 1/e) · Satisfaction(OPT)

在子模函数假设下成立。
```

---

## ✅ 第八部分：系统约束

### 8.1 硬约束

```
1. 时间约束: Σₑ travel_time(e) + Σᵥ visit_time(v) ≤ T

2. 预算约束: Σₑ cost(e) + Σᵥ ticket(v) ≤ Budget

3. 物理约束: ∀v ∈ P : Reachable(v, σ)

4. 逻辑约束: ∀v ∈ P : temporal_feasible(v, arrival_time(v))
```

### 8.2 软约束（优化目标）

```
1. 偏好匹配: max Σᵥ Match(v, u.preference)

2. 避免拥挤: min Σᵥ Crowd(v, arrival_time(v))

3. 数据可信: max Σᵥ Consistency(v)

4. 新颖性: max Σᵥ Novelty(v, H)
```

---

## 🔬 第九部分：验证与测试

### 9.1 单元测试

```
Test_Consistency:
  给定 v 和多个数据源 DS
  验证 Consistency(v) ∈ [0, 1]
  验证 σᴿ / μᴿ ≤ 1

Test_Reachability:
  给定 σ 和 v
  验证 Reachable(v, σ) 的正确性
  验证时间和空间约束

Test_Score:
  给定 v, σ, u
  验证 Score(v, σ, u) ∈ [0, 1]
  验证单调性
```

### 9.2 集成测试

```
Test_Progressive_Planning:
  初始状态 σ₀
  用户选择序列 [a₁, a₂, ..., aₙ]
  验证每步状态转移正确
  验证最终路径有效
```

---

**数学基础建立完毕！接下来实现架构设计。**
