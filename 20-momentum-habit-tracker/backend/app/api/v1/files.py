import os
import shutil
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from app.api.deps import get_current_active_user
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/files", tags=["File Storage"])

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".jpg", ".jpeg", ".png", ".gif", ".zip", ".rar", ".7z",
    ".txt", ".py", ".dart", ".java", ".cpp", ".c", ".json", ".csv"
}


class FileUploadResponse(BaseModel):
    file_name: str
    file_path: str
    file_url: str
    file_type: str
    file_size: int


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Xavfsiz fayl yuklash (PDF, DOCX, XLSX, Rasm, ZIP va boshqalar)",
)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    original_filename = file.filename or "file.dat"
    _, ext = os.path.splitext(original_filename.lower())

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fayl formati qo'llab-quvvatlanmaydi ({ext}). Ruxsat etilgan: PDF, Word, Excel, Rasm, ZIP va kod fayllari.",
        )

    # Read and validate size
    content = await file.read()
    file_size = len(content)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fayl hajmi ruxsat etilgan maksimal ({settings.MAX_UPLOAD_SIZE_MB}MB) dan katta.",
        )

    # Xavfsiz noyob fayl nomi. Diqqat: original_filename klient tomonidan
    # to'liq boshqariladi — agar u to'g'ridan-to'g'ri saqlash yo'liga
    # qo'shilsa (masalan nomi "../../etc/cron.d/evil" bo'lsa), server
    # UPLOAD_DIR tashqarisiga, istalgan joyga fayl yozib qo'yishi mumkin edi
    # (path traversal). Shuning uchun nomdan faqat bazaviy qismini olamiz va
    # "/", "\" kabi yo'l belgilarini ham tozalaymiz.
    safe_name = os.path.basename(original_filename).replace(' ', '_')
    safe_name = safe_name.replace('/', '_').replace('\\', '_')
    if not safe_name or safe_name in {'.', '..'}:
        safe_name = f"file{ext}"
    unique_filename = f"{uuid.uuid4().hex}_{safe_name}"
    save_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Yakuniy tekshiruv: hisoblangan yo'l hamon UPLOAD_DIR ichida ekanini
    # kafolatlaymiz — himoyaning ikkinchi qatlami.
    upload_dir_abs = os.path.abspath(settings.UPLOAD_DIR)
    save_path_abs = os.path.abspath(save_path)
    if os.path.commonpath([upload_dir_abs, save_path_abs]) != upload_dir_abs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fayl nomi yaroqsiz",
        )

    with open(save_path, "wb") as f:
        f.write(content)

    file_url = f"/uploads/{unique_filename}"

    return FileUploadResponse(
        file_name=original_filename,
        file_path=save_path,
        file_url=file_url,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
    )
