TEXTS = {
    'uz': {
        'welcome': "Assalomu alaykum! Men Hujjat Konvertori botiman.\nO'zingizga kerakli bo'limni tanlang:",
        'choose_lang': "Tilni tanlang / Выберите язык / Choose language:",
        'btn_text_docx': "📝 Matn -> DOCX",
        'btn_img_pdf': "🖼 Rasm -> PDF",
        'btn_zip': "🗜 Fayl -> ZIP",
        'btn_pdf_docx': "📄 PDF -> DOCX",
        'btn_titul': "🎓 TUIT Titul",
        'btn_merge_pdf': "📑 PDF Birlashtirish",
        'btn_split_pdf': "✂️ PDF Qirqish",
        'btn_watermark': "©️ PDF Watermark",
        'btn_office_pdf': "📊 DOC/XLS/PPT -> PDF",
        'btn_ocr': "👁 Rasmdan matn o'qish (OCR)",
        'btn_settings': "⚙️ Sozlamalar",
        'lang_changed': "Til o'zgartirildi!"
    },
    'ru': {
        'welcome': "Здравствуйте! Я бот Конвертер Документов.\nВыберите нужный раздел:",
        'choose_lang': "Tilni tanlang / Выберите язык / Choose language:",
        'btn_text_docx': "📝 Текст -> DOCX",
        'btn_img_pdf': "🖼 Фото -> PDF",
        'btn_zip': "🗜 Файл -> ZIP",
        'btn_pdf_docx': "📄 PDF -> DOCX",
        'btn_titul': "🎓 Титулка TUIT",
        'btn_merge_pdf': "📑 Объединить PDF",
        'btn_split_pdf': "✂️ Разделить PDF",
        'btn_watermark': "©️ PDF Водяной знак",
        'btn_office_pdf': "📊 DOC/XLS/PPT -> PDF",
        'btn_ocr': "👁 Распознавание текста (OCR)",
        'btn_settings': "⚙️ Настройки",
        'lang_changed': "Язык изменен!"
    },
    'en': {
        'welcome': "Hello! I am a Document Converter bot.\nChoose a section below:",
        'choose_lang': "Tilni tanlang / Выберите язык / Choose language:",
        'btn_text_docx': "📝 Text -> DOCX",
        'btn_img_pdf': "🖼 Image -> PDF",
        'btn_zip': "🗜 File -> ZIP",
        'btn_pdf_docx': "📄 PDF -> DOCX",
        'btn_titul': "🎓 TUIT Title Page",
        'btn_merge_pdf': "📑 Merge PDF",
        'btn_split_pdf': "✂️ Split PDF",
        'btn_watermark': "©️ PDF Watermark",
        'btn_office_pdf': "📊 DOC/XLS/PPT -> PDF",
        'btn_ocr': "👁 Extract text (OCR)",
        'btn_settings': "⚙️ Settings",
        'lang_changed': "Language changed!"
    }
}

def get_text(lang_code: str, key: str):
    return TEXTS.get(lang_code, TEXTS['uz']).get(key, TEXTS['uz'].get(key, key))
