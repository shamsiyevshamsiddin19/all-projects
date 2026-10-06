from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class RoleFilter(BaseFilter):
    """Handler registratsiyasida ishlatiladi: @router.message(Command('pending'), RoleFilter(['OPERATOR', 'ADMIN', 'SUPERADMIN']))"""

    def __init__(self, roles: list[str]):
        self.roles = roles

    async def __call__(self, event: TelegramObject, user=None, **kwargs) -> bool:
        if user is None:
            return False
        return user.role in self.roles
