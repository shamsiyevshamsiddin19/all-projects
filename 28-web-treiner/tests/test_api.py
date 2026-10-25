from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_page_is_available() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "train.shamsiyev.uz" in response.text


def test_catalog_hides_answer_keys() -> None:
    response = client.get("/api/exercises")

    assert response.status_code == 200
    assert len(response.json()) == 9
    assert "expected_answers" not in response.text


def test_checking_a_correct_answer() -> None:
    response = client.post("/api/exercises/en-number-48/check", json={"answer": "48"})

    assert response.status_code == 200
    assert response.json()["correct"] is True


def test_unknown_exercise_returns_404() -> None:
    response = client.get("/api/exercises/not-found")

    assert response.status_code == 404
