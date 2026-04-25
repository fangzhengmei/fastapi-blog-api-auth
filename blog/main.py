from fastapi import FastAPI
from . import models
from .database import engine
from .routers import blog, user, authentication, tag

app = FastAPI()

models.Base.metadata.create_all(engine)

@app.get("/")
def root():
    return {"message": "FastAPI Blog API is running 🚀"}

app.include_router(authentication.router, prefix="/auth", tags=["Auth"])
app.include_router(blog.router, prefix="/blog", tags=["Blog"])
app.include_router(user.router, prefix="/user", tags=["User"])
app.include_router(tag.router, prefix="/tags", tags=["Tags"])