from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot API is running"}