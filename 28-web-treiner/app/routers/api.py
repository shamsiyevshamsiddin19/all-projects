from fastapi import APIRouter, Depends, Query, status

from app.exercises.catalog import ExerciseCatalog
from app.schemas.exercises import AnswerPayload, AnswerResult, PublicExercise, Track
from app.services.catalog_service import get_catalog

router = APIRouter(prefix="/api", tags=["mashqlar"])


@router.get("/health", tags=["tizim"])
async def health_check() -> dict[str, str]:
    """Load balancer yoki monitoring uchun yengil holat tekshiruvi."""

    return {"status": "ok"}


@router.get("/tracks", response_model=tuple[Track, ...])
async def list_tracks(catalog: ExerciseCatalog = Depends(get_catalog)) -> tuple[Track, ...]:
    """Interfeys filtrlarida ishlatiladigan yo'nalishlarni qaytaradi."""

    return catalog.tracks()


@router.get("/exercises", response_model=tuple[PublicExercise, ...])
async def list_exercises(
    track: str | None = Query(default=None, max_length=32),
    catalog: ExerciseCatalog = Depends(get_catalog),
) -> tuple[PublicExercise, ...]:
    """Tanlangan yo'nalishning mashqlarini xavfsiz ko'rinishda qaytaradi."""

    return catalog.exercises(track_id=track)


@router.get("/exercises/{exercise_id}", response_model=PublicExercise)
async def get_exercise(
    exercise_id: str,
    catalog: ExerciseCatalog = Depends(get_catalog),
) -> PublicExercise:
    """Bitta mashqni javob kalitisiz qaytaradi."""

    return catalog.exercise(exercise_id).public()


@router.post("/exercises/{exercise_id}/check", response_model=AnswerResult, status_code=status.HTTP_200_OK)
async def check_answer(
    exercise_id: str,
    payload: AnswerPayload,
    catalog: ExerciseCatalog = Depends(get_catalog),
) -> AnswerResult:
    """Kiritilgan javobni mashq turiga mos qoidalar bilan tekshiradi."""

    return catalog.check(exercise_id=exercise_id, answer=payload.answer)

