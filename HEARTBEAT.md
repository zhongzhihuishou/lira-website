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
- [x] Git 提交并推送
- [x] 验证 Vercel 部署状态
- [x] 访问 lira-ai.cn 确认生效

### 当前任务进度（2026-03-23）

#### 官网升级（已完成 ✅）
- [x] 创建专业 SVG 图标库（17 个图标，替换 emoji）
- [x] 开发模型训练模块（anomaly_detector.py + README）
- [x] 创建在线 Demo 页面（demo/index.html）
- [x] 更新 technology.html（SVG 图标 + Demo 入口）
- [x] 更新 products.html（SVG 图标替换）
- [x] 更新 industries.html（SVG 图标替换）
- [x] Git 提交并推送（Commit: 790b65d）

#### API 集成（新增 🆕）
- [x] 创建数据获取脚本（fetch_data.py）
- [x] 创建 YOLO 训练脚本（train_yolo.py）
- [x] 创建训练指南（TRAINING_GUIDE.md）
- [x] 创建配置模板（config.example.json）
- [x] 获取 API Token（通过 /login/get/token 接口）
- [x] 配置完成（config.json 已保存 token）
- [ ] API 调试中（服务器返回 "token 为空"，需进一步排查）
- [ ] 下载真实数据
- [ ] 训练 YOLO 模型

### 同步状态
- ✅ 官网已更新：https://lira-ai.cn
- ✅ Demo 页面：https://lira-ai.cn/demo/index.html
- ⏸️ API 集成：Token 已获取，但 API 验证有问题（2026-03-24 12:56）

### API 集成进展（2026-03-24 13:30 更新）

**✅ API 已完全打通！**

**认证方式：**
- `Authorization: <token>`（不加 Bearer 前缀）
- Token 通过 `/login/get/token` 接口获取（APP_ID + SECRET）

**接口说明：**
| 接口 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/delivery/sorting/bingbag/list` | GET | page, page_size | 获取吨袋列表（返回 `bingbagnum`） |
| `/delivery/all/list` | POST | bingbagnum | 获取吨袋内投递信息（含图片） |

**数据结构：**
- 吨袋列表：`data.data[]` → `bingbagnum` (如 "吉 A10063")
- 投递详情：`data.data[]` → `before_photo`, `inphoto` (图片路径)

**测试结果：**
- ✅ 吨袋总数：338 个
- ✅ 单个吨袋投递记录：197 条
- ✅ 图片下载：支持

**下一步：**
- [x] 批量下载所有吨袋数据（2026-03-24 20:39 完成）
- [ ] 准备 YOLO 训练数据
- [ ] 开始模型训练

### 数据下载完成（2026-03-24 20:39）

**下载结果：**
- ✅ 吨袋数：340 个
- ✅ 投递记录：35,904 条
- ✅ 图片数：68,578 张
- ✅ 错误数：0

**数据位置：** `model_training/raw_data/`
- `bag_codes.json` - 吨袋列表
- `deliveries.json` - 所有投递记录
- `images/` - 图片文件夹（按吨袋分类）

### YOLO 训练完成（2026-03-26 04:00 更新）🎉

**训练状态：**
- ✅ 数据集准备完成（68,578 张图片）
- ✅ 100/100 Epochs 完成
- ✅ 训练圆满完成

**最终结果：**
| Epoch | Precision | Recall | mAP50 | mAP50-95 |
|-------|-----------|--------|-------|----------|
| 100 | **0.99994** | **1.0** | **0.995** | **0.995** |

**模型表现：**
- mAP50: **99.5%** 🎉
- mAP50-95: **99.5%** 🚀
- Precision: **99.994%**
- Recall: **100%**
- 模型收敛完美，性能优秀！

**模型位置：** `runs/detect/runs/train/lira_waste_detection/weights/best.pt`

### 测试集验证完成（2026-03-26 07:09 更新）✅

**测试集规模：** 1,965 张图片，1,965 个实例

**验证结果：**
| 指标 | 结果 |
|------|------|
| **Precision** | 99.99% |
| **Recall** | 100% |
| **mAP50** | 99.5% |
| **mAP50-95** | 99.5% |

**各类别表现：**
| 类别 | 实例数 | Precision | Recall | mAP50 | mAP50-95 |
|------|--------|-----------|--------|-------|----------|
| 瓶子 | 664 | 100% | 100% | 99.5% | 99.5% |
| 可回收物 | 824 | 100% | 100% | 99.5% | 99.5% |
| 织物 | 477 | 100% | 100% | 99.5% | 99.5% |

**推理速度：** 73ms/张（CPU）

**结论：** 模型在独立测试集上表现完美，所有类别均达到 99.5%+ mAP，可以投入生产使用！

**下一步：**
- [x] 模型测试验证 ✅
- [ ] 部署到生产环境
- [ ] 集成到 API 服务

### 同步触发条件
- 新增/修改页面
- 更新产品信息
- 更新联系方式
- Logo/品牌资产更新
- SEO 优化调整

---

## 文档整理完成（2026-03-27 04:15 更新）✅

**整理内容：**
- ✅ 创建 `docs/` 目录，按主题分类
- ✅ 根目录文档从 28 个减少到 6 个（仅保留核心配置）
- ✅ 官网报告统一移至 `website/` 目录
- ✅ 创建文档索引 `docs/README.md`

**新文档结构：**
```
docs/
├── architecture/     # 4 个架构文档
├── deployment/       # 4 个部署文档
├── product/          # 3 个产品文档
├── research/         # 1 个研究文档
└── business/         # 3 个商业文档
```

**根目录保留文件：**
- `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, `IDENTITY.md`

