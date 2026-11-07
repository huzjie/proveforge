# -*- coding: utf-8 -*-
"""用 urllib 调用 proveforge HTTP API 的客户端示例。

先起服务：python -m proveforge serve --port 8431
再运行本脚本。
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8431"


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


if __name__ == "__main__":
    print("[health]", get("/health"))
    print("[info]", get("/v1/info"))
    print("[prove]", post("/v1/prove", {"prompt": "p00", "open_ratio": 1.0}))
    print("[verify-tampered]", post("/v1/verify", {"prompt": "p00"}))
