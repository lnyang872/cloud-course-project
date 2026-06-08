# 第二部分：Spark Operator 提交 SparkApplication 作业

## 本地文件

```text
wordcount.py
wordcount-configmap.yaml
sparkapplication.yaml
```

## 0. 说明

`SparkApplication` 使用镜像：

```text
swr.cn-south-1.myhuaweicloud.com/cloud-course/pyspark:v9
```

如果老师给的是其他 SWR PySpark 镜像地址，把 `sparkapplication.yaml` 中的 `spec.image` 替换为老师提供的地址。

任务要求关键参数：

```text
executor.instances = 2
executor.memory = 1g
```

## 1. 上传 Spark Operator 离线 Chart 到 CloudShell

本地 Chart 目录：

```text
D:\Desktop\A.Hui\云计算技术\ks\云计算课程设计_离线资源包_SparkOperator+MPI+Monitoring\离线包\spark\spark-operator
```

将整个 `spark-operator` 文件夹上传到 CloudShell 当前目录。

或者如果 CloudShell 已经有该目录，执行：

```bash
ls
```

确认能看到：

```text
spark-operator
```

## 2. 安装 Spark Operator

```bash
helm install spark-op ./spark-operator -n spark-operator --create-namespace
```

查看 Operator：

```bash
kubectl get pods -n spark-operator
kubectl get crd | grep spark
```

应看到 Spark Operator Pod 为 Running，并且存在：

```text
sparkapplications.sparkoperator.k8s.io
```

## 3. 创建 Spark ServiceAccount 和权限

```bash
kubectl create serviceaccount spark -n default
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark
```

如果提示已存在，可以忽略。

## 4. 在 CloudShell 创建 wordcount-configmap.yaml

```bash
cat > wordcount-configmap.yaml <<'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: wordcount-script
  namespace: default
data:
  wordcount.py: |
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("wordcount").getOrCreate()
    sc = spark.sparkContext

    text = [
        "cloud computing course design",
        "spark operator on kubernetes",
        "spark wordcount example",
        "cloud spark kubernetes"
    ]

    counts = (
        sc.parallelize(text)
        .flatMap(lambda line: line.split())
        .map(lambda word: (word, 1))
        .reduceByKey(lambda a, b: a + b)
        .collect()
    )

    for word, count in sorted(counts):
        print(f"{word}: {count}")

    spark.stop()
EOF
```

应用：

```bash
kubectl apply -f wordcount-configmap.yaml
```

## 5. 在 CloudShell 创建 sparkapplication.yaml

```bash
cat > sparkapplication.yaml <<'EOF'
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: wordcount
  namespace: default
spec:
  type: Python
  mode: cluster
  image: swr.cn-south-1.myhuaweicloud.com/cloud-course/pyspark:v9
  imagePullPolicy: IfNotPresent
  mainApplicationFile: local:///opt/spark/examples/wordcount.py
  sparkVersion: "3.5.0"
  restartPolicy:
    type: Never
  driver:
    cores: 1
    coreLimit: "1200m"
    memory: "1g"
    labels:
      version: "3.5.0"
    serviceAccount: spark
    volumeMounts:
      - name: wordcount-script
        mountPath: /opt/spark/examples/wordcount.py
        subPath: wordcount.py
  executor:
    cores: 1
    instances: 2
    memory: "1g"
    labels:
      version: "3.5.0"
    volumeMounts:
      - name: wordcount-script
        mountPath: /opt/spark/examples/wordcount.py
        subPath: wordcount.py
  volumes:
    - name: wordcount-script
      configMap:
        name: wordcount-script
EOF
```

## 6. 提交 SparkApplication

如果之前提交过同名任务，先删除：

```bash
kubectl delete sparkapplication wordcount --ignore-not-found=true
```

提交：

```bash
kubectl apply -f sparkapplication.yaml
```

查看 SparkApplication：

```bash
kubectl get sparkapplication
kubectl describe sparkapplication wordcount
```

## 7. 查看 Driver 和 Executor Pod

```bash
kubectl get pods -n default
```

应看到类似：

```text
wordcount-driver
wordcount-*-exec-1
wordcount-*-exec-2
```

Driver 完成后状态会变为：

```text
Completed
```

## 8. 查看 Driver 日志

获取 Driver Pod：

```bash
DRIVER_POD=$(kubectl get pods -n default | grep wordcount-driver | awk '{print $1}')
echo $DRIVER_POD
```

查看日志：

```bash
kubectl logs $DRIVER_POD -n default
```

应看到词频统计结果，例如：

```text
cloud: 2
spark: 3
kubernetes: 2
```

## 9. 常见问题

### 1. 镜像拉取失败

如果 Driver/Executor 是 `ImagePullBackOff`，说明 `spec.image` 不对或镜像私有无法拉取。需要改成老师提供的 SWR PySpark 镜像，并确保公开或配置 imagePullSecret。

### 2. SparkApplication CRD 不存在

如果报：

```text
no matches for kind SparkApplication
```

说明 Spark Operator 没装好，先检查：

```bash
kubectl get crd | grep spark
kubectl get pods -n spark-operator
```

### 3. ServiceAccount 权限不足

如果 Driver 日志报 RBAC 权限问题，重新创建绑定：

```bash
kubectl create clusterrolebinding spark-role --clusterrole=edit --serviceaccount=default:spark
```

## 10. 截图清单

- `helm install spark-op ./spark-operator -n spark-operator --create-namespace` 成功截图；
- `kubectl get pods -n spark-operator`，Operator Running；
- `sparkapplication.yaml`，显示 PySpark 镜像、`executor.instances: 2`、`executor.memory: 1g`；
- `kubectl apply -f sparkapplication.yaml` 成功截图；
- `kubectl get pods -n default`，含 Driver 和 2 个 Executor Pod；
- Driver Pod 状态 `Completed` 的截图；
- `kubectl logs <driver-pod>`，显示 wordcount 输出。
