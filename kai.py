import streamlit as st
import pandas as pd

# ---------------------------
# 初期化
# ---------------------------
if "input_vowels" not in st.session_state:
    st.session_state.input_vowels = ""
if "selected_word" not in st.session_state:
    st.session_state.selected_word = None
if "finalized" not in st.session_state:
    st.session_state.finalized = False
if "candidates" not in st.session_state:
    st.session_state.candidates = []

# ---------------------------
# タイトル
# ---------------------------
st.title("🎵 母音パターン単語検索アプリ")
st.write("50音の母音列のボタンを押してください👇")

# ---------------------------
# 母音抽出ロジック（nn → u）
# ---------------------------
def extract_vowels(word):
    vowels = "aiueo"
    result = []
    i = 0
    while i < len(word):
        if word[i] == "n":
            count = 1
            while i + count < len(word) and word[i + count] == "n":
                count += 1
            result.append("u" * (count // 2))
            i += count
            continue

        if word[i] == "-":  
            result.append(result[-1] if result else "")
            i += 1
            continue

        if word[i] in vowels:
            result.append(word[i])

        i += 1
    return "".join(result)

# 長音語判定
def is_chouon_word(romaji):
    return "-" in romaji


# 50音表データ
rows = [
    ["あ", "か", "さ", "た", "な", "は", "ま", "や", "ら", "わ"],
    ["い", "き", "し", "ち", "に", "ひ", "み", "",  "り", "" ],
    ["う", "く", "す", "つ", "ぬ", "ふ", "む", "ゆ", "る", "ん"],
    ["え", "け", "せ", "て", "ね", "へ", "め", "",  "れ", "" ],
    ["お", "こ", "そ", "と", "の", "ほ", "も", "よ",  "ろ", "" ],
]

# CSS（見た目）
st.markdown("""
<style>
.bottom-space { height: 300px; }
.letter-table { border-collapse: collapse; width: 100%; }
.letter-table td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
    width: 50px;
    height: 45px;
    font-size: 20px;
}
.row-container { display: flex; align-items: center; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 50音ボード（参考）")

# 50音ボタンUI
for i, row in enumerate(rows):
    html_row = "<table class='letter-table'><tr>"
    for col in row:
        html_row += f"<td>{col}</td>" if col else "<td></td>"
    html_row += "</tr></table>"

    cols = st.columns([5, 1.2])

    with cols[0]:
        st.markdown(f"<div class='row-container'>{html_row}</div>", unsafe_allow_html=True)

    with cols[1]:
        vowel_display = ["あ", "い", "う", "え", "お"][i]
        vowel_romaji = ["a", "i", "u", "e", "o"][i]

        if st.button(vowel_display, key=f"btn_{vowel_display}", use_container_width=True):
            st.session_state.input_vowels += vowel_romaji
            st.session_state.finalized = False

# 削除
if st.button("⌫ 削除"):
    if st.session_state.input_vowels:
        st.session_state.input_vowels = st.session_state.input_vowels[:-1]
    st.session_state.finalized = False

st.markdown(f"### 📝 入力母音： `{st.session_state.input_vowels}`")

# 辞書読み込み
word_dict = {}
with open("romaji_words.txt", encoding="utf-8") as f:
    for line in f:
        r, j = line.strip().split(",")
        word_dict[r] = j


# ---------------------------
# マッチング条件
# ---------------------------
def match_pattern(word_vowels, input_pattern, romaji_word):
    if not input_pattern:
        return True

    chouon = is_chouon_word(romaji_word)
    wl = len(word_vowels)
    il = len(input_pattern)

    # ---- 長音語：±1許容 ----
    if chouon:
        if abs(wl - il) > 1:
            return False
        min_len = min(wl, il)
        w_cut = word_vowels[:min_len]
        i_cut = input_pattern[:min_len]

    # ---- 非長音語：入力が語を超えない範囲で許容 ----
    else:
        if il > wl:
            return False
        w_cut = word_vowels[:il]
        i_cut = input_pattern

    # ---- 母音内容チェック（u揺らぎ）----
    for w, i in zip(w_cut, i_cut):
        if i == "u":
            if w not in ["u", "n"]:
                return False
        else:
            if w != i:
                return False
    return True


# ---------------------------
# 検索
# ---------------------------
input_vowels = st.session_state.input_vowels

raw_candidates = []
for r in word_dict:
    v = extract_vowels(r)
    if match_pattern(v, input_vowels, r):
        raw_candidates.append((r, word_dict[r], v))


# ---------------------------
# ソート（最重要）
# ---------------------------
def sort_key(item):
    romaji, japanese, vowels = item
    wl = len(vowels)
    il = len(input_vowels)
    chouon = is_chouon_word(romaji)

    # 1. 完全一致
    if vowels == input_vowels:
        return (0, wl)

    # 2. 長さ一致
    if wl == il:
        return (1, wl)

    # 3. 長音語で±1
    if chouon and abs(wl - il) == 1:
        return (2, wl)

    # 4. 非長音語で il < wl
    if not chouon and il < wl:
        return (3, wl)

    # それ以外
    return (9, wl)

candidates_sorted = sorted(raw_candidates, key=sort_key)


# ---------------------------
# 候補表示
# ---------------------------
if not st.session_state.finalized:

    if input_vowels != "":
        if len(candidates_sorted) == 0:
            st.info("該当する単語はありません。")
        else:
            display_candidates = candidates_sorted[:6]

            st.write("候補を選んでください👇")

            for r, j, v in display_candidates:
                if st.button(j, key=f"cand_{r}"):
                    st.session_state.selected_word = j
                    st.session_state.finalized = True
                    st.rerun()


# ---------------------------
# 確定表示
# ---------------------------
if st.session_state.finalized and st.session_state.selected_word:
    st.markdown("---")
    st.markdown(
        f"""
        <h2>💡 あなたが言いたいのは：
        <span style='color: red; font-weight: bold;'>{st.session_state.selected_word}</span></h2>
        """,
        unsafe_allow_html=True
    )

st.markdown("<div class='bottom-space'></div>", unsafe_allow_html=True)
