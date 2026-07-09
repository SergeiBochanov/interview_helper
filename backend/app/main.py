import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.database.database import engine, Base
import app.database.models as models

load_dotenv()

from app.api import parser_router, search, history

app = FastAPI()
app.include_router(parser_router.router)
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(history.router, prefix="/api")

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"status": "Parser component is running online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
