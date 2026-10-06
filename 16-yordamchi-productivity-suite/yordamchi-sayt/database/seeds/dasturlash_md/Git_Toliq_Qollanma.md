# 📘 Git — To'liq Qo'llanma

> **Muallif uchun:** Bu qo'llanma Git versiya boshqaruv tizimining barcha asosiy va ilg'or komandalarini, tushuntirishlarini va amaliy misollarini o'z ichiga oladi.

---

## 📑 Mundarija

1. [Git nima?](#git-nima)
2. [O'rnatish va sozlash](#ornatish-va-sozlash)
3. [Asosiy tushunchalar](#asosiy-tushunchalar)
4. [Repository yaratish](#repository-yaratish)
5. [Asosiy komandalar](#asosiy-komandalar)
6. [Branch (Tarmoq) bilan ishlash](#branch-tarmoq-bilan-ishlash)
7. [Merge va Rebase](#merge-va-rebase)
8. [Remote repository bilan ishlash](#remote-repository-bilan-ishlash)
9. [Stash — Vaqtincha saqlash](#stash--vaqtincha-saqlash)
10. [Tag — Belgilar](#tag--belgilar)
11. [Log va Tarix](#log-va-tarix)
12. [Diff — Farqlarni ko'rish](#diff--farqlarni-korish)
13. [Reset, Revert, Checkout](#reset-revert-checkout)
14. [Cherry-pick](#cherry-pick)
15. [.gitignore fayli](#gitignore-fayli)
16. [Git Alias — Qisqartmalar](#git-alias--qisqartmalar)
17. [Git Config — Sozlamalar](#git-config--sozlamalar)
18. [Git Hooks](#git-hooks)
19. [Submodule](#submodule)
20. [Git Flow — Ish oqimi](#git-flow--ish-oqimi)
21. [Xatolarni tuzatish](#xatolarni-tuzatish)
22. [GitHub / GitLab bilan ishlash](#github--gitlab-bilan-ishlash)
23. [Foydali maslahatlar](#foydali-maslahatlar)
24. [Barcha komandalar jadvali](#barcha-komandalar-jadvali)

---

## Git nima?

**Git** — bu taqsimlangan versiya boshqaruv tizimi (Distributed Version Control System). U loyihangiz kodining har bir o'zgarishini kuzatib boradi va jamoa bilan hamkorlik qilishni osonlashtiradi.

### Git ning afzalliklari:
- ⚡ **Tezkor** — deyarli barcha operatsiyalar lokal
- 🔀 **Tarmoqlanish (Branching)** — oson va tez
- 🛡️ **Xavfsiz** — har bir o'zgarish SHA-1 hash bilan himoyalangan
- 🌐 **Taqsimlangan** — har bir dasturchi to'liq nusxaga ega
- 🆓 **Bepul va Ochiq kodli**

---

## O'rnatish va sozlash

### O'rnatish

**Windows:**
```bash
# https://git-scm.com/download/win saytidan yuklab oling
# yoki winget orqali:
winget install Git.Git
```


### Versiyani tekshirish
```bash
git --version
# Natija: git version 2.45.0 (misol)
```

### Dastlabki sozlash (Majburiy)
```bash
# Ismingizni sozlang
git config --global user.name "Ismingiz Familiyangiz"

# Email manzilingizni sozlang
git config --global user.email "email@example.com"

# Standart text editorni sozlash
git config --global core.editor "code --wait"   # VS Code uchun
git config --global core.editor "notepad"        # Notepad uchun
git config --global core.editor "vim"            # Vim uchun

# Standart branch nomini sozlash
git config --global init.defaultBranch main

# Rang kodlarini yoqish
git config --global color.ui auto

# Barcha sozlamalarni ko'rish
git config --list
```

---

## Asosiy tushunchalar

### Git ning 3 ta asosiy hududi:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Working         │     │  Staging Area    │     │  Repository      │
│  Directory       │────▶│  (Index)         │────▶│  (.git)          │
│                  │ add │                  │commit│                  │
│  Fayllarni       │     │  Commitga        │     │  Saqlangan       │
│  tahrirlash      │     │  tayyorlash      │     │  tarix           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

| Tushuncha | Tavsifi |
|-----------|---------|
| **Working Directory** | Loyiha papkangiz — fayllarni tahrirlaysiz |
| **Staging Area (Index)** | Keyingi commitga kiritiladigan o'zgarishlar ro'yxati |
| **Repository (.git)** | Git ma'lumotlar bazasi — barcha tarix shu yerda |
| **Commit** | Loyihaning bir lahzadagi "surati" (snapshot) |
| **Branch** | Mustaqil ishlanayotgan tarmoq |
| **HEAD** | Hozirgi joylashuvingiz — qaysi commitda ekanligingiz |
| **Remote** | Masofaviy server (GitHub, GitLab, Bitbucket) |
| **Clone** | Remote repositoryni to'liq nusxalash |
| **Fork** | Boshqa birovning repo nusxasini o'z accountingizga olish |
| **Pull Request (PR)** | O'zgarishlarni asosiy branchga qo'shish so'rovi |
| **Merge** | Ikki branchni birlashtirish |
| **Conflict** | Bir xil faylga turli o'zgarishlar bo'lganda yuzaga keladigan ziddiyat |

---

## Repository yaratish

### Yangi repo yaratish
```bash
# Yangi papka yaratib, Git ni ishga tushirish
mkdir loyiha-nomi
cd loyiha-nomi
git init

# Natija: Initialized empty Git repository in /path/loyiha-nomi/.git/
```

### Mavjud loyihada Git ni boshlash
```bash
cd mavjud-loyiha
git init
```

### Mavjud reponi klonlash
```bash
# HTTPS orqali
git clone https://github.com/foydalanuvchi/repo.git

# SSH orqali
git clone git@github.com:foydalanuvchi/repo.git

# Boshqa nom bilan klonlash
git clone https://github.com/foydalanuvchi/repo.git yangi-nom

# Faqat bitta branchni klonlash
git clone --branch feature-branch --single-branch https://github.com/foydalanuvchi/repo.git

# Sayoz (shallow) klon — faqat oxirgi N ta commit
git clone --depth 1 https://github.com/foydalanuvchi/repo.git
```

---

## Asosiy komandalar

### `git status` — Holatni tekshirish
```bash
# To'liq holat
git status

# Qisqa format
git status -s
# yoki
git status --short

# Natija misoli:
#  M  index.html       (Modified — o'zgartirilgan)
# ?? style.css         (Untracked — yangi fayl)
# A  app.js            (Added — stagingga qo'shilgan)
# D  old.txt           (Deleted — o'chirilgan)
```

### `git add` — Fayllarni staging'ga qo'shish
```bash
# Bitta faylni qo'shish
git add fayl.txt

# Bir necha faylni qo'shish
git add fayl1.txt fayl2.txt fayl3.txt

# Barcha fayllarni qo'shish
git add .
# yoki
git add -A
# yoki
git add --all

# Faqat o'zgartirilgan fayllarni qo'shish (yangilarni emas)
git add -u

# Pattern bo'yicha qo'shish
git add *.js          # Barcha .js fayllar
git add src/          # src papkasidagi barcha fayllar

# Interaktiv qo'shish (qism-qism)
git add -p
# yoki
git add --patch
# Variantlar: y(ha), n(yo'q), s(bo'l), q(chiqish)
```

### `git commit` — O'zgarishlarni saqlash
```bash
# Xabar bilan commit
git commit -m "Birinchi commit: loyiha boshlandi"

# Ko'p qatorli xabar
git commit -m "Sarlavha" -m "Batafsil tavsif bu yerda"

# add + commit birgalikda (faqat kuzatilayotgan fayllar uchun)
git commit -am "O'zgarishlar saqlandi"

# Oxirgi commitni o'zgartirish (xabarni yoki fayllarni)
git commit --amend -m "Yangilangan commit xabari"

# Oxirgi commitga fayl qo'shish (xabarni o'zgartirmasdan)
git add unutilgan-fayl.txt
git commit --amend --no-edit

# Bo'sh commit yaratish
git commit --allow-empty -m "Bo'sh commit"

# Muallif bilan commit
git commit --author="Ism <email@example.com>" -m "Xabar"
```

### `git rm` — Fayllarni o'chirish
```bash
# Faylni Git va diskdan o'chirish
git rm fayl.txt

# Faqat Git dan o'chirish (diskda qoldirish)
git rm --cached fayl.txt

# Papkani rekursiv o'chirish
git rm -r papka/

# Majburiy o'chirish
git rm -f fayl.txt
```

### `git mv` — Faylni ko'chirish / nomini o'zgartirish
```bash
# Nomini o'zgartirish
git mv eski-nom.txt yangi-nom.txt

# Boshqa papkaga ko'chirish
git mv fayl.txt papka/fayl.txt
```

---

## Branch (Tarmoq) bilan ishlash

### Branch nima?

Branch — bu loyihaning mustaqil ishlanadigan tarmog'i. Har bir branch o'z commitlar tarixiga ega.

```
          feature-branch
         /              \
main ──●──●──●──●──●──●──●──● (merge)
              \        /
               bugfix
```

### Branch komandalar

```bash
# ─── Ro'yxat ───

# Lokal branchlarni ko'rish
git branch

# Barcha branchlarni ko'rish (lokal + remote)
git branch -a

# Remote branchlarni ko'rish
git branch -r

# Branchlarni oxirgi commit bilan ko'rish
git branch -v

# Merge qilingan branchlarni ko'rish
git branch --merged

# Merge qilinmagan branchlarni ko'rish
git branch --no-merged

# ─── Yaratish ───

# Yangi branch yaratish
git branch feature-login

# Yangi branch yaratib, unga o'tish
git checkout -b feature-login
# yoki (yangi usul)
git switch -c feature-login

# Remote branchdan lokal branch yaratish
git checkout -b feature-login origin/feature-login
# yoki
git switch -c feature-login --track origin/feature-login

# Muayyan commitdan branch yaratish
git branch yangi-branch abc1234

# ─── O'tish ───

# Branchga o'tish
git checkout feature-login
# yoki (yangi usul)
git switch feature-login

# Oldingi branchga qaytish
git checkout -
# yoki
git switch -

# ─── Nomini o'zgartirish ───

# Hozirgi branchni qayta nomlash
git branch -m yangi-nom

# Boshqa branchni qayta nomlash
git branch -m eski-nom yangi-nom

# ─── O'chirish ───

# Lokal branchni o'chirish (merge qilingan bo'lsa)
git branch -d feature-login

# Majburiy o'chirish (merge qilinmagan bo'lsa ham)
git branch -D feature-login

# Remote branchni o'chirish
git push origin --delete feature-login
# yoki
git push origin :feature-login
```

---

## Merge va Rebase

### Merge — Birlashtirish

```bash
# Avval asosiy branchga o'ting
git checkout main

# Feature branchni merge qiling
git merge feature-login

# Merge xabari bilan
git merge feature-login -m "Feature login qo'shildi"

# Fast-forward merge (chiziqli tarix)
git merge --ff-only feature-login

# No fast-forward (har doim merge commit yaratish)
git merge --no-ff feature-login

# Merge ni bekor qilish (conflict paytida)
git merge --abort

# Squash merge (barcha commitlarni bitta qilib)
git merge --squash feature-login
git commit -m "Feature login: barcha o'zgarishlar"
```

### Merge Conflict hal qilish

```bash
# Conflict bo'lganda fayl quyidagicha ko'rinadi:
# <<<<<<< HEAD
# Sizning kodingiz (hozirgi branch)
# =======
# Boshqa branchdagi kod
# >>>>>>> feature-login

# 1. Conflictli faylni oching va qo'lda tahrirlang
# 2. Marker'larni (<<<<, ====, >>>>) o'chiring
# 3. Kerakli kodni qoldiring
# 4. Staging'ga qo'shing
git add conflict-fayl.txt
# 5. Commit qiling
git commit -m "Merge conflict hal qilindi"
```

### Rebase — Tarixni qayta qurish

```bash
# Feature branchda turib, main dagi yangilanishlarni olish
git checkout feature-login
git rebase main

# Interaktiv rebase (oxirgi 3 ta commitni tahrirlash)
git rebase -i HEAD~3
# Variantlar:
# pick   — commitni qoldirish
# reword — commit xabarini o'zgartirish
# edit   — commitni tahrirlash
# squash — oldingi commit bilan birlashtirish
# fixup  — squash kabi, lekin xabarni tashlab yuborish
# drop   — commitni o'chirish

# Rebase ni bekor qilish
git rebase --abort

# Conflict hal qilib davom ettirish
git rebase --continue

# Commitni o'tkazib yuborish
git rebase --skip
```

> ⚠️ **Ogohlantirish:** Ommaviy (push qilingan) branchlarda `rebase` ishlatmang! Bu tarixni o'zgartiradi va boshqa dasturchilarga muammo tug'diradi.

---

## Remote repository bilan ishlash

### Remote sozlash

```bash
# Remote ro'yxatini ko'rish
git remote
git remote -v   # URL bilan

# Remote qo'shish
git remote add origin https://github.com/user/repo.git

# Bir necha remote qo'shish
git remote add upstream https://github.com/original/repo.git

# Remote URL ni o'zgartirish
git remote set-url origin https://github.com/user/yangi-repo.git

# Remote nomini o'zgartirish
git remote rename origin boshqa-nom

# Remote ni o'chirish
git remote remove origin
```

### Push — Yuborish

```bash
# O'zgarishlarni remote ga yuborish
git push origin main

# Birinchi marta push (upstream sozlash)
git push -u origin main
# Keyingi safar shunchaki:
git push

# Barcha branchlarni push qilish
git push --all origin

# Taglarni push qilish
git push --tags

# Majburiy push (ehtiyot bo'ling!)
git push --force origin main
# yoki xavfsizroq variant:
git push --force-with-lease origin main

# Remote branchni o'chirish
git push origin --delete feature-branch
```

### Pull — Olish

```bash
# Remote dan o'zgarishlarni olish va merge qilish
git pull origin main

# Rebase bilan pull (chiziqli tarix uchun)
git pull --rebase origin main

# Barcha remote dan pull
git pull --all
```

### Fetch — Yuklab olish (merge qilmasdan)

```bash
# Barcha remote ma'lumotlarni yuklab olish
git fetch origin

# Barcha remote lardan fetch
git fetch --all

# O'chirilgan remote branchlarni tozalash
git fetch --prune

# Muayyan branchni fetch qilish
git fetch origin feature-branch
```

---

## Stash — Vaqtincha saqlash

Stash — bu hozirgi o'zgarishlarni vaqtincha saqlab, toza working directory olish imkonini beradi.

```bash
# O'zgarishlarni stash ga saqlash
git stash
# yoki xabar bilan
git stash save "Login sahifasidagi o'zgarishlar"
# yoki (yangi usul)
git stash push -m "Login sahifasidagi o'zgarishlar"

# Untracked fayllarni ham stash ga olish
git stash -u
# yoki
git stash --include-untracked

# Barcha fayllarni (ignored ham) stash ga olish
git stash -a

# Stash ro'yxatini ko'rish
git stash list
# Natija:
# stash@{0}: On main: Login sahifasidagi o'zgarishlar
# stash@{1}: WIP on feature: abc1234 Commit xabari

# Oxirgi stash ni qaytarish va o'chirish
git stash pop

# Muayyan stash ni qaytarish va o'chirish
git stash pop stash@{1}

# Stash ni qaytarish (o'chirmasdan)
git stash apply
git stash apply stash@{1}

# Stash tarkibini ko'rish
git stash show
git stash show -p            # To'liq diff
git stash show stash@{1}

# Bitta stash ni o'chirish
git stash drop stash@{0}

# Barcha stash larni tozalash
git stash clear

# Stash dan yangi branch yaratish
git stash branch yangi-branch stash@{0}
```

---

## Tag — Belgilar

Tag'lar muhim nuqtalarni (relizlarni) belgilash uchun ishlatiladi.

```bash
# ─── Lightweight Tag ───

# Oddiy tag yaratish
git tag v1.0.0

# ─── Annotated Tag (tavsiya etiladi) ───

# Xabar bilan tag yaratish
git tag -a v1.0.0 -m "Birinchi stabil reliz"

# Muayyan commitga tag qo'yish
git tag -a v1.0.0 abc1234 -m "Eski commitga tag"

# ─── Ro'yxat ───

# Barcha taglarni ko'rish
git tag
git tag -l

# Pattern bilan filtrlash
git tag -l "v1.*"

# Tag ma'lumotlarini ko'rish
git show v1.0.0

# ─── Push ───

# Bitta tagni push qilish
git push origin v1.0.0

# Barcha taglarni push qilish
git push origin --tags

# ─── O'chirish ───

# Lokal tagni o'chirish
git tag -d v1.0.0

# Remote tagni o'chirish
git push origin --delete v1.0.0
# yoki
git push origin :refs/tags/v1.0.0

# ─── Checkout ───

# Tagga o'tish (detached HEAD)
git checkout v1.0.0

# Tagdan branch yaratish
git checkout -b hotfix-branch v1.0.0
```

---

## Log va Tarix

```bash
# ─── Asosiy log ───

git log

# Qisqa format
git log --oneline

# Oxirgi N ta commit
git log -5

# ─── Chiroyli formatlar ───

# Graph ko'rinishi
git log --oneline --graph --all --decorate

# Batafsil format
git log --pretty=format:"%h - %an, %ar : %s"

# Statistik bilan
git log --stat

# O'zgarishlar bilan (diff)
git log -p

# ─── Filtrlash ───

# Muallif bo'yicha
git log --author="Ism"

# Sana bo'yicha
git log --after="2024-01-01"
git log --before="2024-12-31"
git log --after="2024-01-01" --before="2024-06-30"

# Xabar bo'yicha qidirish
git log --grep="bugfix"

# Fayl bo'yicha
git log -- fayl.txt

# Branch farqlari
git log main..feature

# ─── Boshqa log komandalar ───

# Qisqa log
git shortlog

# Muallif bo'yicha guruhlangan
git shortlog -s -n

# Referenslar logi (barcha harakatlar)
git reflog

# Faylning har bir qatorini kim o'zgartirganini ko'rish
git blame fayl.txt

# Muayyan qatorlarni ko'rish
git blame -L 10,20 fayl.txt
```

### Chiroyli log alias (tavsiya)

```bash
git config --global alias.lg "log --oneline --graph --all --decorate --color"
# Keyin:
git lg
```

---

## Diff — Farqlarni ko'rish

```bash
# Working directory va staging orasidagi farq
git diff

# Staging va oxirgi commit orasidagi farq
git diff --staged
# yoki
git diff --cached

# Ikki commit orasidagi farq
git diff abc1234 def5678

# Ikki branch orasidagi farq
git diff main..feature-login

# Muayyan faylning farqi
git diff fayl.txt
git diff --staged fayl.txt

# Faqat o'zgargan fayl nomlarini ko'rish
git diff --name-only

# Statistik (qo'shilgan/o'chirilgan qatorlar soni)
git diff --stat

# So'z darajasida farq
git diff --word-diff
```

---

## Reset, Revert, Checkout

### `git reset` — Qaytarish

```bash
# ─── Soft Reset ───
# Commitni bekor qilish, o'zgarishlar staging da qoladi
git reset --soft HEAD~1

# ─── Mixed Reset (standart) ───
# Commitni bekor qilish, o'zgarishlar working directory da qoladi
git reset HEAD~1
# yoki
git reset --mixed HEAD~1

# ─── Hard Reset ───
# Commitni va barcha o'zgarishlarni butunlay o'chirish
git reset --hard HEAD~1

# ⚠️ EHTIYOT BO'LING! Hard reset o'zgarishlarni qaytarib bo'lmas qiladi!

# Muayyan commitga qaytish
git reset --hard abc1234

# Faylni staging dan chiqarish
git reset HEAD fayl.txt
# yoki (yangi usul)
git restore --staged fayl.txt
```

### `git revert` — Xavfsiz qaytarish

```bash
# Commitni bekor qiluvchi YANGI commit yaratish
git revert abc1234

# Bir necha commitni revert qilish
git revert abc1234 def5678

# Commit oralig'ini revert qilish
git revert abc1234..def5678

# Merge commitni revert qilish
git revert -m 1 abc1234

# Avtomatik commit qilmasdan revert
git revert --no-commit abc1234
```

> 💡 **Reset vs Revert:**
> - `reset` — tarixni o'zgartiradi (xavfli, ommaviy branchlarda ishlatmang)
> - `revert` — yangi commit yaratadi (xavfsiz, ommaviy branchlarda ishlatish mumkin)

### `git restore` — Fayllarni tiklash (Git 2.23+)

```bash
# Working directory dagi o'zgarishlarni bekor qilish
git restore fayl.txt

# Staging dan chiqarish
git restore --staged fayl.txt

# Muayyan commitdagi holatga qaytarish
git restore --source=abc1234 fayl.txt
```

---

## Cherry-pick

Muayyan commitni boshqa branchga ko'chirish.

```bash
# Bitta commitni ko'chirish
git cherry-pick abc1234

# Bir necha commitni ko'chirish
git cherry-pick abc1234 def5678

# Commit qilmasdan (faqat o'zgarishlarni olish)
git cherry-pick --no-commit abc1234

# Conflict bo'lganda davom ettirish
git cherry-pick --continue

# Bekor qilish
git cherry-pick --abort
```

---

## .gitignore fayli

`.gitignore` fayli Git ga qaysi fayllarni kuzatmaslikni aytadi.

### Sintaksis

```gitignore
# Bu izoh

# Muayyan faylni e'tiborsiz qoldirish
secret.txt
config.local.json

# Kengaytma bo'yicha
*.log
*.tmp
*.cache
*.exe
*.dll

# Papkani e'tiborsiz qoldirish
node_modules/
dist/
build/
.env/
__pycache__/
.vscode/
.idea/

# Papka ichidagi muayyan fayllar
logs/*.log

# Rekursiv (barcha ichki papkalarda)
**/temp/
**/*.pyc

# Inkor qilish (kuzatishga qaytarish)
!important.log
!.gitkeep

# Ildiz papkadagi fayl (ichki papkalardagi emas)
/TODO.txt
```

### Tez-tez ishlatiladigan .gitignore shablonlar

```gitignore
# ═══ Node.js ═══
node_modules/
npm-debug.log
yarn-error.log
.env
.env.local

# ═══ Python ═══
__pycache__/
*.py[cod]
*.egg-info/
dist/
venv/
.env

# ═══ Java ═══
*.class
*.jar
target/
.gradle/

# ═══ IDE ═══
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# ═══ OS ═══
.DS_Store
Thumbs.db
desktop.ini
```

### Global .gitignore
```bash
# Global gitignore faylini yaratish
git config --global core.excludesfile ~/.gitignore_global
```

### Allaqachon kuzatilayotgan faylni gitignore ga qo'shish
```bash
# Avval Git dan o'chirish (diskda qoldirish)
git rm --cached fayl.txt
# Keyin .gitignore ga qo'shing
echo "fayl.txt" >> .gitignore
git add .gitignore
git commit -m "fayl.txt gitignore ga qo'shildi"
```

---

## Git Alias — Qisqartmalar

```bash
# Alias yaratish
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage "reset HEAD --"
git config --global alias.last "log -1 HEAD"
git config --global alias.lg "log --oneline --graph --all --decorate"
git config --global alias.visual "!gitk"

# Alias ishlatish
git co main        # = git checkout main
git br             # = git branch
git ci -m "xabar"  # = git commit -m "xabar"
git st             # = git status
git lg             # = chiroyli log

# Alias ro'yxatini ko'rish
git config --get-regexp alias

# Alias o'chirish
git config --global --unset alias.co
```

---

## Git Config — Sozlamalar

```bash
# ─── Darajalar ───

# System (barcha foydalanuvchilar uchun)
git config --system setting.name value

# Global (hozirgi foydalanuvchi uchun)
git config --global setting.name value

# Local (faqat hozirgi repo uchun)
git config --local setting.name value

# ─── Foydali sozlamalar ───

# Qator oxiri sozlamasi (Windows uchun muhim)
git config --global core.autocrlf true    # Windows
git config --global core.autocrlf input   # Mac/Linux

# Push strategiyasi
git config --global push.default current

# Pull strategiyasi
git config --global pull.rebase true

# Merge vositasi
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait --merge $REMOTE $LOCAL $BASE $MERGED'

# Diff vositasi
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'

# Credential helper (parolni saqlash)
git config --global credential.helper store     # Faylda saqlash
git config --global credential.helper cache     # 15 daqiqa cache
git config --global credential.helper 'cache --timeout=3600'  # 1 soat

# ─── Ko'rish ───

git config --list                    # Barcha sozlamalar
git config --list --show-origin      # Qaysi fayldan kelganini ko'rsatish
git config user.name                 # Muayyan sozlamani ko'rish

# ─── Tahrirlash ───

git config --global --edit           # Global config faylini ochish
```

---

## Git Hooks

Hooks — bu Git hodisalariga bog'langan avtomatik ishga tushadigan skriptlar.

### Hook fayllari joylashuvi
```
.git/hooks/
├── pre-commit          # Commit oldidan
├── prepare-commit-msg  # Commit xabari tayyorlanayotganda
├── commit-msg          # Commit xabari yozilgandan keyin
├── post-commit         # Commitdan keyin
├── pre-push            # Push oldidan
├── post-merge          # Merge dan keyin
├── pre-rebase          # Rebase oldidan
└── post-checkout       # Checkout dan keyin
```

### Hook misoli — Pre-commit

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Testlarni ishga tushirish
echo "Testlar ishga tushirilmoqda..."
npm test

# Agar test muvaffaqiyatsiz bo'lsa, commit ni to'xtatish
if [ $? -ne 0 ]; then
    echo "❌ Testlar muvaffaqiyatsiz! Commit bekor qilindi."
    exit 1
fi

echo "✅ Barcha testlar o'tdi!"
```

### Hook misoli — Commit-msg

```bash
#!/bin/sh
# .git/hooks/commit-msg

# Commit xabari uzunligini tekshirish
MSG=$(cat "$1")
if [ ${#MSG} -lt 10 ]; then
    echo "❌ Commit xabari kamida 10 ta belgidan iborat bo'lishi kerak!"
    exit 1
fi
```

> 💡 **Maslahat:** Jamoaviy hook'lar uchun [Husky](https://typicode.github.io/husky/) yoki [pre-commit](https://pre-commit.com/) vositalarini ishlating.

---

## Submodule

Submodule — bu boshqa Git repositoryni o'z loyihangiz ichiga kiritish.

```bash
# Submodule qo'shish
git submodule add https://github.com/user/library.git libs/library

# Submodule bilan klonlash
git clone --recurse-submodules https://github.com/user/repo.git

# Mavjud klonda submodule larni yuklash
git submodule init
git submodule update
# yoki birgalikda:
git submodule update --init --recursive

# Submodule larni yangilash
git submodule update --remote

# Submodule ni o'chirish
git submodule deinit libs/library
git rm libs/library
rm -rf .git/modules/libs/library

# Submodule ro'yxati
git submodule status
```

---

## Git Flow — Ish oqimi

### Asosiy Git Flow modeli

```
main (production)
│
├── develop (rivojlantirish)
│   │
│   ├── feature/login     (yangi funksiya)
│   ├── feature/dashboard  (yangi funksiya)
│   │
│   └── release/v1.0      (reliz tayyorlash)
│
└── hotfix/critical-bug    (shoshilinch tuzatish)
```

### Branch turlari

| Branch | Maqsad | Qayerdan | Qayerga |
|--------|--------|----------|---------|
| `main` | Production kod | — | — |
| `develop` | Rivojlantirish | main | main |
| `feature/*` | Yangi funksiya | develop | develop |
| `release/*` | Reliz tayyorlash | develop | main + develop |
| `hotfix/*` | Shoshilinch tuzatish | main | main + develop |

### Amaliy misol

```bash
# ─── Feature boshlash ───
git checkout develop
git pull origin develop
git checkout -b feature/login

# ... kod yozish ...
git add .
git commit -m "feat: login sahifasi yaratildi"
git commit -m "feat: autentifikatsiya qo'shildi"

# Feature ni tugallash
git checkout develop
git merge --no-ff feature/login
git branch -d feature/login
git push origin develop

# ─── Release tayyorlash ───
git checkout develop
git checkout -b release/v1.0

# ... versiya raqamlarini yangilash, bugfix ...
git commit -m "chore: v1.0 uchun versiya yangilandi"

# Release ni tugallash
git checkout main
git merge --no-ff release/v1.0
git tag -a v1.0.0 -m "Versiya 1.0.0"
git checkout develop
git merge --no-ff release/v1.0
git branch -d release/v1.0
git push origin main develop --tags

# ─── Hotfix ───
git checkout main
git checkout -b hotfix/critical-bug

# ... tuzatish ...
git commit -m "fix: kritik xato tuzatildi"

git checkout main
git merge --no-ff hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git checkout develop
git merge --no-ff hotfix/critical-bug
git branch -d hotfix/critical-bug
git push origin main develop --tags
```

### Commit xabarlari konvensiyasi (Conventional Commits)

```
<tur>[qo'shimcha maydon]: <tavsif>

[ixtiyoriy tana]

[ixtiyoriy izoh]
```

| Tur | Tavsif |
|-----|--------|
| `feat` | Yangi funksiya |
| `fix` | Xato tuzatish |
| `docs` | Hujjat o'zgarishi |
| `style` | Kod formatlash (mantiq o'zgarmaydi) |
| `refactor` | Kod qayta tuzilishi |
| `test` | Test qo'shish/o'zgartirish |
| `chore` | Build, tool, yordamchi o'zgarishlar |
| `perf` | Ishlash samaradorligini oshirish |
| `ci` | CI/CD o'zgarishlari |
| `build` | Build tizimi o'zgarishlari |
| `revert` | Oldingi commitni qaytarish |

**Misollar:**
```
feat: foydalanuvchi ro'yxatdan o'tish funksiyasi qo'shildi
fix: login sahifasidagi xatolik tuzatildi
docs: README yangilandi
style: kod formatlandi (prettier)
refactor: autentifikatsiya moduli qayta yozildi
test: login uchun unit testlar qo'shildi
chore: eslint konfiguratsiyasi yangilandi
feat!: API v2 ga o'tildi (breaking change)
```

---

## Xatolarni tuzatish

### Tez-tez uchraydigan xatolar va yechimlari

```bash
# ─── Oxirgi commit xabarini o'zgartirish ───
git commit --amend -m "To'g'ri xabar"

# ─── Noto'g'ri branchga commit qildim ───
# 1. Commitni olish
git log --oneline -1  # commit hash ni yozing
# 2. Commitni bekor qilish (o'zgarishlar saqlanadi)
git reset --soft HEAD~1
# 3. To'g'ri branchga o'tish
git stash
git checkout to'g'ri-branch
git stash pop
git add .
git commit -m "Xabar"

# ─── Push qilingan commitni qaytarish ───
git revert abc1234
git push

# ─── Faylni oxirgi commit holatiga qaytarish ───
git checkout -- fayl.txt
# yoki (yangi usul)
git restore fayl.txt

# ─── Staging dan chiqarish ───
git reset HEAD fayl.txt
# yoki
git restore --staged fayl.txt

# ─── O'chirilgan branchni tiklash ───
git reflog  # kerakli commit ni toping
git checkout -b tiklangan-branch abc1234

# ─── O'chirilgan commitni tiklash ───
git reflog  # kerakli commit ni toping
git reset --hard abc1234

# ─── Barcha lokal o'zgarishlarni bekor qilish ───
git checkout -- .
# yoki
git restore .

# ─── Untracked fayllarni o'chirish ───
git clean -n          # Nima o'chirilishini ko'rish (dry run)
git clean -f          # Fayllarni o'chirish
git clean -fd         # Fayl va papkalarni o'chirish
git clean -fdx        # Ignored fayllarni ham o'chirish

# ─── Detached HEAD holatidan chiqish ───
git checkout main
# yoki yangi branch yaratish
git checkout -b yangi-branch

# ─── "fatal: refusing to merge unrelated histories" ───
git pull origin main --allow-unrelated-histories

# ─── Large file xatoligi ───
# Git LFS o'rnatish
git lfs install
git lfs track "*.psd"
git lfs track "*.zip"
git add .gitattributes
```

---

## GitHub / GitLab bilan ishlash

### SSH kalitlarini sozlash

```bash
# SSH kalit yaratish
ssh-keygen -t ed25519 -C "email@example.com"

# SSH agentni ishga tushirish
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Ochiq kalitni nusxalash
cat ~/.ssh/id_ed25519.pub
# Bu kalitni GitHub/GitLab Settings > SSH Keys ga qo'shing

# Ulanishni tekshirish
ssh -T git@github.com
ssh -T git@gitlab.com
```

### GitHub CLI (gh)

```bash
# O'rnatish
winget install GitHub.cli     # Windows
brew install gh               # macOS

# Tizimga kirish
gh auth login

# Repo yaratish
gh repo create loyiha-nomi --public --source=. --remote=origin

# Pull Request yaratish
gh pr create --title "Feature: Login" --body "Login sahifasi qo'shildi"

# PR ro'yxati
gh pr list

# PR ni merge qilish
gh pr merge 1

# Issue yaratish
gh issue create --title "Bug: Login xatosi" --body "Tavsif..."

# Issue ro'yxati
gh issue list
```

### Fork va Pull Request ish oqimi

```bash
# 1. Reponi fork qiling (GitHub UI orqali)

# 2. Fork ni klonlang
git clone https://github.com/SIZNING_USER/repo.git
cd repo

# 3. Upstream qo'shing
git remote add upstream https://github.com/ORIGINAL_USER/repo.git

# 4. Yangi branch yarating
git checkout -b feature/yangi-funksiya

# 5. O'zgarishlar qiling va commit qiling
git add .
git commit -m "feat: yangi funksiya qo'shildi"

# 6. Fork ga push qiling
git push origin feature/yangi-funksiya

# 7. GitHub da Pull Request yarating

# 8. Upstream bilan sinxronizatsiya
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## Foydali maslahatlar

### 1. Bisect — Xatoni topish

```bash
# Xato qaysi commitda paydo bo'lganini topish
git bisect start
git bisect bad              # Hozirgi commit — xato bor
git bisect good abc1234     # Bu commit — xato yo'q

# Git har bir qadamda commitga o'tadi
# Har bir commitni tekshirib:
git bisect good    # Bu commitda xato yo'q
# yoki
git bisect bad     # Bu commitda xato bor

# Natija: birinchi "bad" commit topiladi

# Tugallash
git bisect reset
```

### 2. Worktree — Bir necha working directory

```bash
# Yangi worktree yaratish
git worktree add ../feature-branch feature-branch

# Worktree ro'yxati
git worktree list

# Worktree o'chirish
git worktree remove ../feature-branch
```

### 3. Archive — Loyihani arxivlash

```bash
# ZIP arxiv yaratish
git archive --format=zip --output=loyiha.zip HEAD

# TAR arxiv
git archive --format=tar.gz --output=loyiha.tar.gz HEAD

# Muayyan papkani arxivlash
git archive --format=zip --output=src.zip HEAD src/
```

### 4. Grep — Kod ichidan qidirish

```bash
# Kod ichidan qidirish
git grep "function"

# Katta-kichik harfni e'tiborsiz qoldirish
git grep -i "todo"

# Qator raqami bilan
git grep -n "TODO"

# Faqat fayl nomlarini ko'rsatish
git grep -l "import"
```

### 5. Foydalanishda qulay buyruqlar

```bash
# Oxirgi 5 ta o'zgartirilgan faylni ko'rish
git log --oneline --name-only -5

# Barcha kuzatilayotgan fayllar ro'yxati
git ls-files

# Repo hajmi
git count-objects -vH

# Eng ko'p commit qilgan mualliflar
git shortlog -s -n --all

# Ikki sana orasidagi commitlar soni
git log --after="2024-01-01" --before="2024-12-31" --oneline | wc -l

# O'zgarishlarni vaqtincha saqlamasdan branch almashish
git stash && git checkout boshqa-branch && git stash pop
```

---

## Barcha komandalar jadvali

### 🟢 Asosiy komandalar

| Komanda | Tavsif |
|---------|--------|
| `git init` | Yangi repository yaratish |
| `git clone <url>` | Repository nusxalash |
| `git status` | Holat tekshirish |
| `git add <fayl>` | Faylni staging ga qo'shish |
| `git add .` | Barcha fayllarni staging ga qo'shish |
| `git commit -m "xabar"` | O'zgarishlarni saqlash |
| `git push` | Remote ga yuborish |
| `git pull` | Remote dan olish |
| `git fetch` | Remote ma'lumotlarni yuklash |

### 🔵 Branch komandalar

| Komanda | Tavsif |
|---------|--------|
| `git branch` | Branchlar ro'yxati |
| `git branch <nom>` | Yangi branch yaratish |
| `git checkout <branch>` | Branchga o'tish |
| `git switch <branch>` | Branchga o'tish (yangi) |
| `git checkout -b <nom>` | Yaratib o'tish |
| `git switch -c <nom>` | Yaratib o'tish (yangi) |
| `git branch -d <nom>` | Branch o'chirish |
| `git branch -D <nom>` | Majburiy o'chirish |
| `git merge <branch>` | Branchni birlashtirish |
| `git rebase <branch>` | Tarixni qayta qurish |

### 🟡 Remote komandalar

| Komanda | Tavsif |
|---------|--------|
| `git remote -v` | Remote ro'yxati |
| `git remote add <nom> <url>` | Remote qo'shish |
| `git push -u origin main` | Push + upstream |
| `git push --force-with-lease` | Xavfsiz force push |
| `git fetch --all` | Barcha remote lardan fetch |
| `git pull --rebase` | Rebase bilan pull |

### 🟠 Tarix komandalar

| Komanda | Tavsif |
|---------|--------|
| `git log` | Commit tarixi |
| `git log --oneline` | Qisqa log |
| `git log --graph` | Grafik log |
| `git reflog` | Barcha harakatlar tarixi |
| `git blame <fayl>` | Fayl tarixini ko'rish |
| `git diff` | Farqlarni ko'rish |
| `git show <commit>` | Commit tafsilotlari |

### 🔴 Qaytarish komandalar

| Komanda | Tavsif |
|---------|--------|
| `git reset --soft HEAD~1` | Yumshoq qaytarish |
| `git reset --hard HEAD~1` | Qattiq qaytarish |
| `git revert <commit>` | Xavfsiz qaytarish |
| `git restore <fayl>` | Faylni tiklash |
| `git restore --staged <fayl>` | Staging dan chiqarish |
| `git checkout -- <fayl>` | Eski usulda tiklash |
| `git clean -fd` | Untracked fayllarni o'chirish |

### 🟣 Qo'shimcha komandalar

| Komanda | Tavsif |
|---------|--------|
| `git stash` | Vaqtincha saqlash |
| `git stash pop` | Stash ni qaytarish |
| `git tag <nom>` | Tag yaratish |
| `git cherry-pick <commit>` | Commitni ko'chirish |
| `git bisect` | Xato qidirish |
| `git worktree add` | Qo'shimcha worktree |
| `git submodule add <url>` | Submodule qo'shish |
| `git archive` | Loyihani arxivlash |
| `git grep <pattern>` | Kod ichidan qidirish |

---

## Tez-tez beriladigan savollar (FAQ)

### `merge` va `rebase` — qaysi biri yaxshi?
- **Merge** — tarixni saqlab qoladi, jamoada ishlaganda xavfsiz
- **Rebase** — toza, chiziqli tarix yaratadi, lekin ommaviy branchlarda ishlatmang

### `reset` va `revert` — farqi nima?
- **Reset** — tarixni o'zgartiradi, faqat lokal branchda ishlating
- **Revert** — yangi commit yaratadi, ommaviy branchda xavfsiz

### `fetch` va `pull` — farqi nima?
- **Fetch** — remote ma'lumotlarni yuklab oladi, MERGE qilmaydi
- **Pull** — fetch + merge ni birgalikda bajaradi

### `.git` papkasini o'chirsam nima bo'ladi?
- Barcha Git tarixi, branchlar, commitlar yo'qoladi
- Fayllaringiz saqlanadi, lekin repo endi oddiy papka bo'ladi

---

## Foydali resurslar

| Resurs | Havola |
|--------|--------|
| Git rasmiy sayti | https://git-scm.com |
| Git hujjatlari | https://git-scm.com/doc |
| Pro Git kitobi (bepul) | https://git-scm.com/book |
| GitHub hujjatlari | https://docs.github.com |
| GitLab hujjatlari | https://docs.gitlab.com |
| Git cheatsheet | https://education.github.com/git-cheat-sheet-education.pdf |
| Oh Shit, Git!? | https://ohshitgit.com |
| Learn Git Branching | https://learngitbranching.js.org |
| Conventional Commits | https://conventionalcommits.org |

---

> 📝 **Eslatma:** Bu qo'llanma Git 2.40+ versiyasiga asoslangan. Ba'zi komandalar eski versiyalarda farq qilishi mumkin.

> 💡 **Maslahat:** Eng yaxshi o'rganish usuli — amaliyot! Sinov repository yaratib, barcha komandalarni sinab ko'ring.

---

*Yaratilgan sana: 2026-yil, 1-avgust*
*Qo'llanma versiyasi: 1.0*
