# Teacher–Student Task Management App
## AI Development uchun to‘liq texnik topshiriq va master prompt

Sen tajribali **Senior Mobile Architect, Backend Engineer, UI/UX Designer va Product Engineer** sifatida ishlaysan.

Maqsadimiz — o‘qituvchilar va talabalar uchun zamonaviy, qulay va professional **vazifalarni boshqarish va nazorat qilish mobil ilovasi** yaratish.

Ilovaning asosiy vazifasi:

- O‘qituvchi guruhlar yaratadi.
- Talabalarni guruhlarga qo‘shadi.
- Vazifalar yaratadi.
- Vazifalarni talabalarga biriktiradi.
- Talabalar vazifalarni ko‘radi va bajaradi.
- Talabalar topshiriqlarni yuboradi.
- O‘qituvchi topshiriqlarni tekshiradi.
- Baholaydi va feedback beradi.
- Tizim bajarilish jarayonini kuzatadi.
- Statistikalar va hisobotlar shakllantiradi.
- Ma’lumotlarni **PDF va Excel** formatida eksport qilish imkoniyati bo‘ladi.

---

# 1. MUHIM ISH PRINSIPI

Loyihani birdaniga tartibsiz kodlab ketma.

Avval:

1. Talablarni analiz qil.
2. Arxitekturani ishlab chiq.
3. Database modelini ishlab chiq.
4. API contractlarini aniqlab ol.
5. Authentication va authorization tizimini loyihala.
6. UI/UX strukturasini ishlab chiq.
7. Project folder structure yarat.
8. Keyin developmentni bosqichlarga bo‘l.

Har bir bosqich tugagandan keyin:

- nima qilindi;
- nima uchun shunday qilindi;
- qaysi fayllar yaratildi/o‘zgartirildi;
- keyingi bosqich nima ekanini ko‘rsat.

Agar biror qaror qabul qilish kerak bo‘lsa, eng professional va scalable variantni tanla.

---

# 2. PLATFORMALAR

Birinchi versiya:

**Android**

Lekin arxitektura quyidagilarga tayyor bo‘lishi kerak:

- Android
- iOS
- macOS

UI dizayni platformaga bog‘lanib qolmasligi kerak.

Keyinchalik iOS/macOS versiyalarini chiqarish imkoniyati saqlanib qolishi kerak.

---

# 3. DESIGN PHILOSOPHY

Ilova juda zamonaviy, minimalistik va qulay bo‘lishi kerak.

UI/UX uchun:

- ChatGPT
- Apple
- Linear
- Notion
- modern productivity apps

kabi mahsulotlarning usability tamoyillaridan ilhom ol.

Lekin ularning dizaynini aynan ko‘chirma.

## Asosiy prinsiplar

- Minimalizm
- Ko‘p bo‘sh joy
- Toza typography
- Aniq hierarchy
- Katta va tushunarli buttonlar
- Keraksiz elementlarsiz interfeys
- Dark mode
- Light mode
- Smooth animation
- Subtle transition
- Loading skeleton
- Empty states
- Error states
- Success states
- Responsive layout
- Accessibility

Foydalanuvchi ilovani birinchi marta ochganda ham uni o‘rganish uchun uzoq vaqt sarflamasligi kerak.

---

# 4. USER ROLES

Tizimda kamida ikkita asosiy role bo‘ladi:

## Teacher

O‘qituvchi:

- register/login qiladi;
- profilini boshqaradi;
- guruhlar yaratadi;
- talabalarni qo‘shadi;
- vazifalar yaratadi;
- vazifalarni tahrirlaydi;
- vazifalarni o‘chiradi;
- deadline belgilaydi;
- vazifani ma’lum guruhga biriktiradi;
- individual talabaga vazifa beradi;
- topshirilgan ishlarni ko‘radi;
- baholaydi;
- feedback beradi;
- qayta topshirishni so‘rashi mumkin;
- statistika ko‘radi;
- hisobot yaratadi;
- PDF eksport qiladi;
- Excel eksport qiladi.

## Student

Talaba:

