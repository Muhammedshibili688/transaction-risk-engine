import time
from redis import Redis

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

time.sleep(5)

start = int(
    redis.hget(
        "system:metrics",
        "transactions_processed"
    ) or 0
)

t0 = time.perf_counter()

time.sleep(10)

end = int(
    redis.hget(
        "system:metrics",
        "transactions_processed"
    ) or 0
)

t1 = time.perf_counter()

print(f"TPS = {(end-start)/(t1-t0):.2f}")