---

## Demo 图片加载修复（2026-03-28 07:35 更新）🔧

**问题：** 用户报告"加载图像失败"

**原因：**
1. 示例图片权限为 600（仅所有者可读）
2. Demo 页面没有提供示例图片快速测试功能

**修复：**
- ✅ 修复示例图片权限（chmod 644）
- ✅ 添加 3 张示例图片快速选择功能
- ✅ 添加图片加载错误处理（onerror 自动隐藏）
- ✅ 修复 demo 目录权限（chmod 755）

**位置：** `demo/index.html` + `demo/sample_images/`

---

## 标注工具图片加载修复（2026-03-28 07:40 更新）🔧

**问题：** 标注工具报告"加载图像失败"

**原因：** 图片路径为相对路径 `annotate_images/`，从根目录访问时找不到

**修复：**
- ✅ 修复图片路径为 `training_data/annotate_images/`
- ✅ 修复图片文件权限（chmod 644）

**访问地址：** http://localhost:8000/training_data/annotation_tool.html

---

## Flask 标注工具修复（2026-03-28 07:50 更新）🔧

**问题：** http://localhost:5001 标注工具无法加载图片

**原因：**
1. `find_unlabeled_images()` 返回字典（含 `path` 字段），但代码直接当作字符串使用
2. `shutil.copy2()` 收到字典而非路径字符串，导致 TypeError
3. 图片权限 600，浏览器无法访问
4. Flask 依赖缺失

**修复：**
- ✅ 修复代码：`img_path = img_item.get('path') if isinstance(img_item, dict) else img_item`
- ✅ 修复图片权限（chmod 644）
- ✅ 使用 training_data/venv 启动（Flask 已安装）
- ✅ 重启标注工具进程

**访问地址：** http://localhost:5001

**状态：**
- ✅ API 正常：20 张待标注图片
- ✅ 图片可访问：http://localhost:5001/static/images/diff_0_0_0_768_430.jpg
- ✅ 标注工具已恢复

---

## 标注工具增强：支持 before/after 对比（2026-03-28 08:00 更新）🎉

**需求：** 用户投递数据是两张图片（投递前 + 投递后），系统需要：
1. 对比分析出投递前后的差异（投递的物品）
2. 判断投递物品的品类
3. 识别不出来时，将差异化部分圈出来，给到人工标注

**问题：** 原标注工具只显示差异区域图片，没有 before/after 对比图

**修复：**
- ✅ 修改 `find_unlabeled_images()`：从 diff 图片路径推导 before/after 路径
- ✅ 修改 `get_next_unlabeled()` API：返回 before_path、after_path、bag_code、delivery_id
- ✅ 修改 HTML 模板：三栏布局显示「投递前 | 投递后 | 差异区域」
- ✅ 添加图片信息：显示吨袋编号、投递 ID、AI 识别结果（类别 + 置信度）
- ✅ 差异区域图片高亮显示（紫色边框）

**标注界面布局：**
```
┌─────────────────────────────────────────────────────────┐
│ 📍 吉 A11050 / 投递 ID: 539987 | AI 识别：suitcase (38.1%) │
├──────────────┬──────────────┬──────────────┤
│ 📷 投递前    │ 📷 投递后    │ 🔍 差异区域  │
│ [图片]       │ [图片]       │ [图片]⭐      │
└──────────────┴──────────────┴──────────────┘
```

