import streamlit as st
import os
import glob
import random
import pickle
import numpy as np
from PIL import Image
from datetime import datetime, timedelta, timezone
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import hashlib
import uuid
import time
import pandas as pd
import phonoglyph_math

# ============================================================
# 1. ページ設定
# ============================================================
st.set_page_config(
    page_title="Phonoglyph",
    page_icon="🌒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 2. Apple スタイル CSS
# ============================================================
APPLE_CSS = """
<style>
/* ---------- 全体 ---------- */
*, *::before, *::after {
    -webkit-font-smoothing: antialiased;
    box-sizing: border-box;
}
html, body, .stApp {
    font-family: -apple-system, "Helvetica Neue", "Hiragino Sans", Arial, sans-serif;
    background: #F2F2F7;
    color: #1C1C1E;
}
.block-container {
    padding: 48px 28px 80px;
    max-width: 780px;
}

/* ---------- サイドバー ---------- */
section[data-testid="stSidebar"] {
    background: #1C1C1E;
}
section[data-testid="stSidebar"] * {
    color: #EBEBF5 !important;
}
section[data-testid="stSidebar"] .stSlider > div > div > div {
    background: #007AFF !important;
}

/* ---------- ヘッダー ---------- */
.pg-eyebrow {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #007AFF;
    margin-bottom: 6px;
}
.pg-title {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #1C1C1E;
    margin: 0 0 6px;
    line-height: 1.2;
}
.pg-subtitle {
    font-size: 15px;
    color: #8E8E93;
    margin: 0 0 32px;
    line-height: 1.5;
}

/* ---------- カード ---------- */
.pg-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.07), 0 4px 12px rgba(0,0,0,.04);
}
.pg-notice {
    background: rgba(0,122,255,.07);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 14px;
    color: #3A3A3C;
    line-height: 1.55;
    margin-bottom: 28px;
}
.pg-notice strong { color: #007AFF; }

/* ---------- 区切り ---------- */
.pg-divider {
    height: 1px;
    background: #E5E5EA;
    margin: 24px 0;
    border: none;
}

/* ---------- ラベル ---------- */
.pg-label {
    font-size: 12px;
    font-weight: 600;
    color: #8E8E93;
    letter-spacing: .4px;
    margin-bottom: 4px;
}

/* ---------- プログレス ---------- */
.pg-progress-track {
    height: 3px;
    background: #E5E5EA;
    border-radius: 100px;
    margin-bottom: 40px;
    overflow: hidden;
}
.pg-progress-fill {
    height: 3px;
    background: #007AFF;
    border-radius: 100px;
    transition: width .4s ease;
}

/* ---------- タスク画面 ---------- */
.pg-task-q {
    font-size: 15px;
    color: #8E8E93;
    text-align: center;
    margin-bottom: 4px;
}
.pg-task-book {
    font-size: 22px;
    font-weight: 700;
    color: #007AFF;
    text-align: center;
    letter-spacing: -.3px;
    margin-bottom: 28px;
}
.pg-option-badge {
    display: inline-block;
    background: #F2F2F7;
    color: #3A3A3C;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .8px;
    padding: 2px 9px;
    border-radius: 100px;
    margin-bottom: 8px;
}

/* ---------- 結果画面 ---------- */
.pg-result-wrap {
    text-align: center;
    padding: 40px 0 24px;
}
.pg-result-num {
    font-size: 86px;
    font-weight: 700;
    letter-spacing: -5px;
    color: #30D158;
    line-height: 1;
}
.pg-result-unit {
    font-size: 32px;
    font-weight: 600;
    color: #30D158;
    letter-spacing: -1px;
}
.pg-result-caption {
    font-size: 15px;
    color: #8E8E93;
    margin-top: 8px;
}

/* ---------- QR コード ---------- */
.pg-qr-wrap {
    text-align: center;
    padding: 20px 0;
}
.pg-qr-caption {
    font-size: 12px;
    color: #8E8E93;
    margin-top: 10px;
    font-family: "SF Mono", "Menlo", monospace;
}

/* ---------- ボタン ---------- */
.stButton > button {
    border: none;
    border-radius: 22px;
    font-size: 15px;
    font-weight: 600;
    padding: 10px 28px;
    width: 100%;
    transition: opacity .15s ease, transform .12s ease;
}
.stButton > button[kind="primary"] {
    background: #007AFF;
    color: #FFFFFF;
}
.stButton > button[kind="primary"]:hover {
    opacity: .87;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(0,122,255,.32);
}
.stButton > button[kind="secondary"],
.stButton > button:not([kind]) {
    background: #E5E5EA;
    color: #1C1C1E;
}
.stButton > button:active { transform: scale(.98); }

/* ---------- 入力フィールド ---------- */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #E5E5EA !important;
    background: #FFFFFF !important;
    font-size: 15px;
    padding: 10px 14px;
    color: #1C1C1E;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #007AFF !important;
    box-shadow: 0 0 0 3px rgba(0,122,255,.12) !important;
}
div[data-baseweb="select"] > div {
    border-radius: 10px !important;
    border: 1.5px solid #E5E5EA !important;
    background: #FFFFFF !important;
}
div[data-baseweb="select"] > div:focus-within {
    border-color: #007AFF !important;
    box-shadow: 0 0 0 3px rgba(0,122,255,.12) !important;
}

/* ---------- チェックボックス ---------- */
.stCheckbox > label > div:first-child {
    border-radius: 6px !important;
}

/* ---------- スライダー ---------- */
.stSlider > div > div > div {
    background: #007AFF !important;
}

/* ---------- 非表示 ---------- */
#MainMenu, footer, header, .stDeployButton { visibility: hidden; }
</style>
"""
st.markdown(APPLE_CSS, unsafe_allow_html=True)

# ============================================================
# 3. 定数
# ============================================================
IMAGE_DIR  = "phonoglyphs_v19"
IMG_SUFFIX = "_v19.png"
DB_PATH    = "features_db.pkl"
DEPLOY_URL = "https://phonoglyph-task.streamlit.app/"

# ============================================================
# 4. データロード (キャッシュ)
# ============================================================
@st.cache_data
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "rb") as f:
            return pickle.load(f)
    return {}


