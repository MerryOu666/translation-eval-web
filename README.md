# Translation Eval Web

一个本地/云端可部署的翻译模型评测 Web 工具：上传测试集 → 选择模型 → 调用翻译 API → Xcomet 自动评分 → 下载翻译结果与评估 Excel。

## 功能

- 支持上传 `.xlsx`、`.xls`、`.csv`、`.txt`
- 支持 20 种语种选择
- 支持模型：
  - 百度翻译 API
  - 有道大模型翻译接口
  - 阿里千问 qwen-mt-plus
  - 阿里千问 qwen-mt-flash
  - 豆包 Seed-Translation
  - 腾讯 hunyuan-translation
  - 腾讯 hunyuan-translation-lite
- 输出：
  - `原文<TAB>译文` TXT
  - 评估 Excel：`评估`、`综合得分统计`、`错误日志`

## 重要说明：GitHub 不能直接长期运行服务

GitHub 只负责托管代码，不负责长期运行 Flask Web 服务。要“一直提供服务”，需要部署到云平台，例如：

- Render
- Railway
- Fly.io
- Google Cloud Run
- AWS App Runner
- 自己的云服务器

本项目已提供：

- `Dockerfile`
- `render.yaml`
- `requirements.txt`

可以直接作为 Render/Railway/Fly/Cloud Run 的部署源。

## Xcomet 评分服务要求

本项目内置了：

```text
xcomet_demo.py
```

但它仍需要访问 Xcomet 服务。默认地址：

```text
http://10.255.124.15:8813/xcomet-xl
```

如果部署到公网云平台，这个内网地址通常无法访问。你需要：

1. 将 Xcomet 服务部署成公网可访问服务；或
2. 将本 Web 工具部署到能访问该内网地址的同一网络/VPC；或
3. 修改环境变量 `XCOMET_URL` / `XCOMET_BASE_URL` 指向可访问的 Xcomet 服务。

否则翻译可以运行，但评分会失败。

## 本地启动

```bash
cd translation_eval_web
pip install -r requirements.txt
python app.py
```

访问：

```text
http://127.0.0.1:5057
```

## Docker 启动

```bash
docker build -t translation-eval-web .
docker run -p 5057:5057 \
  -e PORT=5057 \
  -e XCOMET_URL=http://your-xcomet-host/xcomet-xl/file \
  translation-eval-web
```

访问：

```text
http://127.0.0.1:5057
```

## Render 部署

1. 将本项目推送到 GitHub。
2. 登录 Render。
3. New → Blueprint。
4. 选择该 GitHub 仓库。
5. Render 会读取 `render.yaml`。
6. 在环境变量里配置：

```text
XCOMET_URL=https://your-public-xcomet-service/xcomet-xl/file
XCOMET_BASE_URL=https://your-public-xcomet-service/xcomet-xl
```

> 注意：API Key 不建议写死在环境变量中，因为本工具设计为用户在页面表单中填写各平台 API 凭证。

## 支持语种（20种）

| 代码 | 语种 |
|---|---|
| zh | 中文 Chinese |
| en | 英语 English |
| ja | 日语 Japanese |
| ko | 韩语 Korean |
| fr | 法语 French |
| de | 德语 German |
| es | 西班牙语 Spanish |
| pt | 葡萄牙语 Portuguese |
| it | 意大利语 Italian |
| ru | 俄语 Russian |
| ar | 阿拉伯语 Arabic |
| th | 泰语 Thai |
| vi | 越南语 Vietnamese |
| id | 印尼语 Indonesian |
| ms | 马来语 Malay |
| tr | 土耳其语 Turkish |
| hi | 印地语 Hindi |
| nl | 荷兰语 Dutch |
| pl | 波兰语 Polish |
| uk | 乌克兰语 Ukrainian |

不同厂商 API 对语种支持范围不完全一致。如果某平台不支持某语种，会在错误日志中显示。

## 测试集格式

### Excel / CSV

必须包含以下任一列名：

- `测试用例`
- `query`

推荐格式：

| 序号 | 类别 | 语种 | 语种代码 | 测试用例 |
|---|---|---|---|---|
| 1 | 常规文案 | 中文 | zh | 快递包裹已经到达驿站，请凭取件码前往领取。 |

工具只读取 `测试用例` 或 `query` 列。其他列会被忽略。

### TXT

每行一条测试用例，UTF-8 编码。

```text
快递包裹已经到达驿站，请凭取件码前往领取。
消防演练将于本周五上午十点在办公楼北侧广场进行。
```

## 评分规则

- 调用 Xcomet 的 `scores` 作为综合得分。
- 评分前清洗单条文本内部的换行和 TAB，避免 `原文<TAB>译文` 格式错位。
- 如果译文为空，或译文与原文完全一致，综合得分和 MQM 得分强制置 0。

## API 凭证

各平台 API 凭证在页面表单中填写，仅用于当前请求：

| 模型 | 需要填写 |
|---|---|
| 百度翻译 API | APPID、密钥 |
| 有道大模型翻译 | 应用ID、应用密钥 |
| 阿里千问 | DashScope API Key |
| 豆包 Seed-Translation | Ark API Key、接入点 ID |
| 腾讯混元翻译 | SecretId、SecretKey |

## 安全建议

- 不要把真实 API Key 提交到 GitHub。
- 不要把 `.env`、`uploads/`、`outputs/` 中的敏感文件提交到 GitHub。
- 部署公网服务时，建议增加登录鉴权，避免 API Key 被他人滥用。