- register/login qiladi;
- profilini boshqaradi;
- o‘z guruhlarini ko‘radi;
- vazifalarini ko‘radi;
- vazifa tafsilotlarini ochadi;
- vazifani bajaradi;
- fayl biriktiradi;
- javob yuboradi;
- yuborilgan javobni ko‘radi;
- deadline ko‘radi;
- bahosini ko‘radi;
- teacher feedbackini ko‘radi;
- kerak bo‘lsa qayta topshiradi;
- o‘z progressini ko‘radi.

---

# 5. AUTHENTICATION

Authentication professional darajada bo‘lishi kerak.

Qo‘llab-quvvatlash:

- Registration
- Login
- Logout
- Refresh token
- Access token
- Password hashing
- Forgot password
- Reset password
- Email verification
- Session management

Kelajak uchun:

- Google login
- Apple login

integratsiyasiga tayyor arxitektura ishlab chiq.

Role-based authorization ishlat.

Masalan:

TEACHER endpointlariga STUDENT kira olmasligi kerak.

STUDENT endpointlariga TEACHER noto‘g‘ri permission bilan kira olmasligi kerak.

---

# 6. TEACHER DASHBOARD

Teacher dashboard juda qulay bo‘lishi kerak.

Asosiy statistikalar:

- Total Students
- Total Groups
- Active Assignments
- Completed Assignments
- Pending Assignments
- Late Assignments
- Average Score
- Completion Rate

Dashboardda grafiklar bo‘lishi mumkin:

- Assignment completion
- Student performance
- Group performance
- Weekly activity
- Monthly activity

---

# 7. GROUP MANAGEMENT

Teacher:

### Group yaratishi

Masalan:

"Python Backend 2026"

Group ma'lumotlari:

- id
- name
- description
- teacher
- created_at
- updated_at

### Group CRUD

Create  
Read  
Update  
Delete

Teacher guruhga:

- student qo‘shadi;
- studentni olib tashlaydi;
- studentlar ro‘yxatini ko‘radi.

---

# 8. STUDENT MANAGEMENT

Teacher studentlar ro‘yxatini ko‘rishi kerak.

Har bir student:

- name
- username/email
- avatar
- group
- total assignments
- completed
- pending
- late
- average score
- completion percentage

Teacher student profiliga kirganda uning faoliyatini ko‘ra olishi kerak.

---

# 9. ASSIGNMENT SYSTEM

Bu loyihaning eng muhim qismi.

Teacher assignment yaratadi.

Assignment:

- id
- title
- description
- instructions
- group
- assigned student
- created_by
- created_at
- updated_at
- deadline
- priority
- status
- attachment
- max_score

Priority:

- Low
- Medium
- High
- Urgent

Status:

- Draft
- Published
- In Progress
- Submitted
- Reviewed
- Completed
- Late

---

# 10. ASSIGNMENT CRUD

Teacher:

### Create

Yangi vazifa yaratadi.

### Read

Vazifalarni ko‘radi.

### Update

Vazifani tahrirlaydi.

### Delete

Vazifani o‘chiradi.

Delete qilishda confirmation dialog bo‘lsin.

---

# 11. ASSIGNMENT CREATION UI

Assignment yaratish sahifasi:

Title

Description

Instructions

Select Group

Select Student

Deadline

Priority

Maximum Score

Attachments

Publish / Save Draft

buttonlariga ega bo‘lsin.

Agar Group tanlansa, barcha studentlarga yuborish imkoniyati bo‘lsin.

Alohida student tanlash ham mumkin bo‘lsin.

---

# 12. STUDENT ASSIGNMENT PAGE

Student vazifani ochganda:

- title
- description
- instructions
- deadline
- priority
- attachments
- teacher
- status
- score
- feedback

ko‘rinishi kerak.

Agar hali topshirilmagan bo‘lsa:

**Submit Assignment**

buttoni ko‘rinsin.

---

# 13. ASSIGNMENT SUBMISSION

Student:

- text answer yozishi;
- fayl yuklashi;
- bir nechta attachment qo‘shishi;
- submission yuborishi mumkin.

Submission:

- id
- assignment
- student
- text
- attachments
- submitted_at
- status
- score
- feedback
- reviewed_at
- reviewer

