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

st.set_page_config(page_title="Phonoglyph", page_icon="🌒",
                   layout="centered", initial_sidebar_state="collapsed")

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
.stButton>button{border:none;border-radius:22px;font-size:15px;font-weight:600;padding:10px 28px;width:100%;transition:opacity .15s,transform .12s;}
.stButton>button[kind="primary"],.stButton>button[kind="primary"]:hover,
.stButton>button[kind="primary"]:focus,.stButton>button[kind="primary"] *
{background:#007AFF!important;color:#FFFFFF!important;}
.stButton>button[kind="primary"]:hover{opacity:.87;transform:translateY(-1px);box-shadow:0 4px 16px rgba(0,122,255,.32);}
.stButton>button[kind="secondary"],.stButton>button:not([kind]),
.stButton>button[kind="secondary"] *,.stButton>button:not([kind]) *
{background:#E8E8ED!important;color:#1C1C1E!important;}
.stButton>button:active{transform:scale(.98);}
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
.stCheckbox [role="checkbox"],[data-testid="stCheckbox"] [role="checkbox"]{background:#FFFFFF!important;border:1.5px solid #C7C7CC!important;border-radius:4px!important;}
.stCheckbox [role="checkbox"][aria-checked="true"],[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"]{background:#007AFF!important;border-color:#007AFF!important;}
.stCheckbox label p,.stCheckbox label span{color:#1C1C1E!important;font-size:14px!important;}
.stCheckbox>label{border-radius:8px;padding:5px 6px;transition:background .15s;cursor:pointer;}
.stCheckbox>label:hover{background:rgba(0,122,255,0.06)!important;}
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
.pg-option-badge{display:inline-block;background:#F2F2F7;color:#3A3A3C;font-size:11px;font-weight:700;letter-spacing:.8px;padding:2px 9px;border-radius:100px;margin-bottom:8px;}
.pg-result-wrap{text-align:center;padding:40px 0 24px;}
.pg-result-num{font-size:86px;font-weight:700;letter-spacing:-5px;color:#30D158!important;line-height:1;}
.pg-result-unit{font-size:32px;font-weight:600;color:#30D158!important;letter-spacing:-1px;}
.pg-result-caption{font-size:15px;color:#8E8E93!important;margin-top:8px;}
.pg-qr-wrap{text-align:center;padding:20px 0;}
.pg-qr-caption{font-size:12px;color:#8E8E93;margin-top:10px;font-family:"Menlo","SF Mono",monospace;}
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

IMAGE_DIR="phonoglyphs_v19"; IMG_SUFFIX="_v19.png"
DB_PATH="features_db.pkl"; DEPLOY_URL="https://phonoglyph-task.streamlit.app/"

@st.cache_data
def load_database():
    if os.path.exists(DB_PATH):
        with open(DB_PATH,"rb") as f: return pickle.load(f)
    return {}

@st.cache_data
def _build_image_cache():
    cache={}
    for d in glob.glob(f"{IMAGE_DIR}*"):
        if os.path.isdir(d):
            for p in glob.glob(os.path.join(d,"*.png")):
                cache[os.path.basename(p).replace(IMG_SUFFIX,"")] = p
    return cache

def get_image_path(n): return _build_image_cache().get(n)

def _fallback_df(b):
    df=b.copy(); df["ローマ字ファイル名"]=df["SystemKey"]
    df["日本語書籍名"]=df["SystemKey"].apply(lambda x:str(x).split("_")[0])
    df["著者名"]="不明"; df["知名度スコア"]=0; df["発表年"]=9999
    df["ジャンル"]="不明"; df["あらすじ"]="あらすじ情報なし"
    return df

@st.cache_data
def _load_metadata_core(tup):
    lst=list(tup); base=pd.DataFrame({"SystemKey":lst}); dbg={}
    files=glob.glob("*book_mapping*.xlsx")
    if not files: dbg["error"]="book_mapping が見つかりません"; return _fallback_df(base),dbg
    files.sort(key=os.path.getmtime,reverse=True); tgt=files[0]
    for f in files:
        try:
            if "あらすじ" in pd.read_excel(f,nrows=1).columns: tgt=f; break
        except: pass
    dbg["target_file"]=tgt
    try:
        meta=pd.read_excel(tgt)
        meta.columns=[str(c).strip().replace("﻿","") for c in meta.columns]
        if "ローマ字ファイル名" not in meta.columns:
            meta.rename(columns={meta.columns[0]:"ローマ字ファイル名"},inplace=True)
        s_r=meta["ローマ字ファイル名"].astype(str).str.lower().str.replace(" ","").str.replace("　","")
        s_ta=(meta.get("日本語書籍名","")+"_"+meta.get("著者名","")).astype(str).str.lower().str.replace(" ","").str.replace("　","")
        s_t=meta.get("日本語書籍名","").astype(str).str.lower().str.replace(" ","").str.replace("　","")
        rows=[]
        for k in lst:
            kc=str(k).lower().replace(" ","").replace("　",""); kt=kc.split("_")[0]
            m1=meta[s_r==kc]; m2=meta[s_ta==kc]; m3=meta[s_t==kt]
            if not m1.empty: rows.append(m1.iloc[0].to_dict())
            elif not m2.empty: rows.append(m2.iloc[0].to_dict())
            elif not m3.empty: rows.append(m3.iloc[0].to_dict())
            else: rows.append({})
        matched=pd.DataFrame(rows); merged=pd.concat([base,matched],axis=1)
        merged["ローマ字ファイル名"]=merged["SystemKey"]
        merged["日本語書籍名"]=merged.get("日本語書籍名",merged["SystemKey"]).fillna(merged["SystemKey"].apply(lambda x:str(x).split("_")[0]))
        merged["著者名"]=merged.get("著者名","不明").fillna("不明")
        merged["知名度スコア"]=pd.to_numeric(merged.get("知名度スコア",0),errors="coerce").fillna(0)
        merged["発表年"]=pd.to_numeric(merged.get("発表年",9999),errors="coerce").fillna(9999)
        merged["ジャンル"]=merged.get("ジャンル","不明").fillna("不明").astype(str).str.strip()
        merged["あらすじ"]=merged.get("あらすじ","あらすじ情報なし").fillna("あらすじ情報なし")
        for col in ["著者名読み","日本語書籍名読み"]:
            if col in meta.columns:
                merged[col]=merged.get(col,"").fillna("")
            else:
                merged[col]=""
        dbg.update({"columns":list(meta.columns),"sys_keys":lst[:5],
                    "meta_keys":meta["ローマ字ファイル名"].tolist()[:5],
                    "match_count":sum(1 for r in rows if r)})
        return merged,dbg
    except Exception as e:
        dbg["error"]=str(e); return _fallback_df(base),dbg

def load_book_metadata(lst):
    df,dbg=_load_metadata_core(tuple(lst))
    for k,v in dbg.items(): st.session_state[f"debug_{k}"]=v
    return df

DB_DATA=load_database(); ALL_BOOKS=sorted(list(DB_DATA.keys()))
BOOK_META_DF=load_book_metadata(ALL_BOOKS)

def get_display_name(r):
    row=BOOK_META_DF[BOOK_META_DF["ローマ字ファイル名"]==r]
    if not row.empty and row.iloc[0]["著者名"]!="不明": return f"『{row.iloc[0]['日本語書籍名']}』"
    return f"『{str(r).split('_')[0]}』"

_def={"session_id":str(uuid.uuid4()),"step":1,"user_data":{},"selected_books":[],
      "task_queue":[],"current_q_index":0,"results":[],"current_options":[],
      "data_saved":False,"is_admin":False,"admin_mode":"実験タスク (被験者用)","amp_power":0.8}
for k,v in _def.items():
    if k not in st.session_state: st.session_state[k]=v

def get_dummies(t):
    pool=[b for b in ALL_BOOKS if b not in st.session_state.selected_books and b!=t and b in DB_DATA]
    if len(pool)<4: return random.sample(pool,len(pool))
    ps=sorted(pool,key=lambda b:DB_DATA[b][7]); lay=max(2,len(ps)//5)
    return random.sample(ps[:lay],2)+random.sample(ps[-lay:],2)

def reset_session():
    for k in ["step","user_data","selected_books","task_queue","current_q_index",
              "results","current_options","data_saved","session_id"]:
        if k in st.session_state: del st.session_state[k]

def hd(ey,ti,su=""):
    s=f'<p class="pg-eyebrow">{ey}</p><p class="pg-title">{ti}</p>'
    if su: s+=f'<p class="pg-subtitle">{su}</p>'
    st.markdown(s,unsafe_allow_html=True)

def hr(): st.markdown('<hr class="pg-divider">',unsafe_allow_html=True)

def render_topbar():
    """管理者のみ表示するシミュレーター切り替えバー"""
    if not st.session_state.is_admin:
        return  # 被験者には一切表示しない
    col_l, col_r = st.columns([7, 3])
    with col_r:
        if st.session_state.admin_mode == "シミュレーター (デモ用)":
            if st.button("← 実験タスクに戻る", key="topbar_exp"):
                st.session_state.admin_mode = "実験タスク (被験者用)"
                st.rerun()
        else:
            if st.button("⚙ シミュレーター", key="topbar_sim"):
                st.session_state.admin_mode = "シミュレーター (デモ用)"
                st.rerun()

def _sort_df(df, sb):
    """五十音順ソート：読み列があれば使用、なければ漢字列で代替"""
    has_author_yomi = "著者名読み" in df.columns and df["著者名読み"].str.strip().ne("").any()
    has_title_yomi  = "日本語書籍名読み" in df.columns and df["日本語書籍名読み"].str.strip().ne("").any()
    if sb == "人気・知名度順":
        return df.sort_values(["知名度スコア","日本語書籍名"], ascending=[False,True])
    if sb == "五十音順（作品名）":
        col = "日本語書籍名読み" if has_title_yomi else "日本語書籍名"
        return df.sort_values([col,"日本語書籍名"], ascending=[True,True])
    if sb == "五十音順（著者名）":
        col1 = "著者名読み"       if has_author_yomi else "著者名"
        col2 = "日本語書籍名読み" if has_title_yomi  else "日本語書籍名"
        return df.sort_values([col1,col2], ascending=[True,True])
    if sb == "発表年が新しい順":
        return df.sort_values(["発表年","日本語書籍名"], ascending=[False,True])
    if sb == "発表年が古い順":
        return df.sort_values(["発表年","日本語書籍名"], ascending=[True,True])
    return df

def render_step1():
    hd("Step 1 / 5","実験への参加","以下の説明をよくお読みのうえ、同意いただける場合は基本情報をご入力ください。")
    st.markdown("""
<div class="pg-consent-card">
<div class="pg-consent-section">
  <p class="pg-consent-title">研究の概要</p>
  <p class="pg-consent-body">本研究は東京電機大学 インタラクティブアート&amp;デザイン研究室（山本研）が実施する学術調査です。<br>
  <strong style="color:#1C1C1E">目的：</strong>文章の「音の響き（音素）」から生成した抽象図形が、書籍の雰囲気を直感的に伝える指標として機能するかを検証します。</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">参加内容と所要時間</p>
  <p class="pg-consent-item">読書体験に関する事前アンケート（1〜2分）</p>
  <p class="pg-consent-item">既読の書籍に対応する抽象図形を5択から選ぶタスク（選択作品数 × 約20秒）</p>
  <p class="pg-consent-item">合計所要時間の目安：5〜15分程度</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">取得するデータと利用目的</p>
  <p class="pg-consent-item">基本属性（年齢・性別・専攻・読書頻度など）</p>
  <p class="pg-consent-item">各タスクへの回答（どの図形を選んだか）</p>
  <p class="pg-consent-item">これらのデータは研究目的にのみ使用し、学術論文・学会発表での報告に用いることがあります。</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">個人情報の保護</p>
  <p class="pg-consent-item">入力された氏名は実験中の管理用に使用します。</p>
  <p class="pg-consent-item">データ保存時に氏名はハッシュ化（不可逆変換）され、氏名そのものが保存・公開されることはありません。</p>
  <p class="pg-consent-item">収集データは暗号化された安全な環境で管理され、研究終了後に適切に廃棄されます。</p>
</div>
<div class="pg-consent-section">
  <p class="pg-consent-title">参加の任意性</p>
  <p class="pg-consent-item">本実験への参加は完全に任意です。途中でやめても何ら不利益は生じません。</p>
</div>
<div class="pg-consent-section" style="margin-bottom:0">
  <p class="pg-consent-title">問い合わせ先</p>
  <p class="pg-consent-body" style="font-size:13px;color:#8E8E93">東京電機大学 システムデザイン工学部 デザイン工学科<br>インタラクティブアート&amp;デザイン研究室（山本研）　担当：熊谷 天</p>
</div>
</div>
""", unsafe_allow_html=True)
    consent=st.checkbox("上記の内容を理解し、実験への参加に同意します"); hr()
    c1,c2=st.columns(2)
    with c1:
        name=st.text_input("氏名（漢字またはカタカナ）",placeholder="例：山田 太郎")
        age=st.number_input("年齢",min_value=15,max_value=100,value=20,step=1)
    with c2:
        gender=st.radio("性別",["男性","女性","その他"],horizontal=True)
        major=st.radio("専攻分野",["理数系","文系","芸術・デザイン系","その他"],horizontal=True)
    rf=st.selectbox("読書頻度",["月に1〜2冊","月に3〜5冊","月に6冊以上","全く読まない"],
                    index=None,placeholder="選択してください")
    gn=st.multiselect("よく読むジャンル",["純文学","大衆文学","SF","ラノベ","実用書","その他"])
    syn=st.slider("言葉の響きに色や形を感じるか（1: 全く感じない — 5: 強く感じる）",1,5,3)
    hr(); _,cb=st.columns([1,1])
    with cb:
        if st.button("次へ進む",key="s1_next",type="primary"):
            if not consent: st.error("実験への参加に同意してください。")
            elif not name.strip(): st.error("氏名を入力してください。")
            elif rf is None: st.error("読書頻度を選択してください。")
            else:
                st.session_state.user_data={"name":name.strip(),"age":age,"gender":gender,"major":major,
                    "reading_freq":rf,"genres":", ".join(gn),"synesthesia_score":syn}
                st.session_state.step=2; st.rerun()

def render_step2():
    hd("Step 2 / 5","既読作品の選択","内容を知っている作品にチェックを入れてください。📖 でタイトル・あらすじを確認できます。")
    cs,co,cg=st.columns([2,1.5,1.5])
    with cs: q=st.text_input("検索",placeholder="🔍  例：人間失格",label_visibility="collapsed")
    with co:
        sb=st.selectbox("並び替え",["人気・知名度順","五十音順（作品名）","五十音順（著者名）","発表年が新しい順","発表年が古い順"],label_visibility="collapsed")
    with cg:
        gl=["すべて"]+[g for g in BOOK_META_DF["ジャンル"].unique() if g!="不明"]
        gf=st.selectbox("ジャンル",gl,label_visibility="collapsed")
    df=BOOK_META_DF.copy()
    if q: df=df[df["日本語書籍名"].astype(str).str.contains(q,case=False,na=False)|df["著者名"].astype(str).str.contains(q,case=False,na=False)]
    if gf!="すべて": df=df[df["ジャンル"].astype(str).str.strip()==gf.strip()]
    df=_sort_df(df,sb); recs=df.to_dict("records")
    st.caption(f"{len(recs)} 件表示")
    for i in range(0,len(recs),3):
        cols=st.columns(3)
        for j in range(3):
            if i+j>=len(recs): break
            row=recs[i+j]; rn=row["ローマ字ファイル名"]; jn=row["日本語書籍名"]; au=row["著者名"]
            lbl=f"『{jn}』\n({au})" if au!="不明" else f"『{jn}』"
            with cols[j]:
                c1,c2=st.columns([5,1])
                with c1:
                    ck=rn in st.session_state.selected_books
                    if st.checkbox(lbl,value=ck,key=f"chk_{rn}"):
                        if rn not in st.session_state.selected_books: st.session_state.selected_books.append(rn)
                    else:
                        if rn in st.session_state.selected_books: st.session_state.selected_books.remove(rn)
                with c2:
                    with st.popover("\U0001f4d6",key=f"pop_{rn}"):
                        if au!="不明":
                            g=row["ジャンル"]; yr=int(row["発表年"]); syn=row["あらすじ"]
                            st.markdown(
                                f'<div style="padding:20px 24px 18px">'
                                f'<p style="font-size:10px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:#007AFF;margin:0 0 8px">{g} &nbsp;·&nbsp; {yr}年</p>'
                                f'<p style="font-size:19px;font-weight:700;color:#1C1C1E;letter-spacing:-.3px;line-height:1.25;margin:0 0 4px">{jn}</p>'
                                f'<p style="font-size:13px;color:#8E8E93;margin:0 0 14px">{au}</p>'
                                f'<div style="height:1px;background:#F0F0F5;margin-bottom:12px"></div>'
                                f'<p style="font-size:14px;color:#3A3A3C;line-height:1.7;margin:0">{syn}</p>'
                                f'</div>',unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div style="padding:20px 24px 18px"><p style="font-size:19px;font-weight:700;color:#1C1C1E;margin:0 0 6px">{jn}</p><p style="font-size:13px;color:#C7C7CC;margin:0">詳細情報なし</p></div>',unsafe_allow_html=True)
    hr()
    if st.session_state.is_admin:
        with st.expander("システム診断",expanded=False):
            st.json({"読込":st.session_state.get("debug_target_file","不明"),
                     "結合":f"{st.session_state.get('debug_match_count',0)}/{len(ALL_BOOKS)}"})
            if "debug_error" in st.session_state: st.error(st.session_state.debug_error)
    n=len(st.session_state.selected_books)
    if n>0: st.success(f"✓  {n} 冊を選択中")
    else: st.caption("作品を選択してください")
    cb2,cn2=st.columns(2)
    with cb2:
        if st.button("戻る",key="s2_back"): st.session_state.step=1; st.rerun()
    with cn2:
        if st.button("次へ進む",key="s2_next",type="primary"):
            if n==0: st.error("最低 1 冊は選択してください。")
            else:
                q_=st.session_state.selected_books.copy(); random.shuffle(q_)
                st.session_state.task_queue=q_; st.session_state.step=3; st.rerun()

def render_step3():
    hd("Step 3 / 5","読書体験に関するアンケート","タスク開始前に、以下の 3 問にお答えください。"); hr()
    q1=st.radio("Q1.  表紙のデザインやイラストに惹かれて本を選んだこと（ジャケ買い）がありますか？",["はい","いいえ"],horizontal=True); hr()
    q2=st.radio("Q2.  ジャケ買いをした結果、文章の雰囲気が表紙の印象と違って読むのをやめた経験はありますか？",["よくある","たまにある","あまりない","全くない"],horizontal=True); hr()
    q3=st.radio("Q3.  あらすじや表紙だけでなく「文章の響き・文体」が直感的に分かる指標があれば、本選びの参考にしたいですか？",["思う","やや思う","あまり思わない","思わない"],horizontal=True); hr()
    cb3,cn3=st.columns(2)
    with cb3:
        if st.button("戻る",key="s3_back"): st.session_state.step=2; st.rerun()
    with cn3:
        if st.button("タスクを開始する",key="s3_start",type="primary"):
            st.session_state.user_data.update({"q1":q1,"q2":q2,"q3":q3})
            st.session_state.step=4; st.rerun()

def render_step4():
    if st.session_state.current_q_index>=len(st.session_state.task_queue):
        st.session_state.step=5; st.rerun()
    idx=st.session_state.current_q_index; tot=len(st.session_state.task_queue)
    st.markdown(f'<div class="pg-progress-track"><div class="pg-progress-fill" style="width:{idx/tot*100:.1f}%"></div></div>',unsafe_allow_html=True)
    tb=st.session_state.task_queue[idx]; dn=get_display_name(tb)
    st.markdown(f'<p class="pg-task-q">{idx+1} / {tot} — 音の紋様を選んでください</p><p class="pg-task-book">{dn}</p>',unsafe_allow_html=True)
    if not st.session_state.current_options:
        opts=get_dummies(tb); opts.append(tb); random.shuffle(opts)
        st.session_state.current_options=opts
    opts=st.session_state.current_options; lbs=["A","B","C","D","E"]; cols=st.columns(5)
    for i,bk in enumerate(opts):
        with cols[i]:
            st.markdown(f'<div style="text-align:center"><span class="pg-option-badge">{lbs[i]}</span></div>',unsafe_allow_html=True)
            ip=get_image_path(bk)
            if ip: st.image(Image.open(ip),use_container_width=True)
            else: st.markdown('<div style="height:160px;background:#F2F2F7;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#8E8E93;font-size:12px">画像なし</div>',unsafe_allow_html=True)
    hr()
    ans=st.radio("選択：",lbs,horizontal=True,key=f"q_{idx}",label_visibility="collapsed")
    _,cb4=st.columns([2,1])
    with cb4:
        if st.button("次へ",key=f"next_{idx}",type="primary"):
            ch=opts[lbs.index(ans)]; ic=(ch==tb)
            st.session_state.results.append({"出題書籍":tb,"被験者回答":ch,"正誤":"正解" if ic else "不正解"})
            st.session_state.current_q_index+=1; st.session_state.current_options=[]; st.rerun()

def render_step5():
    st.balloons()
    tot=len(st.session_state.results); cor=sum(1 for r in st.session_state.results if r["正誤"]=="正解")
    acc=(cor/tot*100) if tot else 0
    st.markdown(f'<div class="pg-result-wrap"><div><span class="pg-result-num">{acc:.1f}</span><span class="pg-result-unit">%</span></div><p class="pg-result-caption">正答率 — {cor} / {tot} 問正解</p></div>',unsafe_allow_html=True)
    hr()
    if not st.session_state.data_saved:
        u=st.session_state.user_data; JST=timezone(timedelta(hours=9),"JST")
        ts=datetime.now(JST).strftime("%Y/%m/%d %H:%M:%S")
        rn=u.get("name","unknown"); hn=hashlib.sha256(rn.encode()).hexdigest()[:16] if rn!="unknown" else "unknown"
        rows=[]
        for r in st.session_state.results:
            rows.append([ts,st.session_state.session_id,hn,u.get("age",""),u.get("gender",""),u.get("major",""),
                         u.get("reading_freq",""),u.get("genres",""),u.get("synesthesia_score",""),
                         u.get("q1",""),u.get("q2",""),u.get("q3",""),round(acc,1),r["出題書籍"],r["被験者回答"],r["正誤"]])
        try:
            if "gcp_service_account" in st.secrets:
                sc=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
                cr=Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]),scopes=sc)
                cl=gspread.authorize(cr); sh=cl.open_by_url(st.secrets["private_gsheets_url"]).sheet1
                sv=False
                for att in range(3):
                    try: sh.append_rows(rows); st.session_state.data_saved=True; sv=True; break
                    except:
                        if att<2: time.sleep(2**att+random.uniform(0,1))
                if not sv:
                    st.warning("データの保存に失敗しました。バックアップをダウンロードしてください。")
                    hd2="Timestamp,SessionID,HashedName,Age,Gender,Major,ReadingFreq,Genres,Synesthesia,Q1,Q2,Q3,Accuracy,Target,Answer,Correctness\n"
                    bd="\n".join([",".join(map(str,r)) for r in rows])
                    st.download_button("バックアップをダウンロード",data=hd2+bd,
                                       file_name=f"recovery_{st.session_state.session_id}.csv",mime="text/csv",type="primary")
            else: st.caption("GCP シークレット未設定")
        except Exception as e: st.error(f"認証エラー: {e}")
    hr()
    qru=f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={urllib.parse.quote(DEPLOY_URL)}"
    st.markdown(f'<div class="pg-qr-wrap"><img src="{qru}" width="160" style="border-radius:12px"><p class="pg-qr-caption">{DEPLOY_URL}</p></div>',unsafe_allow_html=True)
    hr()
    cl5,cr5=st.columns(2)
    with cl5:
        if st.button("別の作品で再挑戦する",key="restart",type="primary"):
            reset_session(); st.rerun()
    with cr5: st.caption("新しいセッションが始まります。\n既読作品を再選択して再挑戦できます。")

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
    if mode=="sim":
        st.session_state.is_admin=True
        st.session_state.admin_mode="シミュレーター (デモ用)"

    with st.sidebar:
        st.markdown("### 🌒 Phonoglyph")
        hr()
        if not st.session_state.is_admin:
            st.caption("管理者・研究者向け")
            if st.button("管理者モードに切り替え",key="admin_on"):
                st.session_state.is_admin=True; st.rerun()
        else:
            st.caption("管理者モード 有効")
            sel=st.radio("表示モード",["実験タスク","シミュレーター"],
                         index=0 if st.session_state.admin_mode=="実験タスク (被験者用)" else 1)
            st.session_state.admin_mode="実験タスク (被験者用)" if sel=="実験タスク" else "シミュレーター (デモ用)"
            hr()
            st.caption(f"読込: {st.session_state.get('debug_target_file','—')}")
            st.caption(f"結合: {st.session_state.get('debug_match_count',0)}/{len(ALL_BOOKS)} 件")
            if st.button("管理者モードを解除",key="admin_off"):
                st.session_state.is_admin=False
                st.session_state.admin_mode="実験タスク (被験者用)"; st.rerun()

    render_topbar()

    if st.session_state.admin_mode=="実験タスク (被験者用)":
        {1:render_step1,2:render_step2,3:render_step3,4:render_step4,5:render_step5}.get(st.session_state.step,render_step1)()
    else:
        render_simulator()

if __name__=="__main__":
    main()
