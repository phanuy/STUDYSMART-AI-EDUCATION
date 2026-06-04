import sqlite3
import json
import urllib.parse
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, Response, session, jsonify, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai

app = Flask(__name__)
app.secret_key = "studysmartai_secret_key"

# Cấu hình API Client cho Gemini
client = genai.Client(api_key="YOUR_CODE")

# ==========================================
# CẤU HÌNH DỮ LIỆU TOÀN CỤC (GLOBAL DATA)
# ==========================================
SUBJECT_MAP = {
    "Toán học": "toan",
    "Vật lí": "ly",
    "Hóa học": "hoa",
    "Tiếng Anh": "anh",
    "Ngữ văn": "van",
    "Sinh học": "sinh",
    "Lịch sử": "su",
    "GD Quốc phòng & An ninh": "qp"
}

SUBJECT_NAMES = {
    "toan": "Môn Toán",
    "ly": "Môn Vật lí",
    "hoa": "Môn Hóa học",
    "anh": "Môn Tiếng Anh"
}

# HỆ THỐNG VIDEO DỰ PHÒNG CHUẨN CHO TỪNG MÔN
DEFAULT_VIDEOS = {
    "toan": "E2g2V0W9D0c", # Video Toán tổng hợp
    "ly": "YzhFXIWox_g",   # Video Lý tổng hợp
    "hoa": "aJsdFyUvTSk",  # Video Hóa tổng hợp
    "anh": "5qap5aO4i9A"   # Video Anh tổng hợp
}

