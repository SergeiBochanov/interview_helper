import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.api.parser_router import router as parser_router
from app.api import search

app = FastAPI()
app.include_router(parser_router)
app.include_router(search.router, prefix="/api", tags=["search"])

@app.get("/")
def read_root():
    return {"status": "Parser component is running online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
