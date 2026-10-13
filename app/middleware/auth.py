import os
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyQuery


api_key_query = APIKeyQuery(name="apiKey", auto_error=False)


def authenticate_api_key(api_key: str = Depends(api_key_query)):
    authApiKey = os.getenv('AUTH_API_KEY')
    if not api_key or api_key != authApiKey:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
