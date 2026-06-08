from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, split, row_number, desc
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("douban-spark-sql-analysis").getOrCreate()

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
    .dropna(subset=["movie_id", "title", "year", "rating_score", "genres", "countries"])
    .dropDuplicates(["movie_id"])
)

movies.createOrReplaceTempView("movies")

print("========== 数据概览 ==========")
print(f"有效电影记录数: {movies.count()}")
movies.select("movie_id", "title", "year", "rating_score", "rating_count", "genres", "countries").show(5, truncate=False)

print("========== 查询1：GROUP BY 聚合，按类型统计电影数量和平均评分 ==========")
genre_stats = spark.sql("""
SELECT
  genre,
  COUNT(*) AS movie_count,
  ROUND(AVG(rating_score), 2) AS avg_rating,
  ROUND(AVG(rating_count), 0) AS avg_rating_count
FROM (
  SELECT explode(split(genres, '/')) AS genre, rating_score, rating_count
  FROM movies
  WHERE genres IS NOT NULL AND genres <> ''
) t
GROUP BY genre
ORDER BY movie_count DESC
LIMIT 10
""")
genre_stats.show(truncate=False)
print("分析说明1：通过 GROUP BY 统计不同电影类型的影片数量和平均评分，可以看出样本量较大的类型及其整体口碑，为比较不同类型电影受欢迎程度提供依据。")

print("========== 查询2：ORDER BY Top-N，评分人数最多的前10部电影 ==========")
top_rating_count = spark.sql("""
SELECT title, year, rating_score, rating_count, genres, countries
FROM movies
WHERE rating_count IS NOT NULL
ORDER BY rating_count DESC
LIMIT 10
""")
top_rating_count.show(truncate=False)
print("分析说明2：通过 ORDER BY rating_count DESC 选出评分人数最多的 Top-10 电影。这些影片通常传播度高、观众参与评价人数多，能反映大众关注度最高的电影作品。")

print("========== 查询3：时间维度趋势分析，按年代统计电影数量和平均评分 ==========")
decade_trend = spark.sql("""
SELECT
  FLOOR(year / 10) * 10 AS decade,
  COUNT(*) AS movie_count,
  ROUND(AVG(rating_score), 2) AS avg_rating,
  ROUND(AVG(rating_count), 0) AS avg_rating_count
FROM movies
WHERE year IS NOT NULL
GROUP BY FLOOR(year / 10) * 10
ORDER BY decade
""")
decade_trend.show(30, truncate=False)
print("分析说明3：将年份按年代聚合后，可以观察电影数量和评分随时间的变化趋势。较近年代电影数量通常更多，说明数据集中现代影片收录更充分。")

print("========== 查询4：窗口函数，每个国家/地区评分最高的电影 Top-3 ==========")
country_movies = (
    movies.select(
        "title",
        "year",
        "rating_score",
        "rating_count",
        explode(split(col("countries"), "/")).alias("country"),
    )
    .where((col("country").isNotNull()) & (col("country") != ""))
)
window_spec = Window.partitionBy("country").orderBy(desc("rating_score"), desc("rating_count"))
country_top3 = (
    country_movies.withColumn("rank", row_number().over(window_spec))
    .where(col("rank") <= 3)
    .orderBy("country", "rank")
)
country_top3.show(60, truncate=False)
print("分析说明4：使用 row_number 窗口函数在每个国家/地区内部按评分和评分人数排序，筛选各地区评分最高的 Top-3 电影，体现窗口函数的分组内排名能力。")

print("========== 查询5：国家/地区与类型关联统计 ==========")
country_genre = spark.sql("""
SELECT
  country,
  genre,
  COUNT(*) AS movie_count,
  ROUND(AVG(rating_score), 2) AS avg_rating
FROM (
  SELECT
    country,
    explode(split(genres, '/')) AS genre,
    rating_score
  FROM (
    SELECT
      explode(split(countries, '/')) AS country,
      genres,
      rating_score
    FROM movies
    WHERE countries IS NOT NULL AND genres IS NOT NULL
  ) c
) t
WHERE country <> '' AND genre <> ''
GROUP BY country, genre
HAVING movie_count >= 20
ORDER BY movie_count DESC, avg_rating DESC
LIMIT 20
""")
country_genre.show(truncate=False)
print("分析说明5：该查询同时拆分国家/地区和类型字段，统计不同国家/地区在各类型上的电影数量和平均评分，可用于分析地区电影创作类型偏好。")

spark.stop()
