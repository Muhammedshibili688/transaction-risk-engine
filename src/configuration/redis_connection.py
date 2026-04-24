import redis
import os
import sys
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
from src.exception import FraudException
from src.logger import logging

class RedisClient:
    """
    Thread-safe Singleton Redis Client with Connection Pooling.
    Optimized for low-latency streaming and high-availability production.
    """
    _client = None
    _pool = None

    def __init__(self):
        try:
            if RedisClient._client is None:
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", 6379))
                password = os.getenv("REDIS_PASSWORD", None)

                logging.info(f"Initializing Production Redis Connection Pool ({host}:{port})...")

                # 1. RETRY STRATEGY (Exponential Backoff)
                # In production, if Redis is busy, we wait 0.1s, then 0.2s, then 0.4s...
                # This prevents "Thundering Herd" problems.
                retry_strategy = Retry(ExponentialBackoff(cap=2, base=0.1), 3)

                # 2. CONNECTION POOLING
                # We create a pool of connections that are reused. 
                # Opening a new connection for every transaction is too slow.
                RedisClient._pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    password=password,
                    decode_responses=True,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry=retry_strategy,
                    retry_on_timeout=True,
                    max_connections=20, # Limits total connections to save DB memory
                    health_check_interval=30 # Pings every 30s to keep connection alive
                )

                # 3. CLIENT INITIALIZATION
                RedisClient._client = redis.Redis(connection_pool=RedisClient._pool)

                # 4. INITIAL HEALTH CHECK
                RedisClient._client.ping()
                logging.info(f"Redis connection pool established.")

            self.client = RedisClient._client
        except Exception as e:
            raise FraudException(e, sys)

    @staticmethod
    def get_client():
        """Helper to get client without instantiating if already exists."""
        if RedisClient._client is None:
            RedisClient()
        return RedisClient._client