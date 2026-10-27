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
    assert len(response.json()) == 15
    assert "expected_answers" not in response.text


def test_each_track_includes_its_new_exercises() -> None:
    expected_ids = {
        "russian": {"ru-soft-sign", "ru-long-phrase"},
        "english": {"en-number-19", "en-number-3007"},
        "backend": {"dependency-injection", "created-status-code"},
    }

    for track_id, new_ids in expected_ids.items():
        response = client.get("/api/exercises", params={"track": track_id})

        assert response.status_code == 200
        assert new_ids.issubset({exercise["id"] for exercise in response.json()})


def test_new_exercises_accept_correct_answers() -> None:
    answers = {
        "ru-soft-sign": "Моя семья любит тёплый чай.",
        "en-number-3007": "3,007",
        "dependency-injection": "Depends",
    }

    for exercise_id, answer in answers.items():
        response = client.post(f"/api/exercises/{exercise_id}/check", json={"answer": answer})

        assert response.status_code == 200
        assert response.json()["correct"] is True


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
