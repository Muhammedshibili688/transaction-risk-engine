# debug_velocity.py

from datetime import datetime
from src.components.feature_store.online_feature_store import OnlineFeatureStore

feature_store = OnlineFeatureStore()

user_id = "USR_00001"   # pick any user from dataset

velocity = feature_store.get_velocity_counts(
    user_id,
    datetime.now()
)

print(velocity)

from src.configuration.redis_connection import RedisClient

redis = RedisClient().client

keys = redis.keys("vel:*")

for key in keys[:10]:
    print(
        key,
        redis.zcard(key)
    )