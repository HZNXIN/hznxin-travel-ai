# 空间智能核心（SpatialIntelligenceCore）

**核心理念**: 监控、分析、建议，而非控制、计划、强制

---

## 🎯 设计原则

### ✅ 正确的AI定位

```
用户 = 旅行的主人
AI   = 全知全能的助手

用户：我想去哪就去哪
AI：  好的，让我告诉你这个选择的全局影响
```

### ❌ 错误的AI定位（我之前的设计）

```
AI   = 旅行规划师
用户 = 执行者

AI：  你应该按这个计划走
用户：但我不想...
AI：  不行，计划就是这样的
```

---

## 🧠 SpatialIntelligenceCore 三大职责

### 1. 全局空间建模

**职责**: 理解整个城市的空间关系网络

```python
class SpatialIntelligenceCore:
    """
    空间智能核心
    
    不制定计划，只提供全局视角
    """
    
    def __init__(self):
        # 城市空间网络
        self.spatial_network = SpatialNetwork()
        
        # 全局约束监控
        self.constraint_monitor = ConstraintMonitor()
        
        # 前瞻分析引擎
        self.foresight_engine = ForesightEngine()
    
    def build_spatial_model(self, city: str, pois: List[Location]):
        """
        构建城市空间模型
        
        不是制定路线，而是理解空间关系
        """
        # 1. 构建POI网络
        for poi in pois:
            self.spatial_network.add_node(poi)
        
        # 2. 计算两两距离
        for poi1 in pois:
            for poi2 in pois:
                distance = self._calculate_distance(poi1, poi2)
                travel_time = self._estimate_travel_time(distance)
                
                self.spatial_network.add_edge(
                    poi1.id, poi2.id,
                    distance=distance,
                    time=travel_time
                )
        
        # 3. 识别空间簇（自然形成的区域）
        clusters = self._identify_clusters(pois)
        self.spatial_network.clusters = clusters
        
        # 4. 计算可达性矩阵
        reachability = self._compute_reachability(pois)
        self.spatial_network.reachability = reachability
    
    def _identify_clusters(self, pois):
        """
        识别POI簇（不是规划路线）
        
        例如：
        - 平江路周边：美食+文化区
        - 园林带：拙政园、留园、网师园
        - 湖区：金鸡湖、独墅湖
        """
        # 使用DBSCAN聚类
        from sklearn.cluster import DBSCAN
        
        coords = np.array([[poi.lat, poi.lon] for poi in pois])
        clustering = DBSCAN(eps=0.01, min_samples=2).fit(coords)
        
        clusters = {}
        for idx, label in enumerate(clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(pois[idx])
        
        return clusters
```

### 2. 多约束协同优化

**职责**: 实时监控多个目标的平衡状态

```python
class ConstraintMonitor:
    """
    约束监控器
    
    不强制执行，只提醒用户当前状态
    """
    
    def monitor(self, current_state: State, constraints: Dict) -> ConstraintStatus:
        """
        监控约束状态
        
        返回：当前各项约束的使用情况
        不返回：你应该怎么做
        """
        status = ConstraintStatus()
        
        # 1. 时间使用
        time_used = current_state.current_time
        time_total = constraints['duration']
        status.time_usage = {
            'used': time_used,
            'total': time_total,
            'remaining': time_total - time_used,
            'usage_rate': time_used / time_total,
            'status': self._assess_status(time_used / time_total)
        }
        
        # 2. 预算使用
        budget_spent = constraints['budget'] - current_state.remaining_budget
        budget_total = constraints['budget']
        status.budget_usage = {
            'spent': budget_spent,
            'total': budget_total,
            'remaining': current_state.remaining_budget,
            'usage_rate': budget_spent / budget_total,
            'status': self._assess_status(budget_spent / budget_total)
        }
        
        # 3. 空间覆盖
        visited_areas = self._get_visited_areas(current_state)
        total_areas = len(self.spatial_network.clusters)
        status.spatial_coverage = {
            'visited_areas': visited_areas,
            'total_areas': total_areas,
            'coverage_rate': len(visited_areas) / total_areas,
            'unexplored_clusters': [c for c in self.spatial_network.clusters if c not in visited_areas]
        }
        
        # 4. 体验多样性
        visited_types = self._get_visited_types(current_state)
        status.variety = {
            'types_visited': visited_types,
            'dominant_type': self._get_dominant_type(visited_types),
            'variety_score': len(visited_types) / 6  # 假设6种类型
        }
        
        return status
    
    def _assess_status(self, usage_rate):
        """评估状态（描述性，非指令性）"""
        if usage_rate < 0.3:
            return {'level': 'low', 'description': '充裕'}
        elif usage_rate < 0.7:
            return {'level': 'medium', 'description': '正常'}
        elif usage_rate < 0.9:
            return {'level': 'high', 'description': '紧张'}
        else:
            return {'level': 'critical', 'description': '即将耗尽'}
```

