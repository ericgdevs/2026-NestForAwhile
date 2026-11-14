from fastapi import FastAPI

from app.main import app as main_app

app = FastAPI()

app.mount("/api", main_app)
app.mount("/", main_app)