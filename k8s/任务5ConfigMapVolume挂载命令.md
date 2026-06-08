# 任务 5：ConfigMap Volume 挂载 Nginx 配置

## 说明

本任务在任务 3 后端服务 `backend-svc` 基础上，新增前端服务，并将 Nginx 反向代理配置通过 ConfigMap Volume 挂载到：

```text
/etc/nginx/conf.d/default.conf
```

使用文件：

```text
task5-nginx-configmap-volume.yaml
```

该文件包含：

- `ConfigMap/nginx-conf`，data 中包含完整 `default.conf`；
- `Deployment/frontend`，将 ConfigMap 以 volume 形式挂载到 Nginx 配置文件路径；
- `Service/frontend-svc`，LoadBalancer 暴露前端页面。

## 1. 在 CloudShell 创建 YAML

如果文件还没有上传到 CloudShell，可复制下面内容创建：

```bash
cat > task5-nginx-configmap-volume.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-conf
  namespace: default
data:
  default.conf: |
    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://backend-svc:80;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: swr.cn-south-1.myhuaweicloud.com/cloud-course/frontend:v1
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "200m"
              memory: "256Mi"
          volumeMounts:
            - name: nginx-conf-volume
              mountPath: /etc/nginx/conf.d/default.conf
              subPath: default.conf
      volumes:
        - name: nginx-conf-volume
          configMap:
            name: nginx-conf
            items:
              - key: default.conf
                path: default.conf
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-svc
  namespace: default
  annotations:
    kubernetes.io/elb.class: union
    kubernetes.io/elb.autocreate: '{"type":"public","bandwidth_name":"frontend-elb-bandwidth","bandwidth_chargemode":"traffic","bandwidth_size":5,"bandwidth_sharetype":"PER","eip_type":"5_bgp"}'
spec:
  type: LoadBalancer
  selector:
    app: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
EOF
```

## 2. 应用任务 5 YAML

```bash
kubectl apply -f task5-nginx-configmap-volume.yaml
```

## 3. 查看资源状态

```bash
kubectl get configmap nginx-conf
kubectl get pods -l app=frontend -o wide
kubectl get svc frontend-svc
```

等待前端 Pod 为：

```text
1/1 Running
```

等待 `frontend-svc` 出现公网 `EXTERNAL-IP`。

如果需要持续观察：

```bash
kubectl get svc frontend-svc -w
```

出现公网 IP 后按 `Ctrl+C` 退出。

## 4. 验证 Nginx 配置来自 ConfigMap Volume

获取前端 Pod 名称：

```bash
FRONTEND_POD=$(kubectl get pod -l app=frontend -o jsonpath='{.items[0].metadata.name}')
echo $FRONTEND_POD
```

查看挂载后的 Nginx 配置：

```bash
kubectl exec -it $FRONTEND_POD -- cat /etc/nginx/conf.d/default.conf
```

应看到：

```text
proxy_pass http://backend-svc:80;
```

## 5. 访问前端页面和后端接口

查看前端 Service：

```bash
kubectl get svc frontend-svc
```

假设公网 IP 为 `<FRONTEND_EXTERNAL_IP>`，浏览器访问：

```text
http://<FRONTEND_EXTERNAL_IP>
```

页面点击“测试后端 /api/ping”，应返回后端 JSON。

也可以执行：

```bash
curl http://<FRONTEND_EXTERNAL_IP>/api/ping
```

## 6. 修改 ConfigMap 中后端端口为 5001

按任务要求，将 ConfigMap 中后端端口从 `80` 修改为 `5001`。

使用命令直接 patch：

```bash
kubectl patch configmap nginx-conf --type merge -p '{"data":{"default.conf":"server {\n    listen 80;\n    server_name _;\n\n    root /usr/share/nginx/html;\n    index index.html;\n\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n\n    location /api/ {\n        proxy_pass http://backend-svc:5001;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }\n}\n"}}'
```

## 7. 等待 ConfigMap Volume 更新

Kubernetes 同步 ConfigMap Volume 通常需要几十秒到 1 分钟。

执行：

```bash
sleep 60
kubectl exec -it $FRONTEND_POD -- cat /etc/nginx/conf.d/default.conf
```

应看到：

```text
proxy_pass http://backend-svc:5001;
```

如果没有更新，可以重启前端 Pod 后再查看：

```bash
kubectl delete pod $FRONTEND_POD
kubectl get pods -l app=frontend -w
```

新 Pod Running 后：

```bash
FRONTEND_POD=$(kubectl get pod -l app=frontend -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $FRONTEND_POD -- cat /etc/nginx/conf.d/default.conf
```

## 8. 截图清单

- `task5-nginx-configmap-volume.yaml`，显示 ConfigMap 中 `default.conf`；
- `task5-nginx-configmap-volume.yaml`，显示 `volumeMounts` 挂载到 `/etc/nginx/conf.d/default.conf`；
- `kubectl get pods -l app=frontend -o wide`，前端 Pod Running；
- `kubectl get svc frontend-svc`，前端 LoadBalancer 有公网 IP；
- `kubectl exec ... cat /etc/nginx/conf.d/default.conf`，显示 `proxy_pass http://backend-svc:80;`；
- 修改 ConfigMap 后，再次 `cat /etc/nginx/conf.d/default.conf`，显示 `proxy_pass http://backend-svc:5001;`；
- 浏览器访问前端页面或 `curl http://<FRONTEND_EXTERNAL_IP>/api/ping` 的截图。
