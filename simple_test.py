#!/usr/bin/env python3

from fastapi import FastAPI
import os

app = FastAPI(title="Test App")

@app.get("/")
def root():
    return {"status": "ok", "port": os.getenv("PORT", "not_set")}

@app.get("/health")
def health():
    return {"status": "healthy", "test": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
