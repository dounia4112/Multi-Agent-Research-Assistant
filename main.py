from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import routers


app = FastAPI(title="Multi-Agent Research Assistant")


app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"]
)


app.include_router(routers.router, prefix='/assistant')