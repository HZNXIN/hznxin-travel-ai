# FastAPI后端使用指南

**版本**: 2.0.0  
**更新时间**: 2025-12-12

---

## 🚀 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8000` 启动

### 3. 访问API文档

打开浏览器访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📡 API端点

### 健康检查

```http
GET /api/v1/health
```

**响应**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-12-12T17:30:00"
}
```

---

### 初始化会话

```http
POST /api/v1/session/init
```

**请求体**:
```json
{
  "user_id": "test_user_001",
  "starting_location": "苏州火车站",
  "purpose": "历史文化、休闲游览",
  "pace": "slow",
  "intensity": "low",
  "time_budget": 8.0,
  "money_budget": 500.0
}
```

**响应**:
```json
{
  "session_id": "uuid-xxx-xxx",
  "message": "会话创建成功！起始位置: 苏州火车站",
  "initial_state": {
    "current_location": {
      "id": "start_test_user_001",
      "name": "苏州火车站",
      "lat": 31.3,
      "lon": 120.6,
      ...
    },
    "current_time": 0.0,
    "total_cost": 0.0,
    "visited_count": 1,
    "remaining_budget": 500.0
  },
  "timestamp": "2025-12-12T17:30:00"
}
```

---

### 获取候选选项

```http
GET /api/v1/session/{session_id}/options?top_k=5
```

**响应**:
```json
{
  "session_id": "uuid-xxx-xxx",
  "current_state": { ... },
  "options": [
    {
      "index": 0,
      "node": {
        "id": "suzhou_zzy",
        "name": "拙政园",
        "lat": 31.3229,
        "lon": 120.6309,
        "type": "attraction",
        "address": "苏州市姑苏区东北街178号",
        "average_visit_time": 2.5,
        "ticket_price": 70.0
      },
      "verification": {
        "consistency_score": 0.97,
        "weighted_rating": 4.8,
        "total_reviews": 23456,
        "valid_reviews": 19937,
        "fake_rate": 0.15,
        "positive_rate": 0.92,
        ...
      },
      "quality_score": {
        "playability": 0.80,
        "viewability": 0.88,
        "popularity": 1.00,
        "history": 0.87,
        "overall": 0.89
      },
      "deep_analysis": {
        "reasons": [
          {
            "type": "核心价值",
            "content": "江南园林艺术巅峰之作",
            "weight": 0.30,
            "evidence": "世界文化遗产（1997年）"
          },
          {
            "type": "用户匹配",
            "content": "符合你的'历史文化、观光游览'偏好（89%匹配）",
            "weight": 0.25,
            "evidence": "匹配度89%"
          },
          ...
        ],
        "highlights": {
          "architecture": [
            "亭台楼阁布局精巧，移步换景",
            "借景手法运用极致",
            ...
          ],
          "layout": {
            "东园": "开阔水面为主，远香堂为核心",
            "中园": "精致山水，曲径通幽",
            "西园": "层次丰富，见山楼制高点"
          },
          "history": [
            "明代正德年间建造（1509年）",
            "王献臣私园，文徵明参与设计",
            ...
          ],
          "must_see": [
            {
              "name": "远香堂",
              "description": "中园主厅，观荷花池",
              "importance": 5,
              "best_time": "上午10点",
              "photo_tip": "拍倒影"
            },
            ...
          ],
          "unique_features": [
            "中国园林建筑的经典范例"
          ]
        },
        "strategy": {
          "best_time": "上午9-11点（光线好，人流少）",
          "duration": "2-3小时",
          "route": [
            "入口",
            "远香堂（20分钟）",
            "荷花池（15分钟）",
            ...
          ],
          "photo_spots": [
            {
              "location": "荷花池北侧",
              "subject": "拍远香堂倒影",
              "best_time": "上午10点",
              "tips": "使用广角镜头"
            },
            ...
          ],
          "tips": [
            "周末和节假日人多，建议工作日前往",
            ...
          ]
        },
        "related": [
          {
            "poi_id": "suzhou_ly",
            "name": "留园",
            "relation_type": "同类型",
            "reason": "与拙政园齐名的江南四大名园之一",
            "distance": 3.5
          },
          ...
        ],
        "match_analysis": {
          "overall_match": 0.89,
          "reasons": [
            "文化历史价值顶级",
            "可玩性强",
            ...
          ],
          "strengths": [
            "深度文化体验",
            "游玩体验丰富",
            ...
          ],
          "considerations": [
            "门票较贵，建议提前购买"
          ]
        },
        "overall_score": 9.2
      },
      "edge_score": 5.2,
      "total_score": 9.2,
      "rank": 1
    },
    ...
  ],
  "total_options": 5,
  "timestamp": "2025-12-12T17:30:00"
}
```

---

### 选择选项

```http
POST /api/v1/session/{session_id}/select
```

**请求体**:
```json
{
  "session_id": "uuid-xxx-xxx",
  "option_index": 0
}
```

**响应**:
```json
{
  "session_id": "uuid-xxx-xxx",
  "selected_option": { ... },
  "new_state": {
    "current_location": {
      "id": "suzhou_zzy",
      "name": "拙政园",
      ...
    },
    "current_time": 2.75,
    "total_cost": 85.0,
    "visited_count": 2,
    "remaining_budget": 415.0
  },
  "message": "已选择: 拙政园",
  "timestamp": "2025-12-12T17:30:00"
}
```

---

### 其他端点

#### 获取会话信息
```http
GET /api/v1/session/{session_id}/info
```

#### 删除会话
```http
DELETE /api/v1/session/{session_id}
```

#### 系统统计
```http
GET /api/v1/stats
```

---

## 🧪 测试

### 运行测试脚本

```bash
python test_api.py
```

测试将执行完整流程:
1. 健康检查
2. 初始化会话
3. 获取候选选项（深度分析）
4. 选择选项
5. 渐进式展开（第二轮）
6. 会话管理
7. 系统统计

---

## 📊 深度分析说明

每个候选选项都包含完整的深度分析:

### 1. 推荐理由 (reasons)

5个维度的理由:
- **核心价值** (30%): POI的核心特色
- **用户匹配** (25%): 与用户偏好的匹配度
- **空间便利** (20%): 地理位置和交通便利性
- **时间适配** (15%): 游玩时长匹配
- **口碑验证** (10%): 评论和评分

### 2. 核心亮点 (highlights)

- **建筑艺术**: 建筑特色
- **园林布局**: 布局结构
- **历史文化**: 历史背景
- **必看景观**: 必看景点列表（带星级）
- **独特之处**: 独特特色

### 3. 游玩攻略 (strategy)

- **最佳时间**: 推荐游览时间
- **建议时长**: 游玩时长
- **推荐路线**: 详细游览路线
- **拍照攻略**: 拍照机位和技巧
- **注意事项**: 实用提示

### 4. 关联推荐 (related)

- 同类型景点
- 邻近景点
- 精品路线组合

### 5. 用户匹配分析 (match_analysis)

- 总体匹配度
- 匹配原因
- 优势点
- 需要考虑的点

---

## 🎯 核心特性

### 1. 渐进式展开

用户每选择一步，系统才展开下一层候选选项。

### 2. 质量过滤

只推荐优质POI:
- 评论数 ≥ 50条
- 评分 ≥ 4.0
- 可玩性 ≥ 0.3
- 综合质量 ≥ 0.5

### 3. 深度分析

每个推荐都包含:
- 完整的推荐理由
- 核心亮点详解
- 游玩攻略指导
- 用户匹配分析

### 4. 四项原则验证

- 多源数据交叉验证
- 大数据清洗
- 空间合理性验证
- 时间合理性验证

---

## 🔧 配置

### 环境变量

在 `config.py` 中配置:

```python
GAODE_API_KEY = "your_api_key_here"
```

### 服务配置

在 `app.py` 中修改:

```python
uvicorn.run(
    "app:app",
    host="0.0.0.0",  # 监听地址
    port=8000,        # 监听端口
    reload=True,      # 开发模式自动重载
    log_level="info"  # 日志级别
)
```

---

## 📝 使用示例

### Python客户端

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. 初始化会话
response = requests.post(f"{BASE_URL}/session/init", json={
    "user_id": "user123",
    "starting_location": "苏州火车站",
    "purpose": "历史文化",
    "pace": "slow"
})
session_id = response.json()['session_id']

# 2. 获取候选选项
response = requests.get(f"{BASE_URL}/session/{session_id}/options?top_k=5")
options = response.json()['options']

# 3. 查看深度分析
for option in options:
    print(f"\n{option['node']['name']}")
    print(f"推荐理由: {option['deep_analysis']['reasons'][0]['content']}")
    print(f"核心亮点: {option['deep_analysis']['highlights']['architecture'][0]}")
    print(f"游玩攻略: {option['deep_analysis']['strategy']['best_time']}")

# 4. 选择选项
response = requests.post(f"{BASE_URL}/session/{session_id}/select", json={
    "session_id": session_id,
    "option_index": 0
})
new_state = response.json()['new_state']
```

