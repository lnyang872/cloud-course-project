# 附加题 2：CI/CD 流水线说明

本方案使用 GitHub Actions 实现后端应用的最小可交付 CI/CD：

1. 提交 `backend/` 代码到 `main` 分支；
2. GitHub Actions 自动构建后端 Docker 镜像；
3. 自动登录华为云 SWR 并推送新镜像；
4. 自动把 `k8s/deployment.yaml` 中 backend 的镜像 tag 更新为本次提交的短 SHA；
5. 自动提交回仓库，用于截图展示“镜像 Tag 已自动更新”。

## 一、需要的仓库 Secrets

在 GitHub 仓库 `Settings -> Secrets and variables -> Actions` 中添加：

- `SWR_USERNAME`：华为云 SWR 用户名，例如 `cn-south-1@xxxx`
- `SWR_PASSWORD`：华为云 SWR 登录密码/临时令牌

## 二、流水线文件位置

- `.github/workflows/backend-cicd.yml`

## 三、触发方式

以下情况会触发流水线：

- push 到 `main` 分支；
- 修改了 `backend/**`；
- 修改了 `k8s/deployment.yaml`；
- 手动执行 `workflow_dispatch`。

## 四、镜像命名规则

流水线会将镜像推送到：

- `swr.cn-south-1.myhuaweicloud.com/cloud-course/backend:<short_sha>`

例如：

- `swr.cn-south-1.myhuaweicloud.com/cloud-course/backend:a1b2c3d`

## 五、自动更新内容

流水线会自动修改：

- `k8s/deployment.yaml`

把 backend 镜像从：

- `swr.cn-south-1.myhuaweicloud.com/cloud-course/backend:v1`

更新为：

- `swr.cn-south-1.myhuaweicloud.com/cloud-course/backend:<short_sha>`

## 六、建议截图内容

### 1. 流水线运行成功截图

截图 GitHub Actions 页面，要求能看到：

- `Checkout repository`
- `Log in to SWR`
- `Build and push backend image`
- `Update Kubernetes deployment image tag`
- `Commit updated deployment manifest`
- 总状态为 `Passed` / `Success`

### 2. 镜像更新验证截图

可截图以下任意一种：

- GitHub 仓库中 `k8s/deployment.yaml` 的 backend 镜像 tag 已从 `v1` 变成短 SHA；
- SWR 控制台中出现新的 backend 镜像 tag；
- `kubectl describe deployment backend` 或 `kubectl get deployment backend -o yaml` 显示新 tag。

## 七、如果要真正自动部署到 K8s

当前方案已满足题目中“代码提交 → 自动构建镜像 → 推送 SWR → 更新 K8s Deployment 镜像 Tag”的要求。

如果你还想进一步做到自动 `kubectl apply`，可以额外在 GitHub Secrets 中配置 kubeconfig，然后在流水线末尾增加：

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/backend -n default
```

但这一步不是最小必需项，且会增加密钥配置复杂度。

## 八、报告中可直接使用的概念说明

### 1. CI 与 CD 的区别

- CI（持续集成）强调代码频繁提交后自动执行构建、测试、检查，尽早发现问题；
- CD（持续交付/持续部署）强调在 CI 通过后，将构建产物继续自动推送到制品仓库，并进一步更新部署清单或发布到运行环境。

### 2. 本实验中的体现

本实验中，GitHub Actions 在代码提交后自动完成镜像构建与推送，这属于持续集成与持续交付过程；随后自动更新 Kubernetes Deployment 中的镜像 Tag，用于驱动后续部署发布。

### 3. GitOps 核心理念

GitOps 的核心理念是“以 Git 作为系统期望状态的唯一可信源”。基础设施配置、Kubernetes YAML、镜像版本等都保存在 Git 中，所有变更通过提交记录管理。系统实际状态与 Git 中声明状态保持一致，便于审计、回滚和自动化运维。