### 3. 前瞻式决策建议

**职责**: 预测影响，提供信息，但不做决定

```python
class ForesightEngine:
    """
    前瞻引擎
    
    "如果你选A，会发生什么"
    而不是"你应该选A"
    """
    
    def analyze_choice_impact(self,
                             candidate: Location,
                             current_state: State,
                             constraints: Dict,
                             spatial_network: SpatialNetwork) -> ImpactAnalysis:
        """
        分析选择的全局影响
        
        返回：客观的影响分析
        不返回：主观的建议
        """
        analysis = ImpactAnalysis()
        
        # 1. 空间影响
        analysis.spatial_impact = self._analyze_spatial_impact(
            candidate, current_state, spatial_network
        )
        
        # 2. 时间影响
        analysis.time_impact = self._analyze_time_impact(
            candidate, current_state, constraints
        )
        
        # 3. 预算影响
        analysis.budget_impact = self._analyze_budget_impact(
            candidate, current_state, constraints
        )
        
        # 4. 后续可达性影响
        analysis.reachability_impact = self._analyze_reachability_impact(
            candidate, current_state, spatial_network
        )
        
        return analysis
    
    def _analyze_spatial_impact(self, candidate, state, network):
        """分析空间影响"""
        current_location = state.current_location
        
        # 1. 与当前位置的关系
        distance = network.get_distance(current_location.id, candidate.id)
        
        # 2. 是否进入新区域
        current_cluster = network.get_cluster(current_location)
        candidate_cluster = network.get_cluster(candidate)
        entering_new_area = (current_cluster != candidate_cluster)
        
        # 3. 影响后续选择
        if entering_new_area:
            # 计算新区域的POI数量
            new_area_pois = len(network.clusters[candidate_cluster])
            message = f"进入新区域（{candidate_cluster}），该区域有{new_area_pois}个POI"
        else:
            message = f"继续在{current_cluster}区域探索"
        
        return {
            'distance': distance,
            'entering_new_area': entering_new_area,
            'new_cluster': candidate_cluster if entering_new_area else None,
            'description': message,
            'opens_access_to': new_area_pois if entering_new_area else 0
        }
    
    def _analyze_time_impact(self, candidate, state, constraints):
        """分析时间影响"""
        # 计算耗时
        travel_time = self._estimate_travel_time(state.current_location, candidate)
        visit_time = candidate.average_visit_time
        total_time = travel_time + visit_time
        
        new_total_time = state.current_time + total_time
        remaining_time = constraints['duration'] - new_total_time
        
        # 预测后续可用时间
        if remaining_time < 1.0:
            time_status = "紧张：可能只够回程"
        elif remaining_time < 2.0:
            time_status = "有限：大约还能游览1个短景点"
        else:
            estimated_remaining_pois = int(remaining_time / 2.0)
            time_status = f"充裕：大约还能游览{estimated_remaining_pois}个景点"
        
        return {
            'travel_time': travel_time,
            'visit_time': visit_time,
            'total_time_cost': total_time,
            'new_total_time': new_total_time,
            'remaining_time': remaining_time,
            'time_status': time_status
        }
    
    def _analyze_reachability_impact(self, candidate, state, network):
        """
        分析可达性影响
        
        选了A之后，还能去哪？
        """
        # 模拟选择后的状态
        simulated_time = state.current_time + candidate.average_visit_time
        simulated_budget = state.remaining_budget - candidate.ticket_price
        
        # 找出后续可达的POI
        reachable_pois = []
        for poi in network.nodes:
            if poi.id in state.visited_history or poi.id == candidate.id:
                continue
            
            # 时间可达性
            travel_time = network.get_travel_time(candidate.id, poi.id)
            visit_time = poi.average_visit_time
            
            if simulated_time + travel_time + visit_time <= constraints['duration']:
                # 预算可达性
                if simulated_budget >= poi.ticket_price:
                    reachable_pois.append(poi)
        
        # 按类型统计
        reachable_by_type = {}
        for poi in reachable_pois:
            poi_type = poi.type.value
            if poi_type not in reachable_by_type:
                reachable_by_type[poi_type] = 0
            reachable_by_type[poi_type] += 1
        
        return {
            'reachable_count': len(reachable_pois),
            'reachable_by_type': reachable_by_type,
            'description': f"选择后，还有{len(reachable_pois)}个POI可达",
            'reachable_pois': [poi.name for poi in reachable_pois[:5]]  # 前5个
        }
```

