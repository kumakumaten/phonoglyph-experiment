import streamlit as st
import os, glob, random, pickle
import numpy as np
from PIL import Image
from datetime import datetime, timedelta, timezone
import urllib.parse, gspread, hashlib, uuid, time
import matplotlib.pyplot as plt
import pandas as pd
from google.oauth2.service_account import Credentials
import phonoglyph_math
import threading

st.set_page_config(page_title="Phonoglyph", page_icon="🌒",
                   layout="centered", initial_sidebar_state="collapsed")

# ==========================================
# 1. カスタムCSS (カード型UI・タスクカードUIの大幅刷新)
# ==========================================
CSS = """
<style>
*,*::before,*::after{-webkit-font-smoothing:antialiased;box-sizing:border-box;}
html,body,.stApp{font-family:-apple-system,"Helvetica Neue","Hiragino Sans",Arial,sans-serif;background:#F2F2F7;color:#1C1C1E;}
.block-container{padding:40px 28px 80px;max-width:780px;}
.stApp p,.stApp li{color:#1C1C1E;}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] span,
.stTextInput label,.stNumberInput label,.stSelectbox label,
.stMultiSelect label,.stSlider label,.stRadio label,.stCheckbox label
{color:#1C1C1E!important;font-size:13px;font-weight:500;}
[data-testid="stCaptionContainer"] p{color:#8E8E93!important;}
section[data-testid="stSidebar"]{background:#1C1C1E;}
section[data-testid="stSidebar"] p,section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{color:#EBEBF5!important;}
section[data-testid="stSidebar"] .stSlider>div>div>div{background:#007AFF!important;}
.pg-eyebrow{font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:#007AFF;margin-bottom:6px;}
.pg-title{font-size:28px;font-weight:700;letter-spacing:-0.5px;color:#1C1C1E;margin:0 0 6px;line-height:1.2;}
.pg-subtitle{font-size:15px;color:#8E8E93;margin:0 0 32px;line-height:1.5;}
.pg-notice{background:rgba(0,122,255,.07);border-radius:12px;padding:14px 18px;font-size:14px;color:#3A3A3C!important;line-height:1.55;margin-bottom:20px;}
.pg-notice strong{color:#007AFF!important;}
.pg-divider{height:1px;background:#E5E5EA;margin:24px 0;border:none;}
.pg-consent-card{background:#FFFFFF;border-radius:16px;padding:24px 28px;margin-bottom:20px;
 box-shadow:0 1px 3px rgba(0,0,0,.07),0 4px 12px rgba(0,0,0,.04);}
.pg-consent-section{margin-bottom:18px;}
.pg-consent-title{font-size:11px;font-weight:700;letter-spacing:1.1px;text-transform:uppercase;color:#007AFF;margin:0 0 6px;}
.pg-consent-body{font-size:14px;color:#3A3A3C;line-height:1.65;margin:0;}
.pg-consent-item{font-size:14px;color:#3A3A3C;line-height:1.65;padding-left:1em;margin:2px 0;}
.pg-consent-item::before{content:"·";margin-right:6px;color:#8E8E93;}

/* ボタン共通のモダンデザイン */
.stButton>button{border:none;border-radius:22px;font-size:15px;font-weight:600;padding:10px 28px;width:100%;transition:opacity .15s,transform .12s;}
.stButton>button[kind="primary"],.stButton>button[kind="primary"]:hover,
.stButton>button[kind="primary"]:focus,.stButton>button[kind="primary"] *
{background:#007AFF!important;color:#FFFFFF!important;}
.stButton>button[kind="primary"]:hover{opacity:.87;transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,122,255,.32);}
.stButton>button[kind="secondary"],.stButton>button:not([kind]),
.stButton>button[kind="secondary"] *,.stButton>button:not([kind]) *
{background:#E8E8ED!important;color:#1C1C1E!important;}
.stButton>button:not([kind]):hover{background:#007AFF!important;color:#FFFFFF!important;}
.stButton>button:active{transform:scale(.98);}

/* =========================================
   Step 2: カード型チェックボックス UI
   ========================================= */
div[data-testid="stCheckbox"] {
    background: #FFFFFF;
    border: 2px solid #E5E5EA;
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    transition: all 0.2s ease-in-out;
    display: flex;
    align-items: center;
}
div[data-testid="stCheckbox"]:hover {
    border-color: #30D158;
    box-shadow: 0 4px 14px rgba(48, 209, 88, 0.15);
    transform: translateY(-1px);
}
div[data-testid="stCheckbox"]:has(input:checked) {
    border-color: #30D158;
    background: rgba(48, 209, 88, 0.05);
}
div[data-testid="stCheckbox"] label { cursor: pointer; width: 100%; }
.stCheckbox [role="checkbox"],[data-testid="stCheckbox"] [role="checkbox"]{background:#FFFFFF!important;border:1.5px solid #C7C7CC!important;border-radius:4px!important;}
.stCheckbox [role="checkbox"][aria-checked="true"],[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"]{background:#30D158!important;border-color:#30D158!important;}
.stCheckbox label p,.stCheckbox label span{color:#1C1C1E!important;font-size:14px!important;font-weight:600;}

/* =========================================
   Step 4: 1タップ即決タスクカード UI
   ========================================= */
.pg-task-card {
    background: #FFFFFF;
    border: 2px solid #E5E5EA;
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 20px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
    transition: all 0.2s ease-in-out;
}
.pg-task-card:hover {
    border-color: #007AFF;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,122,255,0.08);
}

.stTextInput>div>div>input{border-radius:10px!important;border:1.5px solid #E5E5EA!important;background:#FFFFFF!important;font-size:15px!important;padding:10px 14px!important;color:#1C1C1E!important;}
.stTextInput>div>div>input::placeholder{color:#C7C7CC!important;opacity:1;}
.stTextInput>div>div>input:focus{border-color:#007AFF!important;box-shadow:0 0 0 3px rgba(0,122,255,.12)!important;}
.stNumberInput>div,.stNumberInput div[data-baseweb="input"],.stNumberInput div[data-baseweb="base-input"]{background:#FFFFFF!important;border:1.5px solid #E5E5EA!important;border-radius:10px!important;}
.stNumberInput input{background:#FFFFFF!important;color:#1C1C1E!important;font-size:15px!important;}
.stNumberInput button{background:transparent!important;color:#3A3A3C!important;border:none!important;}
.stNumberInput button svg{fill:#3A3A3C!important;}
div[data-baseweb="select"]>div{border-radius:10px!important;border:1.5px solid #E5E5EA!important;background:#FFFFFF!important;}
div[data-baseweb="select"]>div:focus-within{border-color:#007AFF!important;box-shadow:0 0 0 3px rgba(0,122,255,.12)!important;}
div[data-baseweb="select"] span,div[data-baseweb="select"] div,div[data-baseweb="select"] p,
div[data-baseweb="select"] *:not(svg):not(path):not([data-baseweb="tag"]){color:#1C1C1E!important;}
div[data-baseweb="select"] input::placeholder{color:#C7C7CC!important;}
div[data-baseweb="tag"]{background:rgba(0,122,255,0.1)!important;border:none!important;border-radius:100px!important;}
div[data-baseweb="tag"] span,div[data-baseweb="tag"] div{color:#007AFF!important;}
ul[data-baseweb="menu"],div[data-baseweb="popover"]>div[role="listbox"]{background:#FFFFFF!important;border:1px solid #E5E5EA!important;border-radius:12px!important;box-shadow:0 4px 20px rgba(0,0,0,0.1)!important;}
ul[data-baseweb="menu"] li{background:#FFFFFF!important;color:#1C1C1E!important;}
ul[data-baseweb="menu"] li *{color:#1C1C1E!important;}
ul[data-baseweb="menu"] li:hover{background:#F2F2F7!important;}
ul[data-baseweb="menu"] li[aria-selected="true"]{background:rgba(0,122,255,0.08)!important;}
.stRadio [role="radio"],[data-testid="stRadio"] [role="radio"]{background:#FFFFFF!important;border:1.5px solid #C7C7CC!important;border-radius:50%!important;}
.stRadio [role="radio"][aria-checked="true"],[data-testid="stRadio"] [role="radio"][aria-checked="true"]{background:#007AFF!important;border-color:#007AFF!important;}
.stRadio [data-testid="stWidgetLabel"] p,.stRadio label p,.stRadio label span{font-size:15px!important;color:#1C1C1E!important;}
.stSlider>div>div>div{background:#007AFF!important;}
.stSlider [data-testid="stTickBarMin"],.stSlider [data-testid="stTickBarMax"],
.stSlider [data-testid="stSliderTickBarMin"],.stSlider [data-testid="stSliderTickBarMax"],
.stSlider p{color:#3A3A3C!important;}
[data-testid="stPopoverBody"],[data-testid="stPopoverBody"]>div,
div[role="dialog"],div[role="dialog"]>div,div[role="tooltip"],
.stPopover div[data-baseweb="popover"]
{background:#FFFFFF!important;background-color:#FFFFFF!important;
 border:none!important;border-radius:20px!important;
 box-shadow:0 12px 40px rgba(0,0,0,0.10),0 2px 8px rgba(0,0,0,0.06)!important;}
[data-testid="stPopoverBody"] *,div[role="dialog"] p,div[role="dialog"] span,
div[role="dialog"] div,div[role="dialog"] strong{color:#1C1C1E!important;background-color:transparent;}
[data-testid="stPopoverBody"]>div>div{padding:12px 16px!important;}
.stPopover button,[data-testid="stPopover"] button{background:transparent!important;border:none!important;font-size:18px!important;color:#8E8E93!important;line-height:1;}
[data-testid="stExpander"]{border:1px solid #E5E5EA!important;border-radius:12px!important;background:#FFFFFF!important;overflow:hidden;}
[data-testid="stExpander"] summary{background:#FFFFFF!important;padding:12px 16px!important;}
[data-testid="stExpander"] summary p,[data-testid="stExpander"] summary span,
[data-testid="stExpanderToggleIcon"]{color:#1C1C1E!important;}
[data-testid="stExpander"]>div:last-child{background:#FFFFFF!important;padding:4px 16px 16px!important;}
.pg-progress-track{height:3px;background:#E5E5EA;border-radius:100px;margin-bottom:40px;overflow:hidden;}
.pg-progress-fill{height:3px;background:#007AFF;border-radius:100px;transition:width .4s;}
.pg-task-q{font-size:15px;color:#8E8E93;text-align:center;margin-bottom:4px;}
.pg-task-book{font-size:22px;font-weight:700;color:#007AFF;text-align:center;letter-spacing:-.3px;margin-bottom:28px;}
.pg-option-badge{display:inline-block;background:#007AFF;color:#FFFFFF;font-size:12px;font-weight:700;letter-spacing:.8px;padding:3px 12px;border-radius:100px;margin-bottom:12px;}
.pg-qr-wrap{text-align:center;padding:20px 0;}
.stSuccess>div{border-radius:10px!important;border:none!important;background:rgba(48,209,88,0.1)!important;}
.stSuccess p{color:#1C7A3A!important;font-weight:600!important;font-size:14px!important;}
@media(max-width:600px){
    .block-container{padding:24px 12px 60px!important;}
    div[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;}
    div[data-testid="column"]{flex:1 1 260px!important;min-width:0!important;}
}
#MainMenu,footer,header,.stDeployButton{visibility:hidden;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def hd(eb,ti,su=None):
    st.markdown(f'<p class="pg-eyebrow">{eb}</p><h1 class="pg-title">{ti}</h1>',unsafe_allow_html=True)
    if su: st.markdown(f'<p class="pg-subtitle">{su}</p>',unsafe_allow_html=True)
def hr(): st.markdown('<hr class="pg-divider">',unsafe_allow_html=True)
def reset_session():
    adm=st.session_state.is_admin; adm_mode=st.session_state.admin_mode; amp=st.session_state.amp_power
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.session_state.is_admin=adm; st.session_state.admin_mode=adm_mode; st.session_state.amp_power=amp
    st.session_state.session_id=str(uuid.uuid4()); st.session_state.step=1; st.session_state.user_data={}
    st.session_state.selected_books=[]; st.session_state.task_queue=[]; st.session_state.current_q_index=0
    st.session_state.results=[]; st.session_state.current_options=[]

IMAGE_DIR = "phonoglyphs_v19"
DB_PATH = "features_db.pkl"
DEPLOY_URL = "https://phonoglyph-task.streamlit.app/"

@st.cache_data
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'rb') as f: return pickle.load(f)
    return {}

def _get_fallback_df(base_df):
    df=base_df.copy(); df['ローマ字ファイル名']=df['SystemKey']
    df['日本語書籍名']=df['SystemKey'].apply(lambda x:str(x).split('_')[0])
    df['著者名']='不明'; df['知名度スコア']=0; df['発表年']=9999; df['ジャンル']='不明'; df['あらすじ']='あらすじ情報なし'
    return df

def load_book_metadata(all_books_list):
    all_books_df=pd.DataFrame({'SystemKey':all_books_list})
    possible_files=glob.glob('*book_mapping*.xlsx')
    if not possible_files:
        st.session_state.debug_error="Excelファイルが見つかりません"
        return _get_fallback_df(all_books_df)
    possible_files.sort(key=os.path.getmtime,reverse=True)
    target_file=possible_files[0]
    for f in possible_files:
        try:
            temp=pd.read_excel(f,nrows=1)
            if 'あらすじ' in temp.columns: target_file=f; break
        except: pass
    try:
        meta_df=pd.read_excel(target_file)
        meta_df.columns=[str(c).strip().replace('\ufeff','') for c in meta_df.columns]
        if 'ローマ字ファイル名' not in meta_df.columns:
            meta_df.rename(columns={meta_df.columns[0]:'ローマ字ファイル名'},inplace=True)
        matched_rows=[]
        romaji_series=meta_df['ローマ字ファイル名'].astype(str).str.lower().str.replace(' ','').str.replace('　','')
        title_author_series=(meta_df.get('日本語書籍名','')+'_'+meta_df.get('著者名','')).astype(str).str.lower().str.replace(' ','').str.replace('　','')
        title_only_series=meta_df.get('日本語書籍名','').astype(str).str.lower().str.replace(' ','').str.replace('　','')
        for sys_key in all_books_list:
            sys_key_clean=str(sys_key).lower().replace(' ','').replace('　','')
            sys_title_only=sys_key_clean.split('_')[0]
            m1=meta_df[romaji_series==sys_key_clean]; m2=meta_df[title_author_series==sys_key_clean]; m3=meta_df[title_only_series==sys_title_only]
            if not m1.empty: matched_rows.append(m1.iloc[0].to_dict())
            elif not m2.empty: matched_rows.append(m2.iloc[0].to_dict())
            elif not m3.empty: matched_rows.append(m3.iloc[0].to_dict())
            else: matched_rows.append({})
        matched_df=pd.DataFrame(matched_rows)
        merged_df=pd.concat([all_books_df,matched_df],axis=1)
        merged_df['ローマ字ファイル名']=merged_df['SystemKey']
        merged_df['日本語書籍名']=merged_df.get('日本語書籍名',merged_df['SystemKey']).fillna(merged_df['SystemKey'].apply(lambda x:str(x).split('_')[0]))
        merged_df['著者名']=merged_df.get('著者名','不明').fillna('不明')
        merged_df['知名度スコア']=pd.to_numeric(merged_df.get('知名度スコア',0),errors='coerce').fillna(0)
        merged_df['発表年']=pd.to_numeric(merged_df.get('発表年',9999),errors='coerce').fillna(9999)
        merged_df['ジャンル']=merged_df.get('ジャンル','不明').fillna('不明').astype(str).str.strip()
        merged_df['あらすじ']=merged_df.get('あらすじ','あらすじ情報なし').fillna('あらすじ情報なし')
        st.session_state.debug_target_file=target_file; st.session_state.debug_match_count=sum(1 for d in matched_rows if d)
        return merged_df
    except Exception as e:
        st.session_state.debug_error=str(e)
        return _get_fallback_df(all_books_df)

def get_image_path(book_name):
    for d in glob.glob(f"{IMAGE_DIR}*"):
        p=os.path.join(d,f"{book_name}_v19.png")
        if os.path.exists(p): return p
    return None

DB_DATA = load_database()
ALL_BOOKS = sorted(list(DB_DATA.keys()))
BOOK_META_DF = load_book_metadata(ALL_BOOKS)

def get_display_name(roman_name):
    row=BOOK_META_DF[BOOK_META_DF['ローマ字ファイル名']==roman_name]
    if not row.empty and row.iloc[0]['著者名']!='不明': return f"『{row.iloc[0]['日本語書籍名']}』"
    return f"『{str(roman_name).split('_')[0]}』"

def async_save_to_sheet(row_data):
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        if "gcp_service_account" in st.secrets:
            sc = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            cr = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=sc)
            cl = gspread.authorize(cr)
            sh = cl.open_by_url(st.secrets["private_gsheets_url"]).sheet1
            for att in range(3):
                try: sh.append_row(row_data); break
                except: time.sleep(2**att + random.uniform(0, 1))
    except Exception as e: print(f"Async save error: {e}")

if 'session_id' not in st.session_state: st.session_state.session_id=str(uuid.uuid4())
if 'step' not in st.session_state: st.session_state.step=1
if 'user_data' not in st.session_state: st.session_state.user_data={}
if 'selected_books' not in st.session_state: st.session_state.selected_books=[]
if 'task_queue' not in st.session_state: st.session_state.task_queue=[]
if 'current_q_index' not in st.session_state: st.session_state.current_q_index=0
if 'results' not in st.session_state: st.session_state.results=[]
if 'current_options' not in st.session_state: st.session_state.current_options=[]
if 'is_admin' not in st.session_state: st.session_state.is_admin=False
if 'admin_mode' not in st.session_state: st.session_state.admin_mode="実験タスク (被験者用)"
if 'amp_power' not in st.session_state: st.session_state.amp_power=0.8

def get_dummies(target_book):
    pool=[b for b in ALL_BOOKS if b not in st.session_state.selected_books and b!=target_book and b in DB_DATA]
    if len(pool)<5: return random.sample(pool,len(pool))
    pool_sorted=sorted(pool,key=lambda b:DB_DATA[b][7])
    ls=max(2,len(pool_sorted)//5)
    return random.sample(pool_sorted[:ls],2)+random.sample(pool_sorted[-ls:],3)

def render_topbar():
    st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px">'
                '<div style="font-weight:800;font-size:18px;letter-spacing:-.5px;color:#1C1C1E">Phonoglyph</div>'
                f'<div style="font-size:12px;font-weight:600;color:#007AFF;background:rgba(0,122,255,.1);padding:4px 10px;border-radius:100px">ID: {st.session_state.session_id[:6]}</div>'
                '</div>',unsafe_allow_html=True)

def render_step1():
    hd("Step 1 / 5","実験への参加","以下の説明をよくお読みのうえ、同意いただける場合は基本情報をご入力ください。")
    st.markdown("""
