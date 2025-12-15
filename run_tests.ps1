# PowerShell脚本 - 运行测试

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  架构重构验证测试" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# 检查Python环境
Write-Host "检查Python环境..." -ForegroundColor Yellow
python --version

# 安装依赖（如果需要）
Write-Host "`n安装测试依赖..." -ForegroundColor Yellow
pip install pytest pytest-cov pytest-asyncio python-dotenv pydantic-settings dependency-injector --quiet

# 运行测试
Write-Host "`n运行单元测试..." -ForegroundColor Yellow
Write-Host "================================`n" -ForegroundColor Cyan

# 运行时空阻尼测试
Write-Host "1. 测试时空阻尼系数模块..." -ForegroundColor Green
python -m pytest tests/unit/test_spatio_temporal_damping.py -v --tb=short

# 运行天气服务测试
Write-Host "`n2. 测试天气服务模块..." -ForegroundColor Green
python -m pytest tests/unit/test_weather_service.py -v --tb=short

# 生成覆盖率报告
Write-Host "`n生成测试覆盖率报告..." -ForegroundColor Yellow
python -m pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "  测试完成！" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "`n查看覆盖率报告: htmlcov\index.html`n" -ForegroundColor Yellow
