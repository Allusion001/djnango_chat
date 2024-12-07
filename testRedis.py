import redis

try:
    redis_client = redis.StrictRedis(
        host='redis://red-ct8nrjij1k6c73e98j1g:6379',  # Replace with your Redis hostname
        port=6379,                       # Ensure this matches Redis's port
        password='yourpassword',         # Add if authentication is required
        decode_responses=True
    )
    redis_client.ping()
    print("Connected to Redis!")
except redis.ConnectionError as e:
    print(f"Redis connection failed: {e}")
