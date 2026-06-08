from pyspark.sql import SparkSession
from pyspark.sql.functions import col, isnan, mean, round as spark_round, sum as spark_sum, when
from pyspark.sql.types import DoubleType, IntegerType

spark = SparkSession.builder.appName("douban-movies-cleaning").getOrCreate()

input_path = "/opt/spark/app/douban_movies.csv"

movies = (
    spark.read.option("header", "true")
    .option("multiLine", "true")
    .option("escape", '"')
    .option("quote", '"')
    .option("encoding", "UTF-8")
    .csv(input_path)
)

movies = (
    movies.withColumn("movie_id", col("movie_id").cast(IntegerType()))
    .withColumn("year", col("year").cast(IntegerType()))
    .withColumn("rating_score", col("rating_score").cast(DoubleType()))
    .withColumn("rating_count", col("rating_count").cast(IntegerType()))
    .withColumn("collect_count", col("collect_count").cast(IntegerType()))
)

print("========== Schema ==========")
movies.printSchema()

print("========== 前 5 行 ==========")
movies.show(5, truncate=False)

row_count_before = movies.count()
print(f"清洗前行数: {row_count_before}")

print("========== 各字段缺失值比例 ==========")
missing_exprs = []
for field in movies.columns:
    field_type = dict(movies.dtypes)[field]
    if field_type in ("double", "float"):
        missing_condition = col(field).isNull() | isnan(col(field))
    else:
        missing_condition = col(field).isNull()
    missing_exprs.append(
        spark_round(
            spark_sum(when(missing_condition, 1).otherwise(0)) / row_count_before * 100,
            2,
        ).alias(field)
    )
movies.select(missing_exprs).show(truncate=False)

print("========== 清洗前数值字段统计 ==========")
numeric_columns = ["year", "rating_score", "rating_count", "collect_count"]
movies.select(numeric_columns).summary("count", "mean", "stddev", "min", "max").show(truncate=False)

rating_mean = movies.select(mean("rating_score")).first()[0]
rating_count_median = movies.approxQuantile("rating_count", [0.5], 0.01)[0]
collect_count_median = movies.approxQuantile("collect_count", [0.5], 0.01)[0]

cleaned = movies.dropna(subset=["movie_id", "title"])
cleaned = cleaned.fillna({
    "original_title": "未知",
    "genres": "未知",
    "countries": "未知",
    "directors": "未知",
    "summary": "暂无简介",
    "rating_score": float(rating_mean) if rating_mean is not None else 0.0,
    "rating_count": int(rating_count_median) if rating_count_median is not None else 0,
    "collect_count": int(collect_count_median) if collect_count_median is not None else 0,
})
cleaned = cleaned.dropna(subset=["year"])
cleaned = cleaned.dropDuplicates(["movie_id"])

row_count_after = cleaned.count()
print(f"清洗后行数: {row_count_after}")
print(f"清洗删除行数: {row_count_before - row_count_after}")

print("========== 清洗后前 5 行 ==========")
cleaned.show(5, truncate=False)

print("========== 清洗后数值字段统计 ==========")
cleaned.select(numeric_columns).summary("count", "mean", "stddev", "min", "max").show(truncate=False)

print("========== 缺失值处理策略说明 ==========")
print("1. movie_id、title 是核心标识字段，缺失会导致样本无法唯一识别，因此使用 dropna 删除。")
print("2. rating_score 使用均值填充，保持评分字段整体分布稳定。")
print("3. rating_count、collect_count 使用中位数填充，降低极端热门电影对填充值的影响。")
print("4. genres、countries、directors、summary 等文本字段使用 '未知' 或 '暂无简介' 填充，保留样本用于后续分析。")
print("5. year 用于年代分析，缺失时无法可靠推断，因此删除 year 缺失记录。")

spark.stop()
