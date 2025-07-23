import subprocess
import os
import logging
import sys

# --- تنظیمات لاگ‌برداری ---
# تنظیم می‌کنیم که لاگ‌ها در کنسول نمایش داده شوند
# فرمت لاگ شامل زمان، سطح لاگ (INFO, ERROR) و پیام خواهد بود
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    stream=sys.stdout,  # ارسال خروجی لاگ به کنسول
)

# آدرس ریپازیتوری گیت
repo_url = "https://github.com/cs-scu/cs-scu.github.io.git"

# نام پوشه‌ای که پس از کلون شدن ایجاد می‌شود
repo_name = repo_url.split('/')[-1].replace('.git', '')

def clone_repository_verbose():
    """
    ریپازیتوری مشخص شده را با لاگ‌برداری کامل در تمام مراحل کلون می‌کند.
    """
    logging.info("اسکریپت کلون کردن ریپازیتوری شروع به کار کرد.")
    
    # بررسی اینکه آیا پوشه ریپازیتوری از قبل وجود دارد یا خیر
    logging.info(f"بررسی وجود پوشه '{repo_name}' در مسیر فعلی...")
    if os.path.isdir(repo_name):
        logging.warning(f"پوشه '{repo_name}' از قبل وجود دارد. عملیات کلون کردن لغو شد.")
        return

    logging.info(f"پوشه '{repo_name}' یافت نشد. آماده‌سازی برای کلون کردن...")
    
    # دستور git clone با گزینه‌های verbose و progress برای نمایش جزئیات
    git_command = ["git", "clone", "--verbose", "--progress", repo_url]
    
    logging.info(f"اجرای دستور: {' '.join(git_command)}")
    
    try:
        # اجرای دستور و دریافت خروجی و خطاها
        # check=True باعث می‌شود در صورت بروز خطا، یک استثنا (exception) پرتاب شود
        result = subprocess.run(
            git_command,
            check=True,
            capture_output=True, # خروجی استاندارد و خطای استاندارد را ذخیره می‌کند
            text=True            # خروجی‌ها را به صورت متن (string) برمی‌گرداند
        )

        # لاگ کردن خروجی استاندارد (stdout) و خطای استاندارد (stderr) از Git
        # Git معمولا پیام‌های پیشرفت را در stderr می‌نویسد
        if result.stdout:
            logging.info("--- خروجی استاندارد از Git ---")
            logging.info(result.stdout)
        if result.stderr:
            logging.info("--- خروجی پیشرفت و وضعیت از Git (stderr) ---")
            logging.info(result.stderr)

        logging.info(f"✅ عملیات با موفقیت به پایان رسید. پوشه '{repo_name}' ایجاد شد.")

    except FileNotFoundError:
        logging.error("❌ خطا: دستور 'git' یافت نشد.")
        logging.error("لطفاً از نصب بودن Git روی سیستم خود و قرار داشتن آن در PATH سیستم مطمئن شوید.")
        
    except subprocess.CalledProcessError as e:
        # این خطا زمانی رخ می‌دهد که دستور git با کد غیر صفر خاتمه یابد (یعنی ناموفق باشد)
        logging.error("❌ خطایی در حین اجرای دستور Git رخ داد:")
        
        # لاگ کردن خروجی‌هایی که منجر به خطا شده‌اند
        if e.stdout:
            logging.error("--- خروجی استاندارد (stdout) ---")
            logging.error(e.stdout)
        if e.stderr:
            logging.error("--- خروجی خطا (stderr) ---")
            logging.error(e.stderr)

if __name__ == "__main__":
    clone_repository_verbose()