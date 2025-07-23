import json
import os
import re
import subprocess
import sys
from flask import Flask, render_template, request, jsonify

try:
    import jdatetime
except ImportError:
    print("Package `jdatetime` not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jdatetime"])
    import jdatetime

# --- پیکربندی و مسیرهای اصلی ---
BASE_DIR = os.path.dirname(__file__)
REPO_NAME = "cs-scu.github.io"
REPO_PATH = os.path.join(BASE_DIR, REPO_NAME)
CLONE_SCRIPT_PATH = os.path.join(BASE_DIR, 'clone_script.py')

MEMBERS_JSON_PATH = os.path.join(REPO_PATH, 'src', 'data', 'members.json')
NEWS_JSON_PATH = os.path.join(REPO_PATH, 'src', 'data', 'news.json')
NEWS_HTML_DIR = os.path.join(REPO_PATH, 'src', 'news')

app = Flask(__name__)

# --- توابع کمکی با بازخورد خطای بهبود یافته ---

def run_sync_script():
    """
    اسکریپت clone_script.py را اجرا کرده و بازخورد دقیقی از موفقیت یا شکست ارائه می‌دهد.
    """
    print("--- Attempting to run sync script... ---")
    if not os.path.exists(CLONE_SCRIPT_PATH):
        error_msg = f"خطای حیاتی: اسکریپت همگام‌سازی در مسیر '{CLONE_SCRIPT_PATH}' یافت نشد!"
        print(f"❌ {error_msg}")
        return False, error_msg
    
    try:
        print(f"-> Executing: {sys.executable} {CLONE_SCRIPT_PATH}")
        result = subprocess.run(
            [sys.executable, CLONE_SCRIPT_PATH], 
            check=True, capture_output=True, text=True, encoding='utf-8'
        )
        output_log = f"--- Sync Script Output ---\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        print(output_log)
        return True, "ریپازیتوری با موفقیت تمیز و همگام‌سازی شد."
    except subprocess.CalledProcessError as e:
        # اگر اسکریپت با خطا تمام شود، خروجی کامل آن را برای دیباگ برمی‌گردانیم
        error_details = (
            f"اسکریپت همگام‌سازی با خطا مواجه شد (کد خروجی: {e.returncode}).\n\n"
            f"--- خروجی استاندارد (stdout) ---\n{e.stdout}\n\n"
            f"--- خروجی خطا (stderr) ---\n{e.stderr}"
        )
        print(f"❌ {error_details}", file=sys.stderr)
        return False, error_details
    except Exception as e:
        # برای خطاهای دیگر مانند مشکلات دسترسی به فایل
        error_msg = f"یک خطای پیش‌بینی نشده در اجرای اسکریپت رخ داد: {e}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return False, error_msg

def run_git_push():
    """دستور git push را اجرا می‌کند و بازخورد دقیقی ارائه می‌دهد."""
    try:
        print("-> Pulling before push...")
        subprocess.run(["git", "pull", "--rebase"], cwd=REPO_PATH, check=True, capture_output=True)
        print("-> Pushing to remote...")
        result = subprocess.run(["git", "push"], cwd=REPO_PATH, check=True, capture_output=True, text=True)
        return True, f"✅ با موفقیت Push شد:\n{result.stdout}\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        error_details = (
            f"عملیات Push با خطا مواجه شد (کد خروجی: {e.returncode}).\n\n"
            f"--- خروجی ---\n{e.stdout}\n{e.stderr}"
        )
        print(f"❌ {error_details}", file=sys.stderr)
        return False, error_details

def get_authors_with_id():
    """لیست نویسندگان را از فایل members.json می‌خواند."""
    try:
        with open(MEMBERS_JSON_PATH, 'r', encoding='utf-8') as f:
            return [{"id": m['id'], "name": m['name']} for m in json.load(f) if m.get('social', {}).get('github')]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def sanitize_slug(text):
    """اسلاگ را برای URL بهینه می‌کند."""
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

# --- روت‌های اصلی وب اپلیکیشن ---

@app.route('/')
def index():
    """صفحه اصلی: ابتدا همه چیز را پاک کرده و سپس فرم را نمایش می‌دهد."""
    print("--- Running sync on main page load... ---")
    sync_success, sync_message = run_sync_script()
    authors = get_authors_with_id() if sync_success else []
    return render_template('index.html', authors=authors, sync_message=sync_message, sync_success=sync_success)

@app.route('/add-news', methods=['POST'])
def add_news():
    """خبر جدید را کامیت کرده و کاربر را به صفحه Push هدایت می‌کند."""
    try:
        # ... (منطق دریافت اطلاعات و ساخت فایل‌ها مثل قبل است) ...
        title = request.form['title']
        author_id = int(request.form['author_id'])
        english_slug_base = request.form['english_slug']
        reading_time_num = request.form['readingTime']
        summary = request.form['summary']
        content_html = request.form['content']
        tags = [[request.form.get(f'tag_name_{i}'), request.form.get(f'tag_color_{i}')] for i in range(1, 6) if request.form.get(f'tag_name_{i}')]

        with open(NEWS_JSON_PATH, 'r+', encoding='utf-8') as f:
            news_data = json.load(f)
            new_id = (max(item['id'] for item in news_data) if news_data else 0) + 1
            final_slug = f"{new_id}-{sanitize_slug(english_slug_base)}"
            image_path = f"assets/img/{final_slug}.webp"
            new_entry = {
                "id": new_id, "title": title, "authorId": author_id, "date": jdatetime.datetime.now().strftime("%d %B %Y"),
                "readingTime": f"{reading_time_num} دقیقه مطالعه", "image": image_path, "summary": summary, "tags": tags, "link": f"#/news/{final_slug}"
            }
            news_data.insert(0, new_entry)
            f.seek(0)
            json.dump(news_data, f, ensure_ascii=False, indent=2)
            f.truncate()

        html_path = os.path.join(NEWS_HTML_DIR, f"{final_slug}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f'<!DOCTYPE html><html><head><title>{title}</title></head><body>{content_html}</body></html>')
            
        subprocess.run(["git", "add", NEWS_JSON_PATH, html_path], cwd=REPO_PATH, check=True)
        subprocess.run(["git", "commit", "-m", f"feat: Add news article '{title}'"], cwd=REPO_PATH, check=True)
        
        return render_template('push_status.html', title=title)

    except Exception as e:
        return f"<h1>❌ خطا در مرحله کامیت!</h1><p>کامیت شما به دلیل خطا ثبت نشد. لطفاً دوباره تلاش کنید.</p><p>جزئیات خطا: {e}</p><a href='/'>بازگشت به صفحه اصلی</a>", 500

# --- اندپوینت‌های Push ---

@app.route('/push-status')
def push_status_page():
    """این صفحه وضعیت Push را نشان می‌دهد. هر بار که بارگذاری شود، همه چیز را پاک می‌کند."""
    print("--- Running sync on push page load/refresh... ---")
    sync_success, sync_message = run_sync_script()
    return render_template('push_status.html', title=None, sync_message=sync_message, sync_success=sync_success)

@app.route('/push-to-github', methods=['POST'])
def push_to_github():
    """تغییرات را به GitHub پوش می‌کند."""
    print("--- Attempting to push to remote... ---")
    success, message = run_git_push()
    return jsonify({'success': success, 'message': message})


if __name__ == '__main__':
    print("--- Starting Panel ---")
    app.run(debug=True, port=5000)
