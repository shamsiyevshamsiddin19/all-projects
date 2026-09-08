/* =========================================================================
   Аудирование / Listening Hub — Zamonaviy Mavzular Katalogi
   - Telegram uslubidagi chat-list kartalari (raqamli avatarlar, nishonlar, darajalar)
   - 4 ta asosiy hayotiy toifa: Hayotiy, Shahar, Sayohat, Ish & Muloqot
   - Yuqori «⚡ Tezkor maishiy trenajyor» blits-kartasi
   - Serverdagi `language_topics` bilan to'liq integratsiya va oflayn zaxira
   ========================================================================= */
(function () {
  'use strict';

  /* Built-in 18 ta amaliy audio-dialog darsi (Rus tili) */
  var RU_TOPICS = [
    // ☕ 1. Повседневная жизнь
    {
      id: 'ru_l_01', num: '01', cat: 'life', catName: 'Повседневная', level: 'A1',
      name: '01. Знакомство и первые фразы',
      desc: 'Tanishuv, ism so\'rash va qayerdanligini aytish',
      folder: 'Повседневная жизнь',
      content:
        'youtube: https://www.youtube.com/watch?v=j3y-q66i2nI\n\n' +
        '# 01. Знакомство и первые фразы\n\n' +
        '[00:01 - 00:04] — Здравствуйте! Меня зовут {Алексей|Aleksey}. А как вас зовут?\n' +
        ':: Assalomu alaykum! Mening ismim Aleksey. Sizning ismingiz nima?\n\n' +
        '[00:05 - 00:09] — Очень приятно! Меня зовут {Анна|Anna}. Вы давно учите русский язык?\n' +
        ':: Juda yoqimli! Mening ismim Anna. Rus tilini o\'rganayotganingizga ancha bo\'ldimi?\n\n' +
        '[00:10 - 00:15] — Нет, я начал учить его только в прошлом {месяце|oy}. Но я стараюсь практиковаться каждый день.\n' +
        ':: Yo\'q, men uni faqat o\'tgan oyda o\'rganishni boshladim. Ammo har kuni mashq qilishga harakat qilaman.\n\n' +
        '[00:16 - 00:20] — Это здорово! У вас уже очень хорошее {произношение|talaffuz}.\n' +
        ':: Bu ajoyib! Sizda allaqachon juda yaxshi talaffuz bor.\n\n' +
        '[00:21 - 00:25] — Спасибо большое! Мне очень нравится звучание этого {языка|til}.\n' +
        ':: Katta rahmat! Menga bu tilning jaranglashi juda yoqadi.\n\n' +
        '? Savol 1: Suhbatdoshlarning ismlari kim?\n' +
        '+ Aleksey va Anna\n' +
        '- Ivan va Mariya\n' +
        '- Dmitriy va Yelena\n\n' +
        '? Savol 2: Aleksey rus tilini qachon boshlagan?\n' +
        '+ O\'tgan oyda\n' +
        '- 2 yil oldin\n' +
        '- Bolaligida\n\n' +
        '? Savol 3: Anna Alekseyning qaysi jihatini maqtadi?\n' +
        '+ Yaxshi talaffuzini\n' +
        '- Tez gapirishini\n' +
        '- Ko\'p so\'z bilishini'
    },
    {
      id: 'ru_l_02', num: '02', cat: 'life', catName: 'Повседневная', level: 'A1',
      name: '02. В кафе — заказ еды и напитков',
      desc: 'Kafeda qahva va yegulik buyurtma qilish',
      folder: 'Повседневная жизнь',
      content:
        'youtube: https://www.youtube.com/watch?v=R9K1uV7u35g\n\n' +
        '# 02. В кафе — заказ еды и напитков\n\n' +
        '[00:01 - 00:04] — Добрый день! Вы готовы сделать {заказ|buyurtma}?\n' +
        ':: Xayrli kun! Buyurtma berishga tayyormisiz?\n\n' +
        '[00:05 - 00:09] — Здравствуйте! Да, принесите, пожалуйста, {кофе|qahva} и круассан.\n' +
        ':: Assalomu alaykum! Ha, menga iltimos qahva va kruassan keltiring.\n\n' +
        '[00:10 - 00:14] — Какой кофе вы предпочитаете: {чёрный|qora} или с молоком?\n' +
        ':: Qanday qahvani ma\'qul ko\'rasiz: qora yoki sutli?\n\n' +
        '[00:15 - 00:18] — С молоком, пожалуйста, и без {сахара|shakar}.\n' +
        ':: Sut bilan, iltimos, va shakarsiz.\n\n' +
        '[00:19 - 00:22] — Хорошо. Что-нибудь ещё {желаете|xohlaysizmi}?\n' +
        ':: Yaxshi. Yana biror narsa xohlaysizmi?\n\n' +
        '[00:23 - 00:26] — Нет, спасибо, это {всё|hammasi}. Сколько с меня?\n' +
        ':: Yo\'q, rahmat, shu xolos. Qancha to\'layman?\n\n' +
        '[00:27 - 00:32] — С вас триста {рублей|rubl}. Оплата картой или {наличными|naqd pul}?\n' +
        ':: Sizdan uch yuz rubl. To\'lov karta orqalimi yoki naqd?\n\n' +
        '[00:33 - 00:36] — Картой, пожалуйста.\n' +
        ':: Karta bilan, iltimos.\n\n' +
        '? Savol 1: Mijoz kafeda nima buyurtma qildi?\n' +
        '+ Qahva va kruassan\n' +
        '- Choy va pishiriq\n' +
        '- Borsh va non\n\n' +
        '? Savol 2: Mijoz qahvani qanday ichadi?\n' +
        '+ Sut bilan va shakarsiz\n' +
        '- Qora va shakar bilan\n' +
        '- Muzli va shirin\n\n' +
        '? Savol 3: Buyurtma hisobi qancha bo\'ldi?\n' +
        '+ 300 rubl\n' +
        '- 500 rubl\n' +
        '- 150 rubl'
    },
    {
      id: 'ru_l_03', num: '03', cat: 'life', catName: 'Повседневная', level: 'A1',
      name: '03. В супермаркете и покупки',
      desc: 'Supermarketda non, mevalar va narxlar',
      folder: 'Повседневная жизнь',
      content:
        '# 03. В супермаркете и покупки\n\n' +
        '— Подскажите, пожалуйста, где у вас {свежий|yangi} хлеб?\n' +
        '— Пройдите прямо, в самом {конце|oxirida} зала, рядом с молочным отделом.\n' +
        '— Спасибо! А сколько стоят эти {яблоки|olmalar}?\n' +
        '— Зелёные яблоки стоят сто пятьдесят {рублей|rubl} за килограмм.\n' +
        '— Взвесьте мне, пожалуйста, {два|ikki} килограмма.\n' +
        '— Вот, пожалуйста. Возьмите также {пакет|paket} на кассе.\n' +
        '— Благодарю за {помощь|yordam}!'
    },
    {
      id: 'ru_l_04', num: '04', cat: 'life', catName: 'Повседневная', level: 'A2',
      name: '04. В аптеке — покупка лекарств',
      desc: 'Dorixonada tomoq og\'rig\'i va shamollashga dori olish',
      folder: 'Повседневная жизнь',
      content:
        '# 04. В аптеке — покупка лекарств\n\n' +
        '— Здравствуйте! У меня со вчерашнего дня сильно болит {горло|tomoq} и насморк.\n' +
        '— Добрый день. Есть ли у вас {температура|harorat}?\n' +
        '— Утром была тридцать семь и {два|ikki}.\n' +
        '— Понятно. Я рекомендую вам спрей для горла и растворимые {витамины|vitaminlar}.\n' +
        '— Как часто нужно {принимать|qabul qilish} этот спрей?\n' +
        '— Три раза в день после {еды|ovqatdan}. И пейте больше тёплой {воды|suv}.\n' +
        '— Спасибо, дайте ещё пачку {салфеток|salfetka}.'
    },
    {
      id: 'ru_l_05', num: '05', cat: 'life', catName: 'Повседневная', level: 'A2',
      name: '05. В ресторане — ужин и счёт',
      desc: 'Restoranda stol band qilish, issiq ovqat va hisob-kitob',
      folder: 'Повседневная жизнь',
      content:
        '# 05. В ресторане — ужин и счёт\n\n' +
        '— Добрый вечер! У вас есть свободный {столик|stol} на двоих у окна?\n' +
        '— Добрый вечер! Да, проходите, пожалуйста, вот {удобное|qulay} место.\n' +
        '— Что вы посоветуете из {горячих|issiq} блюд?\n' +
        '— Сегодня наш шеф-повар рекомендует {запечённую|pishirilgan} рыбу с овощами.\n' +
        '— Прекрасно, нам две {порции|porsiya} рыбы и бутылку минеральной воды.\n' +
        '— Желаете десерт или кофе после {ужина|kechki ovqat}?\n' +
        '— Пока нет, спасибо. Пожалуйста, принесите {счёт|hisob-kitob}.'
    },

    // 🚕 2. Город и транспорт
    {
      id: 'ru_l_06', num: '06', cat: 'city', catName: 'Город & транспорт', level: 'A1',
      name: '06. В такси — поездка по городу',
      desc: 'Taksida vokzalga borish, tirbandlik va to\'lov',
      folder: 'Город и транспорт',
      content:
        '# 06. В такси — поездка по городу\n\n' +
        '— Здравствуйте! Вы заказывали такси до {вокзала|vokzal}?\n' +
        '— Да, добрый день! Нам нужно успеть к {поезду|poyezd}, он отправляется через сорок минут.\n' +
        '— Не переживайте, сейчас нет {пробок|tirbandlik}, доедем за двадцать минут.\n' +
        '— Отлично, можно включить {кондиционер|konditsioner}, пожалуйста?\n' +
        '— Конечно. Вам удобно оплатить через {приложение|ilova}?\n' +
        '— Да, оплата уже привязана к {карте|karta}.\n' +
        '— Вот мы и приехали. Счастливого {пути|yo\'l}!'
    },
    {
      id: 'ru_l_07', num: '07', cat: 'city', catName: 'Город & транспорт', level: 'A2',
      name: '07. Как пройти? Ориентация в городе',
      desc: 'Shaharda yo\'l, metro bekati va burilishlarni so\'rash',
      folder: 'Город и транспорт',
      content:
        '# 07. Как пройти? Ориентация в городе\n\n' +
        '— Извините, вы не подскажете, как быстрее дойти до {музея|muzey}?\n' +
        '— Идите прямо по этой улице до светофора, затем поверните {направо|o\'ngga}.\n' +
        '— Это далеко отсюда? Сколько минут {пешком|piyoda}?\n' +
        '— Минут десять не быстрым шагом. Музей будет по {левой|chap} стороне.\n' +
        '— А там рядом есть станция {метро|metro}?\n' +
        '— Да, прямо напротив музея находится станция «{Центральная|Markaziy}».\n' +
        '— Огромное спасибо за подробное {объяснение|tushuntirish}!'
    },
    {
      id: 'ru_l_08', num: '08', cat: 'city', catName: 'Город & транспорт', level: 'A2',
      name: '08. В метро и общественном транспорте',
      desc: 'Metro chiptasi, yo\'l haqi va boshqa liniyaga o\'tish',
      folder: 'Город и транспорт',
      content:
        '# 08. В метро и общественном транспорте\n\n' +
        '— Скажите, пожалуйста, какой {билет|chipta} выгоднее купить на пять дней?\n' +
        '— Возьмите единую карту, она действует на все виды {транспорта|transport}.\n' +
        '— Сколько стоит одна {поездка|safir} по этой карте?\n' +
        '— Шестьдесят рублей. Вы можете пополнить её в {автомате|avtomatda}.\n' +
        '— Чтобы доехать до парка, мне нужно делать {пересадку|boshqa poyezdga o\'tish}?\n' +
        '— Да, на кольцевой линии перейдите на {синюю|ko\'k} ветку.'
    },
    {
      id: 'ru_l_09', num: '09', cat: 'city', catName: 'Город & транспорт', level: 'A2',
      name: '09. На вокзале — покупка билетов',
      desc: 'Kassada poyezd chiptasi, kupe va jo\'nash vaqti',
      folder: 'Город и транспорт',
      content:
        '# 09. На вокзале — покупка билетов\n\n' +
        '— Здравствуйте! Мне нужен один билет на поезд до {Самары|Samara} на пятницу.\n' +
        '— На утро или на {вечер|kechki payt}? Есть удобный поезд в восемнадцать тридцать.\n' +
        '— Лучше на вечер. Какое место: {нижнее|pastki} или верхнее?\n' +
        '— Осталось одно нижнее место в {купе|kupe}.\n' +
        '— Отлично, оформляйте. Нужен мой {паспорт|pasport}?\n' +
        '— Да, предъявите документ для {регистрации|ro\'yxat}.\n' +
        '— С какого пути будет {отправление|jo\'nash}?\n' +
        '— Путь объявят за полчаса до прибытия {состава|poyezd tarkibi}.'
    },
    {
      id: 'ru_l_10', num: '10', cat: 'city', catName: 'Город & транспорт', level: 'B1',
      name: '10. В аэропорту — регистрация и багаж',
      desc: 'Aeroportda chamadon tortish, joy tanlash va posadochniy talon',
      folder: 'Город и транспорт',
      content:
        '# 10. В аэропорту — регистрация и багаж\n\n' +
        '— Положите ваш {чемодан|chemodan} на весы, пожалуйста.\n' +
        '— Скажите, у меня нет {перевеса|ortiqcha vazn}?\n' +
        '— Вес двадцать один килограмм, норма до {двадцати трёх|yigirma uch} килограммов.\n' +
        '— Замечательно. А ручную кладь тоже нужно {взвешивать|tortish}?\n' +
        '— Только проверьте габариты в {рамке|o\'lchov ramkasi}. Какое место предпочитаете?\n' +
        '— Если можно, у {окна|oyna oldida}, пожалуйста.\n' +
        '— Вот ваш посадочный {талон|talon}. Выход на посадку номер двенадцать.'
    },

    // 🏨 3. Путешествия и отель
    {
      id: 'ru_l_11', num: '11', cat: 'travel', catName: 'Путешествия', level: 'A2',
      name: '11. В гостинице — заселение в номер',
      desc: 'Mehmonxonaga joylashish, kalit, Wi-Fi va nonushta',
      folder: 'Путешествия и отель',
      content:
        '# 11. В гостинице — заселение в номер\n\n' +
        '— Добрый день! У меня {бронь|bron} на имя Рахимов на три ночи.\n' +
        '— Здравствуйте! Минутку, проверяю по {базе|baza}... Да, стандартный номер с одной кроватью.\n' +
        '— В стоимость номера входит {завтрак|nonushta}?\n' +
        '— Да, завтрак «шведский стол» сервируется с семи до десяти {утра|ertalab}.\n' +
        '— Подскажите пароль от беспроводного {интернета|internet}?\n' +
        '— Пароль указан на карточке вашего {ключа|kalit}. Ваш номер триста пять на третьем этаже.'
    },
    {
      id: 'ru_l_12', num: '12', cat: 'travel', catName: 'Путешествия', level: 'A2',
      name: '12. В банке — обмен валюты',
      desc: 'Bankda dollar ayirboshlash kursi va komissiya',
      folder: 'Путешествия и отель',
      content:
        '# 12. В банке — обмен валюты\n\n' +
        '— Здравствуйте! Я хочу обменять пятьсот {долларов|dollar} на рубли.\n' +
        '— Какой сегодня установленный {курс|kurs}?\n' +
        '— Курс покупки девяносто один рубль пятьдесят {копеек|tiyin}.\n' +
        '— Взимается ли какая-нибудь дополнительная {комиссия|komissiya}?\n' +
        '— Нет, обмен производится без комиссии. Пожалуйста, ваш {паспорт|pasport}.\n' +
        '— Вот деньги и документ. Выдайте, пожалуйста, крупными {купюрами|kupyuralar}.'
    },
    {
      id: 'ru_l_13', num: '13', cat: 'travel', catName: 'Путешествия', level: 'B1',
      name: '13. Экскурсия по городу',
      desc: 'Shahar bo\'ylab gid bilan sayr va tarixiy joylar',
      folder: 'Путешествия и отель',
      content:
        '# 13. Экскурсия по городу\n\n' +
        '— Здравствуйте! Какие обзорные {экскурсии|ekskursiyalar} вы предлагаете сегодня?\n' +
        '— У нас есть двухчасовая прогулка по историческому {центру|markaz} с профессиональным гидом.\n' +
        '— Во сколько начинается {маршрут|marshrut}?\n' +
        '— Начало в четырнадцать ноль-ноль от памятника Пушкину.\n' +
        '— Экскурсия пешеходная или на {автобусе|avtobusda}?\n' +
        '— Первая часть на комфортабельном автобусе, а затем пешая {прогулка|sayr}.'
    },
    {
      id: 'ru_l_14', num: '14', cat: 'travel', catName: 'Путешествия', level: 'B1',
      name: '14. Аренда автомобиля',
      desc: 'Avtomobil ijarasi shartlari, avtomat korobka va sug\'urta',
      folder: 'Путешествия и отель',
      content:
        '# 14. Аренда автомобиля\n\n' +
        '— Добрый день! Я хотел бы арендовать компактный {автомобиль|mashina} на выходные.\n' +
        '— Какие требования к коробке передач: {автомат|avtomat} или механика?\n' +
        '— Обязательно автоматическая {коробка|uzatmalar qutisi}.\n' +
        '— У нас есть новый седан. Требуется стаж вождения от двух {лет|yil}.\n' +
        '— Мой стаж более пяти лет. Включена ли полная {страховка|sug\'urta}?\n' +
        '— Да, страховка покрывает все риски, кроме повреждения {колёс|g\'ildiraklar}.'
    },

    // 💼 4. Работа и дела
    {
      id: 'ru_l_15', num: '15', cat: 'work', catName: 'Работа & дела', level: 'A2',
      name: '15. Телефонный разговор — запись на приём',
      desc: 'Klinikaga qo\'ng\'iroq qilib shifokor qabuliga yozilish',
      folder: 'Работа и дела',
      content:
        '# 15. Телефонный разговор — запись на приём\n\n' +
        '— Алло, здравствуйте! Это приёмная доктора Смирнова?\n' +
        '— Добрый день! Да, вы позвонили в {клинику|klinika}. Чем могу помочь?\n' +
        '— Я хочу {записаться|yozilish} на консультацию на этой неделе.\n' +
        '— Есть свободное окно в четверг в шестнадцать {часов|soatda}. Вам подходит?\n' +
        '— Да, это идеальное {время|vaqt}. Что нужно взять с собой?\n' +
        '— Возьмите паспорт и результаты предыдущих {анализов|tahlillar}, если они есть.'
    },
    {
      id: 'ru_l_16', num: '16', cat: 'work', catName: 'Работа & дела', level: 'B1',
      name: '16. Собеседование — рассказ о себе',
      desc: 'Ishga kirish suhbati, tajriba va loyihalar haqida',
      folder: 'Работа и дела',
      content:
        '# 16. Собеседование — рассказ о себе\n\n' +
        '— Добрый день! Расскажите кратко о вашем профессиональном {опыте|tajriba}.\n' +
        '— Здравствуйте! Последние три года я работал {менеджером|menejer} проектов в IT-компании.\n' +
        '— С какими основными трудностями вы {сталкивались|duch kelgansiz}?\n' +
        '— Главное — это координация команды и соблюдение жёстких {сроков|muddatlar}.\n' +
        '— Почему вы решили сменить место {работы|ish}?\n' +
        '— Я ищу новые вызовы и хочу развиваться в масштабных международных {проектах|loyihalar}.'
    },
    {
      id: 'ru_l_17', num: '17', cat: 'work', catName: 'Работа & дела', level: 'B1',
      name: '17. Разговор с коллегами в офисе',
      desc: 'Hamkasblar bilan hisobot va taqdimotni muhokama qilish',
      folder: 'Работа и дела',
      content:
        '# 17. Разговор с коллегами в офисе\n\n' +
        '— Привет! Ты успел посмотреть мой {отчёт|hisobot} по продажам?\n' +
        '— Привет! Да, отличная работа, цифры выглядят очень {убедительно|ishonarli}.\n' +
        '— Как думаешь, когда мы презентуем его руководству?\n' +
        '— Совещание назначено на пятницу после {обеда|tushlikdan keyin}.\n' +
        '— Нужно подготовить несколько слайдов с наглядными {графиками|grafiklar}.\n' +
        '— Согласен, давай разделим презентацию на две {части|qism}.'
    },
    {
      id: 'ru_l_18', num: '18', cat: 'work', catName: 'Работа & дела', level: 'B1',
      name: '18. Аренда жилья — звонок хозяину',
      desc: 'Kvartira ijarasi bo\'yicha uy egasiga qo\'ng\'iroq qilish',
      folder: 'Работа и дела',
      content:
        '# 18. Аренда жилья — звонок хозяину\n\n' +
        '— Здравствуйте! Я звоню по объявлению об аренде однокомнатной {квартиры|xonadon}.\n' +
        '— Добрый день! Квартира ещё свободна, окна выходят в тихий {двор|hovli}.\n' +
        '— Включены ли коммунальные платежи в общую {стоимость|narx}?\n' +
        '— Отопление и вода по счётчикам оплачиваются {отдельно|alohida}.\n' +
        '— Когда можно приехать и посмотреть {жильё|uy}?\n' +
        '— Я буду на месте сегодня вечером после семи {часов|soat}. Приезжайте!'
    }
  ];

  /* Ingliz tili uchun dastlabki mavzular */
  var EN_TOPICS = [
    {
      id: 'en_l_01', num: '01', cat: 'life', catName: 'Daily life', level: 'A1',
      name: '01. Meeting and Greetings',
      desc: 'First conversation, asking names and country',
      folder: 'Daily Life',
      content:
        '# 01. Meeting and Greetings\n\n' +
        '— Hello! My name is {David|Devid}. What is your name?\n' +
        '— Nice to meet you! I am {Sarah|Sara}. I am from {London|Londondan}.\n' +
        '— Welcome! Have you been studying {English|ingliz tili} for a long time?\n' +
        '— No, only for {two|ikki} months. But I try to listen and speak {every|har} day.\n' +
        '— That is great! You have very clear {pronunciation|talaffuz}.\n' +
        '— Thank you very much! I really enjoy {learning|o\'rganish}.'
    },
    {
      id: 'en_l_02', num: '02', cat: 'life', catName: 'Daily life', level: 'A1',
      name: '02. At a Coffee Shop',
      desc: 'Ordering a cappuccino, pastry, and paying',
      folder: 'Daily Life',
      content:
        'youtube: https://www.youtube.com/watch?v=ba34r1rIhyc\n\n' +
        '# 02. At a Coffee Shop\n\n' +
        '[00:01 - 00:04] — Good morning! Are you ready to {order|buyurtma berish}?\n' +
        ':: Xayrli tong! Buyurtma berishga tayyormisiz?\n\n' +
        '[00:05 - 00:09] — Hi! Yes, could I have a {cappuccino|kapuchino} and a croissant, please?\n' +
        ':: Salom! Ha, menga bitta kapuchino va kruassan bera olasizmi, iltimos?\n\n' +
        '[00:10 - 00:14] — Sure! What size would you like: {small|kichik}, medium, or large?\n' +
        ':: Albatta! Qaysi o\'lchamda xohlaysiz: kichik, o\'rta yoki katta?\n\n' +
        '[00:15 - 00:18] — Medium, please. With oat {milk|sut} and no sugar.\n' +
        ':: O\'rtacha, iltimos. Suli suti bilan va shakarsiz.\n\n' +
        '[00:19 - 00:22] — Anything else for {you|siz uchun} today?\n' +
        ':: Bugun siz uchun yana biror narsa bormi?\n\n' +
        '[00:23 - 00:26] — That is all, thank you. How much is {it|bu}?\n' +
        ':: Shu xolos, rahmat. Qancha bo\'ldi?\n\n' +
        '[00:27 - 00:31] — That will be five {dollars|dollar}. Cash or card?\n' +
        ':: Besh dollar bo\'ladi. Naqdmi yoki karta?\n\n' +
        '[00:32 - 00:35] — By card, please.\n' +
        ':: Karta bilan, iltimos.\n\n' +
        '? Savol 1: What did the customer order?\n' +
        '+ A cappuccino and a croissant\n' +
        '- Black tea and a cake\n' +
        '- An orange juice and a sandwich\n\n' +
        '? Savol 2: What kind of milk did the customer choose?\n' +
        '+ Oat milk\n' +
        '- Regular cow milk\n' +
        '- Almond milk\n\n' +
        '? Savol 3: How much did the order cost?\n' +
        '+ 5 dollars\n' +
        '- 10 dollars\n' +
        '- 3 dollars'
    },
    {
      id: 'en_l_03', num: '03', cat: 'city', catName: 'City & Transport', level: 'A2',
      name: '03. Asking for Directions',
      desc: 'Finding the museum, walking time, and bus stop',
      folder: 'City and Travel',
      content:
        '# 03. Asking for Directions\n\n' +
        '— Excuse me, could you tell me how to get to the {museum|muzey}?\n' +
        '— Go straight down this street until the traffic lights, then turn {right|o\'ngga}.\n' +
        '— Is it far from here? How many minutes on {foot|piyoda}?\n' +
        '— About ten minutes walk. It will be on your {left|chap} hand side.\n' +
        '— Is there a bus {station|bekat} nearby?\n' +
        '— Yes, right across from the main entrance.\n' +
        '— Thank you so much for your {help|yordam}!'
    }
  ];

  /* Xotiradagi mavzularni ID bo'yicha tezkor topish */
  var ALL_BUILTIN = {};
  RU_TOPICS.concat(EN_TOPICS).forEach(function (t) { ALL_BUILTIN[t.id] = t; });

  // reading-doc.js ga zaxira manba sifatida ulaymiz
  window.ListeningBuiltin = {
    get: function (id) { return ALL_BUILTIN[id] || null; },
    list: function (sec) { return sec === 'en_listening' ? EN_TOPICS : RU_TOPICS; }
  };

  /* =========================================================
     VIEW: listening_hub — Telegram uslubidagi toza katalog
     ========================================================= */
  App.view('listening_hub', {
    nav: 'languages',
    render: function (page, params) {
      var sec = params.sec || 'ru_listening';
      var isRu = sec === 'ru_listening';
      var backView = isRu ? 'russian' : 'english';
      var title = isRu ? 'Аудирование' : 'Listening';
      var activeTab = params.tab || 'all';

      page.innerHTML =
        '<div class="topbar" style="margin:-16px -15px 12px">' +
        '<button class="icon-btn ghost" data-act="go" data-arg=\'' + App.arg({ v: backView }) + '\'>' +
        '<span data-icon="arrowLeft" data-icon-size="20"></span></button>' +
        '<h1>' + App.esc(title) + '</h1>' +
        (window.Auth && Auth.isReadOnly && Auth.isReadOnly() ? '' :
          '<button class="icon-btn ghost" data-act="libNew" data-arg=\'' + App.arg({ sec: sec, path: '' }) + '\' style="margin-left:auto" aria-label="Yangi dars qo\'shish" title="Mavzu qo\'shish">' +
          '<span data-icon="plus" data-icon-size="20"></span></button>') +
        '</div>' +

        /* Tezkor maishiy trenajyor blits kartasi (Raqamlar, narxlar, telefon, soat) */
        '<div class="lh-hero" data-act="go" data-arg=\'' + App.arg({ v: 'listening_practice', p: { lang: isRu ? 'russian' : 'english' } }) + '\'>' +
        '<div class="lh-hero-ic"><span data-icon="headphones" data-icon-size="22"></span></div>' +
        '<div class="lh-hero-main">' +
          '<div class="lh-hero-title">' +
            (isRu ? 'Быстрый тренажёр' : 'Quick Listening Drill') +
            '<span class="lh-hero-badge">Blitz</span>' +
          '</div>' +
          '<div class="lh-hero-sub">' +
            (isRu ? 'Числа, цены, время, даты и номера телефонов на слух' : 'Numbers, prices, time, dates and phone numbers') +
          '</div>' +
        '</div>' +
        '<div class="lh-hero-arr"><span data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span></div>' +
        '</div>' +

        /* Kategoriya filtrlari (Pills) */
        '<div class="lh-pills" id="lh-pills">' +
          pillBtn(isRu ? 'Все темы' : 'All topics', 'all', activeTab, sec) +
          pillBtn(isRu ? '☕ Повседневная' : '☕ Daily Life', 'life', activeTab, sec) +
          pillBtn(isRu ? '🚕 Город & транспорт' : '🚕 City & Travel', 'city', activeTab, sec) +
          pillBtn(isRu ? '🏨 Путешествия' : '🏨 Hotel & Travel', 'travel', activeTab, sec) +
          pillBtn(isRu ? '💼 Работа & дела' : '💼 Work & Calls', 'work', activeTab, sec) +
        '</div>' +

        '<div id="lh-list"><div class="load-wrap"><div class="spinner"></div></div></div>';

      App.icons(page);
      loadTopics(page, sec, activeTab);
    }
  });

  function pillBtn(label, tabKey, current, sec) {
    var active = current === tabKey;
    return '<button class="lh-pill' + (active ? ' active' : '') + '" data-act="go" data-arg=\'' +
      App.arg({ v: 'listening_hub', p: { sec: sec, tab: tabKey } }) + '\'>' +
      App.esc(label) + '</button>';
  }

  function tickHtml() {
    return '<span class="rm-tick"><svg viewBox="0 0 24 24" width="11" height="11" fill="none">' +
      '<path d="M5 12l5 5L20 6" stroke="currentColor" stroke-width="3.4" ' +
      'stroke-linecap="round" stroke-linejoin="round"/></svg></span>';
  }

  function splitNum(name, fallback) {
    var s = String(name || '').trim();
    var m = s.match(/^(\d{1,3})\s*[.)\-]?\s*(.+)$/);
    if (m && m[2].trim()) {
      var n = parseInt(m[1], 10);
      return { num: (n < 10 ? '0' : '') + n, title: m[2].trim() };
    }
    return { num: String(fallback), title: s };
  }

  function levelBadgeHtml(lvl) {
    lvl = (lvl || 'A1').toUpperCase();
    var cls = lvl === 'B1' ? 'b1' : (lvl === 'A2' ? 'a2' : 'a1');
    return '<span class="lh-level ' + cls + '">' + App.esc(lvl) + '</span>';
  }

  function loadTopics(page, sec, activeTab) {
    var isRu = sec === 'ru_listening';
    var builtinList = isRu ? RU_TOPICS : EN_TOPICS;

    // Serverdan foydalanuvchi qo'shgan mavzularni ham so'raymiz
    App.call('get_topics', null, { query: 'lang=' + encodeURIComponent(sec) }).then(function (j) {
      var serverTopics = (j && j.topics) ? j.topics : [];
      renderMergedList(page, sec, activeTab, builtinList, serverTopics);
    }).catch(function () {
      renderMergedList(page, sec, activeTab, builtinList, []);
    });
  }

  function renderMergedList(page, sec, activeTab, builtinList, serverTopics) {
    var box = page.querySelector('#lh-list');
    if (!box) return;

    // Server mavzulari bilan built-in mavzularni birlashtirish
    var items = [];
    var seenNames = {};

    // 1. Agar serverda mavzular bo'lsa
    serverTopics.forEach(function (st) {
      if (!st.name || st.name === '__folder__') return;
      seenNames[st.name.toLowerCase()] = st.id;
    });

    // 2. Builtin ro'yxatni saralash
    builtinList.forEach(function (bt, i) {
      var serverId = seenNames[bt.name.toLowerCase()];
      items.push({
        id: serverId || bt.id,
        num: bt.num,
        name: bt.name,
        desc: bt.desc,
        cat: bt.cat,
        level: bt.level,
        hasContent: true,
        isCustom: false
      });
    });

    // 3. Foydalanuvchi serverga yangi qo'shgan mavzulari (built-inda yo'qlari)
    serverTopics.forEach(function (st, idx) {
      if (!st.name || st.name === '__folder__') return;
      var key = st.name.toLowerCase();
      var exists = builtinList.some(function (b) { return b.name.toLowerCase() === key; });
      if (!exists) {
        var sp = splitNum(st.name, items.length + 1);
        items.push({
          id: st.id,
          num: sp.num,
          name: st.name,
          desc: st.folder ? ('Papka: ' + st.folder) : 'Qo\'shilgan darslik',
          cat: 'life',
          level: 'A2',
          hasContent: st.has_content,
          isCustom: true
        });
      }
    });

    // Filtrlash
    var filtered = items.filter(function (it) {
      if (activeTab === 'all') return true;
      return it.cat === activeTab;
    });

    if (!filtered.length) {
      box.innerHTML = App.empty({
        icon: 'headphones', title: 'Bu bo\'limda darslar yo\'q',
        text: 'Boshqa toifani tanlang yoki yuqoridagi + tugmasi orqali yangi dars qo\'shing.'
      });
      App.icons(box);
      return;
    }

    var isReadOnly = window.Auth && Auth.isReadOnly && Auth.isReadOnly();

    var html = '<div class="chat-list">';
    html += filtered.map(function (it, idx) {
      var sp = splitNum(it.name, idx + 1);
      var done = (window.LearnMarks && LearnMarks.isTopicRead && LearnMarks.isTopicRead(it.id)) ||
                 (window.ReadMark && ReadMark.isRead && ReadMark.isRead(sec, 'topic', it.id));

      var editBtn = isReadOnly || !it.isCustom ? '' :
        '<button class="icon-btn ghost" style="width:34px;height:34px;flex-shrink:0" data-act="libFileMenu" data-arg=\'' +
        App.arg({ sec: sec, path: '', id: it.id, n: it.name }) + '\'><span data-icon="edit" data-icon-size="15"></span></button>';

      return '<div class="chat-item' + (done ? ' rm-done' : '') + '">' +
        '<button class="chat-row" data-act="go" data-arg=\'' +
        App.arg({ v: 'listening_doc', p: { sec: sec, id: it.id } }) + '\'>' +
        '<span class="rm-av-wrap">' +
          '<span class="chat-av chat-av-num">' + App.esc(it.num || sp.num) + '</span>' +
          (done ? tickHtml() : '') +
        '</span>' +
        '<span class="chat-main">' +
          '<span class="chat-title" style="display:flex;align-items:center;justify-content:space-between">' +
            '<span>' + App.esc(sp.title) + '</span>' +
            levelBadgeHtml(it.level) +
          '</span>' +
          '<span class="chat-sub">' + App.esc(it.desc || (done ? 'Tinglandi' : 'Eshitib tushunish mashqi')) + '</span>' +
        '</span>' +
        '<span class="chat-arrow" data-icon="arrowLeft" data-icon-size="16" style="transform:rotate(180deg)"></span>' +
        '</button>' +
        editBtn +
        '</div>';
    }).join('');
    html += '</div>';

    box.innerHTML = html;
    App.icons(box);
  }

})();
