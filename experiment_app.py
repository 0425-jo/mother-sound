import streamlit as st
import random
import time
import gspread
from google.oauth2.service_account import Credentials

# ===============================
# Google Sheets 設定
# ===============================
@st.cache_resource
def get_worksheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key("1V8eSJwIuwHEWktTsU8VFZlSOzXuM0jUqa8jTjv1vbxQ")
    return sh.sheet1

def append_row(data):
    get_worksheet().append_row(data, value_input_option="USER_ENTERED")

# ===============================
# CSS（横並び強制＋見た目調整）
# ===============================
st.markdown("""
<style>
/* 母音ボタンを絶対に横一列にする */
.vowel-row {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    overflow-x: auto !important;
    padding: 12px 8px !important;
    margin: 10px 0 !important;
    background: rgba(30,30,40,0.9);
    border-radius: 16px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
}
.vowel-row::-webkit-scrollbar { display: none; }

/* 各母音ボタン */
.vowel-btn {
    flex: 1 !important;
    min-width: 64px !important;
}
.vowel-btn > div { width: 100% !important; }
.vowel-btn button {
    width: 100% !important;
    height: 68px !important;
    font-size: 24px !important;
    font-weight: bold !important;
    border-radius: 14px !important;
    background: #3a3a4d !important;
    color: white !important;
}

/* 削除ボタン（赤） */
.delete-btn button {
    background: #e91e63 !important;
    color: white !important;
}

/* 候補ボタン（グリッド） */
.candidate-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 10px;
    padding: 10px;
    margin-top: 10px;
}
.candidate-grid button {
    height: 56px !important;
    font-size: 16px !important;
    border-radius: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 辞書読み込み
# ===============================
def load_dict():
    word_dict = {}
    # romaji_words.txt は「romaji,日本語」のCSV形式（1行1語）
    with open("romaji_words.txt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r, j = line.strip().split(",", 1)
                word_dict[r.strip()] = j.strip()
    return word_dict

def extract_vowels(word):
    vowels = "aiueo"
    result = []
    i = 0
    while i < len(word):
        c = word[i]
        if c == "n":  # 「nn」「n'n」などは「ん」扱い → 母音には含めない
            i += 1
            continue
        if c == "-":  # 長音は直前の母音を繰り返す
            if result:
                result.append(result[-1])
            i += 1
            continue
        if c in vowels:
            result.append(c)
        i += 1
    return "".join(result)

word_dict = load_dict()

# ===============================
# マッチング・ソート補助関数
# ===============================
def match_pattern(vowels_in_dict, input_vowels, romaji):
    # 入力が完全に一致、または入力が前方一致する場合にヒット
    if input_vowels == "":
        return True
    return vowels_in_dict.startswith(input_vowels)

def sort_key(item, input_vowels):
    romaji, japanese, vowels = item
    # 1. 完全一致を最上位
    # 2. 長い単語を優先
    # 3. 辞書順
    if vowels == input_vowels:
        return (0, -len(romaji), romaji)
    return (1, -len(romaji), romaji)

# ===============================
# session_state 初期化
# ===============================
if "phase" not in st.session_state:
    st.session_state.phase = "id_input"

    # 味覚関連
    st.session_state.input_vowels = ""
    st.session_state.vowel_steps = 0
    st.session_state.vowel_deletes = 0
    st.session_state.vowel_result = ""
    st.session_state.vowel_time_start = None
    st.session_state.vowel_time_end = None

    # 体調関連
    st.session_state.body_input_vowels = ""
    st.session_state.body_vowel_steps = 0
    st.session_state.body_vowel_deletes = 0
    st.session_state.body_vowel_result = ""
    st.session_state.body_vowel_time_start = None
    st.session_state.body_vowel_time_end = None

    # その他
    st.session_state.user_id = ""

# ===============================
# ID入力
# ===============================
if st.session_state.phase == "id_input":
    st.title("母音で食べたいもの診断")
    user_id = st.text_input("あなたのIDを入力してください", max_chars=20)
    if st.button("開始"):
        if user_id.strip():
            st.session_state.user_id = user_id.strip()
            st.session_state.vowel_time_start = time.time()
            st.session_state.phase = "vowel_input"
            st.rerun()
        else:
            st.error("IDを入力してください")

# ===============================
# 味覚：母音入力画面
# ===============================
elif st.session_state.phase == "vowel_input":
    st.markdown("### どんな味が食べたい？")

    st.markdown('<div class="vowel-row">', unsafe_allow_html=True)
    col_a, col_i, col_u, col_e, col_o, col_del = st.columns([1,1,1,1,1,1.2])

    with col_a:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("あ", key="v_a"):
            st.session_state.input_vowels += "a"
            st.session_state.vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_i:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("い", key="v_i"):
            st.session_state.input_vowels += "i"
            st.session_state.vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_u:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("う", key="v_u"):
            st.session_state.input_vowels += "u"
            st.session_state.vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_e:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("え", key="v_e"):
            st.session_state.input_vowels += "e"
            st.session_state.vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_o:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("お", key="v_o"):
            st.session_state.input_vowels += "o"
            st.session_state.vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_del:
        st.markdown('<div class="vowel-btn delete-btn">', unsafe_allow_html=True)
        if st.button("削除", key="v_del"):
            if st.session_state.input_vowels:
                st.session_state.input_vowels = st.session_state.input_vowels[:-1]
                st.session_state.vowel_deletes += 1
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align:center; margin:20px 0;'>入力：{st.session_state.input_vowels or 'ー'}</h2>",
                unsafe_allow_html=True)

    # 候補表示
    if st.session_state.input_vowels:
        candidates = []
        for r, j in word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.input_vowels, r):
                candidates.append((r, j, v))
        candidates.sort(key=lambda x: sort_key(x, st.session_state.input_vowels))

        st.markdown('<div class="candidate-grid">', unsafe_allow_html=True)
        for idx, (r, j, v) in enumerate(candidates[:12]):
            if st.button(j, key=f"c_{idx}_{r}"):
                st.session_state.vowel_result = j
                st.session_state.vowel_time_end = time.time()
                st.session_state.phase = "save_vowel"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("候補になかった", use_container_width=True):
        st.session_state.vowel_time_end = time.time()
        st.session_state.phase = "vowel_free_input"
        st.rerun()

# ===============================
# 味覚：候補になかったときの自由入力
# ===============================
elif st.session_state.phase == "vowel_free_input":
    st.markdown("### 食べたいものを直接入力してください")
    free_text = st.text_input("食べたいもの", placeholder="例：ラーメン")
    if st.button("決定"):
        if free_text.strip():
            st.session_state.vowel_result = free_text.strip()
            st.session_state.phase = "save_vowel"
            st.rerun()

# ===============================
# 味覚結果をGoogle Sheetsに保存 → 体調へ
# ===============================
elif st.session_state.phase == "save_vowel":
    append_row([
        time.strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.user_id,
        "taste",
        st.session_state.vowel_result,
        st.session_state.input_vowels,
        st.session_state.vowel_steps,
        st.session_state.vowel_deletes,
        round(st.session_state.vowel_time_end - st.session_state.vowel_time_start, 2)
    ])
    st.success(f"食べたいもの：{st.session_state.vowel_result} で記録しました！")
    st.session_state.body_vowel_time_start = time.time()
    st.session_state.phase = "body_vowel_input"
    st.rerun()

# ===============================
# 体調：母音入力画面（味覚と同じレイアウト）
# ===============================
elif st.session_state.phase == "body_vowel_input":
    st.markdown("### 体調はどう？")

    st.markdown('<div class="vowel-row">', unsafe_allow_html=True)
    col_a, col_i, col_u, col_e, col_o, col_del = st.columns([1,1,1,1,1,1.2])

    with col_a:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("あ", key="bv_a"):
            st.session_state.body_input_vowels += "a"
            st.session_state.body_vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_i:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("い", key="bv_i"):
            st.session_state.body_input_vowels += "i"
            st.session_state.body_vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_u:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("う", key="bv_u"):
            st.session_state.body_input_vowels += "u"
            st.session_state.body_vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_e:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("え", key="bv_e"):
            st.session_state.body_input_vowels += "e"
            st.session_state.body_vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_o:
        st.markdown('<div class="vowel-btn">', unsafe_allow_html=True)
        if st.button("お", key="bv_o"):
            st.session_state.body_input_vowels += "o"
            st.session_state.body_vowel_steps += 1
        st.markdown('</div>', unsafe_allow_html=True)

    with col_del:
        st.markdown('<div class="vowel-btn delete-btn">', unsafe_allow_html=True)
        if st.button("削除", key="bv_del"):
            if st.session_state.body_input_vowels:
                st.session_state.body_input_vowels = st.session_state.body_input_vowels[:-1]
                st.session_state.body_vowel_deletes += 1
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align:center; margin:20px 0;'>入力：{st.session_state.body_input_vowels or 'ー'}</h2>",
                unsafe_allow_html=True)

    if st.session_state.body_input_vowels:
        candidates = []
        for r, j in word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.body_input_vowels, r):
                candidates.append((r, j, v))
        candidates.sort(key=lambda x: sort_key(x, st.session_state.body_input_vowels))

        st.markdown('<div class="candidate-grid">', unsafe_allow_html=True)
        for idx, (r, j, v) in enumerate(candidates[:12]):
            if st.button(j, key=f"bc_{idx}_{r}"):
                st.session_state.body_vowel_result = j
                st.session_state.body_vowel_time_end = time.time()
                st.session_state.phase = "save_body"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("候補になかった", use_container_width=True):
        st.session_state.body_vowel_time_end = time.time()
        st.session_state.phase = "body_vowel_free_input"
        st.rerun()

# ===============================
# 体調：候補になかったときの自由入力
# ===============================
elif st.session_state.phase == "body_vowel_free_input":
    st.markdown("### 体調を直接入力してください")
    free_text = st.text_input("今の体調", placeholder="例：元気")
    if st.button("決定"):
        if free_text.strip():
            st.session_state.body_vowel_result = free_text.strip()
            st.session_state.phase = "save_body"
            st.rerun()

# ===============================
# 体調結果を保存 → 終了
# ===============================
elif st.session_state.phase == "save_body":
    append_row([
        time.strftime("%Y-%m-%d %H:%M:%S"),
        st.session_state.user_id,
        "body",
        st.session_state.body_vowel_result,
        st.session_state.body_input_vowels,
        st.session_state.body_vowel_steps,
        st.session_state.body_vowel_deletes,
        round(st.session_state.body_vowel_time_end - st.session_state.body_vowel_time_start, 2)
    ])
    st.balloons()
    st.markdown(f"""
    ## 完了！
    **ID**: {st.session_state.user_id}  
    **食べたいもの**: {st.session_state.vowel_result}  
    **体調**: {st.session_state.body_vowel_result}
    
    ありがとうございました！また遊んでね  
    """)
    if st.button("最初からやり直す"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