TOPICS = {
    "toan": {
        "10": {
            "Mệnh đề và tập hợp": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-1-menh-de-va-tap-hop.jsp", "yt": "758X_2wFex4"},
            "Bất phương trình bậc nhất hai ẩn": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-2-bat-phuong-trinh-va-he-bat-phuong-trinh-bac-nhat-hai-an.jsp", "yt": "3A_G8Z6z_Yc"},
            "Hệ thức lượng trong tam giác": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-3-he-thuc-luong-trong-tam-giac.jsp", "yt": "v4vG0-V68Yk"},
            "Vectơ": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-4-vecto.jsp", "yt": "m8S9n2fG1v0"},
            "Các số đặc trưng của mẫu số liệu": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-5-cac-so-dac-trung-cua-mau-so-lieu-khong-ghep-nhom.jsp", "yt": "E2g2V0W9D0c"},
            "Hàm số, đồ thị và ứng dụng": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-6-ham-so-do-thi-va-ung-dung.jsp", "yt": "yR_8-16tkmw"},
            "Phương pháp tọa độ trong mặt phẳng": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-7-phuong-phap-toa-do-trong-mat-phang.jsp", "yt": "6a4XpcV8rB0"},
            "Đại số tổ hợp": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-8-dai-so-to-hop.jsp", "yt": "v6G87F9YqS8"},
            "Tính xác suất theo định nghĩa cổ điển": {"vietjack": "https://vietjack.com/toan-10-ket-noi-tri-thuc/chuong-9-tinh-xac-suat-theo-dinh-nghia-co-dien.jsp", "yt": "8nfiPbueiPI"}
        },
        "11": {
            "Hàm số lượng giác và PTLG": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-1-ham-so-luong-giac-va-phuong-trinh-luong-giac.jsp", "yt": "yR_8-16tkmw"},
            "Dãy số - Cấp số cộng - Cấp số nhân": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-2-day-so-cap-so-cong-va-cap-so-nhan.jsp", "yt": "6a4XpcV8rB0"},
            "Các số đặc trưng của mẫu số liệu ghép nhóm": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-3-cac-so-dac-trung-do-xu-the-trung-tam.jsp", "yt": "E2g2V0W9D0c"},
            "Quan hệ song song trong không gian": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-4-quan-he-song-song-trong-khong-gian.jsp", "yt": "7zIgwHSecrE"},
            "Giới hạn - Hàm số liên tục": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-5-gioi-han-ham-so-lien-tuc.jsp", "yt": "v6G87F9YqS8"},
            "Hàm số mũ và hàm số lôgarit": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-6-ham-so-mu-va-ham-so-logarit.jsp", "yt": "8nfiPbueiPI"},
            "Quan hệ vuông góc trong không gian": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-7-quan-he-vuong-goc-trong-khong-gian.jsp", "yt": "nON11I6QkwI"},
            "Các quy tắc tính xác suất": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-8-cac-quy-tac-tinh-xac-suat.jsp", "yt": "E2g2V0W9D0c"},
            "Đạo hàm": {"vietjack": "https://vietjack.com/toan-11-ket-noi-tri-thuc/chuong-9-dao-ham.jsp", "yt": "m8S9n2fG1v0"}
        },
        "12": {
            "Ứng dụng đạo hàm để khảo sát hàm số": {"vietjack": "https://vietjack.com/toan-12-ket-noi-tri-thuc/chuong-1-ung-dung-dao-ham.jsp", "yt": "v6G87F9YqS8"},
            "Vectơ và hệ tọa độ không gian Oxyz": {"vietjack": "https://vietjack.com/toan-12-ket-noi-tri-thuc/chuong-2-vecto-va-he-toa-do.jsp", "yt": "nON11I6QkwI"},
            "Đặc trưng phân tán của mẫu số liệu": {"vietjack": "https://vietjack.com/toan-12-ket-noi-tri-thuc/chuong-3-cac-so-dac-trung.jsp", "yt": "E2g2V0W9D0c"},
            "Nguyên hàm và Tích phân": {"vietjack": "https://vietjack.com/toan-12-ket-noi-tri-thuc/chuong-4-nguyen-ham-va-tich-phan.jsp", "yt": "yR_8-16tkmw"},
            "Quy tắc tính xác suất": {"vietjack": "https://vietjack.com/toan-12-ket-noi-tri-thuc/chuong-5-quy-tac-tinh-xac-suat.jsp", "yt": "8nfiPbueiPI"}
        }
    },
    "ly": {
        "10": {
            "Động học": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-2-dong-hoc.jsp", "yt": "YzhFXIWox_g"},
            "Động lực học": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-3-dong-luc-hoc.jsp", "yt": "7zIgwHSecrE"},
            "Năng lượng, Công, Công suất": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-4-nang-luong-cong-cong-suat.jsp", "yt": "aJsdFyUvTSk"},
            "Động lượng": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-5-dong-luong.jsp", "yt": "m8S9n2fG1v0"},
            "Chuyển động tròn": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-6-chuyen-dong-tron.jsp", "yt": "v4vG0-V68Yk"},
            "Biến dạng của vật rắn. Áp suất": {"vietjack": "https://vietjack.com/vat-li-10-ket-noi-tri-thuc/chuong-7-bien-dang-cua-vat-ran.jsp", "yt": "6a4XpcV8rB0"}
        },
        "11": {
            "Dao động": {"vietjack": "https://vietjack.com/vat-li-11-ket-noi-tri-thuc/chuong-1-dao-dong.jsp", "yt": "7zIgwHSecrE"},
            "Sóng": {"vietjack": "https://vietjack.com/vat-li-11-ket-noi-tri-thuc/chuong-2-song.jsp", "yt": "6a4XpcV8rB0"},
            "Điện trường": {"vietjack": "https://vietjack.com/vat-li-11-ket-noi-tri-thuc/chuong-3-dien-truong.jsp", "yt": "nON11I6QkwI"},
            "Dòng điện, Mạch điện": {"vietjack": "https://vietjack.com/vat-li-11-ket-noi-tri-thuc/chuong-4-dong-dien-mach-dien.jsp", "yt": "v6G87F9YqS8"}
        },
        "12": {
            "Vật lí nhiệt": {"vietjack": "https://vietjack.com/vat-li-12-ket-noi-tri-thuc/chuong-1-vat-li-nhiet.jsp", "yt": "yR_8-16tkmw"},
            "Khí lí tưởng": {"vietjack": "https://vietjack.com/vat-li-12-ket-noi-tri-thuc/chuong-2-khi-li-tuong.jsp", "yt": "6a4XpcV8rB0"},
            "Từ trường": {"vietjack": "https://vietjack.com/vat-li-12-ket-noi-tri-thuc/chuong-3-tu-truong.jsp", "yt": "nON11I6QkwI"},
            "Vật lí hạt nhân": {"vietjack": "https://vietjack.com/vat-li-12-ket-noi-tri-thuc/chuong-4-vat-li-hat-nhan.jsp", "yt": "8nfiPbueiPI"}
        }
    },
    "hoa": {
        "10": {
            "Cấu tạo nguyên tử": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-1-cau-tao-nguyen-tu.jsp", "yt": "6a4XpcV8rB0"},
            "Bảng tuần hoàn các nguyên tố hóa học": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-2-bang-tuan-hoan.jsp", "yt": "v6G87F9YqS8"},
            "Liên kết hóa học": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-3-lien-ket-hoa-hoc.jsp", "yt": "758X_2wFex4"},
            "Phản ứng oxi hóa - khử": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-4-phan-ung-oxi-hoa-khu.jsp", "yt": "3A_G8Z6z_Yc"},
            "Năng lượng hóa học": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-5-nang-luong-hoa-hoc.jsp", "yt": "aJsdFyUvTSk"},
            "Tốc độ phản ứng hóa học": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-6-toc-do-phan-ung.jsp", "yt": "m8S9n2fG1v0"},
            "Nguyên tố nhóm VIIA (Halogen)": {"vietjack": "https://vietjack.com/hoa-hoc-10-ket-noi-tri-thuc/chuong-7-nguyen-to-nhom-viia.jsp", "yt": "v4vG0-V68Yk"}
        },
        "11": {
            "Cân bằng hóa học": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-1-can-bang-hoa-hoc.jsp", "yt": "aJsdFyUvTSk"},
            "Nitrogen và Sulfur": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-2-nitrogen-va-sulfur.jsp", "yt": "8nfiPbueiPI"},
            "Đại cương hóa học hữu cơ": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-3-dai-cuong-hoa-hoc-huu-co.jsp", "yt": "7zIgwHSecrE"},
            "Hydrocarbon": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-4-hydrocarbon.jsp", "yt": "v4vG0-V68Yk"},
            "Dẫn xuất Halogen - Alcohol - Phenol": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-5-dan-xuat-halogen.jsp", "yt": "m8S9n2fG1v0"},
            "Hợp chất Carbonyl - Carboxylic acid": {"vietjack": "https://vietjack.com/hoa-hoc-11-ket-noi-tri-thuc/chuong-6-hop-chat-carbonyl.jsp", "yt": "yR_8-16tkmw"}
        },
        "12": {
            "Ester - Lipid": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-1-ester-lipid.jsp", "yt": "8nfiPbueiPI"},
            "Carbohydrate": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-2-carbohydrate.jsp", "yt": "v4vG0-V68Yk"},
            "Hợp chất chứa Nitrogen": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-3-hop-chat-chua-nitrogen.jsp", "yt": "m8S9n2fG1v0"},
            "Polymer": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-4-polymer.jsp", "yt": "aJsdFyUvTSk"},
            "Đại cương về kim loại": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-5-dai-cuong-ve-kim-loai.jsp", "yt": "758X_2wFex4"},
            "Kim loại kiềm, kiềm thổ, nhôm": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-6-kim-loai-kiem.jsp", "yt": "v6G87F9YqS8"},
            "Sắt và kim loại chuyển tiếp": {"vietjack": "https://vietjack.com/hoa-hoc-12-ket-noi-tri-thuc/chuong-7-sat.jsp", "yt": "3A_G8Z6z_Yc"}
        }
    },
    "anh": {
        "10": {
            "Unit 1: Family Life": {"vietjack": "https://vietjack.com/tieng-anh-10-global-success/unit-1-family-life.jsp", "yt": "5qap5aO4i9A"},
            "Unit 2: Humans and the Environment": {"vietjack": "https://vietjack.com/tieng-anh-10-global-success/unit-2-humans-and-the-environment.jsp", "yt": "5qap5aO4i9A"},
            "Unit 3: Music": {"vietjack": "https://vietjack.com/tieng-anh-10-global-success/unit-3-music.jsp", "yt": "5qap5aO4i9A"},
            "Unit 4: For a Better Community": {"vietjack": "https://vietjack.com/tieng-anh-10-global-success/unit-4-for-a-better-community.jsp", "yt": "5qap5aO4i9A"},
            "Unit 5: Inventions": {"vietjack": "https://vietjack.com/tieng-anh-10-global-success/unit-5-inventions.jsp", "yt": "5qap5aO4i9A"}
        },
        "11": {
            "Unit 1: A Long and Healthy Life": {"vietjack": "https://vietjack.com/tieng-anh-11-global-success/unit-1-a-long-and-healthy-life.jsp", "yt": "5qap5aO4i9A"},
            "Unit 2: The Generation Gap": {"vietjack": "https://vietjack.com/tieng-anh-11-global-success/unit-2-the-generation-gap.jsp", "yt": "5qap5aO4i9A"},
            "Unit 3: Cities of the Future": {"vietjack": "https://vietjack.com/tieng-anh-11-global-success/unit-3-cities-of-the-future.jsp", "yt": "5qap5aO4i9A"},
            "Unit 4: ASEAN and Viet Nam": {"vietjack": "https://vietjack.com/tieng-anh-11-global-success/unit-4-asean-and-viet-nam.jsp", "yt": "5qap5aO4i9A"},
            "Unit 5: Global Warming": {"vietjack": "https://vietjack.com/tieng-anh-11-global-success/unit-5-global-warming.jsp", "yt": "5qap5aO4i9A"}
        },
        "12": {
            "Unit 1: Life Stories": {"vietjack": "https://vietjack.com/tieng-anh-12-global-success/unit-1-life-stories.jsp", "yt": "5qap5aO4i9A"},
            "Unit 2: A Multicultural World": {"vietjack": "https://vietjack.com/tieng-anh-12-global-success/unit-2-a-multicultural-world.jsp", "yt": "5qap5aO4i9A"},
            "Unit 3: Green Living": {"vietjack": "https://vietjack.com/tieng-anh-12-global-success/unit-3-green-living.jsp", "yt": "5qap5aO4i9A"},
            "Unit 4: Urbanisation": {"vietjack": "https://vietjack.com/tieng-anh-12-global-success/unit-4-urbanisation.jsp", "yt": "5qap5aO4i9A"},
            "Unit 5: The World of Work": {"vietjack": "https://vietjack.com/tieng-anh-12-global-success/unit-5-the-world-of-work.jsp", "yt": "5qap5aO4i9A"}
        }
    }
}

