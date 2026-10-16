# -*- coding: utf-8 -*-
"""
Русские падежи. Сборник упражнений (Н.Т. Мелех, И.И. Баранова) kitobidagi
barcha mavzular va mashqlar asosida tuzilgan mukammal interaktiv o'qish (Reading) kutubxonasi.

Har bir matn yordamchi sayt reading.js standartiga 100% mos:
- Sarlavha: # Nomi
- Har bir gapda {so'z|tarjima} shaklidagi bosiladigan interaktiv so'zlar
- Gap ostida :: Butun gapning o'zbekcha tarjimasi
- Xatboshilar orasida 2 ta bo'sh qator
"""

import os
import json

TEXTS = [
    # =========================================================================
    # 01. ПРЕДЛОЖНЫЙ ПАДЕЖ (ГДЕ? О КОМ? О ЧЁМ?)
    # =========================================================================
    {
        "folder": "Русские падежи/01. Предложный падеж (Где? О ком?)",
        "name": "1. Рассказ Анвара (Факультет и Петербург)",
        "content": """# Рассказ Анвара

{Меня|Meni} {зовут|chaqirishadi} {Анвар|Anvar}.
:: Meni Anvar deb atashadi.

{Вот|Mana} {наш|bizning} {подготовительный|tayyorlov} {факультет|fakultet}.
:: Mana bizning tayyorlov fakultetimiz.

{Здесь|Bu yerda} {учусь|o'qiyman} {я|men} и {мои|mening} {друзья|do'stlarim}.
:: Bu yerda men va mening do'stlarim o'qiymiz.

{Наша|Bizning} {факультетская|fakultetga oid} {библиотека|kutubxona} {находится|joylashgan} на {пятом|beshinchi} {этаже|qavatda}.
:: Bizning fakultet kutubxonamiz beshinchi qavatda joylashgan.


{Здесь|Bu yerda} {я|men} {часто|tez-tez} {беру|olaman} {книги|kitoblarni}, {занимаюсь|shug'ullanaman}.
:: Bu yerda men tez-tez kitoblar olaman, shug'ullanaman.

На {первом|birinchi} {этаже|qavatda} {находится|joylashgan} {большой|katta} {спортивный|sport} {зал|zali}.
:: Birinchi qavatda katta sport zali joylashgan.

{Здесь|Bu yerda} {мы|biz} {играем|o'ynaymiz} в {баскетбол|basketbol}, {волейбол|voleybol}.
:: Bu yerda biz basketbol va voleybol o'ynaymiz.

В {нашем|bizning} {здании|binoda} {находятся|joylashgan} {гостиница|mehmonxona} и {общежитие|yotoqxona}.
:: Bizning binomizda mehmonxona va yotoqxona joylashgan.

{Здесь|Bu yerda} {живут|yashashadi} {иностранные|chet ellik} {студенты|talabalar}.
:: Bu yerda chet ellik talabalar yashashadi.


{Это|Bu} {большой|katta} {старый|eski} {университетский|universitet} {парк|bogi}.
:: Bu katta qadimiy universitet bog'i.

{Здесь|Bu yerda} {я|men} {иногда|ba'zan} {гуляю|sayr qilaman} с {другом|do'stim bilan}.
:: Bu yerda men ba'zan do'stim bilan sayr qilaman.

{Мой|Mening} {друг|do'stim} {Джафар|Jafar} — {студент|talabasi} {Политехнического|Politexnika} {университета|universitetining}.
:: Mening do'stim Jafar — Politexnika universiteti talabasi.


А {вот|mana} {площадь|maydoni} {Мужества|Jasorat}.
:: Ana esa Jasorat maydoni.

{Здесь|Bu yerda} {находится|joylashgan} {станция|bekati} {метро|metro}.
:: Bu yerda metro bekati joylashgan.

{Я|Men} {часто|tez-tez} {бываю|bo'lib turaman} {здесь|bu yerda}.
:: Men bu yerda tez-tez bo'lib turaman.

А {недавно|yaqinda} {мы|biz} {ходили|bordik} в {музыкальный|musiqali} {театр|teatrga} на {концерт|konsertga}.
:: Yaqinda esa biz musiqali teatrga konsertga bordik.

{Мне|Menga} и {моим|mening} {друзьям|do'stlarimga} {нравится|yoqadi} {жить|yashash} и {учиться|o'qish} в {Петербурге|Peterburgda}.
:: Menga va do'stlarimga Peterburgda yashash va o'qish yoqadi.
"""
    },
    {
        "folder": "Русские падежи/01. Предложный падеж (Где? О ком?)",
        "name": "2. Моя подруга (Жизнь в общежитии)",
        "content": """# Моя подруга

{Моя|Mening} {подруга|dugonam} {Марта|Marta} {живёт|yashaydi} в {студенческом|talabalar} {общежитии|yotoqxonasida}.
:: Mening dugonam Marta talabalar yotoqxonasida yashaydi.

{Она|U} {приехала|kelgan} из {Германии|Germaniyadan} и {сейчас|hozir} {учится|o'qiyapti} в {России|Rossiyada}.
:: U Germaniyadan kelgan va hozir Rossiyada o'qiyapti.

{Её|Uning} {комната|xonasi} {находится|joylashgan} на {четвёртом|to'rtinchi} {этаже|qavatda}.
:: Uning xonasi to'rtinchi qavatda joylashgan.


{Это|Bu} {небольшая|unacha katta bo'lmagan}, но {очень|juda} {светлая|yorug'} и {уютная|shinam} {комната|xona}.
:: Bu uncha katta bo'lmagan, lekin juda yorug' va shinam xona.

В {комнате|xonada} {налево|chapda} {стоит|turibdi} {письменный|yozuv} {стол|stoli}, а {направо|o'ngda} — {удобная|qulay} {кровать|karavot}.
:: Xonada chap tomonda yozuv stoli, o'ng tomonda esa qulay karavot turibdi.

На {столе|stolda} {лежат|yotibdi} {русские|ruscha} {учебники|darsliklar}, {тетради|daftarlar} и {новый|yangi} {ноутбук|noutbuk}.
:: Stol ustida ruscha darsliklar, daftarlar va yangi noutbuk yotibdi.

На {стене|devorda} {висит|osilib turibdi} {большая|katta} {карта|xarita} {Санкт-Петербурга|Sankt-Peterburgning}.
:: Devorda Sankt-Peterburgning katta xaritasi osilib turibdi.


{Марта|Marta} {много|ko'p} {занимается|shug'ullanadi} в {университетской|universitet} {библиотеке|kutubxonasida}.
:: Marta universitet kutubxonasida ko'p shug'ullanadi.

{Вечером|Kechqurun} {мы|biz} {часто|tez-tez} {встречаемся|uchrashamiz} на {кухне|oshxonada} и {разговариваем|gaplashamiz} о {наших|bizning} {странах|mamlakatlarimiz haqida}.
:: Kechqurun biz tez-tez oshxonada uchrashamiz va mamlakatlarimiz haqida gaplashamiz.

{Она|U} {рассказывает|aytib beradi} о {своей|o'z} {семье|oilasi haqida}, а {я|men} — о {солнечном|quyoshli} {Ташкенте|Toshkent haqida}.
:: U o'z oilasi haqida aytib beradi, men esa quyoshli Toshkent haqida so'zlayman.
"""
    },
    {
        "folder": "Русские падежи/01. Предложный падеж (Где? О ком?)",
        "name": "3. Виктор — мой друг (Знакомство в музее)",
        "content": """# Виктор — мой друг

{Виктор|Viktor} — {мой|mening} {хороший|yaxshi} {русский|rus} {друг|do'stim}.
:: Viktor — mening yaxshi rus do'stim.

{Я|Men} {познакомился|tanishganman} с {ним|u bilan} в {прошлом|o'tgan} {году|yilda} в {Русском|Rus} {музее|muzeyida}.
:: Men u bilan o'tgan yili Rus muzeyida tanishganman.

{Мы|Biz} {стояли|turgan edik} в {зале|zalda} и {разговаривали|gaplashayotgan edik} о {картинах|suratlar haqida} {русских|rus} {художников|rassomlarining}.
:: Biz zalda turgan edik va rus rassomlarining suratlari haqida gaplashayotgan edik.


{Виктор|Viktor} {живёт|yashaydi} в {Петербурге|Peterburgda} {недавно|yaqindan beri}.
:: Viktor Peterburgda yaqindan beri yashaydi.

{Раньше|Ilgari} {он|u} {жил|yashagan} и {учился|o'qigan} в {древнем|qadimiy} {городе|shaharda} {Новгороде|Novgorodda}.
:: Ilgari u qadimiy Novgorod shahrida yashagan va o'qigan.

{Сейчас|Hozir} {он|u} {учится|o'qiyapti} на {историческом|tarix} {факультете|fakultetida}.
:: Hozir u tarix fakultetida o'qiyapti.

{Его|Uning} {родители|ota-onasi} {живут|yashashadi} в {деревне|qishloqda}, на {севере|shimolda} {России|Rossiyaning}.
:: Uning ota-onasi Rossiya shimolidagi qishloqda yashashadi.


{Виктор|Viktor} {прекрасно|a'lo darajada} {знает|biladi} {всё|hamma narsani} о {Санкт-Петербурге|Sankt-Peterburg to'g'risida}.
:: Viktor Sankt-Peterburg to'g'risida hamma narsani a'lo darajada biladi.

На {выходных|dam olish kunlarida} {мы|biz} {гуляем|sayr qilamiz} в {центре|markazda}, на {Невском|Nevskiy} {проспекте|shohko'chasida}.
:: Dam olish kunlarida biz markazda, Nevskiy shohko'chasida sayr qilamiz.

{Он|U} {часто|tez-tez} {рассказывает|so'zlab beradi} мне об {истории|tarixi haqida} {каждого|har bir} {старого|qadimiy} {здания|binoning}.
:: U menga har bir qadimiy binoning tarixi haqida tez-tez so'zlab beradi.
"""
    },
    {
        "folder": "Русские падежи/01. Предложный падеж (Где? О ком?)",
        "name": "4. Наш первый вечер (Концерт и студенты)",
        "content": """# Наш первый вечер

{Недавно|Yaqinda} в {нашем|bizning} {университете|universitetimizda} {был|bo'ldi} {первый|birinchi} {студенческий|talabalar} {вечер|kechasi}.
:: Yaqinda bizning universitetimizda birinchi talabalar kechasi bo'lib o'tdi.

{Этот|Ushbu} {праздник|bayram} {проходил|bo'lib o'tdi} в {большом|katta} {актовом|majlislar} {зале|zalida}.
:: Ushbu bayram katta majlislar zalida bo'lib o'tdi.

В {зале|zalda} {собрались|yig'ilishdi} {студенты|talabalar} из {разных|turli} {стран|mamlakatlardan}.
:: Zalda turli mamlakatlardan kelgan talabalar yig'ilishdi.


Сначала {декан|dekan} {выступил|so'zga chiqdi} на {сцене|sahnada} и {рассказал|gapirib berdi} об {учёбе|o'qish haqida}.
:: Avvaliga dekan sahnada so'zga chiqdi va o'qish haqida gapirib berdi.

{Он|U} {пожелал|tiladi} {успехов|muvaffaqiyatlar} в {изучении|o'rganishda} {русского|rus} {языка|tilini}.
:: U rus tilini o'rganishda muvaffaqiyatlar tiladi.

Потом {на|saqlanadigan} {концерте|konsertda} {студенты|talabalar} {пели|kuylashdi} {песни|qo'shiqlarni} на {разных|turli} {языках|tillarda}.
:: Keyin konsertda talabalar turli tillarda qo'shiqlar kuylashdi.


В {конце|oxirida} {вечера|kechaning} нам {показали|ko'rsatishdi} {фильм|film} о {прекрасном|go'zal} {Петербурге|Peterburg haqida}.
:: Kechaning oxirida bizga go'zal Peterburg haqidagi filmni ko'rsatishdi.

{Все|Barcha} {долго|uzoq} {аплодировали|qarsak chalishdi} и {говорили|gaplashishdi} о {будущих|kelgusi} {планах|rejalar to'g'risida}.
:: Hamma uzoq vaqt qarsak chaldi va kelgusi rejalar to'g'risida suhbatlashdi.

{Этот|Ushbu} {вечер|kecha} {навсегда|butunlay} {останется|qoladi} в {моей|mening} {памяти|xotiramda}.
:: Ushbu kecha butun umr mening xotiramda qoladi.
"""
    },
    {
        "folder": "Русские падежи/01. Предложный падеж (Где? О ком?)",
        "name": "5. Учёба в Петербурге и поездка в Москву",
        "content": """# Учёба в Петербурге и поездка в Москву

{Я|Men} {учусь|o'qiyman} в {Санкт-Петербурге|Sankt-Peterburgda} уже {шесть|olti} {месяцев|oydirki}.
:: Men Sankt-Peterburgda olti oydan beri o'qiyman.

На {подготовительном|tayyorlov} {факультете|fakultetida} {мы|biz} {изучаем|o'rganamiz} {не только|nafaqat} {русский|rus} {язык|tilini}, но и {физику|fizika}, {математику|matematika} и {информатику|informatikani}.
:: Tayyorlov fakultetida biz nafaqat rus tilini, balki fizika, matematika va informatikani ham o'rganamiz.

{Занятия|Darslar} {проходят|o'tadi} в {светлых|yorug'} {лабораториях|laboratoriyalarda} и {аудиториях|auditoriyalarda}.
:: Darslar yorug' laboratoriyalar va auditoriyalarda o'tadi.


В {прошлом|o'tgan} {месяце|oyda} {я|men} {был|bo'ldim} на {экскурсии|ekskursiyada} в {Москве|Moskvada}.
:: O'tgan oyda men Moskvada ekskursiyada bo'ldim.

{Мы|Biz} {гуляли|sayr qildik} на {Красной|Qizil} {площади|maydonda} и {были|bo'ldik} в {Кремле|Kreml ichida}.
:: Biz Qizil maydonda sayr qildik va Kreml ichida bo'ldik.

В {Москве|Moskvada} {я|men} {встретился|uchrashdim} с {другом|do'stim bilan}, который {учится|o'qiydi} в {Московском|Moskva} {университете|universitetida}.
:: Moskvada men Moskva universitetida o'qiydigan do'stim bilan uchrashdim.


{Мы|Biz} {сидели|o'tirdik} в {уютном|shinam} {кафе|kafeda} и {вспоминали|esladik} о {нашей|bizning} {школе|maktabimiz haqida}.
:: Biz shinam kafeda o'tirdik va maktabimiz haqida xotirladik.

{Мне|Menga} {очень|juda} {понравилось|yoqdi} в {столице|poytaxtda}, но я {рад|xursandman} {вернуться|qaytganimdan} в {родной|qadrdon} {Петербург|Peterburgga}.
:: Poytaxt menga juda yoqdi, ammo qadrdon Peterburgga qaytganimdan xursandman.
"""
    },

    # =========================================================================
    # 02. ВИНИТЕЛЬНЫЙ ПАДЕЖ (КУДА? КОГО? ЧТО?)
    # =========================================================================
    {
        "folder": "Русские падежи/02. Винительный падеж (Куда? Кого? Что?)",
        "name": "1. Экскурсия по Санкт-Петербургу",
        "content": """# Экскурсия по Санкт-Петербургу

В {воскресенье|yakshanba kuni} {наша|bizning} {группа|guruhimiz} {поехала|jo'nadi} на {большую|katta} {экскурсию|ekskursiyaga}.
:: Yakshanba kuni bizning guruhimiz katta ekskursiyaga jo'nadi.

{Мы|Biz} {сели|o'tirdik} в {комфортабельный|qulay} {автобус|avtobusga} и {поехали|yo'l oldik} в {центр|markazga} {города|shaharning}.
:: Biz qulay avtobusga o'tirdik va shahar markaziga yo'l oldik.

{Сначала|Avvaliga} {мы|biz} {посетили|ziyorat qildik} {знаменитый|mashhur} {Эрмитаж|Ermitajni}.
:: Avvaliga biz mashhur Ermitajni ziyorat qildik.


В {музее|muzeyda} {мы|biz} {увидели|ko'rdik} {редкие|noyob} {картины|rasmlarni} и {золотые|oltin} {часы|soatlarni}.
:: Muzeyda biz noyob rasmlarni va oltin soatlarni ko'rdik.

Потом {экскурсовод|gid} {повела|boshlab bordi} {нас|bizni} на {Дворцовую|Saroy} {площадь|maydoniga}.
:: So'ngra ekskursovod bizni Saroy maydoniga boshlab bordi.

{Студенты|Talabalar} {фотографировали|suratga olishdi} {красивые|chiroyli} {дворцы|saroylarni} и {реку|daryoni} {Неву|Nevani}.
:: Talabalar go'zal saroylarni va Neva daryosini suratga olishdi.


{После|Keyin} {обеда|tushlikdan} {мы|biz} {пошли|bordik} в {Мариинский|Mariinskiy} {театр|teatriga} и {купили|sotib oldik} {билеты|chiptalarni} на {балет|baletga}.
:: Tushlikdan keyin biz Mariinskiy teatriga bordik va baletga chiptalar sotib oldik.

{Я|Men} {очень|juda} {люблю|sevaman} {русскую|rus} {культуру|madaniyatini} и {этот|ushbu} {чудесный|ajoyib} {город|shaharni}.
:: Men rus madaniyatini va ushbu ajoyib shaharni juda yaxshi ko'raman.
"""
    },
    {
        "folder": "Русские падежи/02. Винительный падеж (Куда? Кого? Что?)",
        "name": "2. В книжном магазине и библиотеке",
        "content": """# В книжном магазине и библиотеке

{Вчера|Kecha} {после|keyin} {занятий|darslardan} {я|men} {пошёл|bordim} в {книжный|kitob} {магазин|do'koniga}.
:: Kecha darslardan keyin men kitob do'koniga bordim.

{Мне|Menga} {нужно|kerak} {было|edi} {купить|sotib olish} {русско-узбекский|ruscha-o'zbekcha} {словарь|lug'atni} и {новую|yangi} {тетрадь|daftar}.
:: Menga ruscha-o'zbekcha lug'at va yangi daftar sotib olish kerak edi.

В {магазине|do'konda} {я|men} {встретил|uchratdim} {нашего|bizning} {преподавателя|o'qituvchimizni}.
:: Do'konda men bizning o'qituvchimizni uchratdim.


{Преподаватель|O'qituvchi} {посоветовал|maslahat berdi} мне {интересную|qiziqarli} {книгу|kitobni} для {чтения|o'qish uchun}.
:: O'qituvchi menga o'qish uchun qiziqarli kitobni maslahat berdi.

{Я|Men} {взял|oldim} {эту|ushbu} {книгу|kitobni}, {оплатил|to'ladim} {покупку|xaridni} и {положил|soldim} {всё|hammasini} в {рюкзак|ryukzakka}.
:: Men ushbu kitobni oldim, xaridni to'ladim va hammasini ryukzakka soldim.


Потом {мы|biz} {вместе|birgalikda} {пошли|bordik} в {городскую|shahar} {библиотеку|kutubxonasiga}.
:: So'ng biz birgalikda shahar kutubxonasiga bordik.

Там {я|men} {сдал|topshirdim} {старый|eski} {журнал|jurnalni} и {взял|oldim} {научную|ilmiy} {статью|maqolani}.
:: U yerda men eski jurnalni topshirdim va ilmiy maqolani oldim.

{Каждый|Har} {день|kuni} {я|men} {узнаю|bilib olaman} {много|ko'plab} {новых|yangi} {русских|ruscha} {слов|so'zlarni}.
:: Men har kuni ko'plab yangi ruscha so'zlarni bilib olaman.
"""
    },
    {
        "folder": "Русские падежи/02. Винительный падеж (Куда? Кого? Что?)",
        "name": "3. Мой день и распорядок студента",
        "content": """# Мой день и распорядок студента

В {будние|ish} {дни|kunlari} {я|men} {встаю|turaman} в {семь|yetti} {часов|soatda} {утра|ertalab}.
:: Ish kunlari men ertalab soat yettida turaman.

{Сначала|Avvaliga} {я|men} {делаю|qilaman} {утреннюю|ertalabki} {зарядку|mashqni} и {принимаю|qabul qilaman} {душ|dushni}.
:: Avvaliga men ertalabki badantarbiyani qilaman va dush qabul qilaman.

Потом {я|men} {варю|pishiraman} {крепкий|achchiq} {кофе|qahvani} и {ем|yeyman} {вкусный|mazali} {бутерброд|buterbrodni}.
:: Keyin men achchiq qahva pishiraman va mazali buterbrod yeyman.


В {восемь|sakkiz} {часов|soatda} {я|men} {иду|boraman} на {автобусную|avtobus} {остановку|bekatiga}.
:: Soat sakkizda men avtobus bekatiga boraman.

{Я|Men} {жду|kutaman} {двадцать|yigirma} {четвёртый|to'rtinchi} {автобус|avtobusni} и {еду|boraman} в {университет|universitetga}.
:: Men 24-avtobusni kutaman va universitetga boraman.

В {понедельник|dushanba kuni} и в {среду|chorshanba kuni} {мы|biz} {пишем|yozamiz} {трудные|qiyin} {тесты|testlarni} и {упражнения|mashqlarni}.
:: Dushanba va chorshanba kunlari biz qiyin testlar va mashqlarni yozamiz.


{Вечером|Kechqurun} {я|men} {учу|yodlayman} {новые|yangi} {слова|so'zlarni} и {слушаю|tinglayman} {русское|rus} {радио|radiosini}.
:: Kechqurun men yangi so'zlarni yodlayman va rus radiosini tinglayman.

В {пятницу|juma kuni} {вечером|oqshomda} {мы|biz} {приглашаем|taklif qilamiz} {друзей|do'stlarni} в {гости|mehmonga}.
:: Juma kuni oqshomda biz do'stlarimizni mehmonga taklif qilamiz.
"""
    },
    {
        "folder": "Русские падежи/02. Винительный падеж (Куда? Кого? Что?)",
        "name": "4. Встреча на Московском вокзале",
        "content": """# Встреча на Московском вокзале

{Сегодня|Bugun} {утром|ertalab} {я|men} {поехал|bordim} на {Московский|Moskva} {вокзал|vokzaliga}.
:: Bugun ertalab men Moskva vokzaliga bordim.

{Мне|Menga} {нужно|kerak} {было|edi} {встретить|kutib olish} {моего|mening} {старшего|katta} {брата|akamni}.
:: Menga o'zimning katta akamni kutib olish kerak edi.

{Брат|Akam} {купил|sotib olgan edi} {билет|chiptani} на {скоростной|tezyurar} {поезд|poyezdga} «{Сапсан|Sapsan}».
:: Akam «Sapsan» tezyurar poyezdiga chipta sotib olgan edi.


В {десять|o'n} {часов|soatda} {поезд|poyezd} {прибыл|yetib keldi} на {первую|birinchi} {платформу|platformaga}.
:: Soat o'nda poyezd birinchi platformaga yetib keldi.

{Я|Men} {сразу|darhol} {увидел|ko'rdim} {своего|o'z} {брата|akamni} в {толпе|olomon orasida}.
:: Men olomon orasida darhol o'z akamni ko'rib qoldim.

{Мы|Biz} {крепко|mahkam} {обняли|quchoqladik} {друг|bir-birimizni} {друга|bir-birimizni}.
:: Biz bir-birimizni mahkam quchoqladik.


{Я|Men} {взял|oldim} {его|uning} {тяжёлый|og'ir} {чемодан|chamadonini}, и {мы|biz} {пошли|tushdik} в {метро|metroga}.
:: Men uning og'ir chamadonini oldim va biz metroga tushdik.

{Брат|Akam} {привёз|keltirdi} {вкусные|mazali} {самаркандские|samarqandcha} {лепёшки|nonlarni} и {сладкую|shirin} {халву|holvani}.
:: Akam mazali Samarqand nonlarini va shirin holvani keltiribdi.
"""
    },
    {
        "folder": "Русские падежи/02. Винительный падеж (Куда? Кого? Что?)",
        "name": "5. Поездка в театр на балет",
        "content": """# Поездка в театр на балет

В {прошлую|o'tgan} {субботу|shanba kuni} {мы|biz} {пошли|bordik} в {знаменитый|mashhur} {театр|teatrga}.
:: O'tgan shanba kuni biz mashhur teatrga bordik.

{Все|Hamma} {студенты|talabalar} {надели|kiyishdi} {праздничные|bayramona} {костюмы|kostyumlarni} и {платья|ko'ylaklarni}.
:: Barcha talabalar bayramona kostyumlar va ko'ylaklarni kiyishdi.

{Мы|Biz} {хотели|xohlagan edik} {посмотреть|tomosha qilishni} {легендарный|afsonaviy} {балет|baletni} «{Лебединое|Oqqush} {озеро|ko'li}».
:: Biz afsonaviy «Oqqush ko'li» baletini tomosha qilishni xohlagan edik.


В {фойе|foyeda} {мы|biz} {встретили|uchratdik} {знакомую|tanish} {преподавательницу|o'qituvchi ayolni}.
:: Foyeda biz tanish o'qituvchi ayolimizni uchratdik.

{Она|U} {купила|sotib olgan edi} {театральную|teatr} {программу|dasturini} и {показала|ko'rsatdi} нам {красивые|chiroyli} {фотографии|suratlarni}.
:: U teatr dasturini sotib olgan ekan va bizga chiroyli suratlarni ko'rsatdi.


{Когда|Qachonki} {оркестр|orkestr} {начал|boshlaganda} {играть|ijro etishni} {волшебную|sehrli} {музыку|musiqani}, {все|hamma} {затаили|ushladi} {дыхание|nafasini}.
:: Orkestr sehrli musiqani chala boshlaganda, hamma nafasini ichiga yutib qoldi.

{Этот|Ushbu} {вечер|oqshom} {подарил|hadya etdi} нам {незабываемую|unutilmas} {радость|quvonchni}.
:: Ushbu oqshom bizga unutilmas quvonch baxsh etdi.
"""
    },

    # =========================================================================
    # 03. РОДИТЕЛЬНЫЙ ПАДЕЖ (ОТКУДА? КОГО? ЧЕГО? СКОЛЬКО?)
    # =========================================================================
    {
        "folder": "Русские падежи/03. Родительный падеж (Откуда? Кого? Чего?)",
        "name": "1. Письмо родителям на родину",
        "content": """# Письмо родителям на родину

{Дорогие|Qadrli} {мама|oyijon} и {папа|dadajon}! {Пишу|Yozyapman} вам {письмо|xat} из {Санкт-Петербурга|Sankt-Peterburgdan}.
:: Qadrli oyijon va dadajon! Sizlarga Sankt-Peterburgdan xat yozyapman.

У {меня|menda} {всё|hamma narsa} {хорошо|yaxshi}, {нет|yo'q} {никаких|hech qanday} {проблем|muammolar}.
:: Menda hamma narsa yaxshi, hech qanday muammolar yo'q.

{Я|Men} {живу|yashayman} {недалеко|yaqinida} от {университета|universitetning}.
:: Men universitetning yaqinida yashayman.


У {меня|menda} {много|ko'plab} {новых|yangi} {друзей|do'stlarim} из {разных|turli} {уголков|burchaklaridan} {мира|dunyoning}.
:: Menda dunyoning turli burchaklaridan ko'plab yangi do'stlarim bor.

Каждый день с {утра|ertalabdan} до {вечера|kechgacha} {мы|biz} {учим|o'rganamiz} {правила|qoidalarni} {русского|rus} {языка|tilining}.
:: Har kuni ertalabdan kechgacha biz rus tili qoidalarini o'rganamiz.

{Без|...siz} {хорошего|yaxshi} {словаря|lug'atsiz} {трудно|qiyin} {понять|tushunish} {тексты|matnlarni}.
:: Yaxshi lug'atsiz matnlarni tushunish qiyin.


{Здесь|Bu yerda} {уже|allaqachon} {холодно|sovuq}, {около|atrofida} {нуля|nol} {градусов|daraja}.
:: Bu yerda allaqachon sovuq, nol daraja atrofida.

{Я|Men} {не|chiqmayman} {выхожу|chiqmayman} на {улицу|ko'chaga} {без|...siz} {тёплой|issiq} {куртки|kurtkasiz} и {шапки|bosh kiyimsiz}.
:: Men ko'chaga issiq kurtka va bosh kiyimsiz chiqmayman.

{Очень|Juda} {скучаю|soginaman} {без|...siz} {вас|sizlarsiz} и {жду|kutaman} {нашей|bizning} {встречи|uchrashuvimizni}!
:: Sizlarsiz juda sog'inaman va uchrashuvimizni kutaman!
"""
    },
    {
        "folder": "Русские падежи/03. Родительный падеж (Откуда? Кого? Чего?)",
        "name": "2. Времена года и природа России",
        "content": """# Времена года и природа России

{Природа|Tabiat} {России|Rossiyaning} {очень|juda} {красива|go'zal} в {любое|har qanday} {время|vaqtida} {года|yilning}.
:: Rossiyaning tabiati yilning har qanday faslida juda go'zal.

{После|Keyin} {долгой|uzoq} {холодной|sovuq} {зимы|qishdan} {наступает|boshlanadi} {тёплая|iliq} {весна|bahor}.
:: Uzoq sovuq qishdan keyin iliq bahor boshlanadi.

С {деревьев|daraxtlardan} {исчезает|yo'qoladi} {снег|qor}, и {появляется|paydo bo'ladi} {зелёная|yashil} {трава|o't-o'lan}.
:: Daraxtlardan qor ketadi va yashil maysa ko'rina boshlaydi.


{Летом|Yozda} {студенты|talabalar} {отдыхают|dam olishadi} {около|yonida} {чистых|tiniq} {озёр|ko'llar} и {широких|keng} {рек|daryolar}.
:: Yozda talabalar tiniq ko'llar va keng daryolar bo'yida dam olishadi.

В {лесу|o'rmonda} {много|ko'p} {грибов|qo'ziqorinlar} и {сладких|shirin} {ягод|mevalar}.
:: O'rmonda qo'ziqorinlar va shirin rezavor mevalar ko'p bo'ladi.


А {осень|kuz} — {время|vaqti} {золотых|oltinrang} {листьев|barglar}.
:: Kuz esa oltinrang barglar faslidir.

До {конца|oxirigacha} {октября|oktabrning} {люди|odamlar} {гуляют|sayr qilishadi} в {парках|bog'larda}.
:: Oktabr oyining oxirigacha odamlar bog'larda sayr qilishadi.

У {каждого|har bir} {времени|vaqtining} {года|yilning} {есть|bor} {своя|o'z} {неповторимая|betakror} {прелесть|go'zalligi}.
:: Yilning har bir faslining o'z betakror go'zalligi bor.
"""
    },
    {
        "folder": "Русские падежи/03. Родительный падеж (Откуда? Кого? Чего?)",
        "name": "3. В гостях у русского друга",
        "content": """# В гостях у русского друга

Вчера {я|men} {был|bo'ldim} в {гостях|mehmonda} у {моего|mening} {русского|rus} {друга|do'stim} {Антона|Antonniki}.
:: Kecha men o'zimning rus do'stim Antonniki mehmonda bo'ldim.

{Его|Uning} {семья|oilasi} {живёт|yashaydi} {недалеко|yaqinida} от {станции|bekatining} {метро|metro}.
:: Uning oilasi metro bekatining yaqinida yashaydi.

У {них|ularda} {очень|juda} {красивая|chiroyli} и {большая|katta} {квартира|xonadon}.
:: Ularning juda chiroyli va katta xonadoni bor.


У {входа|kirish joyida} {меня|meni} {встретила|kutib oldi} {мама|onasi} {Антона|Antonning}.
:: Kirish joyida meni Antonning onasi kutib oldi.

На {столе|stolda} {было|bor edi} {много|ko'plab} {вкусных|mazali} {блюд|taomlar}: {тарелка|likopcha} {пирогов|piroglar}, {кувшин|ko'za} {сока|sharbat} и {килограмм|kilogramm} {конфет|shirinliklar}.
:: Stol ustida ko'plab mazali taomlar bor edi: bir tarelka pirog, bir ko'za sharbat va bir kilogramm konfet.


Мы {пили|ichdik} {чай|choy} из {красивых|chiroyli} {чашек|chashkalardan} и {слушали|eshitdik} {рассказы|hikoyalarni} {отца|otasining} {Антона|Antonning}.
:: Biz chiroyli chashkalardan choy ichdik va Antonning otasining hikoyalarini tingladik.

Я {ушёл|ketdim} от {них|ulardan} {около|atrofida} {одиннадцати|o'n bir} {часов|soat} {ночи|kechasi}.
:: Men ularnikidan kechasi soat o'n bir atrofida qaytdim.
"""
    },
    {
        "folder": "Русские падежи/03. Родительный падеж (Откуда? Кого? Чего?)",
        "name": "4. Прогулка от центра до Невы",
        "content": """# Прогулка от центра до Невы

В {тёплый|iliq} {день|kunda} {мы|biz} {решили|qaror qildik} {пройтись|piyoda yurishga} от {центра|markazdan} до {набережной|qirg'og'igacha} {Невы|Nevaning}.
:: Iliq bir kunda biz markazdan to Neva qirg'og'igacha piyoda yurishga qaror qildik.

{Наш|Bizning} {маршрут|yo'nalishimiz} {начинался|boshlanar edi} от {Казанского|Qozon} {собора|ibodatxonasidan}.
:: Bizning yo'nalishimiz Qozon soboridan boshlanar edi.

Около {собора|ibodatxona yonida} {стояло|turgan edi} {много|ko'plab} {туристов|sayyohlar} из {Китая|Xitoydan} и {Франции|Fransiyadan}.
:: Ibodatxona yonida Xitoy va Fransiyadan kelgan ko'plab sayyohlar turgan edi.


Мы {дошли|yetib bordik} до {Дворцового|Saroy} {моста|ko'prigigacha}.
:: Biz Saroy ko'prigigacha yetib bordik.

От {ветра|shamoldan} {на|daryoda} {реке|daryoda} {были|bor edi} {большие|katta} {волны|to'lqinlar}.
:: Shamoldan daryoda katta to'lqinlar ko'tarilgan edi.

Для {меня|men uchun} {это|bu} {одно|biri} из {самых|eng} {любимых|sevimli} {мест|joylaridan} {города|shaharning}.
:: Men uchun bu shaharning eng sevimli go'shalaridan biridir.
"""
    },
    {
        "folder": "Русские падежи/03. Родительный падеж (Откуда? Кого? Чего?)",
        "name": "5. Покупки в магазине: сколько стоит?",
        "content": """# Покупки в магазине: сколько стоит?

Вчера {я|men} {пошёл|bordim} в {супермаркет|supermarketga} около {нашего|bizning} {общежития|yotoqxonamiz}.
:: Kecha men yotoqxonamiz yonidagi supermarketga bordim.

Мне {нужно|kerak} {было|edi} {купить|xarid qilish} {много|ko'p} {продуктов|mahsulotlar}.
:: Menga ko'p mahsulotlar sotib olish kerak edi.


Я {взял|oldim} {два|ikki} {литра|litr} {молока|sut}, {пачку|pachka} {чёрного|qora} {чая|choy} и {буханку|buxanka} {белого|oq} {хлеба|non}.
:: Men ikki litr sut, bir pachka qora choy va bir buxanka oq non oldim.

Потом {я|men} {купил|sotib oldim} {полкилограмма|yarim kilo} {сыра|pishloq} и {килограмм|bir kilo} {зелёных|yashil} {яблок|olma}.
:: Keyin yarim kilo pishloq va bir kilo yashil olma sotib oldim.


У {меня|menda} {не|yo'q} {было|edi} с {собой|o'zim bilan} {наличных|naqd} {денег|pul}.
:: Menda o'zim bilan naqd pul yo'q edi.

Поэтому {я|men} {оплатил|to'ladim} {всю|barcha} {стоимость|narxni} с {помощью|yordamida} {банковской|bank} {карты|kartasi}.
:: Shu sababli men barcha summani bank kartasi orqali to'ladim.
"""
    },

    # =========================================================================
    # 04. ДАТЕЛЬНЫЙ ПАДЕЖ (КОМУ? ЧЕМУ? К КОМУ?)
    # =========================================================================
    {
        "folder": "Русские падежи/04. Дательный падеж (Кому? Чему?)",
        "name": "1. Поздравления и подарки друзьям",
        "content": """# Поздравления и подарки друзьям

Скоро {Новый|Yangi} {год|yil}, и {я|men} {готовлю|tayyorlayapman} {подарки|sovg'alarni} {своим|o'z} {друзьям|do'stlarimga}.
:: Yaqinda Yangi yil, va men o'z do'stlarimga sovg'alar tayyorlayapman.

{Своему|O'zimning} {лучшему|eng yaxshi} {другу|do'stim} {Антону|Antonga} {я|men} {подарю|sovg'a qilaman} {интересную|qiziqarli} {книгу|kitobni}.
:: O'zimning eng yaxshi do'stim Antonga men qiziqarli kitob sovg'a qilaman.

{Своей|O'z} {сестре|singlimga} {я|men} {купил|sotib oldim} {тёплый|issiq} {шарф|sharfi}.
:: Singlimga men issiq sharf sotib oldim.


{Утром|Ertalab} {я|men} {позвонил|qo'ng'iroq qildim} {своему|o'zimning} {преподавателю|o'qituvchimga} и {пожелал|tiladim} {ему|unga} {крепкого|mustahkam} {здоровья|salomatlik}.
:: Ertalab men o'qituvchimga qo'ng'iroq qildim va unga mustahkam salomatlik tiladim.

{Преподаватель|O'qituvchi} {был|bo'ldi} {очень|juda} {рад|xursand} {моему|mening} {звонку|qo'ng'irog'imdan}.
:: O'qituvchi mening qo'ng'irog'imdan juda xursand bo'ldi.


{Вечером|Kechqurun} {мы|biz} {поедем|boramiz} в {гости|mehmonga} к {нашим|bizning} {узбекским|o'zbek} {землякам|yurtoshlarimiznikiga}.
:: Kechqurun biz o'zbek yurtdoshlarimiznikiga mehmonga boramiz.

{Помогать|Yordam berish} {друзьям|do'stlarga} и {дарить|ulashish} {радость|quvonchni} — {это|bu} {прекрасная|ajoyib} {традиция|an'anadir}.
:: Do'stlarga yordam berish va quvonch ulashish — bu ajoyib an'anadir.
"""
    },
    {
        "folder": "Русские падежи/04. Дательный падеж (Кому? Чему?)",
        "name": "2. В поликлинике: совет врача",
        "content": """# В поликлинике: совет врача

Вчера {моему|mening} {другу|do'stim} {Олегу|Olegning} {стало|bo'ldi} {плохо|yomon}: у {него|unda} {болело|og'riyotgan edi} {горло|tomog'i}.
:: Kecha mening do'stim Olegning tobi qochdi: uning tomog'i og'riyotgan edi.

Я {помог|yordamlashdim} {ему|unga} {пойти|borishga} к {участковому|hududiy} {врачу|shifokorga}.
:: Men unga hududiy shifokorga borishga yordamlashdim.


{Опытный|Tajribali} {доктор|shifokor} {внимательно|diqqat bilan} {осмотрел|ko'rikdan o'tkazdi} {больного|bemorini}.
:: Tajribali shifokor bemorni diqqat bilan ko'rikdan o'tkazdi.

{Врач|Shifokor} {сказал|aytdi} {моему|mening} {другу|do'stimga}, что {ему|unga} {нужно|kerak} {три|uch} {дня|kun} {лежать|yotish} в {постели|o'rinda}.
:: Shifokor do'stimga uch kun o'rinda yotishi kerakligini aytdi.

Он {выписал|yozib berdi} {рецепт|retseptni} и {объяснил|tushuntirdi} {студенту|talabaga}, как {принимать|ichish kerakligini} {лекарство|dorini}.
:: U retsept yozib berdi va talabaga dorilarni qanday ichish kerakligini tushuntirdi.


{Благодаря|Tufayli} {советам|maslahatlariga} {доктора|shifokorning} {Олегу|Oleg} {уже|allaqachon} {сегодня|bugun} {намного|ancha} {лучше|yaxshiroq}.
:: Shifokorning maslahatlari tufayli bugun Oleg o'zini ancha yaxshiroq his qilmoqda.
"""
    },
    {
        "folder": "Русские падежи/04. Дательный падеж (Кому? Чему?)",
        "name": "3. Помощь иностранным студентам",
        "content": """# Помощь иностранным студентам

В {нашем|bizning} {университете|universitetimizda} {старшие|yuqori kurs} {студенты|talabalari} {всегда|doimo} {помогают|yordam berishadi} {новичкам|yangi kelganlarga}.
:: Bizning universitetimizda yuqori kurs talabalari yangi kelganlarga doimo yordam berishadi.

{Русские|Rus} {ребята|yoshlari} {объясняют|tushuntirishadi} {иностранным|chet ellik} {студентам|talabalarga} {сложные|qiyin} {темы|mavzularni}.
:: Rus yoshlari chet ellik talabalarga qiyin mavzularni tushuntirib berishadi.


{Каждому|Har bir} {студенту|talabaga} {нужно|kerak} {время|vaqt}, чтобы {привыкнуть|o'rganib olish uchun} к {новому|yangi} {климату|iqlimga}.
:: Yangi iqlimga o'rganib olish uchun har bir talabaga vaqt kerak.

{Преподаватели|O'qituvchilar} {терпеливо|sabr bilan} {отвечают|javob berishadi} на {все|barcha} {вопросы|savollarga}.
:: O'qituvchilar barcha savollarga sabr bilan javob berishadi.

{Благодаря|Tufayli} {такой|shunday} {поддержке|qo'llab-quvvatlashga} {нам|bizga} {легко|oson} и {радостно|quvonarli} {учиться|o'qish}.
:: Shunday qo'llab-quvvatlash tufayli bizga o'qish oson va quvonarlidir.
"""
    },
    {
        "folder": "Русские падежи/04. Дательный падеж (Кому? Чему?)",
        "name": "4. Телефонный разговор с родителями",
        "content": """# Телефонный разговор с родителями

{Каждое|Har} {воскресенье|yakshanba kuni} {я|men} {звоню|qo'ng'iroq qilaman} {своим|o'z} {родителям|ota-onamga}.
:: Har yakshanba kuni men o'z ota-onamga qo'ng'iroq qilaman.

{Моему|Mening} {отцу|otam} {скоро|yaqinda} {исполнится|to'ladi} {пятьдесят|ellik} {лет|yosh}.
:: Yaqinda otam ellik yoshga to'ladi.

А {мне|menga} {сейчас|hozir} {двадцать|yigirma} {один|bir} {год|yosh}.
:: Menga esa hozir yigirma bir yosh.


{Мама|Onam} {спрашивает|so'raydi} {меня|mendan}, {нравится|yoqayaptimi} ли {мне|menga} {русская|rus} {еда|taomlari}.
:: Onam mendan rus taomlari menga yoqayaptimi deb so'raydi.

{Я|Men} {отвечаю|javob beraman} {ей|unga}, что {мне|menga} {очень|juda} {нравится|yoqadi} {горячий|issiq} {борщ|borshch}.
:: Men unga qaynoq borshch menga juda yoqishini aytaman.

{Родители|Ota-onam} {советуют|maslahat berishadi} {мне|menga} {больше|ko'proq} {отдыхать|dam olishni}.
:: Ota-onam menga ko'proq dam olishni maslahat berishadi.
"""
    },

    # =========================================================================
    # 05. ТВОРИТЕЛЬНЫЙ ПАДЕЖ (С КЕМ? ЧЕМ? КЕМ?)
    # =========================================================================
    {
        "folder": "Русские падежи/05. Творительный падеж (С кем? Чем?)",
        "name": "1. Кем быть? Мечты о профессии",
        "content": """# Кем быть? Мечты о профессии

{Каждый|Har bir} {молодой|yosh} {человек|inson} {думает|o'ylaydi} о {том|shu haqda}, {кем|kim} {быть|bo'lishni}.
:: Har bir yosh inson kelajakda kim bo'lish haqida o'ylaydi.

{Мой|Mening} {друг|do'stim} {Азиз|Aziz} {хочет|xohlaydi} {стать|bo'lishni} {талантливым|iqtidorli} {программистом|dasturchi}.
:: Mening do'stim Aziz iqtidorli dasturchi bo'lishni istaydi.

{Он|U} {с|bilan} {большим|katta} {интересом|qiziqish} {занимается|shug'ullanadi} {компьютерными|kompyuter} {науками|fanlari bilan}.
:: U kompyuter fanlari bilan katta qiziqish bilan shug'ullanadi.


{Марта|Marta} {мечтает|orzu qiladi} {быть|bo'lishni} {детским|bolalar} {врачом|shifokori}.
:: Marta bolalar shifokori bo'lishni orzu qiladi.

{Она|U} {хочет|xohlaydi} {помогать|yordam berishni} {больным|bemor} {детям|bolalarga}.
:: U bemor bolalarga yordam berishni istaydi.


А {я|men} {буду|bo'laman} {инженером-строителем|quruvchi muhandis}.
:: Men esa quruvchi muhandis bo'laman.

{Я|Men} {хочу|xohlayman} {строить|qurishni} {красивые|chiroyli} {мосты|ko'priklar} и {современные|zamonaviy} {здания|binolarni}.
:: Men chiroyli ko'priklar va zamonaviy binolarni qurishni xohlayman.

{Гордиться|Faxrlanish} {своей|o'z} {профессией|kasbi bilan} — {главная|bosh} {цель|maqsaddir}.
:: O'z kasbi bilan faxrlanish — eng asosiy maqsaddir.
"""
    },
    {
        "folder": "Русские падежи/05. Творительный падеж (С кем? Чем?)",
        "name": "2. Встреча с известным учёным",
        "content": """# Встреча с известным учёным

Вчера в {нашем|bizning} {университете|universitetimizda} {состоялась|bo'lib o'tdi} {встреча|uchrashuv} с {известным|mashhur} {профессором|professor bilan}.
:: Kecha bizning universitetimizda mashhur professor bilan uchrashuv bo'lib o'tdi.

{Студенты|Talabalar} {с|bilan} {огромным|ulkan} {вниманием|e'tibor} {слушали|tinglashdi} {его|uning} {лекцию|ma'ruzasini}.
:: Talabalar uning ma'ruzasini ulkan e'tibor bilan tinglashdi.


{Профессор|Professor} {писал|yozar edi} {сложные|murakkab} {формулы|formulalarni} {белым|oq} {мелом|bo'r bilan} на {доске|doskada}.
:: Professor doskaga murakkab formulalarni oq bo'r bilan yozar edi.

{После|Keyin} {лекции|ma'ruzadan} {мы|biz} {долго|uzoq} {беседовали|suhbatlashdik} с {учёным|olim bilan}.
:: Ma'ruzadan so'ng biz olim bilan uzoq suhbatlashdik.

{Он|U} {поделился|bo'lishdi} с {нами|biz bilan} {своим|o'z} {богатым|boy} {жизненным|hayotiy} {опытом|tajribasi bilan}.
:: U biz bilan o'zining boy hayotiy tajribasini o'rtoqlashdi.
"""
    },
    {
        "folder": "Русские падежи/05. Творительный падеж (С кем? Чем?)",
        "name": "3. Прогулка по парку с друзьями",
        "content": """# Прогулка по парку с друзьями

{Осенним|Kuzgi} {днём|kunda} {мы|biz} {гуляли|sayr qildik} с {друзьями|do'stlarimiz bilan} по {старому|qadimiy} {парку|bog' bo'ylab}.
:: Kuzgi bir kunda biz do'stlarimiz bilan qadimiy bog' bo'ylab sayr qildik.

{Под|Tarixida} {ногами|oyoqlar ostida} {шелестели|shitirlar edi} {жёлтые|sariq} {листья|barglar}.
:: Oyoqlar ostida sariq barglar shitirlar edi.


{Антон|Anton} {шёл|borayotgan edi} {рядом|yonma-yon} с {Мартой|Marta bilan}, а {я|men} {разговаривал|suhbatlashardim} с {новым|yangi} {студентом|talaba bilan}.
:: Anton Marta bilan yonma-yon borardi, men esa yangi talaba bilan suhbatlashardim.

{Над|Tepasida} {нашими|bizning} {головами|boshlarimiz} {светило|porlab turardi} {яркое|yorqin} {солнце|quyosh}.
:: Boshimiz uzra yorqin quyosh porlab turardi.

{Между|Orasida} {деревьями|daraxtlar} {виднелась|ko'rinib turardi} {тихая|sokin} {река|daryo}.
:: Daraxtlar orasidan sokin daryo ko'rinib turardi.
"""
    },
    {
        "folder": "Русские падежи/05. Творительный падеж (С кем? Чем?)",
        "name": "4. Увлечения: спорт и музыка",
        "content": """# Увлечения: спорт и музыка

В {свободное|bo'sh} {время|vaqtda} {каждый|har kim} {занимается|shug'ullanadi} {своим|o'z} {любимым|sevimli} {делом|ishi bilan}.
:: Bo'sh vaqtda har bir inson o'z sevimli mashg'uloti bilan shug'ullanadi.

{Мой|Mening} {сосед|qo'shnim} {серьёзно|jiddiy} {увлекается|qiziqadi} {классической|mumtoz} {музыкой|musiqa bilan}.
:: Mening qo'shnim mumtoz musiqa bilan jiddiy qiziqadi.

{Он|U} {виртуозно|mahorat bilan} {играет|chaladi} на {скрипке|skripka} и {интересуется|qiziqadi} {театром|teatr bilan}.
:: U skripkani mahorat bilan chaladi va teatr san'ati bilan qiziqadi.


А {я|men} с {детства|bolalikdan} {занимаюсь|shug'ullanaman} {восточными|sharqona} {единоборствами|yakkakurashlar bilan}.
:: Men esa bolalikdan sharqona yakkakurashlar bilan shug'ullanaman.

{Спорт|Sport} {делает|qiladi} {человека|insonni} {сильным|kuchli}, {выносливым|chidamlilik} и {дисциплинированным|tartibli}.
:: Sport insonni kuchli, chidamli va tartibli qiladi.
"""
    },

    # =========================================================================
    # 06. ИМЕНИТЕЛЬНЫЙ ПАДЕЖ И МНОЖЕСТВЕННОЕ ЧИСЛО
    # =========================================================================
    {
        "folder": "Русские падежи/06. Именительный падеж и Множественное число",
        "name": "1. Наша интернациональная группа",
        "content": """# Наша интернациональная группа

В {нашей|bizning} {группе|guruhimizda} {учатся|o'qishadi} {двенадцать|o'n ikki} {студентов|talaba}.
:: Bizning guruhimizda o'n ikki nafar talaba o'qiydi.

{Студенты|Talabalar} {приехали|kelishgan} из {разных|turli} {стран|mamlakatlardan}: {Узбекистана|O'zbekistondan}, {Вьетнама|Vyetnamdan}, {Китая|Xitoydan} и {Сирии|Suriyadan}.
:: Talabalar turli mamlakatlardan kelishgan: O'zbekiston, Vyetnam, Xitoy va Suriya.


{Все|Barcha} {ребята|yoshlar} — {очень|juda} {дружные|inoq} и {трудолюбивые|mehnatkash}.
:: Barcha yoshlar — juda inoq va mehnatkash.

На {уроках|darslarda} {мы|biz} {вместе|birgalikda} {читаем|o'qiymiz} {сложные|murakkab} {тексты|matnlarni} и {учим|o'rganamiz} {новые|yangi} {слова|so'zlarni}.
:: Darslarda biz birgalikda murakkab matnlarni o'qiymiz va yangi so'zlarni o'rganamiz.

{Наши|Bizning} {преподаватели|o'qituvchilarimiz} — {настоящие|haqiqiy} {мастера|ustalari} {своего|o'z} {дела|ishining}.
:: Bizning o'qituvchilarimiz — o'z ishining haqiqiy ustalari.
"""
    },
    {
        "folder": "Русские падежи/06. Именительный падеж и Множественное число",
        "name": "2. Моя семья и родной дом",
        "content": """# Моя семья и родной дом

{Моя|Mening} {семья|oilam} {живёт|yashaydi} в {городе|shaharda} {Ташкенте|Toshkentda}.
:: Mening oilam Toshkent shahrida yashaydi.

{Мой|Mening} {отец|otam} — {опытный|tajribali} {инженер|muhandis}, а {мать|onam} — {школьная|maktab} {учительница|o'qituvchisi}.
:: Mening otam — tajribali muhandis, onam esa — maktab o'qituvchisi.


У {меня|menda} {есть|bor} {старший|katta} {брат|aka} и {младшая|kichik} {сестра|singil}.
:: Mening katta akam va kichik singlim bor.

{Брат|Akam} {работает|ishlaydi} в {банке|bankda}, а {сестра|singlim} ещё {учится|o'qiydi} в {школе|maktabda}.
:: Akam bankda ishlaydi, singlim esa hali maktabda o'qiydi.

{Родители|Ota-onam} {всегда|doimo} {поддерживают|qo'llab-quvvatlaydi} {меня|meni} во {всех|barcha} {начинаниях|boshlanmalarda}.
:: Ota-onam meni barcha boshlanmalarimda doimo qo'llab-quvvatlaydi.
"""
    },
    {
        "folder": "Русские падежи/06. Именительный падеж и Множественное число",
        "name": "3. Политехнический университет",
        "content": """# Политехнический университет

{Санкт-Петербургский|Sankt-Peterburg} {политехнический|politexnika} {университет|universiteti} — {один|biri} из {старейших|eng qadimiy} {вузов|oliygohlaridan} {России|Rossiyaning}.
:: Sankt-Peterburg politexnika universiteti — Rossiyaning eng qadimiy oliygohlaridan biridir.

{Здесь|Bu yerda} {учатся|o'qishadi} {тысячи|minglab} {талантливых|iqtidorli} {студентов|talabalar}.
:: Bu yerda minglab iqtidorli talabalar ta'lim olishadi.


{Университетский|Universitet} {кампус|shaharchasi} {занимает|egallaydi} {огромную|ulkan} {территорию|hududni}.
:: Universitet shaharchasi ulkan hududni egallaydi.

{Красивые|Chiroyli} {учебные|o'quv} {корпуса|korpuslari}, {современные|zamonaviy} {лаборатории|laboratoriyalari} и {зелёные|yashil} {парки|bog'lari} {радуют|quvontiradi} {глаз|ko'zni}.
:: Chiroyli o'quv korpuslari, zamonaviy laboratoriyalar va yashil bog'lar ko'zni quvontiradi.

{Учиться|Ta'lim olish} в {таком|bunday} {месте|joyda} — {большая|katta} {честь|sharafdir}.
:: Bunday maskanda ta'lim olish — katta sharafdir.
"""
    },

    # =========================================================================
    # 07. КОМПЛЕКСНЫЕ ТЕКСТЫ И ДИАЛОГИ
    # =========================================================================
    {
        "folder": "Русские падежи/07. Комплексные тексты и диалоги",
        "name": "1. Путешествие по городам России",
        "content": """# Путешествие по городам России

{Россия|Rossiya} — {огромная|ulkan} {страна|mamlakat} с {богатой|boy} {историей|tarixga ega} и {культурой|madaniyatga ega}.
:: Rossiya — boy tarix va madaniyatga ega ulkan mamlakat.

{Иностранные|Chet ellik} {студенты|talabalar} с {удовольствием|mamnuniyat bilan} {путешествуют|sayohat qilishadi} по {русским|rus} {городам|shaharlari bo'ylab}.
:: Chet ellik talabalar rus shaharlari bo'ylab mamnuniyat bilan sayohat qilishadi.


В {Москве|Moskvada} {туристы|sayyohlar} {восхищаются|hayratlanishadi} {величественным|muhtasham} {Кремлём|Kreml bilan}.
:: Moskvada sayyohlar muhtasham Kreml bilan hayratga tushishadi.

В {Санкт-Петербурге|Sankt-Peterburgda} {они|ular} {гуляют|sayr qilishadi} по {набережным|qirg'oqlar bo'ylab} и {любуются|zavqlanishadi} {разводными|ochiluvchi} {мостами|ko'priklar bilan}.
:: Sankt-Peterburgda ular qirg'oqlar bo'ylab sayr qilishadi va ochiluvchi ko'priklar bilan zavqlanishadi.

В {древнем|qadimiy} {Новгороде|Novgorodda} {можно|mumkin} {прикоснуться|tegish} к {самым|eng} {истокам|ildizlariga} {истории|tarixning}.
:: Qadimiy Novgorodda esa tarixning eng tub ildizlarini his qilish mumkin.


{Каждая|Har bir} {поездка|safar} {дарит|hadya etadi} {человеку|insonga} {новых|yangi} {друзей|do'stlarni} и {незабываемые|unutilmas} {впечатления|taassurotlarni}.
:: Har bir sayohat insonga yangi do'stlar va unutilmas taassurotlar baxsh etadi.
"""
    },
    {
        "folder": "Русские падежи/07. Комплексные тексты и диалоги",
        "name": "2. Праздники: Новый год и Навруз",
        "content": """# Праздники: Новый год и Навруз

{Праздники|Bayramlar} {объединяют|birlashtiradi} {людей|odamlarni} {всего|butun} {мира|dunyoning}.
:: Bayramlar butun dunyo odamlarini birlashtiradi.

В {России|Rossiyada} с {нетерпением|intiqlik bilan} {ждут|kutishadi} {Новый|Yangi} {год|yilni}.
:: Rossiyada Yangi yilni intiqlik bilan kutishadi.

{Люди|Odamlar} {украшают|bezatishadi} {зелёную|yashil} {ёлку|archa} {яркими|yorqin} {игрушками|o'yinchoqlar bilan} и {дарят|ulashishadi} {подарки|sovg'alarni}.
:: Odamlar yashil archani yorqin o'yinchoqlar bilan bezatishadi va sovg'alar ulashishadi.


А в {Узбекистане|O'zbekistonda} {самый|eng} {главный|asosiy} {весенний|bahorgi} {праздник|bayram} — {Навруз|Navro'z}.
:: O'zbekistonda esa eng asosiy bahor bayrami — Navro'zdir.

В {этот|ushbu} {день|kunda} {женщины|ayollar} {готовят|tayyorlashadi} {праздничный|bayramona} {сумаляк|sumalakni} и {угощают|mehmon qilishadi} {соседей|qo'shnilarni}.
:: Ushbu kunda ayollar bayramona sumalak tayyorlashadi va qo'shnilarni mehmon qilishadi.


{Мы|Biz} {рассказали|gapirib berdik} {русским|rus} {друзьям|do'stlarimizga} о {наших|bizning} {национальных|milliy} {обычаях|urf-odatlarimiz haqida}.
:: Biz rus do'stlarimizga o'zimizning milliy urf-odatlarimiz haqida gapirib berdik.

{Взаимное|O'zaro} {уважение|hurmat} к {культуре|madaniyatga} {делает|qiladi} {дружбу|do'stlikni} {крепкой|mustahkam}.
:: Madaniyatga o'zaro hurmat do'stlikni mustahkam qiladi.
"""
    },
    {
        "folder": "Русские падежи/07. Комплексные тексты и диалоги",
        "name": "3. Итоговый рассказ: Мой первый год в России",
        "content": """# Итоговый рассказ: Мой первый год в России

{Прошёл|O'tdi} {ровно|rosa} {один|bir} {год|yil} с {того|o'sha} {дня|kundan}, как {я|men} {приехал|kelgan edim} в {Санкт-Петербург|Sankt-Peterburgga}.
:: Men Sankt-Peterburgga kelgan kundan buyon roppa-rosa bir yil o'tdi.

Вначале {мне|menga} {было|edi} {очень|juda} {трудно|qiyin} {говорить|gapirish} по-русски и {понимать|tushunish} {быструю|tez} {речь|nutqni}.
:: Boshida menga ruscha gapirish va tez nutqni tushunish juda qiyin edi.


Но {благодаря|tufayli} {ежедневным|har kungi} {упражнениям|mashqlarga} и {терпению|sabr-toqatga} {русский|rus} {язык|tili} {стал|bo'ldi} {мне|menga} {родным|yaqin}.
:: Ammo har kungi mashqlar va sabr-toqat tufayli rus tili menga yaqin bo'lib qoldi.

{Теперь|Endi} {я|men} {свободно|erkin} {общаюсь|muloqot qilaman} с {преподавателями|o'qituvchilar bilan} и {читаю|o'qiyman} {книги|kitoblarni} {без|...siz} {словаря|lug'atsiz}.
:: Endi men o'qituvchilar bilan erkin muloqot qilaman va kitoblarni lug'atsiz o'qiyman.


Впереди {меня|meni} {ждут|kutmoqda} {новые|yangi} {предметы|fanlar}, {интересные|qiziqarli} {проекты|loyihalar} и {большие|katta} {победы|g'alabalar}.
:: Oldinda meni yangi fanlar, qiziqarli loyihalar va ulkan g'alabalar kutmoqda.

{Главное|Eng asosiysi} — {всегда|doimo} {идти|borishdir} {вперёд|oldinga} и {верить|ishonishdir} в {свои|o'z} {силы|kuchiga}!
:: Eng asosiysi — doimo oldinga intilish va o'z kuchiga ishonishdir!
"""
    }
]

print(f"Loaded {len(TEXTS)} interactive Russian reading texts.")