maydonlariga ega bo‘lsin.

---

# 14. TEACHER REVIEW SYSTEM

Teacher submitted assignmentni ochadi.

Ko‘radi:

- Student
- Assignment
- Submission
- Submitted date
- Attachments
- Answer

Teacher:

- score beradi;
- feedback yozadi;
- approve qiladi;
- reject qiladi;
- resubmit so‘raydi.

Masalan:

Score: 85/100

Feedback:

"Good implementation, but improve error handling."

---

# 15. DEADLINE SYSTEM

Deadline tizimi aqlli bo‘lishi kerak.

Assignment deadline yaqinlashganda:

"Due tomorrow"

"Due in 3 hours"

kabi statuslar ko‘rsatilishi mumkin.

Deadline o'tgan bo‘lsa:

"Overdue"

ko‘rsatiladi.

Student topshiriqni deadline'dan keyin topshirsa:

Late Submission sifatida belgilanadi.

---

# 16. NOTIFICATION SYSTEM

Notification tizimi qo‘sh.

Teacher uchun:

- assignment submitted
- student completed assignment
- deadline approaching

Student uchun:

- new assignment
- deadline approaching
- assignment reviewed
- feedback received
- resubmission requested

Notificationlar:

- in-app
- push notification

bo‘lishi uchun arxitekturani tayyorla.

---

# 17. SEARCH VA FILTER

Teacher assignmentlarni:

- title
- student
- group
- status
- priority
- deadline

bo‘yicha qidira va filter qila olishi kerak.

Student:

- active
- completed
- overdue
- upcoming

filterlarini ishlata olishi kerak.

Search tez ishlashi kerak.

---

# 18. SORTING

Assignmentlar:

- Newest
- Oldest
- Deadline
- Priority
- Status

bo‘yicha sort qilinsin.

---

# 19. PROFILE

Teacher va Student profil sahifasiga ega bo‘ladi.

Profile:

- avatar
- full name
- username/email
- role
- groups
- statistics

Settings:

- Language
- Theme
- Notifications
- Account
- Security
- Logout

---

# 20. DARK MODE / LIGHT MODE

Ikki asosiy theme:

Light

Dark

bo‘lsin.

Theme system centralized bo‘lsin.

Hardcoded colorlardan qoch.

Design tokens ishlat.

Masalan:

- background
- surface
- primary
- secondary
- text
- muted
- border
- error
- success
- warning

---

# 21. ANALYTICS

Teacher uchun analytics sahifasi yarat.

Ko‘rsatkichlar:

- Total students
- Total assignments
- Completion rate
- Average score
- Late submissions
- Student ranking
- Group performance

Student uchun:

- completed assignments
- pending assignments
- overdue assignments
- average score
- completion rate
- recent activity

---

# 22. REPORT SYSTEM

Teacher report yaratishi mumkin.

Report turlari:

### Student Report

Bitta studentning:

- assignments
- scores
- completion rate
- late submissions
- average score

### Group Report

Guruhning:

- students
- assignments
- completion
- average score
- performance

### Assignment Report

Bitta assignment:

- assigned students
- submitted
- pending
- late
- average score

---

# 23. PDF EXPORT

Teacher reportni PDF qilib export qila olishi kerak.

PDF professional ko‘rinishda bo‘lsin.

PDF ichida:

- application name
- teacher
- group/student
- date
- report period
- statistics
- tables
- scores
- completion percentage

bo‘lishi mumkin.

PDF generation backend orqali amalga oshirilishi mumkin.

---

# 24. EXCEL EXPORT

Teacher Excel faylini export qila olishi kerak.

Excel:

- students
- assignments
- scores
- statuses
- deadlines
- completion rates

kabi ma'lumotlarni o‘z ichiga olishi kerak.

Excel strukturasi tartibli va professional bo‘lsin.

---

# 25. FILE MANAGEMENT

Assignment attachmentlar uchun:

- PDF
- DOCX
- XLSX
- PPTX
- JPG
- PNG
- ZIP

kabi formatlarni qo‘llab-quvvatlash mumkin.

Security sababli:

- file type validation
- file size validation
- secure filename
- access permission

