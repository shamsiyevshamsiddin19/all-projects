from enum import StrEnum

from pydantic import BaseModel, Field


class ExerciseKind(StrEnum):
    """Interfeys mashqni qanday boshqarishini belgilovchi turlar."""

    PRONUNCIATION = "pronunciation"
    LISTENING_NUMBER = "listening_number"
    CODE_CHALLENGE = "code_challenge"


class Track(BaseModel):
    """Mashqlar yo'nalishi uchun ko'rinadigan ma'lumot."""

    id: str
    title: str
    description: str
    accent: str


class ExerciseChoice(BaseModel):
    """Tanlovli mashqdagi bitta javob varianti."""

    value: str
    label: str


class Exercise(BaseModel):
    """Katalogda saqlanadigan to'liq mashq modeli, shu jumladan javob kaliti."""

    id: str
    track_id: str
    title: str
    description: str
    kind: ExerciseKind
    duration_minutes: int = Field(ge=1, le=60)
    level: str
    instruction: str
    target_text: str | None = None
    audio_text: str | None = None
    code: str | None = None
    choices: tuple[ExerciseChoice, ...] = ()
    hint: str | None = None
    expected_answers: tuple[str, ...] = ()

    def public(self) -> "PublicExercise":
        """Brauzerga tekshiruv kalitini bermaydigan xavfsiz ko'rinishni qaytaradi."""

        return PublicExercise(
            id=self.id,
            track_id=self.track_id,
            title=self.title,
            description=self.description,
            kind=self.kind,
            duration_minutes=self.duration_minutes,
            level=self.level,
            instruction=self.instruction,
            target_text=self.target_text,
            audio_text=self.audio_text,
            code=self.code,
            choices=self.choices,
            hint=self.hint,
        )


class PublicExercise(BaseModel):
    """Mashqning foydalanuvchi interfeysi oladigan qismi."""

    id: str
    track_id: str
    title: str
    description: str
    kind: ExerciseKind
    duration_minutes: int
    level: str
    instruction: str
    target_text: str | None = None
    audio_text: str | None = None
    code: str | None = None
    choices: tuple[ExerciseChoice, ...] = ()
    hint: str | None = None


class AnswerPayload(BaseModel):
    """Bitta mashq uchun foydalanuvchi javobi."""

    answer: str = Field(min_length=1, max_length=1000)


class AnswerResult(BaseModel):
    """Tekshiruvdan keyin foydalanuvchi ko'radigan natija."""

    correct: bool
    message: str
