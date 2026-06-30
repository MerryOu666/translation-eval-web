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

# 🌐 翻译模型评测工具

> 上传测试集 → 选择模型 → 调用翻译 API → Xcomet 自动评分 → 下载结果

---

## 功能介绍

本工具支持一键完成翻译模型的批量测试和质量评价：

1. **上传测试集**：支持 Excel / CSV / TXT 格式
2. **选择模型**：支持7个主流翻译 API
3. **填写凭证**：在页面表单中填写对应平台的 API Key
4. **等待结果**：系统自动完成翻译 + Xcomet 质量评分
5. **下载报告**：获取 `原文<TAB>译文` TXT 和带评分的 Excel

---

## 支持的翻译模型

| 模型 | 平台 | 所需凭证 |
|---|---|---|
| 百度翻译 API | 百度翻译开放平台 | APPID + 密钥 |
| 有道大模型翻译 | 有道智云 | 应用ID + 应用密钥 |
| qwen-mt-plus | 阿里云百炼 | DashScope API Key |
| qwen-mt-flash | 阿里云百炼 | DashScope API Key |
| Doubao Seed-Translation | 火山引擎 Ark | API Key + 接入点 ID |
| hunyuan-translation | 腾讯云 | SecretId + SecretKey |
| hunyuan-translation-lite | 腾讯云 | SecretId + SecretKey |

---

## 支持的语种（20种）

中文、英语、日语、韩语、法语、德语、西班牙语、葡萄牙语、意大利语、俄语、阿拉伯语、泰语、越南语、印尼语、马来语、土耳其语、印地语、荷兰语、波兰语、乌克兰语。

---

## 测试集格式要求

### Excel / CSV

必须包含以下任一列名：

- `测试用例`
- `query`

推荐格式：

| 序号 | 类别 | 语种 | 语种代码 | 测试用例 |
|---|---|---|---|---|
| 1 | 常规文案 | 中文 | zh | 快递包裹已经到达驿站，请凭取件码前往领取。 |
| 2 | 口语俚语 | 中文 | zh | 确实，这波操作我没话说。 |

其他列（序号、类别、语种等）会被忽略，工具只读取测试用例列。

### TXT

每行一条测试用例，UTF-8 编码：

```text
快递包裹已经到达驿站，请凭取件码前往领取。
消防演练将于本周五上午十点在办公楼北侧广场进行。
```

---

## 输出文件说明

完成后可下载两个文件：

### 1. 翻译结果 TXT

格式为 `原文<TAB>译文`，每行一条：

```text
快递包裹已经到达驿站，请凭取件码前往领取。	The express package has arrived at the post station.
消防演练将于本周五上午十点在办公楼北侧广场进行。	The fire drill will be held at 10 a.m. this Friday.
```

### 2. 评估 Excel

包含以下 sheet：

| Sheet | 内容 |
|---|---|
| 评估 | 原文、译文、综合得分、MQM 得分 |
| 综合得分统计 | 模型、语向、样本数、平均分 |
| 错误日志 | 翻译失败的行（如有） |

---

## 评分说明

- 评分工具：**Xcomet**（`scores` 综合得分，0~1，越高越好）
- 评分前自动清洗单条文本内换行/TAB，避免格式错位
- 译文为空或译文与原文完全一致 → 得分强制置 0
- Xcomet 对超长文本、稀有字符、纯符号样例可能误判，建议人工抽检

---

## 本地部署

```bash
git clone https://github.com/MerryOu666/translation-eval-web.git
cd translation-eval-web
pip install -r requirements.txt
python app.py
```

浏览器打开：

```
http://127.0.0.1:7860
```
