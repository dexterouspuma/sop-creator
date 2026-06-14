from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.modules.extractor.extractor import extract_content
from app.modules.ai.client import generate_sop

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile = File(...)):
    file_bytes = await file.read()
    content_blocks = extract_content(file_bytes, file.filename)
    sop = await generate_sop(content_blocks)
    return templates.TemplateResponse(
        "partials/sop_result.html",
        {"request": request, "sop": sop}
    )