bo‘lishi shart.

Student faqat o‘ziga tegishli fayllarni ko‘ra olishi kerak.

---

# 26. DATABASE

Database relational database bo‘lishi kerak.

Asosiy entitylar:

User

Teacher

Student

Group

GroupMembership

Assignment

AssignmentAttachment

Submission

SubmissionAttachment

Feedback

Notification

Report

AuditLog

kerak bo‘lsa qo‘shimcha entitylar qo‘sh.

Database relationshiplarini professional tarzda loyihala.

Foreign keylar.

Indexes.

Constraints.

Unique fields.

Timestamps.

Soft delete kerak bo‘lsa qo‘llash.

---

# 27. API

RESTful API yoki loyiha uchun eng yaxshi deb topilgan API architecture ishlat.

API endpointlar mantiqiy va consistent bo‘lsin.

Masalan:

POST /auth/register

POST /auth/login

POST /auth/refresh

GET /groups

POST /groups

GET /groups/{id}

PATCH /groups/{id}

DELETE /groups/{id}

GET /assignments

POST /assignments

GET /assignments/{id}

PATCH /assignments/{id}

DELETE /assignments/{id}

POST /assignments/{id}/submit

POST /submissions/{id}/review

GET /reports

GET /reports/export/pdf

GET /reports/export/excel

va boshqalar.

Endpointlarni project talablariga qarab to‘liq ishlab chiq.

---

# 28. API SECURITY

Quyidagilarni hisobga ol:

- Authentication
- Authorization
- RBAC
- Rate limiting
- Input validation
- File validation
- Secure headers
- SQL injection protection
- XSS protection
- CSRF protection kerak bo‘lgan joylarda
- Secure token storage
- Password hashing

---

# 29. MOBILE ARCHITECTURE

Mobile application uchun:

- clean architecture
- feature-based architecture
- reusable components
- repository pattern
- state management
- API layer
- local cache

kabi professional yondashuvlardan foydalan.

Architecture scalable bo‘lishi kerak.

Kod bir-biriga qattiq bog‘lanib qolmasin.

---

# 30. OFFLINE / CACHE

Internet vaqtincha bo‘lmasa:

- oldin yuklangan assignmentlar;
- student ma'lumotlari;
- dashboard ma'lumotlari

cache orqali ko‘rinishi mumkin.

Internet qaytganda synchronization ishlashi uchun architecture tayyor bo‘lsin.

---

# 31. ERROR HANDLING

Har bir xatolik foydalanuvchiga tushunarli ko‘rsatilishi kerak.

Masalan:

"Something went wrong"

o‘rniga:

"Vazifani yuklashda muammo yuz berdi. Internet aloqangizni tekshirib, qayta urinib ko‘ring."

kabi foydalanuvchi tushunadigan message ishlat.

---

# 32. LOADING STATES

Har bir API request uchun:

- loading
- success
- error
- empty

state mavjud bo‘lsin.

Skeleton loading ishlatish mumkin.

---

# 33. EMPTY STATES

Masalan studentda vazifa bo‘lmasa:

"You're all caught up"

"No assignments yet."

kabi yoqimli empty state yarat.

Faqat bo‘sh ekran ko‘rsatma.

---

# 34. UX PRINCIPLES

Ilovada:

- minimal clicks;
- intuitive navigation;
- clear hierarchy;
- predictable behavior;
- instant feedback;
- confirmation only when necessary

tamoyillariga amal qil.

Foydalanuvchini keraksiz popup va formalar bilan charchatma.

---

# 35. NAVIGATION

Student uchun taxminiy navigation:

Home

Assignments

Calendar

Progress

Profile

Teacher uchun:

Dashboard

Assignments

Students

Groups

Reports

Profile

bo‘lishi mumkin.

Platformaga qarab navigationni optimal tarzda tanla.

---

# 36. CALENDAR

Calendar sahifasini qo‘sh.

Student:

- upcoming deadlines
- overdue tasks
- completed tasks

ni ko‘radi.

Teacher:

- assignment deadlines
- submissions
- review tasks

ni ko‘radi.

---

# 37. AUDIT LOG

