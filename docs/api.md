# HTTP API

零依赖的 HTTP 服务，基于标准库 `http.server`。

```bash
python -m proveforge serve --host 127.0.0.1 --port 8431
```

## 端点

### `GET /health`

```bash
curl http://127.0.0.1:8431/health
# {"status": "ok", "service": "proveforge"}
```

### `GET /v1/info`

返回模型元信息与承诺。

```bash
curl http://127.0.0.1:8431/v1/info
# {"vocab": 32, "layers": 3, "bits": 8, "commitment": "<root hex>", "rows": 128, "entries": 4096}
```

### `POST /v1/commit`

```bash
curl -X POST http://127.0.0.1:8431/v1/commit -d '{}'
# {"commitment": "<root hex>", "entries": 4096}
```

### `POST /v1/prove`

为一个 prompt 生成证明。

```bash
curl -X POST http://127.0.0.1:8431/v1/prove -d '{"prompt":"p00","open_ratio":1.0}'
# {"prompt": [...], "output": [...], "open_rows": 128}
```

字段：`prompt`（prompt id，默认 `p00`）、`open_ratio`（默认取配置 `prove.open_ratio`）。

### `POST /v1/verify`

演示一次 token 篡改攻击被校验器拒绝。

```bash
curl -X POST http://127.0.0.1:8431/v1/verify -d '{"prompt":"p00"}'
# {"tampered": true, "accepted": false, "binding_ok": true, "integrity_ok": false}
```

## 说明

- 该服务是**单机、内存态**的参考实现，启动时重建语料、承诺与模型，不做持久化。
- 生产部署请走 `deploy/k8s/` 或 `deploy/helm/` 中的清单。
