#!/usr/bin/env python3
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Standalone Repository Mappings
# Format: "relative/path/to/folder": "https://github.com/username/reponame.git"
REPOS = {
    "15-wstore-digital-marketplace/django": "https://github.com/shamsiyevshamsiddin19/wstore.uz.git",
    "10-cloudnexus-hosting-platform": "https://github.com/shamsiyevshamsiddin19/whost.uz.git",
    "01-boostday-productivity-bot": "https://github.com/shamsiyevshamsiddin19/boostday-bot.git",
    "02-docforge-converter": "https://github.com/shamsiyevshamsiddin19/docforge-converter-.git",
    "04-cinehub-movie-bot": "https://github.com/shamsiyevshamsiddin19/cinehub-movie-bot-.git",
    "08-captionflow-video-bot": "https://github.com/shamsiyevshamsiddin19/captionflow-bot-.git",
    "11-mathcraft-web-calc": "https://github.com/shamsiyevshamsiddin19/calculator.git",
    "12-scarpion-music-streaming": "https://github.com/shamsiyevshamsiddin19/SCARPION-MUSIC.git",
    "13-shamsiyev-portfolio-hub": "https://github.com/shamsiyevshamsiddin19/shamsiyev.uz.git",
    "14-tictactoe-minimax-pro": "https://github.com/shamsiyevshamsiddin19/tic-tac-toe.git",
    "16-yordamchi-productivity-suite": "https://github.com/shamsiyevshamsiddin19/yordamchi.git",
    "18-paycore-gateway-sdks": "https://github.com/shamsiyevshamsiddin19/payment-integrations.git",
    "19-captionflow-desktop-studio": "https://github.com/shamsiyevshamsiddin19/captionflow-desktop-.git",
    "23-study-timer": "https://github.com/shamsiyevshamsiddin19/study-timer.git",
}

ROOT_DIR = Path(__file__).resolve().parent

def run(cmd, cwd=ROOT_DIR, check=True):
    return subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True, check=check)

def sync_standalone(rel_path, repo_url, commit_msg):
    src_dir = ROOT_DIR / rel_path
    if not src_dir.exists():
        print(f"⚠️  Papka topilmadi: {rel_path}, o'tkazib yuborildi.")
        return

    print(f"\n📦 Standalone repoga sinxronlanmoqda: {repo_url}")
    temp_dir = Path(tempfile.mkdtemp(prefix="git_sync_"))
    try:
        # Clone repo
        clone_res = run(f"git clone --depth 1 {repo_url} {temp_dir}", check=False)
        if clone_res.returncode != 0:
            print(f"⚠️  Clone xatosi ({repo_url}): {clone_res.stderr.strip()}")
            return

        # Remove everything except .git
        for item in temp_dir.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Copy files from src_dir
        shutil.copytree(
            src_dir,
            temp_dir,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", "node_modules", ".venv", "venv", "env",
                ".env*", "*.pem", "*.key", "*.log", ".DS_Store"
            )
        )

        # Commit and push
        run("git add -A", cwd=temp_dir)
        diff = run("git diff --staged --quiet", cwd=temp_dir, check=False)
        if diff.returncode != 0:
            run(f'git commit -m "{commit_msg}"', cwd=temp_dir)
            push_res = run("git push origin HEAD", cwd=temp_dir, check=False)
            if push_res.returncode == 0:
                print(f"✅ Muvaffaqiyatli yuklandi: {repo_url}")
            else:
                print(f"⚠️  Push xatosi: {push_res.stderr.strip()}")
        else:
            print(f"ℹ️  {repo_url} da o'zgarish yo'q, yangilanish shart emas.")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else "feat: update projects and enhance codebase"
    
    print("=" * 60)
    print("🚀 GIT ACTIVITY & AUTO-SYNC BOSHLANDI")
    print(f"📝 Commit xabari: {commit_msg}")
    print("=" * 60)

    # 1. Stage in all-projects
    run("git add -A")
    staged_diff = run("git diff --staged --quiet", check=False)
    
    changed_files = []
    if staged_diff.returncode != 0:
        # Files that are being committed
        changed_files_out = run("git diff --staged --name-only").stdout
        changed_files = [f for f in changed_files_out.strip().splitlines() if f]
        
        # Commit to all-projects
        run(f'git commit -m "{commit_msg}"')
        print("💾 all-projects commit qilindi.")
        
        push_all = run("git push origin HEAD", check=False)
        if push_all.returncode == 0:
            print("✅ all-projects (origin) ga muvaffaqiyatli push qilindi!")
        else:
            print(f"⚠️  all-projects push xatosi: {push_all.stderr.strip()}")
    else:
        print("ℹ️  all-projects da yangi kiritilgan o'zgarish yo'q.")
        # Check last commit files
        last_files = run("git diff-tree --no-commit-id --name-only -r HEAD", check=False).stdout
        changed_files = [f for f in last_files.strip().splitlines() if f]

    # 2. Check each mapped standalone repo
    synced_any = False
    for rel_path, repo_url in REPOS.items():
        # Match by root project directory prefix
        proj_prefix = rel_path.split("/")[0]
        matched = any(f.startswith(proj_prefix) for f in changed_files)
        if matched:
            sync_standalone(rel_path, repo_url, commit_msg)
            synced_any = True

    if not synced_any:
        print("\nℹ️  Alohida repoga ega loyihalarda o'zgarish sezilmadi.")

    print("\n🎉 Git faollik va sinxronizatsiya yakunlandi!")

if __name__ == "__main__":
    main()