Muhim actionlarni log qil:

- assignment created
- assignment updated
- assignment deleted
- submission created
- submission reviewed
- score changed
- student added
- student removed

Bu kelajakda debugging va security uchun kerak bo‘ladi.

---

# 38. PERFORMANCE

Ilova tez ishlashi kerak.

Quyidagilarga e'tibor ber:

- pagination
- lazy loading
- image optimization
- API caching
- database indexing
- optimized queries
- unnecessary API requestsni kamaytirish

---

# 39. ACCESSIBILITY

Ilova:

- screen reader
- proper contrast
- scalable text
- touch target
- semantic labels

kabi accessibility talablariga javob bersin.

---

# 40. INTERNATIONALIZATION

Arxitektura ko‘p tillilikka tayyor bo‘lsin.

Boshlang‘ich:

- Uzbek
- Russian
- English

tillarini qo‘llash imkoniyati bo‘lsin.

Textlarni kod ichida hardcode qilma.

---

# 41. TESTING

Testlar yozilishi shart.

Backend:

- Unit tests
- Integration tests
- API tests
- Authentication tests
- Permission tests

Mobile:

- Unit tests
- UI tests
- ViewModel/state tests

Muhim business logic test qilinsin.

---

# 42. CODE QUALITY

Kod:

- clean
- readable
- modular
- maintainable
- scalable

bo‘lishi kerak.

Duplicate code kamaytir.

Magic number va magic stringlardan qoch.

Environment variables ishlat.

Secretsni source code ichiga yozma.

---

# 43. ENVIRONMENT

Development, testing va production environmentlar alohida bo‘lishi kerak.

Masalan:

.env

.env.example

ishlat.

Secret:

- API keys
- database password
- JWT secret
- storage credentials

repositoryga joylanmasin.

---

# 44. DOCUMENTATION

Loyiha documentationga ega bo‘lishi kerak.

README ichida:

- Project description
- Architecture
- Installation
- Environment variables
- Database setup
- Running backend
- Running mobile
- API documentation
- Testing
- Deployment

bo‘lsin.

---

# 45. UI COMPONENT SYSTEM

Reusable componentlar yarat:

- Button
- Input
- TextField
- SearchBar
- Card
- Avatar
- Badge
- Chip
- Modal
- BottomSheet
- Dialog
- Toast
- Snackbar
- Dropdown
- DatePicker
- ProgressBar
- ProgressCircle
- Skeleton
- EmptyState
- ErrorState

Bir xil componentni project bo‘ylab qayta ishlat.

---

# 46. DESIGN SYSTEM

Design system yarat.

Typography:

- Display
- Heading
- Body
- Caption

Spacing:

4
8
12
16
20
24
32
40
48

kabi consistent scale ishlat.

Border radius, shadows va elevation ham centralized bo‘lsin.

---

# 47. SECURITY RULE

Teacher faqat o‘ziga tegishli:

- groups
- students
- assignments
- submissions
- reports

ni boshqara olishi kerak.

Student faqat:

- o‘z profilini;
- o‘z guruhlarini;
- o‘z assignmentlarini;
- o‘z submissionlarini;
- o‘z feedbacklarini

ko‘ra olishi kerak.

ID orqali boshqa foydalanuvchining ma'lumotiga kirishning oldini ol.

---

# 48. FUTURE FEATURES

Architecture kelajakda quyidagilarni qo‘shishga tayyor bo‘lsin:

- AI assignment generation
- AI feedback
- AI student performance analysis
- Chat between teacher and student
- Group chat
- Attendance tracking
- Exam system
- Quiz system
- Certificate
- Gamification
- Leaderboard
- Badges
- Streaks
- Calendar synchronization
- Google Calendar integration
- Apple Calendar integration
- Email notifications
- Telegram notifications

Lekin MVPda keraksiz featurelarni haddan tashqari ko‘paytirma.

---

# 49. MVP

Birinchi versiyada eng muhim funksiyalar:

### Authentication

- Register
- Login
- Logout

### Teacher

- Dashboard
- CRUD Groups
- CRUD Assignments
- Student management
- Assignment review
- Score
- Feedback
- Reports

### Student

