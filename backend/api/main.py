"""Main FastAPI application setup"""
from fastapi import FastAPI

app = FastAPI(title="Complyo API")

@app.get("/")
async def root():
    return {"message": "Complyo Enterprise API v2.0"}
