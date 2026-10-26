from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_page_is_available() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "train.shamsiyev.uz" in response.text


def test_exercise_has_a_dedicated_page() -> None:
    response = client.get("/mashq/en-number-48")

    assert response.status_code == 200
    assert 'data-page="exercise"' in response.text
    assert 'data-exercise-id="en-number-48"' in response.text


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


def test_unknown_exercise_page_returns_404() -> None:
    response = client.get("/mashq/not-found")

    assert response.status_code == 404