@st.cache_data
def _build_image_cache():
    """画像パス辞書をキャッシュ — get_image_path を O(1) にする"""
    cache = {}
    for d in glob.glob(f"{IMAGE_DIR}*"):
        if os.path.isdir(d):
            for fpath in glob.glob(os.path.join(d, "*.png")):
                key = os.path.basename(fpath).replace(IMG_SUFFIX, "")
                cache[key] = fpath
    return cache


def get_image_path(book_name):
    return _build_image_cache().get(book_name)


def _fallback_df(base_df):
    df = base_df.copy()
    df["ローマ字ファイル名"] = df["SystemKey"]
    df["日本語書籍名"]      = df["SystemKey"].apply(lambda x: str(x).split("_")[0])
    df["著者名"]            = "不明"
    df["知名度スコア"]      = 0
    df["発表年"]            = 9999
    df["ジャンル"]          = "不明"
    df["あらすじ"]          = "あらすじ情報なし"
    return df


@st.cache_data
def _load_metadata_core(all_books_tuple):
    """純粋データ処理 (Streamlit API なし) — キャッシュ対象"""
    all_books_list = list(all_books_tuple)
    base_df        = pd.DataFrame({"SystemKey": all_books_list})
    debug          = {}

    xlsx_files = glob.glob("*book_mapping*.xlsx")
    if not xlsx_files:
        debug["error"] = "book_mapping ファイルが見つかりません"
        return _fallback_df(base_df), debug

    xlsx_files.sort(key=os.path.getmtime, reverse=True)
    target = xlsx_files[0]
    for f in xlsx_files:
        try:
            if "あらすじ" in pd.read_excel(f, nrows=1).columns:
                target = f
                break
        except Exception:
            pass
    debug["target_file"] = target

    try:
        meta = pd.read_excel(target)
        meta.columns = [str(c).strip().replace("﻿", "") for c in meta.columns]
        if "ローマ字ファイル名" not in meta.columns:
            meta.rename(columns={meta.columns[0]: "ローマ字ファイル名"}, inplace=True)

        s_rom  = meta["ローマ字ファイル名"].astype(str).str.lower().str.replace(" ", "").str.replace("　", "")
        s_ta   = (meta.get("日本語書籍名", "") + "_" + meta.get("著者名", "")).astype(str).str.lower().str.replace(" ", "").str.replace("　", "")
        s_t    = meta.get("日本語書籍名", "").astype(str).str.lower().str.replace(" ", "").str.replace("　", "")

        rows = []
        for key in all_books_list:
            k  = str(key).lower().replace(" ", "").replace("　", "")
            kt = k.split("_")[0]
            m1 = meta[s_rom == k]
            m2 = meta[s_ta  == k]
            m3 = meta[s_t   == kt]
            if   not m1.empty: rows.append(m1.iloc[0].to_dict())
            elif not m2.empty: rows.append(m2.iloc[0].to_dict())
            elif not m3.empty: rows.append(m3.iloc[0].to_dict())
            else:              rows.append({})

        matched = pd.DataFrame(rows)
        merged  = pd.concat([base_df, matched], axis=1)
        merged["ローマ字ファイル名"] = merged["SystemKey"]
        merged["日本語書籍名"] = merged.get("日本語書籍名", merged["SystemKey"]).fillna(
            merged["SystemKey"].apply(lambda x: str(x).split("_")[0]))
        merged["著者名"]      = merged.get("著者名",      "不明").fillna("不明")
        merged["知名度スコア"] = pd.to_numeric(merged.get("知名度スコア", 0),   errors="coerce").fillna(0)
        merged["発表年"]      = pd.to_numeric(merged.get("発表年",      9999), errors="coerce").fillna(9999)
        merged["ジャンル"]    = merged.get("ジャンル",    "不明").fillna("不明").astype(str).str.strip()
        merged["あらすじ"]    = merged.get("あらすじ", "あらすじ情報なし").fillna("あらすじ情報なし")

        debug.update({
            "columns":     list(meta.columns),
            "sys_keys":    all_books_list[:5],
            "meta_keys":   meta["ローマ字ファイル名"].tolist()[:5],
            "match_count": sum(1 for r in rows if r),
        })
        return merged, debug

    except Exception as e:
        debug["error"] = str(e)
        return _fallback_df(base_df), debug


