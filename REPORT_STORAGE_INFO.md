# 研究报告存储位置说明

## 📍 研究报告存储位置

### 1. **流式响应中（主要来源）**
- **位置**: 通过 Server-Sent Events (SSE) 发送
- **事件类型**: `research_complete`
- **数据字段**: `data.report`
- **格式**: Markdown 或 HTML 格式的字符串
- **生命周期**: 仅在流式连接期间可用

### 2. **前端内存中**
- **位置**: React 组件状态 (`finalReportData`)
- **组件**: `App.js` → `ResearchPanel` → `FinalReport`
- **生命周期**: 页面刷新后丢失

### 3. **前端下载功能**
研究报告可以通过前端界面下载为：
- **PDF**: 使用 `html2pdf.js` 生成
- **HTML**: 可直接在浏览器中打开
- **DOCX**: 使用 `docx` 库生成 Word 文档

下载按钮位置: `FinalReport` 组件中的下载按钮

### 4. **后端存储**
- **默认**: ❌ 不自动保存到文件系统
- **Benchmark 模式**: ✅ 会保存到 `benchmarks/` 目录下的 JSON 文件
- **命令行模式**: ✅ 可以指定输出文件路径

## 💾 如何保存报告

### 方法 1: 使用提供的脚本
```bash
python save_report_example.py
```

### 方法 2: 通过 API 获取并保存
研究报告通过流式 API 返回，需要：
1. 启动研究任务 (`POST /deep-research`)
2. 连接流式端点 (`GET /stream/{stream_id}`)
3. 等待 `research_complete` 事件
4. 从 `data.report` 字段提取报告内容
5. 保存到文件

### 方法 3: 前端下载
1. 在浏览器中打开应用
2. 等待研究完成
3. 点击报告页面的下载按钮（PDF/HTML/DOCX）

## 📂 报告文件格式

研究报告通常包含：
- **Markdown 格式**: 纯文本，包含标题、段落、列表、代码块等
- **HTML 格式**: 包含样式和格式的 HTML 内容
- **可视化**: 可能包含图表和图片（base64 编码）

## 🔍 查找报告

如果使用 benchmark 模式或命令行工具：
- **Benchmark 结果**: `benchmarks/results/` 目录
- **命令行输出**: 指定的输出文件路径

## ⚠️ 注意事项

1. **流式模式**: 报告只在流式连接期间可用，连接断开后无法重新获取
2. **非持久化**: 默认情况下报告不会保存到服务器
3. **建议**: 研究完成后立即下载或保存报告
