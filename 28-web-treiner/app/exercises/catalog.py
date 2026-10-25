import re
import unicodedata
from collections.abc import Iterable

from fastapi import HTTPException, status

from app.schemas.exercises import AnswerResult, Exercise, ExerciseKind, PublicExercise, Track


def normalize_answer(value: str) -> str:
    """Bo'shliq, registr va tinish belgisi farqlarini tekshiruvda neytrallashtiradi."""

    normalized = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"[^\\w]+", "", normalized, flags=re.UNICODE)


class ExerciseCatalog:
    """Mashqlarni qo'shish va ularga oid asosiy qoidalarni bitta joyda boshqaradi."""

    def __init__(self, tracks: Iterable[Track], exercises: Iterable[Exercise]) -> None:
        self._tracks = {track.id: track for track in tracks}
        self._exercises = {exercise.id: exercise for exercise in exercises}
        self._validate()

    def _validate(self) -> None:
        for exercise in self._exercises.values():
            if exercise.track_id not in self._tracks:
                raise ValueError(f"Noma'lum yo'nalish: {exercise.track_id}")
            if not exercise.expected_answers:
                raise ValueError(f"Javob kaliti yo'q mashq: {exercise.id}")

    def tracks(self) -> tuple[Track, ...]:
        return tuple(self._tracks.values())

    def exercises(self, track_id: str | None = None) -> tuple[PublicExercise, ...]:
        items = self._exercises.values()
        if track_id:
            if track_id not in self._tracks:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yo'nalish topilmadi")
            items = (item for item in items if item.track_id == track_id)
        return tuple(item.public() for item in items)

    def exercise(self, exercise_id: str) -> Exercise:
        try:
            return self._exercises[exercise_id]
        except KeyError as error:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mashq topilmadi") from error

    def check(self, exercise_id: str, answer: str) -> AnswerResult:
        exercise = self.exercise(exercise_id)
        normalized = normalize_answer(answer)
        expected = {normalize_answer(item) for item in exercise.expected_answers}
        correct = normalized in expected

        if exercise.kind is ExerciseKind.PRONUNCIATION:
            required_words = normalize_answer(exercise.target_text or "")
            correct = correct or (len(normalized) >= 8 and required_words in normalized)

        if correct:
            return AnswerResult(correct=True, message="To'g'ri. Mashq bugungi natijangizga qo'shildi.")
        return AnswerResult(
            correct=False,
            message="Yana bir bor urinib ko'ring. Ko'rsatmani sekin o'qing yoki tinglang.",
        )

