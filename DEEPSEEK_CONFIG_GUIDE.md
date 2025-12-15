# DeepSeek API 配置指南

## 🚀 快速配置

### 方式1: 修改 config.py（推荐）

编辑 `c:\Users\Administrator\Desktop\GAODE\config.py`：

```python
# 第52-54行
llm_api_key: str = Field(
    default="sk-your-deepseek-api-key-here",  # ← 填入你的DeepSeek API Key
    description="LLM API密钥"
)
```

### 方式2: 使用环境变量（最安全）

**PowerShell:**
```powershell
$env:LLM_API_KEY="sk-your-deepseek-api-key-here"
python xiamen_ultimate.py
```

**或创建 .env 文件:**
```bash
# 在项目根目录创建 .env 文件
LLM_API_KEY=sk-your-deepseek-api-key-here
```

---

## 📝 获取 DeepSeek API Key

1. 访问: https://platform.deepseek.com/
2. 注册/登录账号
3. 进入"API Keys"页面
4. 创建新的API Key
5. 复制并填入上面的配置

---

## 💰 价格对比（2024年12月）

| 模型 | 输入价格 | 输出价格 | 性价比 |
|------|---------|---------|--------|
| **DeepSeek** | ¥0.001/千tokens | ¥0.002/千tokens | ⭐⭐⭐⭐⭐ |
| GPT-3.5-Turbo | $0.0005/千tokens | $0.0015/千tokens | ⭐⭐⭐ |
| GPT-4 | $0.03/千tokens | $0.06/千tokens | ⭐ |

**示例：规划一次厦门旅行（约20次LLM调用）**
- DeepSeek成本: ≈ ¥0.04元（极便宜！）
- GPT-3.5成本: ≈ ¥0.20元
- GPT-4成本: ≈ ¥4.00元

---

## ✅ 验证配置

运行测试：
```bash
python xiamen_ultimate.py
```

如果配置成功，会看到：
```
🔧 初始化核心组件...
✅ 高德API客户端
   🤖 真实DeepSeek大模型已启用（deepseek-chat）
✅ W轴初始化完成（δ=0.1, ε=0.1）
✅ W轴 + 真实DeepSeek大模型 🤖
```

运行时会看到LLM推理日志：
```
   🤖 LLM推理[1]: 鼓浪屿→厦门市博物馆 = 0.850
   🤖 LLM推理[2]: 厦门市博物馆→局口拌面 = 0.920
   ...
```

---

## 🔧 配置当前已生效

当前系统配置：
- API Base: `https://api.deepseek.com/v1`
- 模型: `deepseek-chat`
- 只需填入 API Key 即可使用！

---

## ⚠️ 常见问题

### Q1: 看到 "📋 无API Key，使用智能规则"
**A:** 说明API Key未配置，系统使用规则模拟。按上面方式配置即可。

### Q2: 看到 "openai库未安装"
**A:** 运行安装命令：
```bash
pip install openai
```

### Q3: 看到 "LLM调用失败"
**A:** 检查：
1. API Key是否正确
2. 网络连接是否正常
3. DeepSeek服务是否可用

---

## 📊 系统会自动统计LLM调用

运行结束时会显示：
```
✅ 集成验证:
   ...
   大模型推理: ✅ 真实DeepSeek调用 (15次) 🤖
   ...
```

这说明大模型真正被调用了！
