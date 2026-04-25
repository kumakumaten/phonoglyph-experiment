import streamlit as st
import os
import glob
import random
import pickle
import numpy as np
from PIL import Image
import csv
from datetime import datetime, timedelta, timezone
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import hashlib
import uuid
import time

# ==========================================
# 1. ページ設定とカスタムCSS
# ==========================================
st.set_page_config(
    page_title="Phonoglyph 感性評価実験", 
    page_icon="🌒", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif; }
    .step-header { border-bottom: 3px solid #4CAF50; padding-bottom: 10px; margin-bottom: 25px; font-weight: 700; }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.3s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} 
    .option-img-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 定数とデータロード
# ==========================================
BOOKS_DIR = "books"
IMAGE_DIR = "phonoglyphs_v19"
DB_PATH = "features_db.pkl"
DEPLOY_URL = "https://phonoglyph-task.streamlit.app/"

@st.cache_data
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as f:
            return pickle.load(f)
    return {}

@st.cache_data
def get_all_books():
    files = []
    for d in glob.glob(f"{BOOKS_DIR}*"):
        if os.path.isdir(d):
            files.extend(glob.glob(os.path.join(d, "*.txt")))
    return sorted([os.path.basename(f).replace(".txt", "") for f in files])

@st.cache_data
def get_book_preview(book_name):
    for d in glob.glob(f"{BOOKS_DIR}*"):
        path = os.path.join(d, f"{book_name}.txt")
        if os.path.exists(path):
            for enc in ['shift_jis', 'utf-8', 'cp932']:
                try:
                    with open(path, 'r', encoding=enc, errors='replace') as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
    return "テキストが見つかりません。"

def get_image_path(book_name):
    for d in glob.glob(f"{IMAGE_DIR}*"):
        path = os.path.join(d, f"{book_name}_v19.png")
        if os.path.exists(path):
            return path
    return None

DB_DATA = load_database()
ALL_BOOKS = get_all_books()

# ==========================================
# 3. セッションステート初期化
# ==========================================
# 衝突検知用のユニークなセッションIDを発行
if 'session_id' not in st.session_state: st.session_state.session_id = str(uuid.uuid4())

if 'step' not in st.session_state: st.session_state.step = 1
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'selected_books' not in st.session_state: st.session_state.selected_books = []
if 'task_queue' not in st.session_state: st.session_state.task_queue = []
if 'current_q_index' not in st.session_state: st.session_state.current_q_index = 0
if 'results' not in st.session_state: st.session_state.results = []
if 'current_options' not in st.session_state: st.session_state.current_options = []
if 'data_saved' not in st.session_state: st.session_state.data_saved = False
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "実験タスク (被験者用)"

# ==========================================
# 4. 実験用ロジック
# ==========================================
def get_dummies_bouba_kiki(target_book):
    pool = [b for b in ALL_BOOKS if b not in st.session_state.selected_books and b != target_book and b in DB_DATA]
    if len(pool) < 4: return random.sample(pool, len(pool))
    pool_sorted = sorted(pool, key=lambda b: DB_DATA[b][7])
    layer_size = max(2, len(pool_sorted) // 5)
    return random.sample(pool_sorted[:layer_size], 2) + random.sample(pool_sorted[-layer_size:], 2)

# ==========================================
# 5. 各画面レンダリング（UI）
# ==========================================
def render_step1():
    st.markdown("<h2 class='step-header'>Step 1: 実験への同意と基本情報</h2>", unsafe_allow_html=True)
    st.info("【実験協力のお願い】 本実験は「音象徴と幾何学図形の認知」に関する学術調査です。取得したデータは匿名化され、研究以外の目的には使用されません。")
    consent = st.checkbox("上記の内容を理解し、実験への参加に同意する")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("氏名（漢字またはカタカナ）*", placeholder="例：山田 太郎")
        age = st.number_input("年齢*", min_value=15, max_value=100, value=20, step=1)
    with col2:
        gender = st.radio("性別*", ["男性", "女性", "その他"], horizontal=True)
        major = st.radio("専攻分野*", ["理数系", "文系", "芸術・デザイン系", "その他"], horizontal=True)
    reading_freq = st.selectbox("読書頻度", ["全く読まない", "月に1〜2冊", "月に3〜5冊", "月に6冊以上"])
    genres = st.multiselect("よく読むジャンル", ["純文学", "大衆文学", "SF", "ラノベ", "実用書", "その他"])
    synesthesia = st.slider("言葉の響きに色や形を感じるか", 1, 5, 3)

    if st.button("次へ進む", key="s1_next", type="primary"):
        if not consent or not name.strip():
            st.error("⚠️ 同意チェックと氏名入力は必須です。")
        else:
            st.session_state.user_data = {
                "name": name.strip(), "age": age, "gender": gender, "major": major, 
                "reading_freq": reading_freq, "genres": ", ".join(genres), "synesthesia_score": synesthesia
            }
            st.session_state.step = 2
            st.rerun()

def render_step2():
    st.markdown("<h2 class='step-header'>Step 2: 既読作品の選択</h2>", unsafe_allow_html=True)
    st.write("内容を知っている作品を選択してください。📖ボタンで内容を全文確認できます。")
    search_query = st.text_input("🔍 検索", placeholder="例：人間")
    filtered_books = [book for book in ALL_BOOKS if search_query.lower() in book.lower()]

    cols = st.columns(3)
    for i, book in enumerate(filtered_books):
        with cols[i % 3]:
            col_chk, col_btn = st.columns([3, 1])
            with col_chk:
                is_checked = book in st.session_state.selected_books
                if st.checkbox(book, value=is_checked, key=f"chk_{book}"):
                    if book not in st.session_state.selected_books: st.session_state.selected_books.append(book)
                else:
                    if book in st.session_state.selected_books: st.session_state.selected_books.remove(book)
            with col_btn:
                with st.popover("📖", key=f"pop_{book}"):
                    st.markdown(f"### {book}")
                    content = get_book_preview(book)
                    st.text_area("本文データ（全文）", value=content, height=400, key=f"area_{book}")

    st.write("---")
    st.success(f"現在の選択数: **{len(st.session_state.selected_books)} 冊**")
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る", key="s2_back"): st.session_state.step = 1; st.rerun()
    with col_next:
        if st.button("次へ進む", key="s2_next", type="primary"):
            if len(st.session_state.selected_books) == 0:
                st.error("⚠️ 最低1冊は選択してください。")
            else:
                st.session_state.task_queue = st.session_state.selected_books.copy()
                random.shuffle(st.session_state.task_queue)
                st.session_state.step = 3
                st.rerun()

def render_step3():
    st.markdown("<h2 class='step-header'>Step 3: 読書体験に関する事前アンケート</h2>", unsafe_allow_html=True)
    st.write("マッチングタスクを開始する前に、普段の読書体験について以下の3つの質問にお答えください。")

    st.write("---")
    q1 = st.radio(
        "**Q1. 表紙のデザインやイラストに惹かれて本を買ったこと（ジャケ買い）はありますか？**",
        ["はい", "いいえ"],
        horizontal=True
    )
    
    q2 = st.radio(
        "**Q2. ジャケ買いをした結果、中身の文章の雰囲気や読みやすさが表紙の印象と違って、読むのをやめたりガッカリした経験はありますか？**",
        ["よくある", "たまにある", "あまりない", "全くない"],
        horizontal=True
    )
    
    q3 = st.radio(
        "**Q3. あらすじや表紙だけでなく、事前に「文章の響きやリズム（文体）」が直感的に分かる指標があれば、本選びの参考にしたいと思いますか？**",
        ["思う", "やや思う", "あまり思わない", "思わない"],
        horizontal=True
    )

    st.write("---")
    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る", key="s3_back"): st.session_state.step = 2; st.rerun()
    with col_next:
        if st.button("タスクを開始する", key="s3_start", type="primary"):
            st.session_state.user_data["q1"] = q1
            st.session_state.user_data["q2"] = q2
            st.session_state.user_data["q3"] = q3
            st.session_state.step = 4
            st.rerun()

def render_step4():
    if st.session_state.current_q_index >= len(st.session_state.task_queue):
        st.session_state.step = 5
        st.rerun()

    target_book = st.session_state.task_queue[st.session_state.current_q_index]
    st.markdown(f"<h2 class='step-header'>タスク ({st.session_state.current_q_index + 1} / {len(st.session_state.task_queue)})</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>『<span style='color: #4CAF50;'>{target_book}</span>』<br>を表す「音の紋様」はどれ？</h4>", unsafe_allow_html=True)

    if not st.session_state.current_options:
        options = get_dummies_bouba_kiki(target_book)
        options.append(target_book)
        random.shuffle(options)
        st.session_state.current_options = options

    options = st.session_state.current_options
    cols = st.columns(5)
    display_labels = ["A", "B", "C", "D", "E"]
    for i, option_book in enumerate(options):
        with cols[i]:
            st.markdown(f"<div style='text-align:center; font-weight:bold;'>{display_labels[i]}</div>", unsafe_allow_html=True)
            img_path = get_image_path(option_book)
            if img_path:
                st.image(Image.open(img_path), use_container_width=True)
            else:
                st.error("画像なし")

    st.write("---")
    answer_label = st.radio("正解を選択：", display_labels, horizontal=True, key=f"q_{st.session_state.current_q_index}")
    if st.button("次へ", key=f"btn_next_{st.session_state.current_q_index}", type="primary"):
        selected_book = options[display_labels.index(answer_label)]
        is_correct = (selected_book == target_book)
        st.session_state.results.append({"出題書籍": target_book, "被験者回答": selected_book, "正誤": "正解" if is_correct else "不正解"})
        st.session_state.current_q_index += 1
        st.session_state.current_options = []
        st.rerun()

def render_step5():
    st.balloons()
    st.markdown("<h2 class='step-header'>実験完了！</h2>", unsafe_allow_html=True)
    total = len(st.session_state.results)
    correct = sum(1 for r in st.session_state.results if r["正誤"] == "正解")
    accuracy = (correct / total) * 100 if total > 0 else 0
    st.markdown(f"<h1 style='text-align:center; color:#4CAF50; font-size:60px;'>{accuracy:.1f} %</h1>", unsafe_allow_html=True)

    if not st.session_state.data_saved:
        u_data = st.session_state.user_data
        JST = timezone(timedelta(hours=+9), 'JST')
        timestamp = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
        
        # 氏名のハッシュ化（匿名化処理）
        raw_name = u_data.get("name", "unknown")
        hashed_name = hashlib.sha256(raw_name.encode('utf-8')).hexdigest()[:16] if raw_name != "unknown" else "unknown"

        combined_rows = []
        for r in st.session_state.results:
            combined_rows.append([
                timestamp, 
                st.session_state.session_id,  # [NEW] 回答ID（重複排除用）
                hashed_name,                  # [UPDATED] ハッシュ化された氏名
                u_data.get("age", ""), 
                u_data.get("gender", ""), 
                u_data.get("major", ""), 
                u_data.get("reading_freq", ""), 
                u_data.get("genres", ""), 
                u_data.get("synesthesia_score", ""),
                u_data.get("q1", ""), 
                u_data.get("q2", ""), 
                u_data.get("q3", ""),
                round(accuracy, 1), 
                r["出題書籍"], 
                r["被験者回答"], 
                r["正誤"]
            ])

        # GCP送信処理（指数的バックオフによるリトライ実装）
        try:
            if "gcp_service_account" in st.secrets:
                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
                client = gspread.authorize(creds)
                sheet = client.open_by_url(st.secrets["private_gsheets_url"]).sheet1
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        sheet.append_rows(combined_rows
                        st.session_state.data_saved = True
                        break # 成功したらループを抜ける
                    except Exception as api_err:
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt + random.uniform(0, 1)) # ジッター付き指数バックオフ
                        else:
                            st.error(f"GCP書き込みエラー（リトライ上限超過）: {api_err}")
            else:
                st.warning("GCPシークレットが設定されていません。")
        except Exception as e:
            st.error(f"認証エラー: {e}")

    st.write("---")
    st.code(DEPLOY_URL, language="text")
    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={urllib.parse.quote(DEPLOY_URL)}")

# ==========================================
# 6. プレゼン用デモ・シミュレーター
# ==========================================
def render_simulator():
    st.markdown("<h2 class='step-header'>🧬 PhonoGlyph モデル・シミュレーター</h2>", unsafe_allow_html=True)
    col_params, col_plot = st.columns([1, 1.5])
    
    BASELINE = {'vf': 16.6, 'vb': 34.3, 'obs': 24.7, 'son': 19.0, 'vd': 5.3}
    
    with col_params:
        vf = st.slider("前舌母音 (VF) [鋭さ]", 0.0, 50.0, BASELINE['vf'])
        vb = st.slider("後舌母音 (VB) [大きさ]", 0.0, 50.0, BASELINE['vb'])
        obs = st.slider("阻害音 (OBS) [トゲ]", 0.0, 50.0, BASELINE['obs'])
        son = st.slider("共鳴音 (SON) [丸み]", 0.0, 50.0, BASELINE['son'])
        vd = st.slider("有声音 (VD) [太さ]", 0.0, 20.0, BASELINE['vd'])

    with col_plot:
        def get_amp(val, baseline_key):
            diff = val - BASELINE[baseline_key]
            return np.sign(diff) * (abs(diff) ** 0.8) * 1.2

        d_vf  = get_amp(vf, 'vf')
        d_vb  = get_amp(vb, 'vb')
        d_obs = get_amp(obs, 'obs')
        d_son = get_amp(son, 'son')
        d_vd  = get_amp(vd, 'vd')

        theta = np.linspace(0, 2 * np.pi, 3000)

        r = 0.3 + (d_vb * 0.1)
        r += (0.4 + d_son) * np.cos(2 * theta)
        r += (0.3 + d_vf) * np.cos(3 * theta)
        
        spike_amp = max(0, 0.1 + d_obs * 0.5)
        r += spike_amp * np.cos(17 * theta)

        x = r * np.cos(theta)
        y = r * np.sin(theta)

        fig, ax = plt.subplots(figsize=(6, 6), facecolor='white')
        line_w = max(0.5, 1.5 + d_vd * 2.0)
        
        ax.plot(x, y, color='black', linewidth=line_w, solid_joinstyle='round')
        ax.fill(x, y, color='black', alpha=0.05)
        
        ax.set_aspect('equal')
        ax.axis('off')
        
        st.pyplot(fig)

# ==========================================
# 7. メインルーチン
# ==========================================
def main():
    query_params = st.query_params
    mode_val = query_params.get("mode")
    
    if isinstance(mode_val, list) and len(mode_val) > 0:
        mode_val = mode_val[0]
        
    if mode_val == "admin":
        st.session_state.is_admin = True

    mode = "実験タスク (被験者用)"

    if st.session_state.is_admin:
        st.sidebar.title("🌘 管理者モード")
        
        if 'admin_mode' not in st.session_state:
            st.session_state.admin_mode = "実験タスク (被験者用)"
        
        selected_mode = st.sidebar.radio(
            "機能を選択", 
            ["実験タスク (被験者用)", "モデル・シミュレーター (教授陣デモ用)"],
            index=0 if st.session_state.admin_mode == "実験タスク (被験者用)" else 1
        )
        st.session_state.admin_mode = selected_mode
        mode = selected_mode
        st.sidebar.write("---")
        st.sidebar.caption("管理者として認証されています。")

    if mode == "実験タスク (被験者用)":
        if st.session_state.step == 1: render_step1()
        elif st.session_state.step == 2: render_step2()
        elif st.session_state.step == 3: render_step3()
        elif st.session_state.step == 4: render_step4()
        elif st.session_state.step == 5: render_step5()
    else:
        render_simulator()

if __name__ == "__main__":
    main()