- Dashboard
- Assignments
- Assignment submission
- Score
- Feedback
- Progress

### Export

- PDF
- Excel

### UI

- Light mode
- Dark mode
- Responsive design
- Modern UX

Shular birinchi navbatda mukammal ishlasin.

---

# 50. DEVELOPMENT ORDER

Loyihani quyidagi tartibda ishlab chiq:

## Phase 1

Project architecture

## Phase 2

Database

## Phase 3

Authentication

## Phase 4

User roles

## Phase 5

Groups

## Phase 6

Assignments

## Phase 7

Submissions

## Phase 8

Review and grading

## Phase 9

Dashboard

## Phase 10

Notifications

## Phase 11

Reports

## Phase 12

PDF export

## Phase 13

Excel export

## Phase 14

Mobile UI polish

## Phase 15

Testing

## Phase 16

Security audit

## Phase 17

Performance optimization

## Phase 18

Production deployment

---

# 51. AI BILAN ISHLASH QOIDASI

Sen menga butun loyihani birdaniga minglab qator kod qilib bermaysan.

Har bir phase bilan ishlaysan.

Har bir phase oldidan:

1. Maqsadni tushuntir.
2. Architecture qarorini tushuntir.
3. Fayllar strukturasini ko‘rsat.
4. Kodni yoz.
5. Qanday ishga tushirishni ko‘rsat.
6. Test qilish usulini ko‘rsat.
7. Potential problemsni ko‘rsat.

Keyin keyingi phasega o'tamiz.

Agar oldingi phase'da xatolik bo‘lsa, keyingi phasega o'tma.

---

# 52. FILE STRUCTURE

Project structure professional va scalable bo‘lsin.

Masalan:

backend/

    app/

        auth/

        users/

        groups/

        assignments/

        submissions/

        notifications/

        reports/

        analytics/

        common/

    tests/

    config/

    manage.py

mobile/

    core/

    features/

        auth/

        dashboard/

        assignments/

        groups/

        students/

        submissions/

        reports/

        profile/

    shared/

    components/

    navigation/

    theme/

    tests/

Strukturani ishlatiladigan technologyga mos ravishda optimallashtir.

---

# 53. TECHNOLOGY SELECTION

Technology stackni o‘zingcha taxmin qilib tanlama.

Avval project talablarini analiz qil.

Android + iOS + macOS uchun eng yaxshi cross-platform solutionni tanlashni taklif qil.

Backend uchun scalable backend technology tanla.

Database uchun production-ready relational database ishlat.

File storage uchun scalable storage architecture ishlat.

Agar bir nechta yaxshi variant bo‘lsa, ularni:

- performance
- development speed
- scalability
- maintainability
- ecosystem
- cross-platform support

bo‘yicha taqqoslab, eng yaxshi variantni tanla.

---

# 54. FINAL PRODUCT REQUIREMENT

Final product quyidagicha his qilinishi kerak:

**"Professional education productivity app."**

Ilova:

- tez;
- sodda;
- chiroyli;
- professional;
- zeriktirmaydigan;
- intuitiv;
- xavfsiz;
- scalable

bo‘lishi kerak.

Foydalanuvchi ilovadan foydalanayotganda "qayerni bosaman?" deb o‘ylanib qolmasligi kerak.

Har bir action o‘zining aniq feedbackiga ega bo‘lsin.

---

# 55. FIRST RESPONSE

Hozircha kod yozishni boshlama.

Birinchi javobingda faqat quyidagilarni tayyorla:

1. Project overview
2. Recommended technology stack
3. System architecture
4. Database ER diagram description
5. User roles
6. Main screens
7. API architecture
8. Folder structure
9. Development roadmap
10. MVP scope
11. Security architecture
12. UI/UX design system

Shundan keyin men tasdiqlaganimdan so‘ng **Phase 1**ni boshlaymiz.

Muhim:

**Kod yozishdan oldin architecture va technology tanlovini asosla.**
**Noaniq joylarda professional engineering qarorini qabul qil.**
**Keraksiz featurelarni MVPga tiqishtirma.**
**Security, scalability va maintainabilityni boshidan hisobga ol.**