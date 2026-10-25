from functools import lru_cache

from app.exercises.catalog import ExerciseCatalog
from app.exercises.content import EXERCISES, TRACKS


@lru_cache
def get_catalog() -> ExerciseCatalog:
    """Yagona katalog nusxasini ilovaning barcha endpointlariga ulashadi."""

    return ExerciseCatalog(tracks=TRACKS, exercises=EXERCISES)