---

## 🔄 完整工作流程（正确版）

### 用户请求候选

```python
# 1. 用户：给我推荐
user_request = "给我推荐下一步"

# 2. ProgressivePlanner：生成候选
candidates = planner.get_next_options(session, k=5)

# 3. SpatialIntelligenceCore：为每个候选分析影响
for candidate in candidates:
    # 分析全局影响
    impact = spatial_core.analyze_choice_impact(
        candidate.node,
        session.current_state,
        session.constraints,
        spatial_core.spatial_network
    )
    
    # 附加到候选
    candidate.global_impact = impact

# 4. 返回给用户（带全局视角）
return {
    'candidates': [
        {
            'name': '拙政园',
            'score': 0.75,
            'impact': {
                'spatial': '进入园林区，该区域有3个园林',
                'time': '耗时2.5h，之后还能游览2个景点',
                'budget': '花费70元，剩余430元',
                'reachability': '选择后，还有12个POI可达'
            }
        },
        {
            'name': '平江路',
            'score': 0.70,
            'impact': {
                'spatial': '进入美食区，该区域有5个餐厅',
                'time': '耗时1h，之后还能游览3-4个景点',
                'budget': '花费约50元，剩余450元',
                'reachability': '选择后，还有15个POI可达'
            }
        }
    ]
}
```

### 用户做出选择（自由）

```python
# 用户选择了拙政园
user_choice = candidates[0]

# 用户实际游玩（可能与预期不同）
# 预期：2.5小时
# 实际：用户觉得无聊，30分钟就走了

# 更新状态
actual_visit_time = 0.5  # 用户自己决定的
update_state(actual_visit_time)

# SpatialCore：更新监控数据
status = spatial_core.monitor(new_state, constraints)

# 返回状态（信息性）
return {
    'status': {
        'time': '已用0.5h / 8h，进度6%',
        'budget': '已用70元 / 500元，进度14%',
        'coverage': '游览了1个区域 / 5个区域',
        'variety': '类型：园林(1)'
    }
}
```

---

## 📊 对比总结

| 维度 | 错误设计（我的） | 正确设计（你的） |
|------|-----------------|-----------------|
| **定位** | AI制定计划 | AI提供视角 |
| **用户角色** | 执行者 | 决策者 |
| **AI输出** | "你应该..." | "如果...会..." |
| **计划性** | 刚性计划 | 无计划，实时分析 |
| **自主权** | AI控制 | 用户控制 |
| **灵活性** | 低（偏离就报警） | 高（随时调整） |

---

## 💡 核心理念

### ✅ 正确的AI哲学

```
AI = 全知的顾问
   ≠ 全能的决策者

AI说：
"我看到了全局，让我告诉你当前的状态和影响"
而不是：
"我规划了路线，你必须按我的来"
```

### 实际场景

```
用户: 我想去拙政园
AI: 好的，让我分析：
    • 空间：进入园林区（还有留园、网师园）
    • 时间：预计2.5h，之后还能去2个地方
    • 预算：70元，剩余430元
    • 可达：之后还有12个POI可达
    
    👉 决定权在你

用户: 好，我去（但实际只玩了30分钟）

AI: 收到，更新状态：
    • 实际用时：0.5h
    • 时间充裕度提升
    • 可达POI增加到16个
    
    👉 继续你的自由旅程
```

---

## 🎯 总结

### 你的洞察是对的！

> **"全局AI是用来监控数据的而不是来决定用户的"**

这是**核心设计原则**！

### 修正后的架构

```
SpatialIntelligenceCore (大脑)
├─ 全局空间建模 → 理解城市
├─ 多约束协同优化 → 监控状态
└─ 前瞻式决策建议 → 提供影响分析

NeuralContext (神经)
├─ 上下文感知
└─ 影响传播

ProgressivePlanner (身体)
├─ 生成候选
└─ 执行更新

用户 (主人)
└─ 做所有决策
```

**核心**：AI辅助，用户主导！
