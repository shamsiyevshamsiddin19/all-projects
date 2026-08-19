# 🐍 Django — Noldan Production'gacha Mukammal Qo'llanma

**Django** — Python uchun eng mashhur, "batteries included" (hammasi tayyor) falsafasidagi backend freymvork. Instagram, Pinterest, Mozilla, Disqus kabi loyihalar aynan Django asosida qurilgan.

**Versiya haqida (2026-yil holati):** joriy so'nggi versiya **Django 6.0** (Python 3.12–3.14 talab qiladi), production uchun esa uzoq muddatli qo'llab-quvvatlanadigan **Django 5.2 LTS** (2028-yilgacha, Python 3.10+ bilan mos) tavsiya etiladi. Yangi loyiha boshlayotgan bo'lsangiz va Python versiyangiz ruxsat bersa, 6.0 — yangi imkoniyatlari (masalan, o'rnatilgan background tasks) tufayli yaxshi tanlov.

**Manba:** rasmiy hujjatlar — [docs.djangoproject.com](https://docs.djangoproject.com)

---

## 📑 Mundarija

1. [Muhitni tayyorlash](#1-muhitni-tayyorlash)
2. [Loyiha yaratish va professional struktura](#2-loyiha-yaratish-va-professional-struktura)
3. [MTV arxitektura — Django qanday ishlaydi](#3-mtv-arxitektura--django-qanday-ishlaydi)
4. [Sozlamalar (settings) va .env](#4-sozlamalar-settings-va-env)
5. [Models — ORM chuqur tahlili](#5-models--orm-chuqur-tahlili)
6. [Migratsiyalar](#6-migratsiyalar)
7. [Django Admin panel](#7-django-admin-panel)
8. [Views — Function-based va Class-based](#8-views--function-based-va-class-based)
9. [URLs — marshrutlash](#9-urls--marshrutlash)
10. [Templates — shablon tizimi](#10-templates--shablon-tizimi)
11. [Forms va ModelForm](#11-forms-va-modelform)
12. [Autentifikatsiya va ruxsatlar](#12-autentifikatsiya-va-ruxsatlar)
13. [Custom User model](#13-custom-user-model)
14. [Middleware](#14-middleware)
15. [Signals](#15-signals)
16. [QuerySet optimallashtirish](#16-queryset-optimallashtirish)
17. [Django REST Framework — API yaratish](#17-django-rest-framework--api-yaratish)
18. [Background Tasks (Django 6.0) va Celery](#18-background-tasks-django-60-va-celery)
19. [Testlash](#19-testlash)
20. [Static va Media fayllar](#20-static-va-media-fayllar)
21. [Xavfsizlik cheklisti](#21-xavfsizlik-cheklisti)
22. [Production: Docker, Gunicorn, Nginx, PostgreSQL](#22-production-docker-gunicorn-nginx-postgresql)
23. [Yakuniy to'liq ishchi misol (Blog ilovasi)](#23-yakuniy-toliq-ishchi-misol-blog-ilovasi)
24. [Foydali manbalar](#24-foydali-manbalar)

---

## 1. Muhitni tayyorlash

**Talablar:** Django 6.0 uchun Python 3.12+, Django 5.2 LTS uchun Python 3.10+ yetarli.

```bash
# Virtual muhit — MAJBURIY odat
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows

# Asosiy kutubxonalar
pip install django django-environ

# Keyinroq kerak bo'ladiganlar (ixtiyoriy, mavzular davomida tushuntiriladi)
pip install djangorestframework Pillow psycopg2-binary gunicorn whitenoise
```

```bash
pip freeze > requirements.txt
```

---

## 2. Loyiha yaratish va professional struktura

```bash
django-admin startproject config .        # "." — joriy papkaga yaratadi (tavsiya etiladi)
python manage.py startapp blog             # har bir mustaqil modul — alohida "app"
```

Kichik loyihada bitta `settings.py` yetarli, lekin **professional loyihada** sozlamalar muhitga (development/production) qarab bo'linadi:

```
myproject/
├── .env                        # Maxfiy sozlamalar — Git'ga qo'shilmaydi
├── .gitignore
├── requirements.txt
├── manage.py
│
├── config/                     # Loyiha "miyasi" — global sozlamalar
│   ├── __init__.py
│   ├── urls.py                  # Bosh URL marshrutizatori
│   ├── wsgi.py / asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py               # Umumiy sozlamalar
│       ├── dev.py                 # Development uchun qo'shimchalar (DEBUG=True)
│       └── prod.py                # Production uchun qo'shimchalar (DEBUG=False)
│
├── apps/                        # Barcha ilovalar shu yerda jamlanadi
│   ├── users/                    # Custom User model, profil
│   ├── blog/                     # Masalan: maqolalar ilovasi
│   │   ├── migrations/
│   │   ├── models.py
│   │   ├── admin.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── serializers.py         # DRF uchun (17-bo'lim)
│   │   └── templates/blog/
│   └── core/                      # Umumiy narsalar: base template, utils
│
├── templates/                    # Global shablonlar (base.html va h.k.)
├── static/                       # Loyiha darajasidagi CSS/JS/rasm
└── media/                        # Foydalanuvchi yuklagan fayllar
```

> 💡 Har bir ilova **bitta mas'uliyat**ga ega bo'lsin: `blog` — faqat maqolalar, `users` — faqat foydalanuvchilar. Bu keyinchalik ilovani boshqa loyihaga ko'chirish yoki jamoa bo'lib ishlashni osonlashtiradi.

---

## 3. MTV arxitektura — Django qanday ishlaydi

Django klassik MVC emas, **MTV** (Model-Template-View) naqshiga amal qiladi:

| Qism | Vazifasi | Klassik MVC muqobili |
|---|---|---|
| **Model** | Ma'lumotlar tuzilishi va DB bilan ishlash (ORM) | Model |
| **Template** | HTML — foydalanuvchiga ko'rinadigan qism | View |
| **View** | Biznes mantiq: so'rovni qabul qiladi, Model'dan ma'lumot oladi, Template'ga uzatadi | Controller |

**So'rov yo'li:** Brauzer → `urls.py` (qaysi view chaqirilishini aniqlaydi) → `views.py` (mantiq, DB so'rovi) → `models.py` (ma'lumot) → `templates/*.html` (natija render qilinadi) → Brauzerga HTML qaytadi.

---

## 4. Sozlamalar (settings) va .env

Tokendan farqli o'laroq, Django'da eng muhim maxfiy narsa — **`SECRET_KEY`** va DB ma'lumotlari. Ularni hech qachon kodga yozmang.

`.env`:
```
DEBUG=True
SECRET_KEY=django-insecure-shu-yerga-uzun-tasodifiy-satr-yoziladi
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/mydb
```

`config/settings/base.py`:
```python
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Uchinchi tomon
    "rest_framework",

    # O'z ilovalarimiz
    "apps.users",
    "apps.blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

AUTH_USER_MODEL = "users.User"   # 13-bo'limga qarang — loyiha boshidanoq belgilash shart

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

`config/settings/dev.py`:
```python
from .base import *  # noqa

DEBUG = True
INTERNAL_IPS = ["127.0.0.1"]
```

`config/settings/prod.py`:
```python
from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

Ishga tushirishda qaysi sozlama faylini ishlatishni ko'rsatish:
```bash
python manage.py runserver --settings=config.settings.dev
```

Yoki `manage.py`da default qilib belgilash mumkin (`os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")`).

---

## 5. Models — ORM chuqur tahlili

Model — Python klassi orqali DB jadvalini tasvirlash. Django ORM SQL yozmasdan DB bilan ishlash imkonini beradi.

```python
# apps/blog/models.py
from django.db import models
from django.conf import settings
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        PUBLISHED = "published", "Chop etilgan"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    image = models.ImageField(upload_to="posts/%Y/%m/", blank=True, null=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts"
    )
    tags = models.ManyToManyField("Tag", blank=True, related_name="posts")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    views_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
```

### Relatsiyalar (bog'lanishlar) jadvali

| Turi | Misol | Ma'nosi |
|---|---|---|
| `ForeignKey` | `Post.author` | Ko'p Post — bitta User (1:N) |
| `ManyToManyField` | `Post.tags` | Ko'p Post — ko'p Tag (M:N) |
| `OneToOneField` | `Profile.user` | Bitta Profile — bitta User (1:1) |

### `on_delete` variantlari

| Qiymat | Xatti-harakat |
|---|---|
| `CASCADE` | Bog'liq obyekt o'chirilsa, bu ham o'chadi |
| `SET_NULL` | Bog'liq obyekt o'chirilsa, maydon `NULL` bo'ladi (`null=True` shart) |
| `PROTECT` | Bog'liq obyekt hali ishlatilayotgan bo'lsa, o'chirishga yo'l qo'ymaydi |
| `SET_DEFAULT` | Standart qiymatga o'rnatiladi |

---

## 6. Migratsiyalar

Model o'zgarganda, DB jadvalini ham shunga moslashtirish kerak — buni **migratsiya** deb ataladi.

```bash
python manage.py makemigrations      # models.py o'zgarishlari asosida migratsiya fayli yaratadi
python manage.py migrate             # migratsiyalarni haqiqiy DB'ga qo'llaydi
python manage.py sqlmigrate blog 0001  # migratsiya qanday SQL ishlatishini ko'rsatadi (debug uchun)
python manage.py showmigrations      # qaysi migratsiyalar qo'llangan/qo'llanmaganini ko'rsatadi
```

> ⚠️ **Muhim odat:** `makemigrations`ni har doim `migrate`dan oldin, kod review'ga tushishidan oldin chaqiring va migratsiya fayllarini Git'ga qo'shing — jamoada ishlashda bu muvofiqlikni ta'minlaydi.

---

## 7. Django Admin panel

Django'ning eng kuchli tomonlaridan biri — bir necha qatorli kod bilan to'liq boshqaruv panelini olish.

```python
# apps/blog/admin.py
from django.contrib import admin
from .models import Post, Category, Tag


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "status", "created_at")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}   # sarlavha yozilganda slug avtomatik generatsiya bo'ladi
    autocomplete_fields = ("author", "category")
    date_hierarchy = "created_at"
    list_per_page = 25


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Tag)
```

Superuser yaratish (admin panelga kirish uchun):
```bash
python manage.py createsuperuser
```

`http://127.0.0.1:8000/admin/` manzilida panel ochiladi.

**Inline** — bog'langan modelni bosh model sahifasida tahrirlash (masalan, `Comment`larni `Post` sahifasida ko'rish):

```python
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1

class PostAdmin(admin.ModelAdmin):
    inlines = [CommentInline]
```

---

## 8. Views — Function-based va Class-based

Django ikkita uslubni qo'llab-quvvatlaydi: **FBV** (oddiy, tushunarli) va **CBV** (qayta ishlatiladigan, kam kod).

### Function-Based View (FBV)

```python
# apps/blog/views.py
from django.shortcuts import render, get_object_or_404
from .models import Post

def post_list(request):
    posts = Post.objects.filter(status=Post.Status.PUBLISHED)
    return render(request, "blog/post_list.html", {"posts": posts})

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    return render(request, "blog/post_detail.html", {"post": post})
```

### Class-Based View (CBV)

```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Post

class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author", "category")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["title", "slug", "body", "category", "tags", "image", "status"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user   # avtomatik joriy foydalanuvchini biriktiradi
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["title", "body", "category", "tags", "image", "status"]
    template_name = "blog/post_form.html"


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("blog:post_list")
```

### Qachon qaysi birini tanlash

| Holat | Tavsiya |
|---|---|
| Oddiy, bir martalik maxsus mantiq | FBV |
| Standart CRUD (List/Detail/Create/Update/Delete) | CBV — kod ancha qisqaradi |
| Ko'p qayta ishlatiladigan umumiy xatti-harakat (masalan, faqat login qilganlar) | CBV + Mixin |

---

## 9. URLs — marshrutlash

```python
# apps/blog/urls.py
from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    # ⚠️ "post/create/" — "post/<slug:slug>/"dan OLDIN turishi shart!
    # Aks holda Django "create" so'zini slug qiymati deb qabul qilib, PostDetailView'ga yuboradi (404 xato).
    path("post/create/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
]
```

> ⚠️ **Umumiy qoida:** URL patternlarida **aniqroq (statik) yo'llarni doim yuqoriga**, dinamik `<slug>`/`<pk>` qabul qiluvchi yo'llarni pastga yozing — Django patternlarni tepadan pastga qarab, birinchi mos kelganini ishlatadi.

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.blog.urls", namespace="blog")),
    path("api/", include("apps.blog.api_urls")),   # 17-bo'lim: DRF
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Dinamik converter turlari:** `<int:pk>`, `<str:name>`, `<slug:slug>`, `<uuid:id>`, `<path:full_path>`.

---

## 10. Templates — shablon tizimi

`templates/base.html`:
```html
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}Mening saytim{% endblock %}</title>
    {% load static %}
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
</head>
<body>
    <nav>
        {% if user.is_authenticated %}
            Salom, {{ user.username }}! <a href="{% url 'logout' %}">Chiqish</a>
        {% else %}
            <a href="{% url 'login' %}">Kirish</a>
        {% endif %}
    </nav>

    {% for message in messages %}
        <div class="alert">{{ message }}</div>
    {% endfor %}

    {% block content %}{% endblock %}
</body>
</html>
```

`apps/blog/templates/blog/post_list.html`:
```html
{% extends "base.html" %}

{% block title %}Barcha maqolalar{% endblock %}

{% block content %}
    <h1>Maqolalar</h1>
    {% for post in posts %}
        <article>
            <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
            <p>{{ post.body|truncatewords:30 }}</p>
            <small>{{ post.created_at|date:"d-M, Y" }} | {{ post.author.username }}</small>
        </article>
    {% empty %}
        <p>Hozircha maqolalar yo'q.</p>
    {% endfor %}

    {% if is_paginated %}
        <div class="pagination">
            {% if page_obj.has_previous %}
                <a href="?page={{ page_obj.previous_page_number }}">⬅️ Oldingi</a>
            {% endif %}
            <span>{{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
            {% if page_obj.has_next %}
                <a href="?page={{ page_obj.next_page_number }}">Keyingi ➡️</a>
            {% endif %}
        </div>
    {% endif %}
{% endblock %}
```

**Eng ko'p ishlatiladigan template tag va filterlar:**

| Belgi | Vazifasi |
|---|---|
| `{% extends %}` / `{% block %}` | Shablon merosxo'rligi |
| `{% if %}` / `{% for %}` | Shart va sikl |
| `{% url 'name' %}` | URL'ni nom orqali generatsiya qilish (hard-code qilmaslik uchun) |
| `{% static 'path' %}` | Static faylga havola |
| `{{ value\|date:"d-m-Y" }}` | Sana formatlash |
| `{{ value\|truncatewords:20 }}` | Matnni qisqartirish |
| `{{ value\|default:"—" }}` | Bo'sh bo'lsa standart qiymat |

Custom template filter yaratish (`apps/blog/templatetags/blog_extras.py`):
```python
from django import template
register = template.Library()

@register.filter
def reading_time(text):
    words = len(text.split())
    return f"{max(1, words // 200)} daqiqa o'qish"
```

Shablonda: `{{ post.body|reading_time }}`

---

## 11. Forms va ModelForm

```python
# apps/blog/forms.py
from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "slug", "body", "category", "tags", "image", "status"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10, "class": "form-control"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) < 5:
            raise forms.ValidationError("Sarlavha kamida 5 ta belgidan iborat bo'lishi kerak.")
        return title
```

FBV bilan ishlatish:
```python
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()  # ManyToMany maydonlarni saqlash uchun (commit=False bo'lganda kerak)
            return redirect(post.get_absolute_url())
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})
```

Shablonda:
```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Saqlash</button>
</form>
```

> ⚠️ `{% csrf_token %}`ni **har doim** `POST` formada unutmang — bu Django'ning CSRF hujumlaridan avtomatik himoyasi.

---

## 12. Autentifikatsiya va ruxsatlar

Django `django.contrib.auth` orqali tayyor login/logout tizimini beradi.

```python
# config/urls.py ga qo'shish
from django.contrib.auth import views as auth_views

urlpatterns += [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
```

**Ro'yxatdan o'tish (registratsiya):**
```python
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView

class SignUpView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
```

**Ruxsatlarni tekshirish:**

```python
from django.contrib.auth.decorators import login_required, permission_required

@login_required                                   # faqat tizimga kirganlar uchun
def dashboard(request):
    ...

@permission_required("blog.add_post", raise_exception=True)  # muayyan ruxsatga ega bo'lganlar
def post_create(request):
    ...
```

CBV uchun mixinlar:
```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class PostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "blog.add_post"
    login_url = "login"
```

Shablonda muallifni tekshirish (faqat o'z postini tahrirlash huquqi):
```html
{% if post.author == user %}
    <a href="{% url 'blog:post_update' post.slug %}">Tahrirlash</a>
{% endif %}
```

---

## 13. Custom User model

Django'ning standart `User` modeli email, telefon kabi qo'shimcha maydonlarga ega emas. **Har qanday yangi loyihada, birinchi migratsiyadan OLDIN**, custom User model yaratish qat'iy tavsiya etiladi — chunki loyiha o'rtasida almashtirish juda qiyin.

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.username
```

`settings/base.py`da:
```python
AUTH_USER_MODEL = "users.User"
```

```python
# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

admin.site.register(User, UserAdmin)
```

---

## 14. Middleware

Middleware — har bir so'rov/javobni "qatlamlar" orqali o'tkazadi (autentifikatsiya, xavfsizlik, sessiya va h.k. aynan shu orqali ishlaydi). O'z middleware'ingizni yozish mumkin:

```python
# apps/core/middleware.py
import time
import logging

logger = logging.getLogger(__name__)

class RequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        response = self.get_response(request)         # keyingi middleware/view chaqiriladi
        duration = time.time() - start
        logger.info(f"{request.path} — {duration:.3f}s")
        return response
```

`settings/base.py`da ro'yxatga qo'shish:
```python
MIDDLEWARE = [
    ...
    "apps.core.middleware.RequestTimeMiddleware",
]
```

> 📌 Middleware ro'yxatidagi **tartib muhim**: so'rov yuqoridan pastga, javob esa pastdan yuqoriga qarab o'tadi.

---

## 15. Signals

Signal — bir hodisa (masalan, obyekt saqlanishi) sodir bo'lganda, boshqa kodni avtomatik ishga tushirish mexanizmi.

```python
# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:   # faqat YANGI foydalanuvchi yaratilganda ishga tushadi
        Profile.objects.create(user=instance)
```

`apps/users/apps.py`da ro'yxatga olish:
```python
from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        import apps.users.signals  # noqa
```

> ⚠️ Signal'larni ehtiyotkorlik bilan ishlating — ular kodni "yashirin" bog'laydi va debug qilishni qiyinlashtiradi. Ko'pincha oddiy `save()` metodini override qilish yoki `form_valid()` ichida aniq yozish yaxshiroq tushunarli bo'ladi.

---

## 16. QuerySet optimallashtirish

Django ORM qulay, lekin ehtiyotsiz ishlatilsa **N+1 muammosi**ga olib keladi (har bir obyekt uchun alohida DB so'rovi).

```python
# ❌ YOMON: har bir post uchun alohida so'rov (N+1)
posts = Post.objects.all()
for post in posts:
    print(post.author.username)   # har safar yangi DB so'rovi!

# ✅ YAXSHI: select_related — ForeignKey/OneToOne uchun (SQL JOIN qiladi)
posts = Post.objects.select_related("author", "category").all()

# ✅ YAXSHI: prefetch_related — ManyToMany/reverse ForeignKey uchun
posts = Post.objects.prefetch_related("tags", "comments").all()
```

**Boshqa foydali usullar:**

```python
from django.db.models import Count, Q, F

# Faqat kerakli maydonlarni olish (katta jadvallarda tezlik uchun)
Post.objects.only("title", "slug")
Post.objects.defer("body")   # aksincha — bitta maydonni chiqarib tashlash

# Agregatsiya
Category.objects.annotate(post_count=Count("posts")).order_by("-post_count")

# Murakkab shartlar (OR mantiqi)
Post.objects.filter(Q(status="published") | Q(author=request.user))

# F() — DB darajasida bitta maydonni boshqasiga solishtirish/yangilash
Post.objects.filter(views_count__gt=F("comments_count"))
Post.objects.update(views_count=F("views_count") + 1)   # race condition'siz hisoblagich

# Indeks qo'yish (models.py Meta ichida, tez-tez filtrlanadigan maydonlarga)
class Meta:
    indexes = [models.Index(fields=["status", "-created_at"])]
```

> 💡 `python manage.py shell`da `from django.db import connection; print(len(connection.queries))` yoki **Django Debug Toolbar** kutubxonasi orqali sahifa nechta SQL so'rov yuborayotganini tekshirib ko'ring — bu optimallashtirish kerak joylarni tez topishga yordam beradi.

---

## 17. Django REST Framework — API yaratish

Mobil ilova yoki frontend (React/Vue) uchun API kerak bo'lsa, **DRF** standart yechim hisoblanadi.

```bash
pip install djangorestframework
```

```python
INSTALLED_APPS += ["rest_framework"]
```

```python
# apps/blog/serializers.py
from rest_framework import serializers
from .models import Post

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "author", "status", "created_at"]
        read_only_fields = ["id", "created_at"]
```

```python
# apps/blog/api_views.py
from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author")
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

```python
# apps/blog/api_urls.py
from rest_framework.routers import DefaultRouter
from .api_views import PostViewSet

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = router.urls
```

`ModelViewSet` bitta klassda **GET (ro'yxat/bitta), POST, PUT, PATCH, DELETE**ning barchasini avtomatik beradi — `/api/posts/` va `/api/posts/<id>/` manzillari darhol ishlay boshlaydi.

---

## 18. Background Tasks (Django 6.0) va Celery

**Django 6.0** o'rnatilgan `django.tasks` modulini taqdim etdi — email yuborish, fayl qayta ishlash kabi uzoq davom etadigan ishlarni so'rov-javob siklidan tashqarida bajarish uchun:

```python
# apps/blog/tasks.py
from django.tasks import task

@task
def send_welcome_email(user_id: int):
    from apps.users.models import User
    user = User.objects.get(id=user_id)
    # email yuborish logikasi...
```

Chaqirish:
```python
send_welcome_email.enqueue(user_id=user.id)   # darhol emas, navbatga qo'yiladi
```

`settings.py`da backend tanlash kerak (masalan, development uchun darhol bajaruvchi):
```python
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    }
}
```

> ⚠️ **Muhim cheklov:** `django.tasks` faqat vazifani **navbatga qo'yish uchun yagona API** beradi — u o'zi worker jarayonini ishga tushirmaydi (immediate backend'dan tashqari). Oddiy email yuborish kabi 80% holatlar uchun yetarli, lekin **murakkab, ko'p bosqichli, kechiktirilgan (scheduled) vazifalar uchun** hamon **Celery + Redis/RabbitMQ** — sinovdan o'tgan, production'da eng ko'p ishlatiladigan yechim.

Celery bilan qisqacha (eslatma sifatida):
```bash
pip install celery redis
```
```python
# config/celery.py
from celery import Celery
app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```
```python
from celery import shared_task

@shared_task
def send_email_task(user_id):
    ...
```

---

## 19. Testlash

```python
# apps/blog/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post

User = get_user_model()

class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="pass12345")
        self.post = Post.objects.create(
            title="Test post", slug="test-post", body="Matn",
            author=self.user, status=Post.Status.PUBLISHED
        )

    def test_post_str(self):
        self.assertEqual(str(self.post), "Test post")

    def test_post_absolute_url(self):
        self.assertEqual(self.post.get_absolute_url(), f"/post/{self.post.slug}/")


class PostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test", password="pass12345")
        self.post = Post.objects.create(
            title="Test", slug="test", body="Matn", author=self.user,
            status=Post.Status.PUBLISHED
        )

    def test_post_list_status_code(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test")

    def test_post_create_requires_login(self):
        response = self.client.get(reverse("blog:post_create"))
        self.assertEqual(response.status_code, 302)   # login sahifasiga redirect
```

```bash
python manage.py test
```

Katta loyihalarda `pytest-django` (qulayroq fixture va parallel test ishga tushirish) tavsiya etiladi.

---

## 20. Static va Media fayllar

| | STATIC | MEDIA |
|---|---|---|
| Nima uchun | CSS, JS, loyihaning o'z rasmlari | Foydalanuvchi yuklagan fayllar (avatar, post rasmi) |
| Sozlama | `STATIC_URL`, `STATICFILES_DIRS`, `STATIC_ROOT` | `MEDIA_URL`, `MEDIA_ROOT` |
| Production'da kim xizmat qiladi | Nginx yoki WhiteNoise | Nginx yoki bulutli saqlash (S3) |

```bash
python manage.py collectstatic   # barcha static fayllarni STATIC_ROOT'ga yig'adi (production deploy oldidan)
```

Production'da Nginx sozlashning iloji bo'lmasa, **WhiteNoise** eng oson yechim:
```bash
pip install whitenoise
```
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # SecurityMiddleware'dan keyin, eng yuqorida
    ...
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

---

## 21. Xavfsizlik cheklisti

- [ ] `SECRET_KEY` `.env`da, hech qachon Git'ga tushmagan
- [ ] Production'da `DEBUG = False` (aks holda xato sahifalarda butun kod va sozlamalar ko'rinib qoladi)
- [ ] `ALLOWED_HOSTS` aniq domenlar bilan to'ldirilgan (`["*"]` emas)
- [ ] `python manage.py check --deploy` production'ga chiqarishdan oldin ishga tushirilgan
- [ ] Barcha `POST` formalarda `{% csrf_token %}` bor
- [ ] SQL so'rovlar faqat ORM orqali (xom SQL kerak bo'lsa, `%s` parametrlash orqali — hech qachon f-string bilan birlashtirish emas)
- [ ] Fayl yuklashda hajm va turi tekshiriladi (`FileExtensionValidator`, `MAX_UPLOAD_SIZE`)
- [ ] `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT` production'da yoqilgan (HTTPS orqali)
- [ ] Parollar `AbstractUser`ning o'zi hash qiladi — hech qachon parolni oddiy matnda saqlamang yoki loglamang
- [ ] Kutubxonalar muntazam yangilanadi (`pip list --outdated`, xavfsizlik yamoqlari uchun)

---

## 22. Production: Docker, Gunicorn, Nginx, PostgreSQL

`Dockerfile`:
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

`docker-compose.yml`:
```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

  web:
    build: .
    env_file: .env
    depends_on:
      - db
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - web

volumes:
  pgdata:
  static_volume:
  media_volume:
```

`nginx.conf` (qisqartirilgan namuna):
```nginx
server {
    listen 80;

    location /static/ {
        alias /app/staticfiles/;
    }
    location /media/ {
        alias /app/media/;
    }
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## 23. Yakuniy to'liq ishchi misol (Blog ilovasi)

Quyidagi fayllar minimal, lekin to'liq ishlaydigan "Blog" ilovasini tashkil qiladi — model, admin, CBV asosidagi CRUD, URL va shablon.

**`apps/blog/models.py`:**
```python
from django.conf import settings
from django.db import models
from django.urls import reverse


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        PUBLISHED = "published", "Chop etilgan"

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    body = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})
```

**`apps/blog/admin.py`:**
```python
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
```

**`apps/blog/views.py`:**
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(status=Post.Status.PUBLISHED).select_related("author")


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["title", "slug", "body", "status"]
    template_name = "blog/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["title", "body", "status"]
    template_name = "blog/post_form.html"


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/post_confirm_delete.html"
    success_url = reverse_lazy("blog:post_list")
```

**`apps/blog/urls.py`:**
```python
from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    path("post/create/", views.PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("post/<slug:slug>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
]
```

**`apps/blog/templates/blog/post_list.html`:**
```html
{% extends "base.html" %}
{% block content %}
    <h1>Maqolalar</h1>
    <a href="{% url 'blog:post_create' %}">➕ Yangi maqola</a>
    {% for post in posts %}
        <article>
            <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
            <small>{{ post.author.username }} — {{ post.created_at|date:"d.m.Y" }}</small>
        </article>
    {% empty %}
        <p>Maqolalar yo'q.</p>
    {% endfor %}
{% endblock %}
```

**`apps/blog/templates/blog/post_detail.html`:**
```html
{% extends "base.html" %}
{% block content %}
    <h1>{{ post.title }}</h1>
    <p>{{ post.body|linebreaks }}</p>
    {% if post.author == user %}
        <a href="{% url 'blog:post_update' post.slug %}">Tahrirlash</a>
        <a href="{% url 'blog:post_delete' post.slug %}">O'chirish</a>
    {% endif %}
{% endblock %}
```

**`apps/blog/templates/blog/post_form.html`:**
```html
{% extends "base.html" %}
{% block content %}
    <h1>Maqola</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Saqlash</button>
    </form>
{% endblock %}
```

**`apps/blog/templates/blog/post_confirm_delete.html`:**
```html
{% extends "base.html" %}
{% block content %}
    <h1>"{{ post.title }}" haqiqatan o'chirilsinmi?</h1>
    <form method="post">
        {% csrf_token %}
        <button type="submit">Ha, o'chirish</button>
    </form>
{% endblock %}
```

Ishga tushirish:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`http://127.0.0.1:8000/` — maqolalar ro'yxati, `/admin/` — boshqaruv paneli.

---

## 24. Foydali manbalar

- Rasmiy hujjat: [docs.djangoproject.com](https://docs.djangoproject.com)
- Django REST Framework: [django-rest-framework.org](https://www.django-rest-framework.org)
- GitHub: [github.com/django/django](https://github.com/django/django)
- Xavfsizlik bo'yicha rasmiy qo'llanma: [docs.djangoproject.com/en/stable/topics/security](https://docs.djangoproject.com/en/stable/topics/security/)

---

Shu qo'llanma asosida kichik loyihadan boshlab (Model → Admin → View → Template), so'ng autentifikatsiya, optimallashtirish, API va nihoyat Docker orqali production'ga chiqarishgacha bo'lgan yo'lni bosqichma-bosqich o'tishingiz mumkin. 🚀
