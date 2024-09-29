from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict

from src.config import config

# 클라이언트별 버킷을 저장할 딕셔너리
buckets: Dict[str, Dict] = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.client:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="요청에 client 속성이 없습니다.",
            )
        client_ip = request.client.host
        current_time = time.time()

        if client_ip not in buckets:
            buckets[client_ip] = {
                "tokens": config.bucket_size,
                "last_refill": current_time
            }

        bucket = buckets[client_ip]
        time_passed = current_time - bucket["last_refill"]
        refill_amount = time_passed * (config.requests_per_minute / 60)

        bucket["tokens"] = min(bucket["tokens"] + refill_amount, config.bucket_size)
        bucket["last_refill"] = current_time

        if bucket["tokens"] < 1:
            return JSONResponse(
                status_code=429,
                content={"message": "Rate limit exceeded. Please try again later."}
            )

        bucket["tokens"] -= 1
        response = await call_next(request)
        return response

