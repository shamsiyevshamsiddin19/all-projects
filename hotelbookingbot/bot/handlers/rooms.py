from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile, Message

from apps.hotels.models import RoomType

from ..keyboards.inline import PAGE_SIZE, room_details_keyboard, room_types_keyboard
from ..keyboards.reply import MAIN_MENU_ROOMS

router = Router(name="rooms")


async def _send_room_types_page(message: Message, page: int, edit: bool = False):
    total = await RoomType.objects.filter(is_active=True).acount()
    room_types = [
        rt
        async for rt in RoomType.objects.filter(is_active=True)
        .select_related("hotel")
        .order_by("name")[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    ]

    if not room_types:
        text = "Hozircha mavjud xonalar yo'q."
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    text = "🏨 Mavjud xona turlari:"
    kb = room_types_keyboard(room_types, page=page, total=total)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(F.text == MAIN_MENU_ROOMS)
async def rooms_menu(message: Message):
    await _send_room_types_page(message, page=0)


@router.callback_query(F.data.startswith("rooms_page:"))
async def rooms_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    await _send_room_types_page(callback.message, page=page, edit=True)
    await callback.answer()


@router.callback_query(F.data == "back_to_rooms")
async def back_to_rooms(callback: CallbackQuery):
    await _send_room_types_page(callback.message, page=0, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("room_type:"))
async def room_type_details(callback: CallbackQuery):
    room_type_id = int(callback.data.split(":")[1])
    try:
        room_type = await RoomType.objects.select_related("hotel").aget(id=room_type_id, is_active=True)
    except RoomType.DoesNotExist:
        await callback.answer("Bu xona turi topilmadi", show_alert=True)
        return

    amenities = [a async for a in room_type.amenities.all()]
    text = format_room_type_card_sync(room_type, amenities)

    if room_type.main_image:
        await callback.message.answer_photo(
            FSInputFile(room_type.main_image.path),
            caption=text,
            reply_markup=room_details_keyboard(room_type.id),
        )
    else:
        await callback.message.answer(text, reply_markup=room_details_keyboard(room_type.id))
    await callback.answer()


def format_room_type_card_sync(room_type, amenities) -> str:
    amenities_str = ", ".join(a.name for a in amenities) or "-"
    return (
        f"<b>{room_type.name}</b>\n"
        f"{room_type.description}\n\n"
        f"👥 Sig'im: {room_type.capacity} kishi\n"
        f"🛏 Karavotlar: {room_type.bed_count}\n"
        f"💵 Narx: {room_type.base_price} {room_type.currency} / kecha\n"
        f"✨ Qulayliklar: {amenities_str}"
    )
