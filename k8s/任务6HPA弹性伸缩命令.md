# 任务 6：HPA 弹性伸缩

## 使用文件

```text
task6-hpa.yaml
```

## 1. 确认 metrics-server 可用

```bash
kubectl top nodes
kubectl top pods
```

如果有 CPU、MEMORY 数据，说明 metrics-server 可用。

## 2. 确认 backend Deployment 有 CPU requests

```bash
kubectl get deployment backend -o yaml | grep -A 12 resources
```

应能看到：

```text
requests:
  cpu: 100m
```

HPA 按 CPU 利用率工作时，必须有 `resources.requests.cpu`。

## 3. 创建 HPA YAML

如果 CloudShell 中没有文件，可复制执行：

```bash
cat > task6-hpa.yaml <<'EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 1
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
EOF
```

## 4. 应用 HPA

```bash
kubectl apply -f task6-hpa.yaml
```

查看 HPA：

```bash
kubectl get hpa
kubectl describe hpa backend-hpa
```

应看到：

```text
backend-hpa
minPods: 1
maxPods: 4
target: cpu 60%
```

## 5. 开启 Pod 数量监控窗口

开一个 CloudShell 终端窗口执行：

```bash
kubectl get pods -w
```

也可以更聚焦后端：

```bash
kubectl get pods -l app=backend -w
```

## 6. 获取后端 ELB 公网 IP

```bash
kubectl get svc backend-svc
```

你当前后端公网 IP 是：

```text
110.41.0.123
```

## 7. 压测方式一：ab

如果 CloudShell 有 `ab`：

```bash
ab -n 10000 -c 200 http://110.41.0.123/api/ping
```

如果要持续更久，可以多执行几次，或提高请求数：

```bash
ab -n 20000 -c 300 http://110.41.0.123/api/ping
```

## 8. 压测方式二：循环 curl，适合没有 ab 的情况

如果 `ab` 不存在，执行：

```bash
while true; do for i in $(seq 1 200); do curl -s http://110.41.0.123/api/ping >/dev/null & done; wait; done
```

停止压测按：

```text
Ctrl+C
```

## 9. 观察 HPA 和 Pod 扩容

另一个窗口执行：

```bash
kubectl get hpa -w
```

或反复执行：

```bash
kubectl get hpa
kubectl get pods -l app=backend
```

期望看到 backend Pod 数量从 1 或 2 增加到 2、3 或 4。

## 10. 停止压测后观察缩容

停止压测后等待约 5 分钟：

```bash
kubectl get hpa -w
kubectl get pods -l app=backend -w
```

HPA 会逐步缩容，最终回到较低副本数。

## 11. 如果没有触发扩容

查看 HPA 原因：

```bash
kubectl describe hpa backend-hpa
```

常见原因：

- metrics-server 数据还未采集完成，等待 3 分钟；
- 后端接口太轻，CPU 压不上去；
- backend 的 CPU request 较大，实际利用率达不到 60%；
- 压测请求没有打到后端；
- ELB、网络或 CloudShell 并发受限。

如果一直压不上去，可临时把 HPA 阈值降低到 20：

```bash
kubectl patch hpa backend-hpa --type merge -p '{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":20}}}]}}'
```

然后重新压测。

## 12. 截图清单

- `task6-hpa.yaml`，显示 `minReplicas: 1`、`maxReplicas: 4`、`averageUtilization: 60`；
- `kubectl top nodes`，显示 CPU/MEMORY 数据；
- `kubectl get hpa`，显示 HPA 创建成功；
- 压测命令截图，例如 `ab -n 10000 -c 200 http://110.41.0.123/api/ping`；
- `kubectl get pods -w` 或 `kubectl get pods -l app=backend -w`，显示 backend Pod 数量增加；
- 停止压测后，Pod 数量缩回较低副本数；
- 如果未扩容，补充 `kubectl describe hpa backend-hpa` 分析原因。

## 13. 报告分析参考

- 扩容延迟原因：metrics-server 按周期采集指标，HPA controller 也按固定周期计算副本数，因此从压测到扩容会有几十秒到数分钟延迟。
- 冷却时间意义：避免短时间 CPU 波动导致频繁扩缩容，减少系统抖动。
- HPA 价值：根据负载自动调整 Pod 数量，提高高峰期处理能力，低负载时释放资源、降低成本。
