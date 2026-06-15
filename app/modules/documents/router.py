from fastapi import APIRouter, Request, UploadFile, File, Form
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
async def upload(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    document_number: str = Form(""),
    revision: str = Form(""),
    date: str = Form(""),
):
    file_bytes = await file.read()
    content_blocks = extract_content(file_bytes, file.filename)
    sop = await generate_sop(content_blocks)
    meta = {
        "title": title.strip(),
        "document_number": document_number.strip(),
        "revision": revision.strip(),
        "date": date.strip(),
    }
    doc_images = [
        f"data:{b['source']['media_type']};base64,{b['source']['data']}"
        for b in content_blocks
        if b.get("type") == "image"
    ]
    return templates.TemplateResponse(
        "partials/sop_result.html",
        {"request": request, "sop": sop, "meta": meta, "doc_images": doc_images}
    )