<div class="pg-consent-card">
<div class="pg-consent-section">
  <p class="pg-consent-title">研究の概要</p>
  <p class="pg-consent-body">本研究は東京電機大学 インタラクティブアート&amp;デザイン研究室が実施する学術調査です。<br>
  <strong style="color:#1C1C1E">目的：</strong>文章の「音の響き」から生成した抽象図形が、書籍の雰囲気を直感的に伝える指標として機能するかを検証します。</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">参加内容と所要時間</p>
  <p class="pg-consent-item">読書体験に関する事前アンケート（1〜2分）</p>
  <p class="pg-consent-item">既読の書籍に対応する抽象図形を6択から選ぶタスク（選択作品数 × 約20秒）</p>
  <p class="pg-consent-item">合計所要時間の目安：5〜15分程度</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">個人情報の保護</p>
  <p class="pg-consent-item">入力された情報は研究目的にのみ使用し、氏名などの個人を特定できる情報は収集しません。</p>
  <p class="pg-consent-item">収集データは暗号化された安全な環境で管理され、研究終了後に適切に廃棄されます。</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">参加の任意性</p>
  <p class="pg-consent-item">本実験への参加は完全に任意です。途中でやめても何ら不利益は生じません。</p>
</div>
<div class="pg-consent-section" style="margin-bottom:0">
  <p class="pg-consent-title">問い合わせ先</p>
  <p class="pg-consent-body" style="font-size:13px;color:#8E8E93">東京電機大学 システムデザイン工学部 デザイン工学科<br>インタラクティブアート&amp;デザイン研究室　担当：熊谷 天</p>
