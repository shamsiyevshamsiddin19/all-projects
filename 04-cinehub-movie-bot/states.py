"""FSM holatlari (eski PHP 'step' o'rniga)."""
from aiogram.fsm.state import State, StatesGroup


class UserSG(StatesGroup):
    view_mov = State()       # kino guruhini tanlash
    view_ser = State()       # serial tanlash
    view_ep = State()        # qism tanlash
    catalog_select = State() # reyting bo'limi
    search_input = State()   # qidiruv matni
    select_result = State()  # qidiruv natijasini tanlash
    code_wait = State()      # "KOD BILAN QIDIRISH" — kod kutilmoqda


class AdminSG(StatesGroup):
    panel = State()

    # Kino qo'shish
    movie_add_type = State()
    add_movie_name = State()
    add_movie_code = State()
    add_movie_file = State()
    ask_post_channel_mov = State()
    mov_group_browser = State()
    mov_group_search = State()
    add_ext_mov_code = State()
    add_ext_mov_file = State()

    # Serial qo'shish
    series_add_type = State()
    add_series_name = State()
    add_series_code = State()
    add_series_ep = State()
    ser_browser_add = State()
    ser_group_search = State()
    add_ext_series_file = State()
    ask_post_channel_ser = State()

    # Rename
    mov_rename_browser = State()
    rename_mov_search = State()
    mov_rename_input = State()
    ser_rename_browser = State()
    rename_ser_search = State()
    ser_rename_input = State()

    # O'chirish
    del_choice = State()
    del_mov = State()
    del_ser = State()

    # Obuna
    sub_sets = State()
    add_ch = State()
    add_ch_link = State()
    del_ch = State()

    # Manba
    set_sig = State()

    # Ijtimoiy tarmoqlar
    social_menu = State()
    add_social = State()
    del_social = State()

    # Reklama
    broad_collect = State()
