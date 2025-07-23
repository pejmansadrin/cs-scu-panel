import json
import os
import re
import subprocess
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
import glob
from werkzeug.utils import secure_filename

try:
    import jdatetime
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jdatetime"])
    import jdatetime
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image


# --- پیکربندی و مسیرهای اصلی ---
BASE_DIR = os.path.dirname(__file__)
REPO_NAME = "cs-scu.github.io"
REPO_PATH = os.path.join(BASE_DIR, REPO_NAME)
WEBSITE_SRC_PATH = os.path.join(REPO_PATH, 'src')
CLONE_SCRIPT_PATH = os.path.join(BASE_DIR, 'clone_script.py')

MEMBERS_JSON_PATH = os.path.join(WEBSITE_SRC_PATH, 'data', 'members.json')
NEWS_JSON_PATH = os.path.join(WEBSITE_SRC_PATH, 'data', 'news.json')
NEWS_HTML_DIR = os.path.join(WEBSITE_SRC_PATH, 'news')
IMAGE_UPLOAD_DIR = os.path.join(WEBSITE_SRC_PATH, 'assets', 'img')


app = Flask(__name__)

# --- توابع کمکی ---

def run_sync_script():
    """اسکریپت clone_script.py را اجرا می‌کند."""
    try:
        subprocess.run([sys.executable, CLONE_SCRIPT_PATH], check=True, capture_output=True)
        return True, "ریپازیتوری با موفقیت تمیز و همگام‌سازی شد."
    except subprocess.CalledProcessError as e:
        return False, f"اسکریپت همگام‌سازی با خطا مواجه شد:\n{e.stdout}\n{e.stderr}"

