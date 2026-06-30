---
title: Translation Eval Web
emoji: 🌐
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Translation Eval Web

翻译模型评测 Web 工具：上传测试集 → 选择模型 → 调用翻译 API → Xcomet 自动评分 → 下载结果。

## 支持模型

- 百度翻译 API
- 有道大模型翻译接口
- 阿里千问 qwen-mt-plus / qwen-mt-flash
- 豆包 Seed-Translation
- 腾讯 hunyuan-translation / hunyuan-translation-lite

## 支持 20 种语种

中文、英语、日语、韩语、法语、德语、西班牙语、葡萄牙语、意大利语、俄语、阿拉伯语、泰语、越南语、印尼语、马来语、土耳其语、印地语、荷兰语、波兰语、乌克兰语。

## 测试集格式

- Excel/CSV：包含列 `测试用例` 或 `query`
- TXT：每行一条测试用例，UTF-8 编码

## API 凭证

在页面表单中填写各平台凭证，不会存储。

## 本地启动

```bash
pip install -r requirements.txt
python app.py
```
