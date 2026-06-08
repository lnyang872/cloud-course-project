# 华为云 SWR 推送命令

> 使用前请把 `<AK>`、`<SK>`、`<ORG>` 替换为你华为云 SWR 控制台中的实际信息。若 Region 不是 `cn-north-4`，也要替换对应 Region。

## 1. 本地或华为云 ECS 联调

```bash
docker compose up --build
```

浏览器访问：

```text
http://<ECS公网IP>:8080
```

或本机访问：

```text
http://localhost:8080
```

后端接口：

```text
http://<ECS公网IP>:5000/api/ping
```

## 2. 登录 SWR

```bash
docker login -u cn-north-4@<AK> -p <SK> swr.cn-north-4.myhuaweicloud.com
```

## 3. 构建镜像

```bash
docker build -t backend:v1 -f backend/Dockerfile.backend backend
docker build -t frontend:v1 -f frontend/Dockerfile.frontend frontend
```

## 4. 打 Tag

```bash
docker tag backend:v1 swr.cn-north-4.myhuaweicloud.com/<ORG>/backend:v1
docker tag frontend:v1 swr.cn-north-4.myhuaweicloud.com/<ORG>/frontend:v1
```

## 5. 推送镜像到 SWR

```bash
docker push swr.cn-north-4.myhuaweicloud.com/<ORG>/backend:v1
docker push swr.cn-north-4.myhuaweicloud.com/<ORG>/frontend:v1
```

## 6. 任务 1 截图清单

- `backend/Dockerfile.backend` 多阶段构建截图；
- `backend/requirements.txt` 中 `requests==2.31.0` 截图；
- `frontend/static/index.html` 中学号姓名截图；
- `docker compose up --build` 运行截图；
- 前端页面访问截图；
- 点击“测试后端 /api/ping”后的返回结果截图；
- 后端日志显示 `received /api/ping request` 截图；
- SWR 控制台中 `backend:v1` 和 `frontend:v1` 镜像列表截图。
