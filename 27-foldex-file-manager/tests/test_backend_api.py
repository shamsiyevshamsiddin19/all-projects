# -*- coding: utf-8 -*-
import io
import pytest
from httpx import AsyncClient
from app.core.config import settings
from app.core.security import sanitize_filename

@pytest.mark.asyncio
async def test_auth_me_success(client: AsyncClient, admin_headers: dict):
    response = await client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"] is True
    assert data["user_id"] == settings.TELEGRAM_ADMIN_ID

@pytest.mark.asyncio
async def test_auth_me_unauthorized(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_me_forbidden_for_non_admin(client: AsyncClient, non_admin_token: str):
    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {non_admin_token}"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_logout(client: AsyncClient, admin_headers: dict):
    response = await client.post("/api/auth/logout", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_login_page_renders(client: AsyncClient):
    response = await client.get("/login")
    assert response.status_code == 200
    assert "Foldex" in response.text
    assert "Telegram" in response.text

@pytest.mark.asyncio
async def test_folder_crud_flow(client: AsyncClient, admin_headers: dict):
    # 1. Create root folder
    create_res = await client.post(
        "/api/folders/",
        headers=admin_headers,
        json={"name": "Rus tili", "icon": "📚", "color": "blue"}
    )
    assert create_res.status_code == 201
    folder_data = create_res.json()
    folder_id = folder_data["id"]
    assert folder_data["name"] == "Rus tili"

    # 2. Prevent invalid parent_id
    dup_res = await client.post(
        "/api/folders/",
        headers=admin_headers,
        json={"name": "Xato Papka", "parent_id": 999999}
    )
    assert dup_res.status_code == 400

    # 3. Create subfolder
    sub_res = await client.post(
        "/api/folders/",
        headers=admin_headers,
        json={"name": "Grammatika", "parent_id": folder_id}
    )
    assert sub_res.status_code == 201
    sub_data = sub_res.json()
    sub_id = sub_data["id"]
    assert sub_data["parent_id"] == folder_id

    # 4. Get folder tree
    tree_res = await client.get("/api/folders/tree", headers=admin_headers)
    assert tree_res.status_code == 200
    tree_data = tree_res.json()
    assert len(tree_data) >= 1
    assert any(f["id"] == folder_id for f in tree_data)

    # 5. Rename folder (PUT)
    rename_res = await client.put(
        f"/api/folders/{sub_id}",
        headers=admin_headers,
        json={"name": "Grammatika Yangilangan"}
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["name"] == "Grammatika Yangilangan"

    # 6. Delete subfolder
    del_sub_res = await client.delete(f"/api/folders/{sub_id}", headers=admin_headers)
    assert del_sub_res.status_code == 200
    assert del_sub_res.json()["success"] is True

    # 7. Delete root folder
    del_root_res = await client.delete(f"/api/folders/{folder_id}", headers=admin_headers)
    assert del_root_res.status_code == 200
    assert del_root_res.json()["success"] is True

@pytest.mark.asyncio
async def test_file_upload_list_delete(client: AsyncClient, admin_headers: dict):
    # Create parent folder for files
    folder_res = await client.post(
        "/api/folders/",
        headers=admin_headers,
        json={"name": "Test Hujjatlar"}
    )
    assert folder_res.status_code == 201
    f_id = folder_res.json()["id"]

    # Upload mock file
    file_content = b"Salom Foldex Test Fayl Mazmuni"
    files = [("files", ("test_doc.txt", io.BytesIO(file_content), "text/plain"))]
    data = {"folder_id": str(f_id), "description": "Sinov fayli"}

    up_res = await client.post("/api/files/upload", headers=admin_headers, files=files, data=data)
    assert up_res.status_code == 201
    file_list = up_res.json()
    assert len(file_list) == 1
    file_info = file_list[0]
    file_id = file_info["id"]
    assert file_info["name"] == "test_doc.txt"
    assert file_info["file_size"] == len(file_content)

    # List files in folder
    list_res = await client.get(f"/api/files/?folder_id={f_id}", headers=admin_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(f["id"] == file_id for f in list_data["items"])

    # Search files
    search_res = await client.get("/api/files/?search=test_doc", headers=admin_headers)
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1

    # Rename file (PUT)
    ren_res = await client.put(
        f"/api/files/{file_id}",
        headers=admin_headers,
        json={"name": "test_doc_renamed.txt"}
    )
    assert ren_res.status_code == 200
    assert ren_res.json()["name"] == "test_doc_renamed.txt"

    # Delete file
    del_res = await client.delete(f"/api/files/{file_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Clean up folder
    await client.delete(f"/api/folders/{f_id}", headers=admin_headers)

@pytest.mark.asyncio
async def test_stats_dashboard(client: AsyncClient, admin_headers: dict):
    response = await client.get("/api/stats/dashboard", headers=admin_headers)
    assert response.status_code == 200
    stats = response.json()
    assert "total_files" in stats
    assert "total_folders" in stats
    assert "total_size_bytes" in stats
    assert "total_size_formatted" in stats
    assert "categories" in stats

def test_security_sanitization():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("kitob<name>:test.pdf") == "kitob_name__test.pdf"
    assert sanitize_filename("   darslik 2026.docx   ") == "darslik 2026.docx"
    assert sanitize_filename("...") != ""  # Generates fallback name
