import os
import shutil
import subprocess
import sys

# --- Configuration ---
REPO_URL = "https://github.com/cs-scu/cs-scu.github.io.git"
REPO_NAME = "cs-scu.github.io"

def sync_repository(repo_url, repo_path):
    """
    ریپازیتوری محلی را با ریموت همگام‌سازی می‌کند.
    اگر پوشه وجود نداشته باشد آن را کلون می‌کند، در غیر این صورت آن را pull می‌کند.
    """
    print(f"--- Starting Smart Sync for '{repo_path}' ---")
    try:
        # ۱. بررسی وجود پوشه ریپازیتوری
        if os.path.exists(repo_path) and os.path.isdir(os.path.join(repo_path, '.git')):
            print(f"-> Directory '{repo_path}' exists. Attempting to update...")
            
            # به مسیر ریپازیتوری می‌رویم تا دستورات گیت را اجرا کنیم
            original_path = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # برای جلوگیری از هرگونه تداخل، تغییرات محلی را پاک می‌کنیم
                print("-> Cleaning local changes (git reset --hard HEAD)...")
                subprocess.run(
                    ["git", "reset", "--hard", "HEAD"],
                    check=True, capture_output=True, text=True
                )
                
                # فقط تغییرات جدید را از شاخه اصلی دریافت می‌کنیم
                print("-> Pulling latest changes from origin...")
                result = subprocess.run(
                    ["git", "pull"],
                    check=True, capture_output=True, text=True
                )
                
                # بررسی می‌کنیم آیا آپدیتی انجام شده است یا خیر
                if "Already up to date." in result.stdout:
                    print("✅ Repository is already up to date.")
                else:
                    print("✅ Success: Repository has been updated.")
                    # print("   Changes:\n", result.stdout) # برای نمایش جزئیات تغییرات می‌توانید این خط را از کامنت خارج کنید
                    
            finally:
                # به مسیر اصلی برمی‌گردیم
                os.chdir(original_path)

        else:
            # ۲. اگر پوشه وجود نداشت، آن را از نو کلون می‌کنیم
            print(f"-> Directory '{repo_path}' not found or is not a git repository. Cloning fresh...")
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path) # اگر پوشه‌ای با این نام هست ولی ریپازیتوری نیست، حذفش می‌کنیم
                
            subprocess.run(
                ["git", "clone", repo_url, repo_path],
                check=True, capture_output=True
            )
            print(f"✅ Success: Repository has been freshly cloned into '{repo_path}'.")

    except subprocess.CalledProcessError as e:
        print(f"❌ An error occurred during a git command:", file=sys.stderr)
        print(f"   Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

def force_fresh_clone(repo_url, repo_path):
    """
    (تابع قدیمی)
    همیشه ریپازیتوری را حذف و از نو کلون می‌کند.
    """
    print(f"--- Starting Force Fresh Clone for '{repo_path}' ---")
    try:
        if os.path.exists(repo_path):
            print(f"-> Directory '{repo_path}' exists. Removing it...")
            shutil.rmtree(repo_path)
            print("-> Old directory removed.")

        print(f"-> Cloning a fresh copy from {repo_url}...")
        subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True,
            capture_output=True
        )
        print(f"\n✅ Success: Repository has been freshly cloned into '{repo_path}'.")

    except Exception as e:
        print(f"❌ An error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # از این به بعد، تابع بهینه را فراخوانی می‌کنیم
    sync_repository(REPO_URL, REPO_NAME)
    
    # در صورت نیاز می‌توانید تابع قدیمی را فراخوانی کنید
    # force_fresh_clone(REPO_URL, REPO_NAME)