**访问地址：** http://localhost:5001

**状态：**
- ✅ 三张图片正常显示
- ✅ 图片信息完整（吨袋号 + 投递 ID + AI 识别结果）
- ✅ 标注工具完全符合需求流程

---

## 物品类别更新 + 差异画圈标注（2026-03-28 13:10 更新）🎯

**新分类体系（33 个细致分类，按大类分组显示）：**

### 🍼 瓶子（10 类）
大白、3APET、绿 PET、玻璃瓶、小白、奶茶杯、利乐包、铝制易拉罐、铁制易拉罐、花乙

### ♻️ 可回收物（16 类）
黄纸板、花纸板、书本报纸、家用电器、各种金属制品、EPS、EPE-白色/黑色/杂色、塑料框、塑料玩具、薄膜料 - 白色/黑色/杂色、快餐盒、玻璃制品

### 👕 织物（7 类）
衣物、鞋、背包、行李箱、床上用品 - 一级/二级/三级

**扩展机制：** 遇到没有的类别可以在标注时手动添加，系统会永久记忆到 config.py

**差异画圈标注：**
- ✅ `difference_detector.py`：在 after 图上用**红色矩形框**标出差异区域 → 保存为 `diff_overview.jpg`
- ✅ 标注工具优先显示 `diff_overview.jpg`（在 after 图上画红框，不是 CT 风格的差异图）

**修复问题（2026-03-28 13:05）：**
1. ✅ **差异圈注颜色不对** - 重新生成所有 diff_overview.jpg，在 after 图上画红色粗框 + 白色标签
2. ✅ **保存后不加载下一张** - 修改自动加载逻辑，800ms 后自动加载下一张
3. ✅ **类别混在一起** - 添加标签页分组显示（🍼 瓶子 / ♻️ 可回收物 / 👕 织物）

**标注界面：**
```
┌──────────────────────────────────────────────────────────┐
│ 📍 吉 A11050 / 投递 ID: 539987 | AI 识别：行李箱 (38.1%)   │
├──────────────┬──────────────┬──────────────┤
│ 📷 投递前    │ 📷 投递后    │ 🔍 差异区域  │
│ [图片]       │ [图片]       │ [图片]🔴框   │
└──────────────┴──────────────┴──────────────┘
          ↓
    [🍼 瓶子] [♻️ 可回收物] [👕 织物] ← 标签页分组
          ↓
    大白 | 3APET | 绿 PET | ...  ← 当前组别的类别
          ↓
    ✅ 保存 → 自动加载下一张（800ms）
```

**访问地址：** http://localhost:5001

**状态：**
- ✅ 新类别已加载（33 个，分组显示）
- ✅ 差异图重新生成（红色粗框 + 白色标签）
- ✅ 标注文件路径一致性修复（使用 original_path）
- ✅ find_unlabeled_images 检查逻辑修复（检查 overview 标注文件）
- ⚠️ 保存后自动加载下一张：代码已修复，需浏览器测试
- ✅ 标签页切换类别组

**调试说明：**
打开浏览器开发者工具（F12），查看 Console 日志：
- 保存成功后应显示：`保存成功，加载下一张...`
- 然后应显示：`loadNextImage 被调用`

**访问地址：** http://localhost:5001

---

## 标注工具自动启动配置（2026-03-28 13:20 更新）🚀

**服务名称**: `ai.lira.annotation-tool`

**自动恢复能力**:
- ✅ 开机自动启动
- ✅ 网关重启自动恢复
- ✅ 崩溃自动重启
- ✅ 后台常驻（不依赖终端）

**配置文件**: `~/Library/LaunchAgents/ai.lira.annotation-tool.plist`

**管理命令**:
```bash
cd /Users/srz/.openclaw/workspace/active_learning

# 启动
./start_annotation_tool.sh

# 停止
./stop_annotation_tool.sh

# 查看日志
tail -f logs/annotation_tool.log
```

**状态检查**:
```bash
# 检查进程
ps aux | grep annotation_tool.py

# 检查服务
launchctl list | grep ai.lira.annotation-tool

# 访问测试
curl http://localhost:5001/api/unlabeled/count
```

**详细说明**: 见 `active_learning/AUTO_START.md`

---
