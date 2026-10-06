import pytest
from httpx import ASGITransport, AsyncClient
from app.core.database import init_db
from app.main import app


@pytest.mark.asyncio
async def test_full_system_flow():
    # Initialize DB tables for testing
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Register Teacher
        teacher_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "teacher@example.com",
                "password": "Password123!",
                "full_name": "Aziz O'qituvchi",
                "role": "TEACHER",
                "phone": "+998901234567",
            },
        )
        assert teacher_reg.status_code == 201
        teacher_data = teacher_reg.json()
        teacher_token = teacher_data["access_token"]
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

        # 3. Register Student
        student_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "student@example.com",
                "password": "Password123!",
                "full_name": "Jasur Talaba",
                "role": "STUDENT",
                "phone": "+998907654321",
            },
        )
        assert student_reg.status_code == 201
        student_data = student_reg.json()
        student_token = student_data["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 4. Teacher creates Group
        group_res = await client.post(
            "/api/v1/groups",
            headers=teacher_headers,
            json={
                "name": "Python Backend 2026",
                "description": "FastAPI & Flutter master kursi",
            },
        )
        assert group_res.status_code == 201
        group_data = group_res.json()
        group_id = group_data["id"]
        invite_code = group_data["invite_code"]
        assert len(invite_code) == 6

        # 5. Student joins Group via invite code
        join_res = await client.post(
            "/api/v1/groups/join",
            headers=student_headers,
            json={"invite_code": invite_code},
        )
        assert join_res.status_code == 200
        assert len(join_res.json()["members"]) == 1

        # 6. Teacher creates Assignment
        assignment_res = await client.post(
            "/api/v1/assignments",
            headers=teacher_headers,
            json={
                "title": "REST API va Database Schema yaratish",
                "description": "SQLAlchemy 2.0 bilan 10 ta jadval modelini quring.",
                "instructions": "GitHub linkini yuboring va PDF hisobot biriktiring.",
                "group_id": group_id,
                "deadline": "2026-12-31T23:59:59Z",
                "priority": "HIGH",
                "max_score": 100,
                "status": "PUBLISHED",
            },
        )
        assert assignment_res.status_code == 201
        assignment_id = assignment_res.json()["id"]

        # 7. Student lists assignments
        student_tasks = await client.get("/api/v1/assignments", headers=student_headers)
        assert student_tasks.status_code == 200
        assert len(student_tasks.json()) == 1
        assert student_tasks.json()[0]["title"] == "REST API va Database Schema yaratish"

        # 8. Student submits assignment
        submit_res = await client.post(
            f"/api/v1/assignments/{assignment_id}/submit",
            headers=student_headers,
            json={
                "answer_text": "Barcha modellar va testlar muvaffaqiyatli tayyorlandi!",
                "attachments": [
                    {
                        "file_name": "solution.py",
                        "file_path": "/storage/uploads/solution.py",
                        "file_type": "text/x-python",
                        "file_size": 2048,
                    }
                ],
            },
        )
        assert submit_res.status_code == 201
        submission_id = submit_res.json()["id"]

        # 9. Teacher reviews & grades submission
        review_res = await client.post(
            f"/api/v1/submissions/{submission_id}/review",
            headers=teacher_headers,
            json={
                "score": 95,
                "feedback_text": "A'lo darajada bajarilgan! Clean Architecture qoidalariga rioya qilingan.",
                "decision": "APPROVED",
            },
        )
        assert review_res.status_code == 200
        assert review_res.json()["status"] == "GRADED"
        assert review_res.json()["latest_score"] == 95

        # 10. Teacher checks Dashboard Stats
        dash_res = await client.get("/api/v1/analytics/dashboard", headers=teacher_headers)
        assert dash_res.status_code == 200
        stats = dash_res.json()
        assert stats["total_students"] == 1
        assert stats["total_groups"] == 1
        assert stats["average_score"] == 95.0

        # 11. PDF Export check
        pdf_res = await client.get("/api/v1/analytics/export/pdf", headers=teacher_headers)
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert len(pdf_res.content) > 500

        # 12. Excel Export check
        excel_res = await client.get("/api/v1/analytics/export/excel", headers=teacher_headers)
        assert excel_res.status_code == 200
        assert "spreadsheetml" in excel_res.headers["content-type"]
        assert len(excel_res.content) > 500

        # 13. IDOR: guruhga a'zo bo'lmagan boshqa talaba shu vazifani
        # ko'ra olmasligi va unga javob topshira olmasligi kerak.
        outsider_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "outsider@example.com",
                "password": "Password123!",
                "full_name": "Begona Talaba",
                "role": "STUDENT",
            },
        )
        assert outsider_reg.status_code == 201
        outsider_headers = {"Authorization": f"Bearer {outsider_reg.json()['access_token']}"}

        outsider_detail_res = await client.get(
            f"/api/v1/assignments/{assignment_id}", headers=outsider_headers
        )
        assert outsider_detail_res.status_code == 403

        outsider_submit_res = await client.post(
            f"/api/v1/assignments/{assignment_id}/submit",
            headers=outsider_headers,
            json={"answer_text": "Ruxsatsiz urinish"},
        )
        assert outsider_submit_res.status_code == 403

        # Guruh a'zosi bo'lgan haqiqiy talaba esa hamon ko'ra olishi kerak.
        member_detail_res = await client.get(
            f"/api/v1/assignments/{assignment_id}", headers=student_headers
        )
        assert member_detail_res.status_code == 200


@pytest.mark.asyncio
async def test_file_upload_rejects_path_traversal():
    """Fayl nomi "../" bilan yuborilsa, u UPLOAD_DIR tashqarisiga yozilmasligi
    va nom ichidagi yo'l belgilari tozalanishi kerak."""
    await init_db()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "uploader@example.com",
                "password": "Password123!",
                "full_name": "Yuklovchi Ustoz",
                "role": "TEACHER",
            },
        )
        assert reg.status_code == 201
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        res = await client.post(
            "/api/v1/files/upload",
            headers=headers,
            files={"file": ("../../../../tmp/evil.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert res.status_code == 201
        data = res.json()
        # Saqlangan yo'l hamon uploads papkasi ichida bo'lishi shart.
        assert "storage/uploads" in data["file_path"]
        assert ".." not in data["file_path"]
