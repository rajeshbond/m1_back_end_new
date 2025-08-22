 
from fastapi import FastAPI, Request

# from app.routers import tenant
from . import models
from .database import engine
from .routers import (fadmin,auth,admin,tenant,tenant_user,shifts,declaration,product,inspection,inspection_result,mold,machine,mold_machine)
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles



models.Base.metadata.create_all(bind=engine) # commented becase now alembic is genetatic the table for us

app = FastAPI()

##### lIST OF origins

origins = ['*']


# #  pasting CORAS CODE #################
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# # #####################################

# ------------ define the routers ---------------
app.include_router(admin.router)
app.include_router(auth.router,include_in_schema=False)
app.include_router(fadmin.router)
app.include_router(tenant.router)
app.include_router(tenant_user.router)
app.include_router(shifts.router)
app.include_router(declaration.router)
app.include_router(product.router)
app.include_router(inspection.router)
app.include_router(inspection_result.router)
app.include_router(mold.router)
app.include_router(machine.router)
app.include_router(mold_machine.router)


# ---------------Ends-----------------------------



app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/",response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})

