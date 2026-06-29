"""图像生成 API AI API适配器 — 支持图片/视频生成

对接 https://apihub.图像生成 API-ai.com/v1
  - 图片: 图像生成 API-image-2.1-flash
  - 视频: 图像生成 API-video-v2.0（异步）
"""
import json, subprocess, time
from .base import BaseAdapter, AdapterConfig, AdapterError, AuthError, TimeoutError


class 图像生成 APIImageAdapter(BaseAdapter):
    """图像生成 API图片生成适配器"""

    def __init__(self, config: AdapterConfig = None):
        super().__init__("图像生成 API_image", config)
        self.base_url = config.base_url or "https://apihub.图像生成 API-ai.com/v1"
        self.supported_sizes = ["1024x1024", "1920x1080", "2048x1152"]
        self.default_size = "1920x1080"
        self.default_model = "图像生成 API-image-2.1-flash"

    def generate(self, prompt: str, **kwargs) -> dict:
        """生成图片"""
        payload = {
            "model": kwargs.get("model", self.default_model),
            "prompt": prompt[:3000],
            "n": 1,
            "size": kwargs.get("size", self.default_size),
            "negative_prompt": kwargs.get("negative_prompt",
                "cartoon, anime, kawaii, Disney, Pixar, modern elements, text, watermark"),
        }
        try:
            r = subprocess.run([
                "curl", "-s", self.base_url + "/images/generations",
                "-H", "Content-Type: application/json",
                "-H", "Authorization: Bearer " + self.config.api_key,
                "-d", json.dumps(payload)
            ], capture_output=True, text=True, timeout=kwargs.get("timeout", 60))
            resp = json.loads(r.stdout)
            if "error" in resp:
                msg = resp["error"].get("message", "Unknown")
                if "token" in msg.lower() or "auth" in msg.lower():
                    raise AuthError(msg)
                raise AdapterError(msg)
            url = resp.get("data", [{}])[0].get("url", "")
            return {"adapter": "图像生成 API_image", "url": url, "format": "png", "size": kwargs.get("size", self.default_size)}
        except json.JSONDecodeError:
            raise AdapterError(f"API返回非JSON: {r.stdout[:200]}")

    def health_check(self) -> dict:
        return {"available": bool(self.config.api_key), "name": "图像生成 API_image", "model": self.default_model}


class 图像生成 APIVideoAdapter(BaseAdapter):
    """图像生成 API视频生成适配器（异步任务模式）"""

    def __init__(self, config: AdapterConfig = None):
        super().__init__("图像生成 API_video", config)
        self.base_url = config.base_url or "https://apihub.图像生成 API-ai.com/v1"
        self.default_model = "图像生成 API-video-v2.0"
        self.poll_interval = 15
        self.max_polls = 20

    def generate(self, prompt: str, **kwargs) -> dict:
        """提交视频任务并轮询结果"""
        payload = {
            "model": kwargs.get("model", self.default_model),
            "prompt": prompt[:2000],
            "n": 1,
            "duration": kwargs.get("duration", 5),
        }
        # 提交任务
        r = subprocess.run([
            "curl", "-s", self.base_url + "/video/generations",
            "-H", "Content-Type: application/json",
            "-H", "Authorization: Bearer " + self.config.api_key,
            "-d", json.dumps(payload)
        ], capture_output=True, text=True, timeout=30)
        resp = json.loads(r.stdout)
        if "error" in resp:
            raise AdapterError(resp["error"].get("message", "Unknown"))

        task_id = resp.get("task_id", "")
        if not task_id:
            raise AdapterError("无task_id")

        # 轮询
        for i in range(self.max_polls):
            time.sleep(self.poll_interval)
            r2 = subprocess.run([
                "curl", "-s", self.base_url + f"/video/generations/{task_id}",
                "-H", "Authorization: Bearer " + self.config.api_key,
            ], capture_output=True, text=True, timeout=30)
            status_resp = json.loads(r2.stdout)
            data = status_resp.get("data", {}) if "data" in status_resp else status_resp
            status = data.get("status", "unknown")
            if status == "SUCCEEDED":
                video_url = data.get("data", {}).get("video_info", {}).get("video_url", "") or                             data.get("video_url", "")
                return {"adapter": "图像生成 API_video", "url": video_url, "task_id": task_id, "polls": i + 1}
            elif status in ("FAILED", "CANCELLED"):
                reason = data.get("fail_reason", "Unknown")
                raise AdapterError(f"视频生成失败: {reason}")
            # 还在进行中

        raise TimeoutError(f"视频生成超时 (task: {task_id})")

    def health_check(self) -> dict:
        return {"available": bool(self.config.api_key), "name": "图像生成 API_video", "model": self.default_model}
