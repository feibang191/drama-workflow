#!/usr/bin/env python3
"""
示例项目视频生成管线 — T2V + 异步轮询 + 自动下载

用途: 提交示例项目风格的视频生成任务到 图像生成 API API，轮询完成并下载
使用: python3 scripts/run_video_pipeline.py

依赖: curl, Python 3.8+, config.yaml 需含 apihub.图像生成 API-ai.com API Key

注意: 
  - execute_code 有 5 分钟超时限制，视频生成通常 3-8 分钟
  - 必须用 terminal(background=true) 运行此脚本
  - URL 会过期，脚本内部自动下载
"""

import json, subprocess, time, os, sys

# Step 1: 从 config.yaml 读 key（不从代码硬编码）
import yaml
CFG_PATH = "/mnt/c/Users/Administrator/AppData/Local/hermes/config.yaml"
if not os.path.exists(CFG_PATH):
    CFG_PATH = r"C:\Users\Administrator\AppData\Local\hermes\config.yaml"

with open(CFG_PATH) as f:
    cfg = yaml.safe_load(f)
KEY = next(
    p["api_key"] for p in cfg.get("custom_providers", [])
    if "apihub.图像生成 API" in p.get("base_url", "")
)

API = "https://apihub.图像生成 API-ai.com/v1"
TARGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "示例项目", "04_素材库", "测试生图", "video"
) if False else "/mnt/e/MyBrain/WIKI/短视频风格库/06_项目库/示例项目/04_素材库/测试生图/video"

os.makedirs(TARGET, exist_ok=True)

def log(m):
    print(m)
    with open("/tmp/video_pipeline.log", "a") as f:
        f.write(m + "\n")

def submit_video(prompt, duration=5):
    """提交T2V视频任务，返回task_id"""
    payload = json.dumps({
        "model": "图像生成 API-video-v2.0",
        "prompt": prompt,
        "n": 1,
        "duration": duration
    })
    r = subprocess.run([
        "curl", "-s", API + "/video/generations",
        "-H", "Content-Type: application/json",
        "-H", "Authorization: Bearer " + KEY,
        "-d", payload
    ], capture_output=True, text=True, timeout=120)
    resp = json.loads(r.stdout)
    tid = resp.get("task_id", "")
    if not tid:
        raise RuntimeError("提交失败: " + json.dumps(resp, ensure_ascii=False)[:200])
    return tid

def poll_video(task_id, max_polls=40, interval=15):
    """轮询视频任务直到完成"""
    for i in range(max_polls):
        time.sleep(interval)
        r = subprocess.run([
            "curl", "-s", API + "/video/generations/" + task_id,
            "-H", "Authorization: Bearer " + KEY
        ], capture_output=True, text=True, timeout=30)
        sr = json.loads(r.stdout)
        d = sr.get("data", sr)
        if not isinstance(d, dict):
            log(f"[{i+1}] 响应异常: {json.dumps(sr, ensure_ascii=False)[:200]}")
            continue
        
        status = d.get("status", "")
        progress = d.get("progress", "")
        log(f"[{i+1}] {status} {progress}")
        
        if status == "SUCCEEDED":
            d2 = d.get("data", {})
            if isinstance(d2, dict):
                url = d2.get("video_info", {}).get("video_url", "") or d2.get("output_url", "")
            if not url:
                url = d.get("video_url", "") or sr.get("url", "")
            return url
        elif status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"生成失败: {d.get('fail_reason', '?')}")
    
    raise TimeoutError(f"超时: {max_polls}次轮询后未完成")

def download_video(url, output_path):
    """下载视频到本地"""
    r = subprocess.run(["curl", "-sL", "-o", output_path, url],
                       capture_output=True, text=True, timeout=120)
    sz = os.path.getsize(output_path)
    with open(output_path, "rb") as f:
        h = f.read(12)
    is_mp4 = h[4:8] == b"ftyp"
    return sz, is_mp4

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = (
            "Chinese ink-wash xianxia style, "
            "Forgotten River scene, old woman spirit rising from dark crimson water, "
            "Red Spider Lilies, blood mist, cold red atmosphere, slow camera push-in, ethereal"
        )
    
    log("=== 视频管线开始 ===")
    try:
        tid = submit_video(prompt)
        log(f"TASK_ID={tid}")
        
        url = poll_video(tid)
        log(f"URL={url}")
        
        out = os.path.join(TARGET, f"video_{tid[:8]}.mp4")
        sz, is_mp4 = download_video(url, out)
        log(f"SAVED={out} ({sz}B, MP4={is_mp4})")
        log("=== 完成 ===")
    except Exception as e:
        log(f"错误: {e}")
        sys.exit(1)