def load_book_metadata(all_books_list):
    df, debug = _load_metadata_core(tuple(all_books_list))
    for k, v in debug.items():
        st.session_state[f"debug_{k}"] = v
    return df


# ============================================================
# 5. モジュールレベル初期化
# ============================================================
DB_DATA      = load_database()
ALL_BOOKS    = sorted(list(DB_DATA.keys()))
BOOK_META_DF = load_book_metadata(ALL_BOOKS)


def get_display_name(roman_name):
    row = BOOK_META_DF[BOOK_META_DF["ローマ字ファイル名"] == roman_name]
    if not row.empty and row.iloc[0]["著者名"] != "不明":
        return f"『{row.iloc[0]['日本語書籍名']}』"
    return f"『{str(roman_name).split('_')[0]}』"


# ============================================================
# 6. セッションステート初期化
# ============================================================
_defaults = {
    "session_id":      str(uuid.uuid4()),
    "step":            1,
    "user_data":       {},
    "selected_books":  [],
    "task_queue":      [],
    "current_q_index": 0,
    "results":         [],
    "current_options": [],
    "data_saved":      False,
    "is_admin":        False,
    "admin_mode":      "実験タスク (被験者用)",
    "amp_power":       0.8,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# 7. 実験ロジック
# ============================================================
def get_dummies_bouba_kiki(target_book):
    pool = [b for b in ALL_BOOKS
            if b not in st.session_state.selected_books and b != target_book and b in DB_DATA]
    if len(pool) < 4:
        return random.sample(pool, len(pool))
    pool_sorted = sorted(pool, key=lambda b: DB_DATA[b][7])
    layer       = max(2, len(pool_sorted) // 5)
    return random.sample(pool_sorted[:layer], 2) + random.sample(pool_sorted[-layer:], 2)

# ============================================================
# 8. UI ヘルパー
# ============================================================
def pg_header(eyebrow, title, subtitle=""):
    s  = f'<p class="pg-eyebrow">{eyebrow}</p>'
    s += f'<p class="pg-title">{title}</p>'
    if subtitle:
        s += f'<p class="pg-subtitle">{subtitle}</p>'
    st.markdown(s, unsafe_allow_html=True)


def pg_divider():
    st.markdown('<hr class="pg-divider">', unsafe_allow_html=True)


# ============================================================
# 9. 各ステップ レンダリング
# ============================================================

# ---- Step 1: 同意 + 基本情報 ----
def render_step1():
    pg_header("Step 1 / 5", "実験への参加",
              "基本情報をご入力のうえ、実験への参加に同意してください。")

    st.markdown("""
    <div class="pg-notice">
      <strong>実験協力のお願い</strong><br>
      本実験は「音象徴と幾何学図形の認知」に関する学術調査です。
      取得したデータは匿名化され、研究目的にのみ使用されます。
    </div>""", unsafe_allow_html=True)

    consent = st.checkbox("上記の内容を理解し、実験への参加に同意する")

    pg_divider()

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("氏名（漢字またはカタカナ）", placeholder="例：山田 太郎")
        age  = st.number_input("年齢", min_value=15, max_value=100, value=20, step=1)
    with col2:
        gender = st.radio("性別", ["男性", "女性", "その他"], horizontal=True)
        major  = st.radio("専攻分野", ["理数系", "文系", "芸術・デザイン系", "その他"], horizontal=True)

    reading_freq = st.selectbox("読書頻度",
                                ["全く読まない", "月に1〜2冊", "月に3〜5冊", "月に6冊以上"])
    genres      = st.multiselect("よく読むジャンル",
                                  ["純文学", "大衆文学", "SF", "ラノベ", "実用書", "その他"])
    synesthesia = st.slider("言葉の響きに色や形を感じるか（1: 全く感じない — 5: 強く感じる）", 1, 5, 3)

    pg_divider()
    _, col_btn = st.columns([1, 1])
    with col_btn:
        if st.button("次へ進む", key="s1_next", type="primary"):
            if not consent or not name.strip():
                st.error("同意チェックと氏名入力は必須です。")
            else:
                st.session_state.user_data = {
                    "name": name.strip(), "age": age, "gender": gender, "major": major,
                    "reading_freq": reading_freq, "genres": ", ".join(genres),
                    "synesthesia_score": synesthesia,
                }
                st.session_state.step = 2
                st.rerun()


# ---- Step 2: 既読作品の選択 ----
def render_step2():
    pg_header("Step 2 / 5", "既読作品の選択",
              "内容を知っている作品にチェックを入れてください。📖 でタイトル・あらすじを確認できます。")

    col_s, col_o, col_g = st.columns([2, 1.5, 1.5])
    with col_s:
        q = st.text_input("検索（作品名・著者名）", placeholder="例：人間失格",
                          label_visibility="collapsed")
    with col_o:
        sort_by = st.selectbox("並び替え",
                               ["人気・知名度順", "五十音順（作品名）", "五十音順（著者名）",
                                "発表年が新しい順", "発表年が古い順"],
                               label_visibility="collapsed")
    with col_g:
        genres_list   = ["すべて"] + [g for g in BOOK_META_DF["ジャンル"].unique() if g != "不明"]
        genre_filter  = st.selectbox("ジャンル", genres_list, label_visibility="collapsed")

    df = BOOK_META_DF.copy()
    if q:
        df = df[df["日本語書籍名"].astype(str).str.contains(q, case=False, na=False)
              | df["著者名"].astype(str).str.contains(q, case=False, na=False)]
    if genre_filter != "すべて":
        df = df[df["ジャンル"].astype(str).str.strip() == genre_filter.strip()]

    _sort = {
        "人気・知名度順":      (["知名度スコア", "日本語書籍名"], [False, True]),
        "五十音順（作品名）":  (["日本語書籍名"],                  [True]),
        "五十音順（著者名）":  (["著者名", "日本語書籍名"],        [True, True]),
        "発表年が新しい順":    (["発表年", "日本語書籍名"],        [False, True]),
        "発表年が古い順":      (["発表年", "日本語書籍名"],        [True, True]),
    }
    sc, sa = _sort[sort_by]
    df = df.sort_values(by=sc, ascending=sa)
    records = df.to_dict("records")

    st.caption(f"{len(records)} 件表示")

    for i in range(0, len(records), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j >= len(records):
                break
            row   = records[i + j]
            rname = row["ローマ字ファイル名"]
            jname = row["日本語書籍名"]
            auth  = row["著者名"]
            label = f"『{jname}』\n({auth})" if auth != "不明" else f"『{jname}』"

            with cols[j]:
                c1, c2 = st.columns([5, 1])
                with c1:
                    checked = rname in st.session_state.selected_books
                    if st.checkbox(label, value=checked, key=f"chk_{rname}"):
                        if rname not in st.session_state.selected_books:
                            st.session_state.selected_books.append(rname)
                    else:
                        if rname in st.session_state.selected_books:
                            st.session_state.selected_books.remove(rname)
                with c2:
                    with st.popover("📖", key=f"pop_{rname}"):
                        st.markdown(f"**{jname}**")
                        if auth != "不明":
                            st.caption(f"{auth}  ·  {row['ジャンル']}  ·  {int(row['発表年'])}年")
                            pg_divider()
                            st.write(row["あらすじ"])
                        else:
                            st.caption("詳細情報なし")

    pg_divider()

    # 管理者のみ: デバッグパネル
    if st.session_state.is_admin:
        with st.expander("システム診断", expanded=False):
            st.json({
                "読込ファイル": st.session_state.get("debug_target_file", "不明"),
                "結合成功数":   f"{st.session_state.get('debug_match_count', 0)} / {len(ALL_BOOKS)}",
                "sys_keys 例": st.session_state.get("debug_sys_keys", []),
                "meta_keys 例": st.session_state.get("debug_meta_keys", []),
            })
            if "debug_error" in st.session_state:
                st.error(st.session_state.debug_error)

    n = len(st.session_state.selected_books)
    st.caption(f"選択中: {n} 冊")

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る", key="s2_back"):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("次へ進む", key="s2_next", type="primary"):
            if n == 0:
                st.error("最低 1 冊は選択してください。")
            else:
                q_ = st.session_state.selected_books.copy()
                random.shuffle(q_)
                st.session_state.task_queue = q_
                st.session_state.step = 3
                st.rerun()


# ---- Step 3: 事前アンケート ----
def render_step3():
    pg_header("Step 3 / 5", "読書体験に関するアンケート",
              "タスク開始前に、以下の 3 問にお答えください。")

    pg_divider()
    q1 = st.radio(
        "Q1.  表紙のデザインやイラストに惹かれて本を選んだこと（ジャケ買い）がありますか？",
        ["はい", "いいえ"], horizontal=True)
    pg_divider()
    q2 = st.radio(
        "Q2.  ジャケ買いをした結果、文章の雰囲気が表紙の印象と違って読むのをやめた経験はありますか？",
        ["よくある", "たまにある", "あまりない", "全くない"], horizontal=True)
    pg_divider()
    q3 = st.radio(
        "Q3.  あらすじや表紙だけでなく「文章の響き・文体」が直感的に分かる指標があれば、本選びの参考にしたいですか？",
        ["思う", "やや思う", "あまり思わない", "思わない"], horizontal=True)
    pg_divider()

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("戻る", key="s3_back"):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("タスクを開始する", key="s3_start", type="primary"):
            st.session_state.user_data.update({"q1": q1, "q2": q2, "q3": q3})
            st.session_state.step = 4
            st.rerun()


# ---- Step 4: マッチングタスク ----
def render_step4():
    if st.session_state.current_q_index >= len(st.session_state.task_queue):
        st.session_state.step = 5
        st.rerun()

    idx   = st.session_state.current_q_index
    total = len(st.session_state.task_queue)
    pct   = idx / total * 100

    # プログレスバー
    st.markdown(f"""
    <div class="pg-progress-track">
      <div class="pg-progress-fill" style="width:{pct:.1f}%"></div>
    </div>""", unsafe_allow_html=True)

    target_book = st.session_state.task_queue[idx]
    display_name = get_display_name(target_book)

    st.markdown(f'<p class="pg-task-q">{idx + 1} / {total} — 音の紋様を選んでください</p>',
                unsafe_allow_html=True)
    st.markdown(f'<p class="pg-task-book">{display_name}</p>', unsafe_allow_html=True)

    if not st.session_state.current_options:
        opts = get_dummies_bouba_kiki(target_book)
        opts.append(target_book)
        random.shuffle(opts)
        st.session_state.current_options = opts

    options = st.session_state.current_options
    labels  = ["A", "B", "C", "D", "E"]
    cols    = st.columns(5)

    for i, book in enumerate(options):
        with cols[i]:
            st.markdown(f'<div style="text-align:center">'
                        f'<span class="pg-option-badge">{labels[i]}</span></div>',
                        unsafe_allow_html=True)
            img = get_image_path(book)
            if img:
                st.image(Image.open(img), use_container_width=True)
            else:
                st.markdown('<div style="height:160px;background:#F2F2F7;'
                            'border-radius:12px;display:flex;align-items:center;'
                            'justify-content:center;color:#8E8E93;font-size:12px">'
                            '画像なし</div>', unsafe_allow_html=True)

    pg_divider()
    answer = st.radio("選択：", labels, horizontal=True,
                      key=f"q_{idx}", label_visibility="collapsed")

    _, col_btn = st.columns([2, 1])
    with col_btn:
        if st.button("次へ", key=f"next_{idx}", type="primary"):
            chosen     = options[labels.index(answer)]
            is_correct = (chosen == target_book)
            st.session_state.results.append({
                "出題書籍": target_book,
                "被験者回答": chosen,
                "正誤": "正解" if is_correct else "不正解",
            })
            st.session_state.current_q_index += 1
            st.session_state.current_options  = []
            st.rerun()


# ---- Step 5: 結果 ----
def render_step5():
    st.balloons()

    total    = len(st.session_state.results)
    correct  = sum(1 for r in st.session_state.results if r["正誤"] == "正解")
    accuracy = (correct / total * 100) if total else 0

    st.markdown(f"""
    <div class="pg-result-wrap">
      <div>
        <span class="pg-result-num">{accuracy:.1f}</span>
        <span class="pg-result-unit">%</span>
      </div>
      <p class="pg-result-caption">正答率 — {correct} / {total} 問正解</p>
    </div>""", unsafe_allow_html=True)

    pg_divider()

    if not st.session_state.data_saved:
        u         = st.session_state.user_data
        JST       = timezone(timedelta(hours=9), "JST")
        timestamp = datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
        raw_name  = u.get("name", "unknown")
        h_name    = hashlib.sha256(raw_name.encode()).hexdigest()[:16] if raw_name != "unknown" else "unknown"

        rows = []
        for r in st.session_state.results:
            rows.append([
                timestamp, st.session_state.session_id, h_name,
                u.get("age",""), u.get("gender",""), u.get("major",""),
                u.get("reading_freq",""), u.get("genres",""), u.get("synesthesia_score",""),
                u.get("q1",""), u.get("q2",""), u.get("q3",""),
                round(accuracy, 1), r["出題書籍"], r["被験者回答"], r["正誤"],
            ])

        try:
            if "gcp_service_account" in st.secrets:
                scopes = ["https://www.googleapis.com/auth/spreadsheets",
                          "https://www.googleapis.com/auth/drive"]
                creds  = Credentials.from_service_account_info(
                    dict(st.secrets["gcp_service_account"]), scopes=scopes)
                client = gspread.authorize(creds)
                sheet  = client.open_by_url(st.secrets["private_gsheets_url"]).sheet1
                saved  = False
                for attempt in range(3):
                    try:
                        sheet.append_rows(rows)
                        st.session_state.data_saved = True
                        saved = True
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(2 ** attempt + random.uniform(0, 1))
                if not saved:
                    _show_recovery(rows)
            else:
                st.caption("GCP シークレット未設定")
        except Exception as e:
            st.error(f"認証エラー: {e}")

    # QR + URL
    pg_divider()
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(DEPLOY_URL)}"
    st.markdown(f"""
    <div class="pg-qr-wrap">
      <img src="{qr_url}" width="160" style="border-radius:12px">
      <p class="pg-qr-caption">{DEPLOY_URL}</p>
    </div>""", unsafe_allow_html=True)


def _show_recovery(rows):
    st.warning("データの保存に失敗しました。下のボタンでバックアップをダウンロードしてください。")
    header = "Timestamp,SessionID,HashedName,Age,Gender,Major,ReadingFreq,Genres,Synesthesia,Q1,Q2,Q3,Accuracy,Target,Answer,Correctness\n"
    body   = "\n".join([",".join(map(str, r)) for r in rows])
    st.download_button("バックアップをダウンロード",
                       data=header + body,
                       file_name=f"recovery_{st.session_state.session_id}.csv",
                       mime="text/csv", type="primary")


# ---- シミュレーター (管理者用) ----
def render_simulator():
    pg_header("管理者", "Phonoglyph シミュレーター",
              "音素パラメータをリアルタイムで変化させて図形を確認できます。")

    BASELINE = phonoglyph_math.BASELINE
    col_p, col_v = st.columns([1, 1.5])

    with col_p:
        vf  = st.slider("前舌母音 VF — 鋭さ",      0.0, 50.0, BASELINE["vf"])
        vb  = st.slider("後舌母音 VB — 芯の膨らみ", 0.0, 50.0, BASELINE["vb"])
        obs = st.slider("阻害音 OBS — トゲ",        0.0, 50.0, BASELINE["obs"])
        son = st.slider("共鳴音 SON — 丸み",        0.0, 50.0, BASELINE["son"])
        pg_divider()
        st.caption("有声音 VD — 線の太さ (交絡変数排除のため固定)")
        vd  = st.slider("VD", 0.0, 20.0, BASELINE["vd"], disabled=True,
                        label_visibility="collapsed")

    with col_v:
        x, y, lw = phonoglyph_math.calculate_phonoglyph_coordinates(
            vf, vb, obs, son, vd, amp_power=st.session_state.amp_power)
        fig, ax = plt.subplots(figsize=(5, 5), facecolor="white")
        ax.plot(x, y, color="black", linewidth=lw, solid_joinstyle="round")
        ax.fill(x, y, color="black", alpha=0.05)
        ax.set_aspect("equal")
        ax.axis("off")
        st.pyplot(fig)


# ============================================================
# 10. メインエントリポイント
# ============================================================
def main():
    mode = st.query_params.get("mode")
    if isinstance(mode, list):
        mode = mode[0] if mode else None
    if mode == "admin":
        st.session_state.is_admin = True

    # 管理者サイドバー
    if st.session_state.is_admin:
        st.sidebar.title("管理者モード")
        selected = st.sidebar.radio(
            "機能",
            ["実験タスク (被験者用)", "シミュレーター (デモ用)"],
            index=0 if st.session_state.admin_mode == "実験タスク (被験者用)" else 1,
        )
        st.session_state.admin_mode = selected
        st.sidebar.markdown("---")
        st.sidebar.caption("アルゴリズム検証")
        st.session_state.amp_power = st.sidebar.slider(
            "非線形増幅係数 β", 0.1, 2.0, st.session_state.amp_power, 0.1)
        st.sidebar.markdown("---")
        st.sidebar.caption(f"読込: {st.session_state.get('debug_target_file', '—')}")
        st.sidebar.caption(f"結合: {st.session_state.get('debug_match_count', 0)} / {len(ALL_BOOKS)} 件")

    # ルーティング
    if st.session_state.admin_mode == "実験タスク (被験者用)":
        renderers = {1: render_step1, 2: render_step2, 3: render_step3,
                     4: render_step4, 5: render_step5}
        fn = renderers.get(st.session_state.step)
        if fn:
            fn()
    else:
        render_simulator()


if __name__ == "__main__":
    main()