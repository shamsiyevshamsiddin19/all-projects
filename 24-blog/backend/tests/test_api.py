import pytest
from fastapi.testclient import TestClient
import uuid

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def random_suffix():
    return str(uuid.uuid4())[:8]

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["database"] == "PostgreSQL"

    res_h = client.get("/api/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "healthy"

def test_auth_register_and_login(random_suffix):
    email = f"test_{random_suffix}@example.com"
    username = f"user_{random_suffix}"
    password = "SuperPassword123"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email

    # Duplicate register should fail
    dup_res = client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert dup_res.status_code == 400

    # 2. Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 3. Get profile /me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

def test_categories(random_suffix):
    # Need user to create category
    token = client.post("/api/auth/register", json={
        "username": f"cat_user_{random_suffix}",
        "email": f"cat_{random_suffix}@example.com",
        "password": "Password123"
    }).json()["access_token"]

    cat_name = f"SciFi_{random_suffix}"
    res = client.post("/api/categories", json={
        "name": cat_name,
        "description": "Science fiction topics"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 201
    cat_id = res.json()["id"]

    # List categories
    list_res = client.get("/api/categories")
    assert list_res.status_code == 200
    cats = list_res.json()
    assert any(c["name"] == cat_name for c in cats)

    # Get single category
    cat_res = client.get(f"/api/categories/{cat_id}")
    assert cat_res.status_code == 200
    assert cat_res.json()["name"] == cat_name

def test_post_lifecycle_and_features(random_suffix):
    # 1. Register User A
    user_a = client.post("/api/auth/register", json={
        "username": f"author_a_{random_suffix}",
        "email": f"author_a_{random_suffix}@example.com",
        "password": "Password123"
    }).json()
    token_a = user_a["access_token"]
    user_a_id = user_a["user"]["id"]

    # 2. Register User B
    user_b = client.post("/api/auth/register", json={
        "username": f"commenter_b_{random_suffix}",
        "email": f"commenter_b_{random_suffix}@example.com",
        "password": "Password123"
    }).json()
    token_b = user_b["access_token"]

    # 3. Create a category
    cat = client.post("/api/categories", json={
        "name": f"AI_Tech_{random_suffix}",
        "description": "Artificial Intelligence"
    }, headers={"Authorization": f"Bearer {token_a}"}).json()

    # 4. Create Post
    post_res = client.post("/api/posts", json={
        "title": f"Future of Neural Networks {random_suffix}",
        "content": "Deep exploration of transformer neural networks and reasoning models.",
        "category_id": cat["id"],
        "rating": 5,
        "published": True
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert post_res.status_code == 201
    post = post_res.json()
    post_id = post["id"]
    assert post["title"] == f"Future of Neural Networks {random_suffix}"

    # 5. List Posts
    posts_res = client.get("/api/posts")
    assert posts_res.status_code == 200
    assert any(p["id"] == post_id for p in posts_res.json())

    # 6. Filter by Category
    filter_res = client.get(f"/api/posts?category_id={cat['id']}")
    assert filter_res.status_code == 200
    assert all(p["category_id"] == cat["id"] for p in filter_res.json())

    # 7. Search
    search_res = client.get(f"/api/posts?search={random_suffix}")
    assert search_res.status_code == 200
    assert any(p["id"] == post_id for p in search_res.json())

    # 8. Add Comment by User B
    c_res = client.post(f"/api/posts/{post_id}/comments", json={
        "content": "This is an extraordinary breakdown!"
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert c_res.status_code == 201
    comment_id = c_res.json()["id"]

    # 9. Get Comments
    get_c_res = client.get(f"/api/posts/{post_id}/comments")
    assert get_c_res.status_code == 200
    assert len(get_c_res.json()) >= 1
    assert get_c_res.json()[-1]["id"] == comment_id

    # 10. Post Detail (includes comments)
    detail_res = client.get(f"/api/posts/{post_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == post_id
    assert detail["comments_count"] >= 1
    assert any(c["id"] == comment_id for c in detail["comments"])

    # 11. User Posts
    user_posts_res = client.get(f"/api/users/{user_a_id}/posts")
    assert user_posts_res.status_code == 200
    assert any(p["id"] == post_id for p in user_posts_res.json())

    # 12. Current User Posts (/api/users/me/posts)
    my_posts_res = client.get("/api/users/me/posts", headers={"Authorization": f"Bearer {token_a}"})
    assert my_posts_res.status_code == 200
    assert any(p["id"] == post_id for p in my_posts_res.json())

    # 13. Update Post
    upd_res = client.put(f"/api/posts/{post_id}", json={
        "title": f"Updated Future of Neural Networks {random_suffix}",
        "rating": 4
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert upd_res.status_code == 200
    assert upd_res.json()["title"] == f"Updated Future of Neural Networks {random_suffix}"

    # Non-author cannot update post
    upd_forbidden = client.put(f"/api/posts/{post_id}", json={
        "title": "Hacked Title"
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert upd_forbidden.status_code == 403

    # 14. Delete Comment
    del_c_res = client.delete(f"/api/comments/{comment_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_c_res.status_code == 200

    # 15. Delete Post
    del_post_res = client.delete(f"/api/posts/{post_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert del_post_res.status_code == 200