### JavaScript客户端

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// 1. 初始化会话
const initResponse = await fetch(`${BASE_URL}/session/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        user_id: 'user123',
        starting_location: '苏州火车站',
        purpose: '历史文化',
        pace: 'slow'
    })
});
const { session_id } = await initResponse.json();

// 2. 获取候选选项
const optionsResponse = await fetch(
    `${BASE_URL}/session/${session_id}/options?top_k=5`
);
const { options } = await optionsResponse.json();

// 3. 展示深度分析
options.forEach(option => {
    console.log(`\n${option.node.name}`);
    console.log(`推荐理由: ${option.deep_analysis.reasons[0].content}`);
    console.log(`必看景观: ${option.deep_analysis.highlights.must_see[0].name}`);
});
```

---

## ❓ 常见问题

### 1. 服务启动失败

**检查**:
- 端口8000是否被占用
- 依赖是否已安装
- Python版本是否>=3.8

### 2. 会话不存在

会话24小时后自动过期，需要重新初始化。

### 3. 获取选项为空

**可能原因**:
- 当前位置附近没有POI
- 所有POI都被质量过滤掉了
- 高德API调用失败

---

## 📚 更多信息

- **项目文档**: 查看 `README.md`
- **系统架构**: 查看 `ARCHITECTURE_COMPLETE.md`
- **深度分析**: 查看 `DEEP_ANALYSIS_ARCHITECTURE.md`
- **质量设计**: 查看 `QUALITY_FIRST_DESIGN.md`

---

**Day 2完成！FastAPI后端已就绪！** ✅
