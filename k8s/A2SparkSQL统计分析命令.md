# A-2 Spark SQL 统计分析

## 文件

```text
douban_sql_analysis.py
Dockerfile.douban-sql
douban-sql-sparkapplication.yaml
```

## 查询内容

- 查询1：GROUP BY 聚合，按类型统计电影数量和平均评分；
- 查询2：ORDER BY Top-N，评分人数最多的前 10 部电影；
- 查询3：时间维度趋势分析，按年代统计电影数量和平均评分；
- 查询4：窗口函数，每个国家/地区评分最高的电影 Top-3；
- 查询5：国家/地区与类型关联统计。

## 1. 上传文件到 ECS

在 Windows PowerShell 执行：

```powershell
scp "D:\Desktop\A.Hui\云计算技术\ks\douban_movies.csv" root@139.9.212.208:/root/
scp "D:\Desktop\A.Hui\云计算技术\ks\k8s\douban_sql_analysis.py" root@139.9.212.208:/root/
scp "D:\Desktop\A.Hui\云计算技术\ks\k8s\Dockerfile.douban-sql" root@139.9.212.208:/root/Dockerfile.douban-sql
```

如果 `douban_movies.csv` 已经上传过，可以只上传脚本和 Dockerfile。

## 2. 在 ECS 构建并推送镜像

```bash
cd /root
ls douban_movies.csv douban_sql_analysis.py Dockerfile.douban-sql

docker build -f Dockerfile.douban-sql -t swr.cn-south-1.myhuaweicloud.com/cloud-course/douban-sql:v1 .
docker push swr.cn-south-1.myhuaweicloud.com/cloud-course/douban-sql:v1
```

推送后去 SWR 华南广州区域，将：

```text
cloud-course/douban-sql:v1
```

设置为公开。

## 3. 在 CloudShell 创建 SparkApplication

```bash
cat > douban-sql-sparkapplication.yaml <<'EOF'
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: douban-sql-analysis
  namespace: default
spec:
  type: Python
  mode: cluster
  image: swr.cn-south-1.myhuaweicloud.com/cloud-course/douban-sql:v1
  imagePullPolicy: Always
  mainApplicationFile: local:///opt/spark/app/douban_sql_analysis.py
  sparkVersion: "3.4.3"
  restartPolicy:
    type: Never
  driver:
    cores: 1
    coreLimit: "1200m"
    memory: "1g"
    labels:
      version: "3.4.3"
    serviceAccount: spark
  executor:
    cores: 1
    instances: 2
    memory: "1g"
    labels:
      version: "3.4.3"
EOF
```

## 4. 提交作业

```bash
kubectl delete sparkapplication douban-sql-analysis --ignore-not-found=true
kubectl delete pod douban-sql-analysis-driver --ignore-not-found=true
kubectl apply -f douban-sql-sparkapplication.yaml
```

观察：

```bash
kubectl get pods -n default -w
```

等：

```text
douban-sql-analysis-driver   Completed
```

## 5. 生成干净日志

```bash
kubectl logs douban-sql-analysis-driver -n default | grep -v " INFO " | grep -v " WARN " > douban_sql.log
```

## 6. 分别查看并截图

### 查询1：GROUP BY 聚合

```bash
grep -A 18 "查询1" douban_sql.log
```

### 查询2：ORDER BY Top-N

```bash
grep -A 18 "查询2" douban_sql.log
```

### 查询3：时间维度趋势分析

```bash
grep -A 35 "查询3" douban_sql.log
```

### 查询4：窗口函数

```bash
grep -A 70 "查询4" douban_sql.log
```

### 查询5：国家/地区与类型关联统计

```bash
grep -A 30 "查询5" douban_sql.log
```

## 7. 截图清单

每个查询一张截图，截图里需要包含：

- 查询标题；
- 查询结果表；
- 不少于 50 字的分析说明。

如果一张图放不下，查询4可以截结果表一张、分析说明一张。