</div>
</div>
""", unsafe_allow_html=True)
    consent=st.checkbox("上記の内容を理解し、実験への参加に同意します"); hr()
    
    c1,c2,c3=st.columns(3)
    with c1: age=st.number_input("年齢",min_value=15,max_value=100,value=20,step=1)
    with c2: gender=st.radio("性別",["男性","女性","その他"],horizontal=True)
    with c3: major=st.radio("専攻分野",["理数系","文系","芸術・デザイン系","その他"],horizontal=True)
        
    rf=st.selectbox("読書頻度",["月に1〜2冊","月に3〜5冊","月に6冊以上","全く読まない"],index=None,placeholder="選択してください")
    gn=st.multiselect("よく読むジャンル",["純文学","大衆文学","SF","ラノベ","実用書","その他"])
    syn=st.slider("言葉の響きに色や形を感じるか（1: 全く感じない — 5: 強く感じる）",1,5,3)
    hr(); _,cb=st.columns([1,1])
    with cb:
        if st.button("次へ進む",key="s1_next",type="primary"):
            if not consent: st.error("実験への参加に同意してください。")
            elif rf is None: st.error("読書頻度を選択してください。")
            else:
                st.session_state.user_data={"age":age,"gender":gender,"major":major,"reading_freq":rf,"genres":", ".join(gn),"synesthesia_score":syn}
                st.session_state.step=2; st.rerun()

def render_step2():
    hd("Step 2 / 5","既読作品の選択","内容を知っている作品を選択してください。📖ボタンであらすじ等を確認できます。")
    st.markdown('<div class="pg-notice">最低1冊以上選択してください。選択した作品の数だけタスクが出題されます。</div>',unsafe_allow_html=True)
    cs,co,cg=st.columns([2,1.5,1.5])
    with cs: sq=st.text_input("🔍 検索",placeholder="作品名・著者名")
    with co: sb=st.selectbox("並び替え", ["人気・知名度順","五十音順 (作品名)","五十音順 (著者名)","発表年が新しい順","発表年が古い順"])
    with cg: 
        ug=["すべて"]+[g for g in BOOK_META_DF['ジャンル'].unique() if g!='不明']
        gf=st.selectbox("ジャンル",ug)
    
    df=BOOK_META_DF.copy()
    if sq: df=df[df['日本語書籍名'].astype(str).str.contains(sq,case=False,na=False)|df['著者名'].astype(str).str.contains(sq,case=False,na=False)]
    if gf!="すべて": df=df[df['ジャンル'].astype(str).str.strip()==gf.strip()]
    if sb=="人気・知名度順": df=df.sort_values(by=['知名度スコア','日本語書籍名'],ascending=[False,True])
    elif sb=="五十音順 (作品名)": df=df.sort_values(by='日本語書籍名',ascending=True)
    elif sb=="五十音順 (著者名)": df=df.sort_values(by=['著者名','日本語書籍名'],ascending=[True,True])
    elif sb=="発表年が新しい順": df=df.sort_values(by=['発表年','日本語書籍名'],ascending=[False,True])
    elif sb=="発表年が古い順": df=df.sort_values(by=['発表年','日本語書籍名'],ascending=[True,True])

    dr=df.to_dict('records')
    st.caption(f"該当: {len(dr)} 件")

    for i in range(0,len(dr),3):
        cols=st.columns(3)
        for j in range(3):
            if i+j<len(dr):
                r=dr[i+j]; rn=r['ローマ字ファイル名']; jp=r['日本語書籍名']; au=r['著者名']
                dl=f"『{jp}』\n{au}" if au!='不明' else f"『{jp}』"
                with cols[j]:
                    cc,cb=st.columns([4,1])
                    with cc:
                        ic=rn in st.session_state.selected_books
                        if st.checkbox(dl,value=ic,key=f"chk_{rn}"):
                            if rn not in st.session_state.selected_books: st.session_state.selected_books.append(rn)
                        else:
                            if rn in st.session_state.selected_books: st.session_state.selected_books.remove(rn)
                    with cb:
                        with st.popover("📖",key=f"pop_{rn}"):
                            st.markdown(f'<p style="font-weight:700;font-size:16px;margin-bottom:4px;color:#1C1C1E">『{jp}』</p>',unsafe_allow_html=True)
                            if au!='不明':
                                st.caption(f"著者: {au} | {r['ジャンル']} | {r['発表年']}年")
                                hr(); st.markdown(f'<p style="font-size:14px;line-height:1.6;color:#3A3A3C">{r["あらすじ"]}</p>',unsafe_allow_html=True)
                            else: st.caption("詳細情報なし")

    hr()
    if st.session_state.selected_books: st.success(f"現在の選択数: {len(st.session_state.selected_books)} 冊")
    cbk,cn=st.columns([1,1])
    with cbk:
        if st.button("戻る",key="s2_back"): st.session_state.step=1; st.rerun()
    with cn:
        if st.button("次へ進む",key="s2_next",type="primary"):
            if not st.session_state.selected_books: st.error("最低1冊は選択してください。")
            else:
                st.session_state.task_queue=st.session_state.selected_books.copy()
                random.shuffle(st.session_state.task_queue)
                st.session_state.step=3; st.rerun()

def render_step3():
    hd("Step 3 / 5","事前アンケート","マッチングタスクを開始する前に、普段の読書体験についてお答えください。")
    st.markdown('<div class="pg-notice">質問はすべて<strong>直感</strong>でお答えください。</div>',unsafe_allow_html=True)
    q1=st.radio("Q1. 表紙のデザインやイラストに惹かれて本を買ったこと（ジャケ買い）はありますか？",["はい","いいえ"],horizontal=True)
    hr()
    q2=st.radio("Q2. ジャケ買いをした結果、中身の文章の雰囲気や読みやすさが表紙の印象と違って、読むのをやめたりガッカリした経験はありますか？",["よくある","たまにある","あまりない","全くない"],horizontal=True)
    hr()
    q3=st.radio("Q3. あらすじや表紙だけでなく、事前に「文章の響きやリズム（文体）」が直感的に分かる指標があれば、本選びの参考にしたいと思いますか？",["思う","やや思う","あまり思わない","思わない"],horizontal=True)
    hr(); cbk,cn=st.columns([1,1])
    with cbk:
        if st.button("戻る",key="s3_back"): st.session_state.step=2; st.rerun()
    with cn:
        if st.button("タスクを開始する",key="s3_start",type="primary"):
            st.session_state.user_data.update({"q1":q1,"q2":q2,"q3":q3})
            st.session_state.step=4; st.rerun()

def render_step4():
    if st.session_state.current_q_index >= len(st.session_state.task_queue):
        st.session_state.step = 5
        st.rerun()

    # セッションステート初期化
    if 'temp_selected_idx' not in st.session_state:
        st.session_state.temp_selected_idx = None

    idx = st.session_state.current_q_index
    tot = len(st.session_state.task_queue)
    
    st.markdown(f'<div class="pg-progress-track"><div class="pg-progress-fill" style="width:{idx/tot*100:.1f}%"></div></div>', unsafe_allow_html=True)
    tb = st.session_state.task_queue[idx]
    dn = get_display_name(tb)
    
    st.markdown(f'<p class="pg-task-q">{idx+1} / {tot} — 音の紋様を選んでください</p><p class="pg-task-book">{dn}</p>', unsafe_allow_html=True)
    
    if not st.session_state.current_options:
        opts = get_dummies(tb)
        opts.append(tb)
        random.shuffle(opts)
        st.session_state.current_options = opts
        st.session_state.temp_selected_idx = None # 新問でリセット

    opts = st.session_state.current_options
    
    # 3x2 のグリッドで図形を表示
    for row_start in [0, 3]:
        cols = st.columns(3)
        for j in range(3):
            opt_idx = row_start + j
            if opt_idx >= len(opts): break
            
            with cols[j]:
                # 選択されているか判定
                is_selected = (st.session_state.temp_selected_idx == opt_idx)
                card_style = "border: 3px solid #007AFF;" if is_selected else "border: 2px solid #E5E5EA;"
                
                st.markdown(f'<div class="pg-task-card" style="{card_style}">', unsafe_allow_html=True)
                ip = get_image_path(opts[opt_idx])
                if ip: st.image(Image.open(ip), use_container_width=True)
                
                # 選択ボタン
                if st.button(f"選択する", key=f"sel_{idx}_{opt_idx}"):
                    st.session_state.temp_selected_idx = opt_idx
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    hr()
    # 確定ボタン（選択中のみアクティブ）
    if st.session_state.temp_selected_idx is not None:
        if st.button("この紋様で確定して次へ", type="primary", use_container_width=True):
            ch = opts[st.session_state.temp_selected_idx]
            ic = (ch == tb)
            
            # データの準備
            u = st.session_state.user_data
            ts = datetime.now(timezone(timedelta(hours=9), "JST")).strftime("%Y/%m/%d %H:%M:%S")
            hn = f"anon_{st.session_state.session_id[-6:]}"
            
            row_data = [ts, st.session_state.session_id, hn, u.get("age",""), u.get("gender",""), u.get("major",""),
                        u.get("reading_freq",""), u.get("genres",""), u.get("synesthesia_score",""),
                        u.get("q1",""), u.get("q2",""), u.get("q3",""), 0, tb, ch, "正解" if ic else "不正解"]
            
            threading.Thread(target=async_save_to_sheet, args=(row_data,), daemon=True).start()
            
            st.session_state.current_q_index += 1
            st.session_state.current_options = []
            st.session_state.temp_selected_idx = None
            st.rerun()
    else:
        st.button("選択してください", disabled=True, use_container_width=True)

def render_step5():
    st.balloons()
    hd("Step 5 / 5", "実験完了", "すべてのタスクが終了しました。ご協力いただき誠にありがとうございました。")
    st.markdown("""
    <div class="pg-notice" style="background:#FFFFFF; border:2px solid #E5E5EA; padding:32px;">
        <h3 style="color:#007AFF; margin-top:0; margin-bottom:16px;">Phonoglyph 研究プロジェクト</h3>
        <p style="font-size:15px; line-height:1.7;">文章の音の響き（音象徴）から直感的な図形を生成し、未知の書籍との新しい出会いを創出するための研究にご参加いただき、深く感謝申し上げます。</p>
        <p style="font-size:15px; line-height:1.7;">皆様からいただいた直感的な評価データは、本研究のアルゴリズムを検証・発展させるための極めて重要な基礎となります。貴重なお時間を割いていただき、本当にありがとうございました。</p>
    </div>
    """, unsafe_allow_html=True)
    hr()
    qru=f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(DEPLOY_URL)}"
    st.markdown(f'<div class="pg-qr-wrap"><img src="{qru}" width="160" style="border-radius:12px"></div>',unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:13px;color:#8E8E93;margin:8px 0 4px">右上のアイコンでURLをコピーしてシェアできます</p>',unsafe_allow_html=True)
    st.code(DEPLOY_URL, language=None)
    hr()
    cl5,cr5=st.columns(2)
    with cl5:
        if st.button("トップに戻る",key="restart",type="primary"): reset_session(); st.rerun()
    with cr5: st.caption("新しいセッションが始まります。\n別の被験者がすぐに実験を開始できます。")

def render_simulator():
    hd("管理者","Phonoglyph シミュレーター","音素パラメータをリアルタイムで変化させて図形を確認できます。")
    BL=phonoglyph_math.BASELINE; cp,cv=st.columns([1,1.5])
    with cp:
        vf=st.slider("前舌母音 VF",0.0,50.0,BL["vf"]); vb=st.slider("後舌母音 VB",0.0,50.0,BL["vb"])
        obs=st.slider("阻害音 OBS",0.0,50.0,BL["obs"]); son=st.slider("共鳴音 SON",0.0,50.0,BL["son"])
        hr(); st.caption("有声音 VD（交絡変数排除のため固定）")
        vd=st.slider("VD",0.0,20.0,BL["vd"],disabled=True,label_visibility="collapsed")
        hr(); st.caption("増幅係数 β")
        st.session_state.amp_power=st.slider("β",0.1,2.0,st.session_state.amp_power,0.1,label_visibility="collapsed")
    with cv:
        x,y,lw=phonoglyph_math.calculate_phonoglyph_coordinates(vf,vb,obs,son,vd,amp_power=st.session_state.amp_power)
        fig,ax=plt.subplots(figsize=(5,5),facecolor="white")
        ax.plot(x,y,color="black",linewidth=lw,solid_joinstyle="round")
        ax.fill(x,y,color="black",alpha=0.05); ax.set_aspect("equal"); ax.axis("off"); st.pyplot(fig)

def main():
    mode=st.query_params.get("mode")
    if isinstance(mode,list): mode=mode[0] if mode else None
    if mode=="admin": st.session_state.is_admin=True
    if mode=="sim": st.session_state.is_admin=True; st.session_state.admin_mode="シミュレーター (デモ用)"

    with st.sidebar:
        st.markdown("### 🌒 Phonoglyph")
        hr()
        if not st.session_state.is_admin:
            st.caption("管理者・研究者向け")
            if st.button("管理者モードに切り替え",key="admin_on"): st.session_state.is_admin=True; st.rerun()
        else:
            st.caption("管理者モード 有効")
            sel=st.radio("表示モード",["実験タスク","シミュレーター"],index=0 if st.session_state.admin_mode=="実験タスク (被験者用)" else 1)
            st.session_state.admin_mode="実験タスク (被験者用)" if sel=="実験タスク" else "シミュレーター (デモ用)"
            hr()
            st.caption(f"読込: {st.session_state.get('debug_target_file','—')}")
            st.caption(f"結合: {st.session_state.get('debug_match_count',0)}/{len(ALL_BOOKS)} 件")
            if st.button("管理者モードを解除",key="admin_off"): st.session_state.is_admin=False; st.session_state.admin_mode="実験タスク (被験者用)"; st.rerun()

    render_topbar()
    if st.session_state.admin_mode=="実験タスク (被験者用)":
        {1:render_step1,2:render_step2,3:render_step3,4:render_step4,5:render_step5}.get(st.session_state.step,render_step1)()
    else: render_simulator()

if __name__=="__main__": main()