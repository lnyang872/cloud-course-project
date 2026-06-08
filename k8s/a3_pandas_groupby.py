import time
import pandas as pd

input_path = "/root/douban_movies.csv"

start_time = time.perf_counter()

df = pd.read_csv(input_path)

for column in ["movie_id", "year", "rating_score", "rating_count", "collect_count"]:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=["movie_id", "title", "year", "rating_score", "genres"])
df = df.drop_duplicates(subset=["movie_id"])

genres = df.assign(genre=df["genres"].str.split("/")).explode("genre")
result = (
    genres.groupby("genre")
    .agg(
        movie_count=("movie_id", "count"),
        avg_rating=("rating_score", "mean"),
        avg_rating_count=("rating_count", "mean"),
    )
    .sort_values("movie_count", ascending=False)
    .head(10)
)

elapsed = time.perf_counter() - start_time

print("========== Pandas 单机 GROUP BY 查询结果 ==========")
print(result.to_string())
print(f"PANDAS_TIME_SECONDS={elapsed:.4f}")