def run_git_push():
    """دستور git push را اجرا می‌کند."""
    try:
        result = subprocess.run(["git", "push"], cwd=REPO_PATH, check=True, capture_output=True, text=True)
        return True, f"✅ با موفقیت Push شد:\n{result.stdout}\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        return False, f"خطا در هنگام Push: {e.stdout}\n{e.stderr}"

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
    """صفحه اصلی: ابتدا همه چیز را پاک کرده، next_id را محاسبه کرده و سپس فرم را نمایش می‌دهد."""
    sync_success, sync_message = run_sync_script()
    authors = []
    next_id = 1
    if sync_success:
        authors = get_authors_with_id()
        try:
            with open(NEWS_JSON_PATH, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
                if news_data:
                    next_id = max(item.get('id', 0) for item in news_data) + 1
        except (FileNotFoundError, json.JSONDecodeError):
            next_id = 1
            
    return render_template('index.html', authors=authors, sync_message=sync_message, sync_success=sync_success, next_id=next_id)


@app.route('/site-preview/<path:filename>')
def serve_website_files(filename):
    """فایل‌های سایت کلون‌شده را برای پیش‌نمایش زنده سرویس‌دهی می‌کند."""
    return send_from_directory(WEBSITE_SRC_PATH, filename)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    """تصویر را آپلود و با نام‌گذاری هوشمند ذخیره می‌کند."""
    form = request.form
    if 'image_file' not in request.files or 'english_slug' not in form or 'next_id' not in form or 'upload_type' not in form:
        return jsonify({'success': False, 'error': 'درخواست ناقص است.'}), 400
    
    file = request.files['image_file']
    slug = sanitize_slug(form['english_slug'])
    next_id = form['next_id']
    upload_type = form['upload_type']

    if file.filename == '' or not slug:
        return jsonify({'success': False, 'error': 'فایل یا نامک انگلیسی انتخاب نشده است.'}), 400

    try:
        base_filename = f"{next_id}-{slug}"
        if upload_type == 'content':
            existing_files = glob.glob(os.path.join(IMAGE_UPLOAD_DIR, f"{base_filename}-*.webp"))
            next_number = len(existing_files) + 1
            new_filename = f"{base_filename}-{next_number}.webp"
        else: # 'cover'
            new_filename = f"{base_filename}.webp"

        save_path = os.path.join(IMAGE_UPLOAD_DIR, new_filename)
        image = Image.open(file.stream)
        image.save(save_path, 'webp', quality=85)
        
        relative_path = f"assets/img/{new_filename}"
        return jsonify({'success': True, 'path': relative_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete-image', methods=['POST'])
def delete_image():
    """یک فایل تصویر آپلود شده را از سرور پاک می‌کند."""
    data = request.json
    path_to_delete = data.get('path')
    if not path_to_delete:
        return jsonify({'success': False, 'error': 'مسیر فایل مشخص نشده است.'}), 400

    try:
        secure_path = os.path.join(IMAGE_UPLOAD_DIR, os.path.basename(path_to_delete))
        if os.path.commonprefix((os.path.realpath(secure_path), IMAGE_UPLOAD_DIR)) != IMAGE_UPLOAD_DIR:
            return jsonify({'success': False, 'error': 'مسیر نامعتبر است.'}), 403
        
        if os.path.exists(secure_path):
            os.remove(secure_path)
            print(f"Deleted image: {secure_path}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': True, 'message': 'فایل یافت نشد.'})
    except Exception as e:
        print(f"Error deleting image: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/live-update', methods=['POST'])
def live_update():
    """
    اطلاعات فرم را دریافت کرده و فایل‌های خبر را به صورت موقت با شناسه واقعی بعدی می‌نویسد.
    """
    try:
        data = request.json
        next_id_str = data.get('next_id')
        if not next_id_str:
            return jsonify({'success': False, 'error': 'next_id is missing'}), 400
        next_id = int(next_id_str)

        try:
            with open(NEWS_JSON_PATH, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            news_data = []

        news_data = [item for item in news_data if item.get('id') != next_id]

        slug_base = sanitize_slug(data.get('english_slug', 'temp-news'))
        final_slug = f"{next_id}-{slug_base}"
        temp_entry = {
            "id": next_id, "title": data.get('title', 'عنوان موقت'), "authorId": int(data.get('author_id', 1)),
            "date": jdatetime.datetime.now().strftime("%d %B %Y"), "readingTime": f"{data.get('readingTime', 1)} دقیقه مطالعه",
            "image": data.get('cover_image_path') or f"assets/img/{final_slug}.webp", 
            "summary": data.get('summary', ''), "tags": data.get('tags', []),
            "link": f"#/news/{final_slug}"
        }
        news_data.insert(0, temp_entry)

        with open(NEWS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)

        for temp_file in glob.glob(os.path.join(NEWS_HTML_DIR, f"{next_id}-*.html")):
            os.remove(temp_file)
        html_path = os.path.join(NEWS_HTML_DIR, f"{final_slug}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(data.get('content', ''))

        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Live update error: {e}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add-news', methods=['POST'])
def add_news():
    """خبر را به صورت دائمی ثبت و کامیت می‌کند و نام فایل‌ها را اصلاح می‌کند."""
    try:
        form = request.form
        next_id_str = form.get('next_id')
        if not next_id_str:
            return "<h1>❌ خطا!</h1><p>شناسه موقت خبر یافت نشد. لطفا صفحه را رفرش کنید.</p>", 400
        temp_id = int(next_id_str)
        
        try:
            with open(NEWS_JSON_PATH, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            news_data = []
        
        news_data = [item for item in news_data if item.get('id') != temp_id]
        
        new_id = (max(item.get('id', -1) for item in news_data) if news_data else -1) + 1

        title = form['title']
        english_slug_base = form['english_slug']
        final_slug_base = sanitize_slug(english_slug_base)
        
        temp_base_name = f"{temp_id}-{final_slug_base}"
        final_base_name = f"{new_id}-{final_slug_base}"
        
        final_cover_path_short = form.get('cover_image_path', f"assets/img/{final_base_name}.webp")
        temp_cover_path_short = form.get('cover_image_path')
        if temp_cover_path_short:
            temp_cover_path_full = os.path.join(WEBSITE_SRC_PATH, temp_cover_path_short)
            if os.path.exists(temp_cover_path_full):
                final_cover_name = f"{final_base_name}.webp"
                os.rename(temp_cover_path_full, os.path.join(IMAGE_UPLOAD_DIR, final_cover_name))
                final_cover_path_short = f"assets/img/{final_cover_name}"

        content_html = form['content']
        content_images = glob.glob(os.path.join(IMAGE_UPLOAD_DIR, f"{temp_base_name}-*.webp"))
        for i, temp_img_path in enumerate(sorted(content_images)):
            final_img_name = f"{final_base_name}-{i+1}.webp"
            os.rename(temp_img_path, os.path.join(IMAGE_UPLOAD_DIR, final_img_name))
            temp_img_name = os.path.basename(temp_img_path)
            content_html = content_html.replace(temp_img_name, final_img_name)

        new_entry = {
            "id": new_id, "title": title, "authorId": int(form['author_id']),
            "date": jdatetime.datetime.now().strftime("%d %B %Y"),
            "readingTime": f"{form['readingTime']} دقیقه مطالعه",
            "image": final_cover_path_short, "summary": form['summary'],
            "tags": [[form.get(f'tag_name_{i}'), form.get(f'tag_color_{i}')] for i in range(1, 6) if form.get(f'tag_name_{i}')],
            "link": f"#/news/{final_base_name}"
        }
        news_data.insert(0, new_entry)

        with open(NEWS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)

        html_path = os.path.join(NEWS_HTML_DIR, f"{final_base_name}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content_html)
            
        subprocess.run(["git", "add", "."], cwd=WEBSITE_SRC_PATH, check=True)
        subprocess.run(["git", "commit", "-m", f"feat: Add news article '{title}'"], cwd=REPO_PATH, check=True)
        
        return render_template('push_status.html', title=title)
    except Exception as e:
        return f"<h1>❌ خطا در مرحله کامیت!</h1><p>{e}</p><a href='/'>بازگشت به صفحه اصلی</a>", 500

@app.route('/push-to-github', methods=['POST'])
def push_to_github():
    """تغییرات را به GitHub پوش می‌کند."""
    success, message = run_git_push()
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
