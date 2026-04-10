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

# ==========================================
# 1. ページ設定とカスタムCSS
# ==========================================
st.set_page_config(page_title="Phonoglyph 感性評価実験", page_icon="🌒", layout="centered")

st.markdown("""
    <style>
    .stApp { font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif; }
    .step-header { border-bottom: 3px solid #4CAF50; padding-bottom: 10px; margin-bottom: 25px; font-weight: 700; }
    .stButton>button { border-radius: 8px; font-weight: bold; transition: all 0.3s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .option-img-container { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 定数とバックエンドデータのロード
# ==========================================
BOOKS_DIR = "books"
IMAGE_DIR = "phonoglyphs_v19"
DB_PATH = "features_db.pkl"

@st.cache_data
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as f:
            return pickle.load(f)
    return {}

@st.cache_data
def get_all_books():
    if os.path.exists(BOOKS_DIR):
        files = glob.glob(os.path.join(BOOKS_DIR, "*.txt"))
        return sorted([os.path.basename(f).replace(".txt", "") for f in files])
    return []

DB_DATA = load_database()
ALL_BOOKS = get_all_books()
DEPLOY_URL = "https://phonoglyph-task.streamlit.app/"

# ==========================================
# 3. セッションステートの初期化
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 1
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'selected_books' not in st.session_state: st.session_state.selected_books = []
if 'task_queue' not in st.session_state: st.session_state.task_queue = []
if 'current_q_index' not in st.session_state: st.session_state.current_q_index = 0
if 'results' not in st.session_state: st.session_state.results = []
if 'current_options' not in st.session_state: st.session_state.current_options = []
if 'data_saved' not in st.session_state: st.session_state.data_saved = False

# ==========================================
# 4. ブーバ・キキ効果に基づくダミー抽出ロジック
# ==========================================
def get_dummies_bouba_kiki(target_book):
    pool = [b for b in ALL_BOOKS if b not in st.session_state.selected_books and b != target_book and b in DB_DATA]
    if len(pool) < 4:
        return random.sample(pool, len(pool))

    pool_sorted = sorted(pool, key=lambda b: DB_DATA[b][7])
    layer_size = max(2, len(pool_sorted) // 5)
    
    spiky_pool = pool_sorted[:layer_size]
    round_pool = pool_sorted[-layer_size:]

    return random.sample(spiky_pool, 2) + random.sample(round_pool, 2)

# ==========================================
# 5. 各画面（View）のレンダリング
# ==========================================
def render_step1():
    st.markdown("<h2 class='step-header'>Step 1: 実験への同意と基本情報</h2>", unsafe_allow_html=True)
    st.info("【実験協力のお願い】\n本実験は「音象徴（言葉の響き）と幾何学図形の認知」に関する学術調査です。直感的なマッチングタスクを行っていただきます。取得したデータは個人を特定できない形で統計処理され、研究目的以外には使用されません。")
    consent = st.checkbox("上記の内容を理解し、実験への参加に同意する")

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("氏名（漢字またはカタカナ）*", placeholder="例：山田 太郎")
        age = st.number_input("年齢*", min_value=15, max_value=100, value=20, step=1)
    with col2:
        gender = st.radio("性別*", ["男性", "女性", "その他/回答しない"], horizontal=True)
        major = st.radio("専攻分野 / 職業属性*", ["理数系", "文系", "芸術・デザイン系", "その他"], horizontal=True)

    st.write("---")
    st.subheader("📚 読書に関する情報")
    reading_freq = st.selectbox("読書頻度（月間）", ["全く読まない", "月に1〜2冊", "月に3〜5冊", "月に6冊以上"])
    genres = st.multiselect("よく読むジャンル（複数選択可）", ["純文学", "大衆文学（ミステリー・ホラー等）", "SF・ファンタジー", "ライトノベル", "ノンフィクション・実用書", "その他"])

    st.write("---")
    st.subheader("🧠 感覚に関する質問")
    synesthesia = st.slider("言葉の「響き（音）」を聞いたとき、色や形、硬さなどを直感的に感じることがありますか？", 1, 5, 3, help="1: 全く感じない 〜 5: 日常的によく感じる")

    if st.button("次へ進む（既読書の選択）", type="primary"):
        if not consent: st.error("⚠️ 実験に参加するには、同意のチェックが必要です。")
        elif not name.strip(): st.error("⚠️ 氏名を入力してください。")
        else:
            st.session_state.user_data = {"name": name.strip(), "age": age, "gender": gender, "major": major, 
                                          "reading_freq": reading_freq, "genres": ", ".join(genres), "synesthesia_score": synesthesia}
            st.session_state.step = 2
            st.rerun()

def render_step2():
    st.markdown("<h2 class='step-header'>Step 2: 既読作品の選択</h2>", unsafe_allow_html=True)
    st.write("あなたがこれまでに読んだことがある、あるいは**あらすじや内容をよく知っている作品**をすべて選択してください。")
    search_query = st.text_input("🔍 書籍名や著者名で検索", placeholder="例：人間")
    filtered_books = [book for book in ALL_BOOKS if search_query.lower() in book.lower()]

    st.markdown("### 作品リスト")
    cols = st.columns(3)
    for i, book in enumerate(filtered_books):
        with cols[i % 3]:
            is_checked = book in st.session_state.selected_books
            if st.checkbox(book, value=is_checked, key=f"chk_{book}"):
                if book not in st.session_state.selected_books: st.session_state.selected_books.append(book)
            else:
                if book in st.session_state.selected_books: st.session_state.selected_books.remove(book)

    st.write("---")
    st.success(f"現在の選択数: **{len(st.session_state.selected_books)} 冊**")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る（基本情報の修正）"):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("実験を開始する（ここから戻れません）", type="primary"):
            if len(st.session_state.selected_books) == 0:
                st.error("⚠️ 最低1冊は作品を選択してください。")
            else:
                st.session_state.task_queue = st.session_state.selected_books.copy()
                random.shuffle(st.session_state.task_queue)
                st.session_state.current_q_index = 0
                st.session_state.results = []
                st.session_state.current_options = []
                st.session_state.data_saved = False
                st.session_state.step = 3
                st.rerun()

def render_step3():
    if st.session_state.current_q_index >= len(st.session_state.task_queue):
        st.session_state.step = 4
        st.rerun()

    target_book = st.session_state.task_queue[st.session_state.current_q_index]
    st.markdown(f"<h2 class='step-header'>マッチングタスク ({st.session_state.current_q_index + 1} / {len(st.session_state.task_queue)})</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center; color: #333;'>以下の5つの図形のうち、<br>『<span style='color: #4CAF50; font-size: 1.2em;'>{target_book}</span>』<br>を表している「音の紋様」はどれだと思いますか？</h4>", unsafe_allow_html=True)

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
            st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:18px;'>{display_labels[i]}</div>", unsafe_allow_html=True)
            img_path = os.path.join(IMAGE_DIR, f"{option_book}_v19.png")
            if os.path.exists(img_path):
                img = Image.open(img_path)
                st.image(img, use_container_width=True)
            else:
                st.error("画像なし")

    st.write("---")
    answer_label = st.radio("正解だと思う図形を選択してください：", display_labels, horizontal=True)
    
    if st.button("回答を確定して次へ", type="primary"):
        selected_idx = display_labels.index(answer_label)
        selected_book = options[selected_idx]
        
        is_correct = (selected_book == target_book)
        st.session_state.results.append({
            "出題書籍": target_book,
            "被験者回答": selected_book,
            "正誤": "正解" if is_correct else "不正解"
        })
        
        st.session_state.current_q_index += 1
        st.session_state.current_options = []
        st.rerun()

def render_step4():
    st.balloons()
    st.markdown("<h2 class='step-header'>実験完了！ご協力ありがとうございました。</h2>", unsafe_allow_html=True)

    correct_count = sum(1 for r in st.session_state.results if r["正誤"] == "正解")
    total = len(st.session_state.results)
    accuracy = (correct_count / total) * 100 if total > 0 else 0

    st.markdown(f"<h3 style='text-align:center;'>あなたの感性スコア（正答率）</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center; color:#4CAF50; font-size:60px;'>{accuracy:.1f} %</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:20px;'>({correct_count}問正解 / 全{total}問)</p>", unsafe_allow_html=True)

    # ＝＝＝＝ 【完全版】Googleスプレッドシート連携ロジック ＝＝＝＝
    if not st.session_state.data_saved:
        u_data = st.session_state.user_data
        # 強制的に日本標準時（JST: UTC+9）を設定
        JST = timezone(timedelta(hours=+9), 'JST')
        timestamp = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
        
        combined_rows = []
        for r in st.session_state.results:
            row = [
                timestamp,
                u_data.get("name", "unknown"),
                u_data.get("age", ""),
                u_data.get("gender", ""),
                u_data.get("major", ""),
                u_data.get("reading_freq", ""),
                u_data.get("genres", ""),
                u_data.get("synesthesia_score", ""),
                round(accuracy, 1),
                r["出題書籍"],
                r["被験者回答"],
                r["正誤"]
            ]
            combined_rows.append(row)

        # 1. ローカルバックアップ（フェイルセーフ）
        try:
            log_dir = "results"
            os.makedirs(log_dir, exist_ok=True)
            fieldnames = ["タイムスタンプ", "氏名", "年齢", "性別", "専攻分野", "読書頻度", "よく読むジャンル", "共感覚スコア", "全体正答率(%)", "出題書籍", "被験者回答", "正誤"]
            master_file = os.path.join(log_dir, "master_results.csv")
            file_exists = os.path.exists(master_file)
            with open(master_file, mode='a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(fieldnames)
                writer.writerows(combined_rows)
        except Exception as e:
            print(f"ローカルバックアップエラー: {e}")

        # 2. Googleスプレッドシートへの本命通信
        try:
            if "gcp_service_account" in st.secrets:
                scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
                client = gspread.authorize(creds)
                
                sheet_url = st.secrets["private_gsheets_url"]
                sheet = client.open_by_url(sheet_url).sheet1
                
                # スプレッドシートへ一括書き込み
                for row_data in combined_rows:
                    sheet.append_row(row_data)
                
                # st.success("データベースへの送信が完了しました。") # UIノイズになるため表示しない
            else:
                st.warning("⚠️ クラウドDBの鍵が未設定のため、ローカルのみに保存されました。")
                
        except Exception as sheet_err:
            st.error(f"⚠️ データベース通信エラー: {sheet_err}")

        st.session_state.data_saved = True

    st.write("---")
    st.subheader("🔗 友人や他の人に実験をシェアする")
    st.write("この研究に興味を持ちそうな方がいれば、以下のリンクまたはQRコードから実験にご招待ください。")
    st.code(DEPLOY_URL, language="text")
    encoded_url = urllib.parse.quote(DEPLOY_URL)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={encoded_url}"
    st.image(qr_url, caption="実験へのアクセスQRコード")

# ==========================================
# メインルーチン
# ==========================================
def main():
    if st.session_state.step == 1: render_step1()
    elif st.session_state.step == 2: render_step2()
    elif st.session_state.step == 3: render_step3()
    elif st.session_state.step == 4: render_step4()

if __name__ == "__main__":
    main()