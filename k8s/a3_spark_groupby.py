import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, split
from pyspark.sql.types import DoubleType, IntegerType

spark = SparkSession.builder.appName("a3-spark-groupby-performance").getOrCreate()

input_path = "/opt/spark/app/douban_movies.csv"

start_time = time.perf_counter()

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
    .dropna(subset=["movie_id", "title", "year", "rating_score", "genres"])
    .dropDuplicates(["movie_id"])
)

genre_stats = (
    movies.select(explode(split(col("genres"), "/")).alias("genre"), "movie_id", "rating_score", "rating_count")
    .groupBy("genre")
    .agg(
        {"movie_id": "count", "rating_score": "avg", "rating_count": "avg"}
    )
    .withColumnRenamed("count(movie_id)", "movie_count")
    .withColumnRenamed("avg(rating_score)", "avg_rating")
    .withColumnRenamed("avg(rating_count)", "avg_rating_count")
    .orderBy(col("movie_count").desc())
    .limit(10)
)

rows = genre_stats.collect()
elapsed = time.perf_counter() - start_time

print("========== PySpark GROUP BY 查询结果 ==========")
for row in rows:
    print(row)
print(f"PYSPARK_TIME_SECONDS={elapsed:.4f}")

spark.stop()
