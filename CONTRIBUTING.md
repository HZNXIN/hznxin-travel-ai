# 贡献指南

感谢你对 JARVIS Travel Agent 项目的关注！我们欢迎任何形式的贡献。

## 🤝 如何贡献

### 报告问题
- 在 [Issues](../../issues) 中提交 bug 报告
- 请提供详细的复现步骤和环境信息
- 附上相关的错误日志或截图

### 提交代码
1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范
- Python 代码遵循 PEP 8
- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串
- 确保代码通过现有测试

### 提交信息规范
```
<type>: <subject>

<body>

<footer>
```

**Type 类型：**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

## 📝 开发流程

### 环境设置
```bash
# 克隆仓库
git clone https://github.com/your-username/GAODE.git
cd GAODE

# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/
```

### 测试
- 添加新功能时请包含测试用例
- 确保所有测试通过再提交PR
- 运行测试：`python -m pytest tests/`

### 文档
- 更新相关文档以反映你的更改
- 新功能需要在 README.md 中说明
- 复杂的功能需要在 docs/ 目录添加详细文档

## 🎯 优先开发方向

### 高优先级
- [ ] 性能优化（LLM推理加速）
- [ ] 更多城市POI数据支持
- [ ] 移动端适配

### 中优先级
- [ ] 多语言支持
- [ ] 用户账号系统
- [ ] 行程分享功能

### 低优先级
- [ ] 主题切换
- [ ] 更多地图供应商
- [ ] 数据导出功能

## 💬 讨论
- 重大更改请先在 [Discussions](../../discussions) 中讨论
- 加入我们的开发社区获取帮助

## 📄 许可证
通过贡献代码，你同意你的贡献将以 MIT 许可证授权。

---

**再次感谢你的贡献！** 🙏
