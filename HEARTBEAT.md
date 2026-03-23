# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 官网同步协议（新增）

**原则：** 网站内容更新后，自动同步到线上（GitHub + Vercel）

### 同步流程
1. **本地修改** → `website/` 目录或直接根目录
2. **Git 提交** → `git add . && git commit -m "更新说明"`
3. **推送 GitHub** → `git push origin main`
4. **Vercel 自动部署** → 无需手动操作

### 自动同步检查
- [x] 检查 website 文件变更
- [ ] Git 提交并推送
- [ ] 验证 Vercel 部署状态
- [ ] 访问 lira-ai.cn 确认生效

### 当前任务进度（2026-03-23）
- [x] 创建专业 SVG 图标库（17 个图标，替换 emoji）
- [x] 开发模型训练模块（anomaly_detector.py + README）
- [x] 创建在线 Demo 页面（demo/index.html）
- [x] 更新 technology.html（SVG 图标 + Demo 入口）
- [ ] 更新 products.html（SVG 图标替换）
- [ ] 更新 industries.html（SVG 图标替换）
- [ ] Git 提交并推送

### 同步触发条件
- 新增/修改页面
- 更新产品信息
- 更新联系方式
- Logo/品牌资产更新
- SEO 优化调整

---
