# 🚀 GAODE 空间智能系统部署指南

**版本**: 2.0.0  
**更新时间**: 2025-12-14  
**适用环境**: 开发 / 测试 / 生产

---

## 📋 目录

1. [环境要求](#环境要求)
2. [快速开始](#快速开始)
3. [配置说明](#配置说明)
4. [本地开发](#本地开发)
5. [生产部署](#生产部署)
6. [监控和维护](#监控和维护)
7. [常见问题](#常见问题)

---

## 🔧 环境要求

### **硬件要求**

| 环境 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发环境 | 2核+ | 4GB+ | 10GB+ |
| 测试环境 | 4核+ | 8GB+ | 20GB+ |
| 生产环境 | 8核+ | 16GB+ | 50GB+ |

### **软件要求**

- **Python**: 3.8+ (推荐 3.9 或 3.10)
- **pip**: 最新版本
- **操作系统**: Windows / Linux / macOS

### **第三方服务**

必需：
- ✅ **高德开放平台 API Key**
  - 注册地址: https://lbs.amap.com/
  - 需要开通的服务: Web服务API（路径规划、POI搜索、地理编码等）

可选：
- Redis (用于缓存)
- PostgreSQL / MySQL (用于数据持久化)
- Nginx (反向代理)

---

## ⚡ 快速开始

### **步骤1: 克隆项目**

```bash
# 如果从Git仓库克隆
git clone <repository_url>
cd GAODE

# 或者直接使用现有目录
cd c:\Users\86176\Desktop\GAODE
```

### **步骤2: 安装依赖**

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### **步骤3: 配置API Key**

创建 `config.py` 文件：

```python
# config.py
GAODE_API_KEY = "your_gaode_api_key_here"  # 替换为你的高德API Key
```

⚠️ **重要**: 不要将 `config.py` 提交到版本控制！

### **步骤4: 启动服务**

```bash
# 启动API服务器
python api_server_progressive.py

# 或使用uvicorn（生产环境推荐）
uvicorn api_server_progressive:app --host 0.0.0.0 --port 8000 --reload
```

### **步骤5: 访问服务**

- **API文档**: http://localhost:8000/docs
- **前端页面**: 打开 `frontend/progressive.html`
- **健康检查**: http://localhost:8000/

---

## ⚙️ 配置说明

### **环境变量**

可以通过环境变量覆盖默认配置：

```bash
# Windows (CMD)
set GAODE_API_KEY=your_key_here
set LOG_LEVEL=INFO
set CACHE_TTL=3600

# Windows (PowerShell)
$env:GAODE_API_KEY="your_key_here"
$env:LOG_LEVEL="INFO"

# Linux/Mac
export GAODE_API_KEY=your_key_here
export LOG_LEVEL=INFO
export CACHE_TTL=3600
```

### **配置文件**

系统配置集中在 `src/core/config_params.py`：

```python
from src.core.config_params import SystemConfig, ConfigPresets

# 使用预设配置
config = ConfigPresets.get_quality_first_config()

# 或自定义配置
SystemConfig.update_planner_config(
    max_distance_km=100.0,
    min_trust_score=0.7
)
```

### **日志配置**

日志系统在 `src/utils/logger.py`：

```python
from src.utils.logger import system_logger

# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
system_logger.info("系统启动", version="2.0.0")
```

日志文件位置: `logs/`

---

## 💻 本地开发

### **开发模式启动**

```bash
# 开发模式（自动重载）
uvicorn api_server_progressive:app --reload --log-level debug

# 指定端口
uvicorn api_server_progressive:app --port 8080 --reload
```

### **运行测试**

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_core_components.py -v

# 查看测试覆盖率
pytest --cov=src tests/
```

### **代码检查**

```bash
# 使用pylint
pylint src/

# 使用flake8
flake8 src/

# 使用black格式化
black src/
```

### **调试技巧**

1. **使用Mock API Key**
   ```python
   # config.py
   GAODE_API_KEY = "mock_key"  # 系统会使用Mock数据
   ```

2. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **使用Python调试器**
   ```python
   import pdb; pdb.set_trace()  # 设置断点
   ```

---

## 🏭 生产部署

### **方式1: 直接部署 (单机)**

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
export GAODE_API_KEY=your_production_key
export LOG_LEVEL=INFO

# 3. 使用Gunicorn启动（推荐）
gunicorn api_server_progressive:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log

# 4. 使用Supervisor管理进程（可选）
# 参考 deployment/supervisor.conf
```

### **方式2: Docker部署**

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api_server_progressive:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 构建镜像
docker build -t gaode-system:2.0.0 .

# 运行容器
docker run -d \
    --name gaode-api \
    -p 8000:8000 \
    -e GAODE_API_KEY=your_key \
    -v $(pwd)/logs:/app/logs \
    gaode-system:2.0.0
```

### **方式3: Docker Compose（推荐）**

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GAODE_API_KEY=${GAODE_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    restart: always
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: always
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - api
    restart: always
```

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### **Nginx配置示例**

```nginx
# nginx.conf
upstream api_backend {
    server api:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        index progressive.html;
        try_files $uri $uri/ /progressive.html;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
    }
}
```

---

## 📊 监控和维护

### **健康检查**

```bash
# 检查API状态
curl http://localhost:8000/

# 期望输出
{
  "name": "Event Horizon Progressive API",
  "version": "2.0.0",
  "status": "running",
  "poi_count": 150,
  "active_sessions": 5
}
```

### **日志监控**

```bash
# 查看实时日志
tail -f logs/system_*.jsonl

# 查看错误日志
tail -f logs/error_*.jsonl

# 统计错误数量
grep "ERROR" logs/*.jsonl | wc -l
```

### **性能监控**

系统提供内置性能指标：

```python
from src.utils.logger import performance_monitor

# 查看性能摘要
summary = performance_monitor.get_summary()
print(summary)
```

### **数据库备份**

```bash
# 备份POI缓存数据（如果使用持久化）
# 定期备份logs目录
tar -czf backup_$(date +%Y%m%d).tar.gz logs/ config/
```

### **系统更新**

```bash
# 1. 备份当前版本
cp -r GAODE GAODE_backup_$(date +%Y%m%d)

# 2. 拉取最新代码
git pull origin main

# 3. 更新依赖
pip install -r requirements.txt --upgrade

# 4. 重启服务
# Docker:
docker-compose restart

# Supervisor:
supervisorctl restart gaode-api
```

---

## 🔍 常见问题

### **Q1: API Key无效或配额不足**

**症状**: 无法获取POI数据，返回错误
**解决**:
1. 检查API Key是否正确配置
2. 登录高德开放平台检查配额使用情况
3. 如需要，升级到更高配额的套餐

### **Q2: 服务启动慢**

**症状**: `startup_event()` 执行时间长
**解决**:
```python
# 减少启动时加载的POI数量
all_pois = poi_db.get_pois_in_city("苏州", limit=50)  # 从200改为50
```

### **Q3: 内存占用高**

**症状**: 系统内存持续增长
**解决**:
1. 限制活跃会话数量
2. 定期清理过期会话
3. 启用Redis缓存（外部存储）

```python
# 清理过期会话
def cleanup_old_sessions():
    now = datetime.now()
    for sid in list(sessions.keys()):
        session_time = sessions[sid].get('created_at')
        if (now - session_time).hours > 2:
            del sessions[sid]
```

### **Q4: CORS错误**

**症状**: 前端无法访问API
**解决**: 检查CORS配置

```python
# api_server_progressive.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **Q5: POI搜索结果为空**

**症状**: 无法获取候选POI
**解决**:
1. 检查城市名称是否正确
2. 放宽距离限制
3. 关闭质量过滤

```python
planner.config['max_distance_km'] = 100.0
planner.config['enable_quality_filter'] = False
```

---

## 📞 技术支持

### **获取帮助**

- 📧 Email: support@example.com
- 💬 Issues: https://github.com/your-repo/issues
- 📖 文档: 查看项目根目录的Markdown文档

### **报告Bug**

请提供以下信息：
1. 系统版本
2. 错误日志
3. 复现步骤
4. 环境信息（OS、Python版本等）

---

## 📝 更新日志

### v2.0.0 (2025-12-14)
- ✅ 修复POIType.OTHER引用错误
- ✅ 实现公交和地铁路径规划
- ✅ 添加神经网络服务接口
- ✅ 完善多源数据采集容错
- ✅ 集中配置管理系统
- ✅ 添加结构化日志系统
- ✅ 完善部署文档

### v1.0.0 (2025-12-10)
- 初始版本发布

---

## 🎉 部署成功

如果所有步骤都正确执行，你应该能看到：

```
🚀 初始化渐进式规划系统...
   ✅ AI大脑（SpatialIntelligenceCore）已启用
   ✅ ProgressivePlanner配置已优化
✅ 系统初始化完成！
   POI数据: 150 个
   高德API: 已连接
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**恭喜！系统已成功部署！** 🎊

访问 http://localhost:8000/docs 查看API文档并开始使用。

---

**编写者**: 世界顶级空间智能体编程师  
**最后更新**: 2025-12-14  
**文档版本**: 2.0.0
