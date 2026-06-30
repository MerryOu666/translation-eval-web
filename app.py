#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地翻译评测Web工具
功能：上传测试集 -> 选择模型 -> 调API翻译 -> Xcomet评分 -> 下载结果
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests
from flask import Flask, render_template, request, send_file

try:
    from tencentcloud.common import credential
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models as hunyuan_models
except Exception:
    credential = None
    hunyuan_client = None
    hunyuan_models = None

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
XCOMET_DEMO = BASE_DIR / "xcomet_demo.py"
XCOMET_URL = os.getenv("XCOMET_URL", "http://10.255.124.15:8813/xcomet-xl/file")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

LANGUAGE_OPTIONS = {
    "zh": "中文 Chinese",
    "en": "英语 English",
    "ja": "日语 Japanese",
    "ko": "韩语 Korean",
    "fr": "法语 French",
    "de": "德语 German",
    "es": "西班牙语 Spanish",
    "pt": "葡萄牙语 Portuguese",
    "it": "意大利语 Italian",
    "ru": "俄语 Russian",
    "ar": "阿拉伯语 Arabic",
    "th": "泰语 Thai",
    "vi": "越南语 Vietnamese",
    "id": "印尼语 Indonesian",
    "ms": "马来语 Malay",
    "tr": "土耳其语 Turkish",
    "hi": "印地语 Hindi",
    "nl": "荷兰语 Dutch",
    "pl": "波兰语 Polish",
    "uk": "乌克兰语 Ukrainian",
}

LANGUAGE_MAP = {
    "zh": {"baidu": "zh", "youdao": "zh-CHS", "doubao": "zh", "qwen": "Chinese", "tencent": "zh"},
    "en": {"baidu": "en", "youdao": "en", "doubao": "en", "qwen": "English", "tencent": "en"},
    "ja": {"baidu": "jp", "youdao": "ja", "doubao": "ja", "qwen": "Japanese", "tencent": "ja"},
    "ko": {"baidu": "kor", "youdao": "ko", "doubao": "ko", "qwen": "Korean", "tencent": "ko"},
    "fr": {"baidu": "fra", "youdao": "fr", "doubao": "fr", "qwen": "French", "tencent": "fr"},
    "de": {"baidu": "de", "youdao": "de", "doubao": "de", "qwen": "German", "tencent": "de"},
    "es": {"baidu": "spa", "youdao": "es", "doubao": "es", "qwen": "Spanish", "tencent": "es"},
    "pt": {"baidu": "pt", "youdao": "pt", "doubao": "pt", "qwen": "Portuguese", "tencent": "pt"},
    "it": {"baidu": "it", "youdao": "it", "doubao": "it", "qwen": "Italian", "tencent": "it"},
    "ru": {"baidu": "ru", "youdao": "ru", "doubao": "ru", "qwen": "Russian", "tencent": "ru"},
    "ar": {"baidu": "ara", "youdao": "ar", "doubao": "ar", "qwen": "Arabic", "tencent": "ar"},
    "th": {"baidu": "th", "youdao": "th", "doubao": "th", "qwen": "Thai", "tencent": "th"},
    "vi": {"baidu": "vie", "youdao": "vi", "doubao": "vi", "qwen": "Vietnamese", "tencent": "vi"},
    "id": {"baidu": "id", "youdao": "id", "doubao": "id", "qwen": "Indonesian", "tencent": "id"},
    "ms": {"baidu": "may", "youdao": "ms", "doubao": "ms", "qwen": "Malay", "tencent": "ms"},
    "tr": {"baidu": "tr", "youdao": "tr", "doubao": "tr", "qwen": "Turkish", "tencent": "tr"},
    "hi": {"baidu": "hi", "youdao": "hi", "doubao": "hi", "qwen": "Hindi", "tencent": "hi"},
    "nl": {"baidu": "nl", "youdao": "nl", "doubao": "nl", "qwen": "Dutch", "tencent": "nl"},
    "pl": {"baidu": "pl", "youdao": "pl", "doubao": "pl", "qwen": "Polish", "tencent": "pl"},
    "uk": {"baidu": "ukr", "youdao": "uk", "doubao": "uk", "qwen": "Ukrainian", "tencent": "uk"},
}

MODEL_OPTIONS = {
    "baidu": "百度翻译API",
    "youdao": "有道大模型翻译接口",
    "qwen-mt-plus": "阿里千问 qwen-mt-plus",
    "qwen-mt-flash": "阿里千问 qwen-mt-flash",
    "doubao-seed-translation": "豆包 Seed-Translation",
    "hunyuan-translation": "腾讯 hunyuan-translation",
    "hunyuan-translation-lite": "腾讯 hunyuan-translation-lite",
}


