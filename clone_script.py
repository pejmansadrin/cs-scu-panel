import os
import shutil
import subprocess
import sys

# --- پیکربندی ---
REPO_URL = "https://github.com/cs-scu/cs-scu.github.io.git"
REPO_NAME = "cs-scu.github.io"
# نام شاخه اصلی روی گیت‌هاب (معمولا main یا master)
MAIN_BRANCH = "main" 

def sync_repository(repo_url, repo_path):
    """
    ریپازیتوری محلی را به صورت کاملاً سختگیرانه با ریموت همگام‌سازی می‌کند.
    تمام کامیت‌های محلی و فایل‌های اضافه شده را از بین می‌برد.
    """
    print(f"--- Starting STRICT Sync for '{repo_path}' ---")
    try:
        if os.path.exists(repo_path) and os.path.isdir(os.path.join(repo_path, '.git')):
            print(f"-> Repository exists. Forcing it to match remote state...")
            
            original_path = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # مرحله ۱ (جدید): دریافت آخرین وضعیت از ریپازیتوری اصلی بدون ادغام کردن
                print("-> Fetching latest state from origin...")
                subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
                
                # مرحله ۲ (جدید و کلیدی): بازگرداندن کامل ریپازیتوری به وضعیت ریموت
                # این دستور تمام کامیت‌های محلی که push نشده‌اند را از بین می‌برد.
                print(f"-> Resetting local repository to match origin/{MAIN_BRANCH}...")
                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{MAIN_BRANCH}"],
                    check=True, capture_output=True
                )
                
                # مرحله ۳: حذف تمام فایل‌ها و پوشه‌های اضافه شده (ردیابی نشده)
                print("-> Removing all untracked files and directories...")
                subprocess.run(
                    ["git", "clean", "-fd"],
                    check=True, capture_output=True
                )
                
                print("✅ Success: Local repository is now an exact mirror of the remote.")
                    
            finally:
                os.chdir(original_path)

        else:
            # اگر پوشه وجود نداشت، از نو کلون می‌کنیم
            print(f"-> Directory not found. Cloning fresh repository...")
            subprocess.run(["git", "clone", repo_url, repo_path], check=True, capture_output=True)
            print(f"✅ Success: Repository has been freshly cloned.")

    except subprocess.CalledProcessError as e:
        error_details = f"Error during git command (Exit Code: {e.returncode}):\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}"
        print(f"❌ {error_details}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    sync_repository(REPO_URL, REPO_NAME)
