from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    choosing_type = State()
    entering_topic = State()
    entering_details = State()
    entering_otm = State()        # OTM nomi (titul varag'i uchun)
    choosing_language = State()
    entering_count = State()
    choosing_format = State()
    choosing_tier = State()       # Standart / Premium
    confirming = State()
    waiting_payment = State()


class TopupStates(StatesGroup):
    entering_amount = State()


class ReviseStates(StatesGroup):
    waiting_feedback = State()    # revizyon izohi kutilmoqda


class RateStates(StatesGroup):
    waiting_comment = State()     # past baho izohi kutilmoqda