def clean_cell(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def sanitize_for_xcomet(value: str) -> str:
    return re.sub(r"[\t\r\n]+", " ", clean_cell(value)).strip()


def read_testset(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                text = line.rstrip("\n")
                if text:
                    rows.append({"测试用例": text})
        df = pd.DataFrame(rows)

    if "测试用例" not in df.columns:
        if "query" in df.columns:
            df = df.rename(columns={"query": "测试用例"})
        else:
            raise ValueError("测试集必须包含列：测试用例（或 query）")

    df = df[df["测试用例"].apply(lambda x: bool(clean_cell(x)))].copy()
    df["测试用例"] = df["测试用例"].apply(clean_cell)
    return df


def baidu_translate(text: str, source: str, target: str, creds: Dict[str, str]) -> str:
    appid = creds.get("baidu_appid", "").strip()
    secret = creds.get("baidu_secret", "").strip()
    if not appid or not secret:
        raise ValueError("百度翻译需要 APPID 和密钥")
    salt = str(random.randint(10000, 99999))
    sign = hashlib.md5((appid + text + salt + secret).encode("utf-8")).hexdigest()
    params = {
        "q": text,
        "from": LANGUAGE_MAP[source]["baidu"],
        "to": LANGUAGE_MAP[target]["baidu"],
        "appid": appid,
        "salt": salt,
        "sign": sign,
    }
    resp = requests.post("https://fanyi-api.baidu.com/api/trans/vip/translate", data=params, timeout=30)
    data = resp.json()
    if "trans_result" not in data:
        raise RuntimeError(f"百度API错误：{data}")
    return "\n".join(item.get("dst", "") for item in data["trans_result"]).strip()


def youdao_translate(text: str, source: str, target: str, creds: Dict[str, str]) -> str:
    app_key = creds.get("youdao_app_key", "").strip()
    app_secret = creds.get("youdao_app_secret", "").strip()
    if not app_key or not app_secret:
        raise ValueError("有道大模型需要应用ID和应用密钥")
    salt = str(int(time.time() * 1000) % 100000)
    curtime = str(int(time.time()))
    input_str = text if len(text) <= 20 else text[:10] + str(len(text)) + text[-10:]
    sign = hashlib.sha256((app_key + input_str + salt + curtime + app_secret).encode("utf-8")).hexdigest()
    payload = {
        "appKey": app_key,
        "salt": salt,
        "curtime": curtime,
        "sign": sign,
        "signType": "v3",
        "i": text,
        "from": LANGUAGE_MAP[source]["youdao"],
        "to": LANGUAGE_MAP[target]["youdao"],
        "streamType": "full",
        "handleOption": "3",
    }
    resp = requests.post("https://openapi.youdao.com/proxy/http/llm-trans", data=payload, timeout=60, stream=True)
    result_text = ""
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode("utf-8")
        if not line_str.startswith("data:"):
            continue
        data = json.loads(line_str[5:].strip())
        if data.get("code") not in (None, "0", 0):
            raise RuntimeError(f"有道API错误：{data}")
        payload_data = data.get("data") or {}
        if "transFull" in payload_data:
            result_text = payload_data["transFull"]
    return result_text.strip()


def qwen_translate(text: str, source: str, target: str, model: str, creds: Dict[str, str]) -> str:
    api_key = creds.get("qwen_api_key", "").strip()
    if not api_key:
        raise ValueError("阿里千问需要 DashScope API Key")
    source_name = LANGUAGE_MAP[source]["qwen"]
    target_name = LANGUAGE_MAP[target]["qwen"]
    prompt = f"Translate the following text from {source_name} to {target_name}. Only output the translation:\n\n{text}"
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", json=payload, headers=headers, timeout=60)
    data = resp.json()
    if "choices" not in data:
        raise RuntimeError(f"阿里千问API错误：{data}")
    return data["choices"][0]["message"]["content"].strip()


def doubao_translate(text: str, source: str, target: str, creds: Dict[str, str]) -> str:
    api_key = creds.get("doubao_api_key", "").strip()
    endpoint = creds.get("doubao_endpoint", "").strip()
    if not api_key or not endpoint:
        raise ValueError("豆包需要 API Key 和接入点ID")
    payload = {
        "model": endpoint,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": text, "translation_options": {"source_language": LANGUAGE_MAP[source]["doubao"], "target_language": LANGUAGE_MAP[target]["doubao"]}}]}],
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post("https://ark.cn-beijing.volces.com/api/v3/responses", json=payload, headers=headers, timeout=60)
    data = resp.json()
    try:
        return data["output"][0]["content"][0]["text"].strip()
    except Exception:
        raise RuntimeError(f"豆包API错误：{data}")


def hunyuan_translate(text: str, source: str, target: str, model: str, creds: Dict[str, str]) -> str:
    if credential is None:
        raise RuntimeError("请先安装 tencentcloud-sdk-python")
    secret_id = creds.get("tencent_secret_id", "").strip()
    secret_key = creds.get("tencent_secret_key", "").strip()
    if not secret_id or not secret_key:
        raise ValueError("腾讯混元需要 SecretId 和 SecretKey")
    cred = credential.Credential(secret_id, secret_key)
    client = hunyuan_client.HunyuanClient(cred, "ap-beijing")
    req = hunyuan_models.ChatTranslationsRequest()
    req.Model = model
    req.Source = LANGUAGE_MAP[source]["tencent"]
    req.Target = LANGUAGE_MAP[target]["tencent"]
    req.Text = text
    req.Stream = False
    resp = client.ChatTranslations(req)
    return resp.Choices[0].Message.Content.strip()


def translate_one(text: str, source: str, target: str, model: str, creds: Dict[str, str]) -> str:
    if model == "baidu":
        return baidu_translate(text, source, target, creds)
    if model == "youdao":
        return youdao_translate(text, source, target, creds)
    if model in ("qwen-mt-plus", "qwen-mt-flash"):
        return qwen_translate(text, source, target, model, creds)
    if model == "doubao-seed-translation":
        return doubao_translate(text, source, target, creds)
    if model in ("hunyuan-translation", "hunyuan-translation-lite"):
        return hunyuan_translate(text, source, target, model, creds)
    raise ValueError(f"不支持的模型：{model}")


def run_xcomet(originals: List[str], translations: List[str]) -> Tuple[List[float], List[float]]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
        tmp_path = Path(tmp.name)
        for original, translation in zip(originals, translations):
            tmp.write(f"{sanitize_for_xcomet(original)}\t{sanitize_for_xcomet(translation)}\n")
    try:
        result = subprocess.run(["python3", str(XCOMET_DEMO), "-i", str(tmp_path)], capture_output=True, text=True, timeout=300)
        parsed = ast.literal_eval(result.stdout.strip())
        scores = parsed.get("scores", [])
        mqm_scores = parsed.get("mqm_scores", [])
    finally:
        tmp_path.unlink(missing_ok=True)
    while len(scores) < len(originals):
        scores.append(0.0)
    while len(mqm_scores) < len(originals):
        mqm_scores.append(0.0)
    return scores[: len(originals)], mqm_scores[: len(originals)]


def correct_obvious_failures(originals: List[str], translations: List[str], scores: List[float], mqm_scores: List[float]) -> None:
    for idx, (original, translation) in enumerate(zip(originals, translations)):
        if not translation.strip() or translation.strip() == original.strip():
            scores[idx] = 0.0
            mqm_scores[idx] = 0.0


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", models=MODEL_OPTIONS, languages=LANGUAGE_OPTIONS)


@app.route("/run", methods=["POST"])
def run_task():
    try:
        uploaded = request.files["testset"]
        model = request.form["model"]
        source = request.form["source"]
        target = request.form["target"]
        creds = dict(request.form)
        job_id = uuid.uuid4().hex[:10]
        input_path = UPLOAD_DIR / f"{job_id}_{uploaded.filename}"
        uploaded.save(input_path)

        df = read_testset(input_path)
        originals = df["测试用例"].tolist()
        translations = []
        errors = []
        for idx, text in enumerate(originals, start=1):
            try:
                translated = translate_one(text, source, target, model, creds)
            except Exception as exc:
                translated = ""
                errors.append(f"第{idx}行失败：{exc}")
            translations.append(translated)
            time.sleep(float(request.form.get("delay", "0.2")))

        scores, mqm_scores = run_xcomet(originals, translations)
        correct_obvious_failures(originals, translations, scores, mqm_scores)

        result_df = pd.DataFrame({
            "query": originals,
            "translation": translations,
            "综合得分": scores,
            "MQM得分": mqm_scores,
        })
        avg_score = sum(scores) / len(scores) if scores else 0.0
        summary_df = pd.DataFrame([{
            "模型": MODEL_OPTIONS[model],
            "源语言": source,
            "目标语言": target,
            "样本数": len(originals),
            "综合得分平均分": round(avg_score, 4),
            "失败行数": len(errors),
        }])

        txt_path = OUTPUT_DIR / f"{job_id}_{model}_translation.txt"
        xlsx_path = OUTPUT_DIR / f"{job_id}_{model}_evaluation.xlsx"
        with txt_path.open("w", encoding="utf-8") as f:
            for original, translation in zip(originals, translations):
                f.write(f"{original}\t{translation}\n")
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="评估", index=False)
            summary_df.to_excel(writer, sheet_name="综合得分统计", index=False)
            if errors:
                pd.DataFrame({"错误": errors}).to_excel(writer, sheet_name="错误日志", index=False)

        return render_template("result.html", job_id=job_id, model=MODEL_OPTIONS[model], avg=round(avg_score, 4), count=len(originals), errors=errors[:20], txt_name=txt_path.name, xlsx_name=xlsx_path.name)
    except Exception as exc:
        return render_template("error.html", error=str(exc)), 500


@app.route("/download/<filename>")
def download(filename: str):
    path = OUTPUT_DIR / filename
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "7860")), debug=os.getenv("FLASK_DEBUG") == "1")