@app.context_processor
def inject_global_variables():
    return {
        'SUBJECT_MAP': SUBJECT_MAP,
        'SUBJECT_NAMES': SUBJECT_NAMES
    }

# ==========================================
# CƠ SỞ DỮ LIỆU (DATABASE SYSTEM)
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('studysmart.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            password TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            progress_data TEXT DEFAULT '{}',
            study_plan TEXT DEFAULT '[]'
        )
    ''')
    try:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN study_plan TEXT DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

# ==========================================
# THUẬT TOÁN HỖ TRỢ (HELPERS)
# ==========================================
def calculate_subject_average(tx1, tx2, tx3, tx4, gk, ck):
    tx_avg = (tx1 + tx2 + tx3 + tx4) / 4
    return round((tx_avg + gk * 2 + ck * 3) / 6, 2)

def generate_study_plan(weakest_topics, study_hours, target_score, available_topics, subject_raw=None, grade=None):
    plan = []
    today = datetime.now()

    prioritized = sorted(
        weakest_topics,
        key=lambda x: (x[1], -available_topics.get(x[0], {}).get("weight", 1.0))
    )

    for i in range(7):
        study_date = today + timedelta(days=i)
        date_str = study_date.strftime("%d/%m")

        if not prioritized: continue

        topic, score = prioritized[i % len(prioritized)]
        
        daily_minutes = int(study_hours * 60)
        sessions = []
        
        if daily_minutes <= 60:
            sessions.append(f"📘 Tập trung học: {daily_minutes} phút")
        elif daily_minutes <= 120:
            half = daily_minutes // 2
            sessions.append(f"📘 Phiên 1: {half} phút")
            sessions.append("☕ Nghỉ giải lao 10 phút")
            sessions.append(f"📘 Phiên 2: {half} phút")
        else:
            block = daily_minutes // 3
            sessions.append(f"📘 Khởi động & Kiến thức: {block} phút")
            sessions.append("☕ Nghỉ ngắn")
            sessions.append(f"📘 Luyện tập sâu: {block} phút")
            sessions.append("☕ Nghỉ ngắn")
            sessions.append(f"📘 Tổng kết & Bài tập: {block} phút")
        
        sessions.append("✅ Hoàn thành mục tiêu ngày")

        topic_info = available_topics.get(topic, {})
        fallback_query = urllib.parse.quote(f"Lý thuyết và bài tập {topic} {subject_raw or ''} lớp {grade or ''} kết nối tri thức")
        resource_link = topic_info.get("vietjack", f"https://www.google.com/search?q={fallback_query}")
        
        review_dates = [(study_date + timedelta(days=d)).strftime("%d/%m") for d in [3, 7, 14]]

        plan.append({
            "day": study_date.strftime("%A"),
            "date": date_str,
            "topic": topic,
            "score": score,
            "duration": daily_minutes,
            "resource": resource_link,
            "review_dates": review_dates,
            "schedule": sessions
        })
    return plan

@app.route('/generate-plan', methods=['GET', 'POST'])
def generate_plan():
    if request.method == 'GET':
        return redirect(url_for('index'))

    subject_raw = request.form.get('subject', 'toan')
    grade = request.form.get('grade', '11')
    study_hours = request.form.get('study_hours', '3')
    target_score = request.form.get('target_score', '8.0')

    subject_key = 'toan'
    if subject_raw in TOPICS:
        subject_key = subject_raw
    else:
        for k, v in SUBJECT_NAMES.items():
            if v == subject_raw:
                subject_key = k
                break
                
    available_topics = TOPICS.get(subject_key, {}).get(grade, {})
    
    # LẤY VIDEO DỰ PHÒNG CHUẨN THEO MÔN HỌC HIỆN TẠI
    safe_fallback_video = DEFAULT_VIDEOS.get(subject_key, "E2g2V0W9D0c")

    try:
        study_hours_num = float(study_hours)
        target_score_num = float(target_score)
    except ValueError:
        study_hours_num = 3.0
        target_score_num = 8.0

    all_topics = []
    chart_labels = []
    chart_scores = []
    weakest_topics = []
    
    for i in range(30):
        topic_name = request.form.get(f'topic_name_{i}')
        score_str = request.form.get(f'topic_score_{i}')
        
        if topic_name and score_str:
            try:
                score_val = float(score_str)
            except ValueError:
                score_val = 5.0
                
            all_topics.append({"name": topic_name, "score": score_val})
            chart_labels.append(topic_name)
            chart_scores.append(score_val)
            weakest_topics.append((topic_name, score_val))

    if not all_topics:
        return "Lỗi: Không tìm thấy dữ liệu chuyên đề. Vui lòng quay lại và chọn điểm.", 400

    if session.get('user_id'):
        user_id = session['user_id']
        ai_plan = generate_study_plan(weakest_topics, study_hours_num, target_score_num, available_topics, subject_raw, grade)
        
        conn = get_db_connection()
        conn.execute("UPDATE users SET study_plan = ? WHERE id = ?", (json.dumps(ai_plan), user_id))
        conn.commit()
        conn.close()

    focus_topics = []
    sorted_topics = sorted(all_topics, key=lambda x: x['score'])
    
    for item in sorted_topics:
        if item['score'] < target_score_num:
            topic_name = item['name']
            topic_info = available_topics.get(topic_name, {})
            
            # ĐÃ SỬA LỖI: Sử dụng video dự phòng đúng môn học thay vì gán cứng Vật Lí
            video_id = topic_info.get("yt", safe_fallback_video) 
            
            fallback_query = urllib.parse.quote(f"Lý thuyết và bài tập {topic_name} {subject_raw} lớp {grade} kết nối tri thức")
            real_doc_link = topic_info.get("vietjack", f"https://www.google.com/search?q={fallback_query}")
            
            focus_topics.append({
                "name": topic_name,
                "score": item['score'],
                "doc_link": real_doc_link,
                "video_id": video_id
            })

    if not focus_topics:
        focus_topics = [{"name": "Tất cả chuyên đề đều vượt mục tiêu!", "score": target_score_num, "doc_link": "#", "video_id": safe_fallback_video}]
    else:
        focus_topics = focus_topics[:3] if focus_topics else [{"name": "Tất cả chuyên đề đều vượt mục tiêu!", "score": target_score_num, "doc_link": "#", "video_id": "5qap5aO4i9A"}]

    ai_advices = [
        f"Bạn đang hướng tới {target_score_num} điểm, một mục tiêu hoàn toàn khả thi nếu phân bổ thời gian hợp lý.",
        f"Lỗ hổng lớn nhất hiện tại nằm ở '{focus_topics[0]['name']}'. Hãy bắt tay vào xem lại các công thức biến đổi cơ bản của phần này trước.",
        f"Áp dụng ngay mức học {study_hours_num} giờ/ngày. Khi gặp các bài toán yêu cầu nhiều bước tính toán trung gian, hãy viết rõ từng bước ra nháp để tránh sai số.",
        "Nhấn vào nút 'Tài liệu' bên dưới để mở ngay tổng hợp bài tập liên quan nhất nhé!"
    ]

    days_of_week = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekly_schedule = []
    
    for idx, day_name in enumerate(days_of_week):
        doc_link = "#"
        video_id = safe_fallback_video

        if idx < len(focus_topics):
            focus_item = f"Trọng tâm: {focus_topics[idx]['name']}"
            doc_link = focus_topics[idx]['doc_link']
            video_id = focus_topics[idx]['video_id']
        elif idx == 5:
            focus_item = "Tổng hợp lý thuyết & Giải bài tập tự luận"
            video_id = safe_fallback_video
        elif idx == 6:
            focus_item = "Làm đề kiểm tra đánh giá năng lực tuần"
            video_id = safe_fallback_video
        else:
            topic_name = all_topics[idx % len(all_topics)]['name']
            focus_item = f"Ôn tập: {topic_name}"
            topic_info = available_topics.get(topic_name, {})
            
            video_id = topic_info.get("yt", safe_fallback_video)
            
            fallback_query = urllib.parse.quote(f"Lý thuyết và bài tập {topic_name} {subject_raw} lớp {grade} kết nối tri thức")
            doc_link = topic_info.get("vietjack", f"https://www.google.com/search?q={fallback_query}")

        weekly_schedule.append({
            "name": day_name,
            "focus": focus_item,
            "duration": f"{study_hours_num} giờ" if idx != 6 else "1.5 giờ",
            "doc_link": doc_link,
            "video_id": video_id
        })

    return render_template(
        'generate_plan.html',
        subject=subject_raw,
        grade=grade,
        study_hours=study_hours,
        target_score=target_score,
        chart_labels=chart_labels,
        chart_scores=chart_scores,
        ai_advices=ai_advices,
        focus_topics=focus_topics,
        weekly_schedule=weekly_schedule
    )

@app.route("/", methods=["GET", "POST"])
def index():
    default_subject = "toan"
    default_grade = "11"
    
    subject = default_subject
    grade = default_grade
    
    if request.method == "POST":
        subject = request.form.get("subject", default_subject)
        grade = request.form.get("grade", default_grade)
        available_topics = TOPICS.get(subject, {}).get(grade, {})
        
        if "submit_btn" in request.form:
            if not session.get('user_id'):
                return "Vui lòng đăng nhập trước khi tạo lộ trình!"
                
            user_id = session['user_id']
            
            try:
                study_hours = float(request.form.get("study_hours", 2))
            except ValueError:
                study_hours = 2.0
                
            weakest_topics = []
            for topic_name in available_topics.keys():
                score_input = request.form.get(f"score_{topic_name}")
                if score_input is not None:
                    try:
                        weakest_topics.append((topic_name, float(score_input)))
                    except ValueError:
                        weakest_topics.append((topic_name, 5.0))
                        
            if not weakest_topics:
                weakest_topics = [(t, 4.0) for t in available_topics.keys()]
                
            ai_plan = generate_study_plan(weakest_topics, study_hours, 8.0, available_topics, subject, grade)
            
            conn = get_db_connection()
            conn.execute("UPDATE users SET study_plan = ? WHERE id = ?", (json.dumps(ai_plan), user_id))
            conn.commit()
            conn.close()
            
            return redirect(url_for('study_plan_page'))
            
        else:
            return render_template(
                "index.html", 
                available_topics=available_topics,
                selected_subject=subject,  
                selected_grade=grade       
            )
        
    available_topics = TOPICS.get(subject, {}).get(grade, {})
    return render_template(
        "index.html", 
        available_topics=available_topics,
        selected_subject=subject,  
        selected_grade=grade       
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()      
        password = request.form["password"].strip()
        
        if not username or not email or not password:
            return render_template("register.html", error="Vui lòng điền đầy đủ tất cả các trường!")
            
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                        (username, email, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Tên đăng nhập đã tồn tại!")
        finally:
            conn.close()
            
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["xp"] = user["xp"]
            session["streak"] = user["streak"]
            
            try:
                session["progress"] = json.loads(user["progress_data"])
            except:
                session["progress"] = {}
                
            return redirect(url_for("study_plan_page"))
        else:
            return render_template("login.html", error="Sai tên đăng nhập hoặc mật khẩu!")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/overview", methods=["GET", "POST"])
def overview():
    result = None
    if request.method == "POST":
        subjects = {}
        try:
            for sub_name, sub_key in SUBJECT_MAP.items():
                tx1 = float(request.form[f"{sub_key}_tx1"])
                tx2 = float(request.form[f"{sub_key}_tx2"])
                tx3 = float(request.form[f"{sub_key}_tx3"])
                tx4 = float(request.form[f"{sub_key}_tx4"])
                gk = float(request.form[f"{sub_key}_gk"])
                ck = float(request.form[f"{sub_key}_ck"])

                avg = calculate_subject_average(tx1, tx2, tx3, tx4, gk, ck)
                subjects[sub_name] = avg

            overall = round(sum(subjects.values()) / len(subjects), 2)
            weakest = min(subjects, key=subjects.get)

            result = {
                "subjects": subjects,
                "overall": overall,
                "weakest": weakest
            }
        except (ValueError, KeyError):
            result = {
                "error": "Vui lòng nhập đầy đủ và chính xác điểm số (từ 0 đến 10) cho tất cả các môn!"
            }

    return render_template("overview.html", result=result)

@app.route('/study-plan')
def study_plan_page():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    
    try:
        plan_data = json.loads(user['study_plan']) if user['study_plan'] else []
    except:
        plan_data = []
        
    try:
        progress_data = json.loads(user["progress_data"]) if user["progress_data"] else {}
    except:
        progress_data = {}
        
    return render_template("study_plan.html", plan=plan_data, progress=progress_data)

@app.route('/toggle-task', methods=['POST'])
def toggle_task():
    if not session.get('user_id'):
        return jsonify({"error": "Vui lòng đăng nhập!"}), 401
    
    data = request.json or {}
    day_key = data.get('day')
    try:
        task_index = int(data.get('index'))
    except (TypeError, ValueError):
        return jsonify({"error": "Dữ liệu vị trí không hợp lệ!"}), 400
    
    user_id = session['user_id']
    
    conn = get_db_connection()
    user = conn.execute("SELECT progress_data FROM users WHERE id = ?", (user_id,)).fetchone()
    
    try:
        progress = json.loads(user["progress_data"]) if user["progress_data"] else {}
    except:
        progress = {}
        
    if day_key not in progress:
        progress[day_key] = []
        
    if task_index in progress[day_key]:
        progress[day_key].remove(task_index)
    else:
        progress[day_key].append(task_index)
        
    session['progress'] = progress
    session.modified = True  
    
    conn.execute("UPDATE users SET progress_data = ? WHERE id = ?", (json.dumps(progress), user_id))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "progress": progress})

@app.route('/complete-day', methods=['POST'])
def complete_day():
    if not session.get('user_id'):
        return jsonify({"error": "Vui lòng đăng nhập!"}), 401
        
    user_id = session['user_id']
    data = request.json or {}
    day_key = data.get('day') 
    
    new_xp = session.get('xp', 0) + 10
    new_streak = session.get('streak', 0) + 1
    
    session['xp'] = new_xp
    session['streak'] = new_streak
    
    conn = get_db_connection()
    user = conn.execute("SELECT progress_data FROM users WHERE id = ?", (user_id,)).fetchone()
    
    try:
        progress = json.loads(user['progress_data']) if user['progress_data'] else {}
    except:
        progress = {}
        
    if 'completed_days' not in progress:
        progress['completed_days'] = []
        
    if day_key and day_key not in progress['completed_days']:
        progress['completed_days'].append(day_key)
        
    session['progress'] = progress
    session.modified = True 
    
    conn.execute("UPDATE users SET xp = ?, streak = ?, progress_data = ? WHERE id = ?", 
                 (new_xp, new_streak, json.dumps(progress), user_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success", 
        "xp": new_xp, 
        "streak": new_streak, 
        "completed_days": progress['completed_days']
    })

@app.route("/stream")
def stream():
    question = request.args.get("q", "")
    prompt = f"Bạn là gia sư Toán THPT Việt Nam.\n\nQuy tắc:\n- Công thức toán phải dùng LaTeX.\n- Công thức trong dòng dùng $...$\n- Công thức riêng dòng dùng $$...$$\n- Trình bày rõ ràng.\n\nCâu hỏi:\n{question}"

    def generate():
        try:
            response = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt
            )
            for chunk in response:
                if getattr(chunk, "text", None):
                    yield chunk.text
        except Exception as e:
            yield f"Lỗi Gemini: {e}"

    return Response(generate(), mimetype="text/plain")

@app.route("/planner")
def planner():
    scores = session.get("scores")
    if not scores:
        return "<h2>Chưa có dữ liệu điểm</h2><a href='/'>Quay lại nhập điểm</a>"

    weakest = sorted(scores.items(), key=lambda x: x[1])
    return render_template("planner.html", weakest=weakest)

@app.route("/ai", methods=["GET"])
def ai_page():
    return render_template("ai.html")

@app.route("/ask-ai", methods=["POST"])
def ask_ai():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"response": "Không nhận được dữ liệu yêu cầu."}), 400
            
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"response": "Vui lòng nhập nội dung câu hỏi."}), 400

        prompt_instruction = (
            "Bạn là SmartAI Tutor, một gia sư trí tuệ nhân tạo xuất sắc tại Việt Nam. "
            "Hãy hỗ trợ học sinh giải đáp các kiến thức, bài tập thuộc các môn Toán, Vật lí, "
            "Hóa học, Tiếng Anh từ lớp 10 đến lớp 12 theo chương trình GDPT 2018. "
            "Trả lời ngắn gọn, dễ hiểu, logic, thân thiện và có ví dụ minh họa rõ ràng."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction=prompt_instruction,
                temperature=0.7
            )
        )
        
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Lỗi hệ thống AI: {e}")
        return jsonify({"response": "Gia sư AI đang bận xử lý dữ liệu, bạn vui lòng thử lại sau vài giây nhé!"}), 500

if __name__ == "__main__":
    app.run(debug=True)