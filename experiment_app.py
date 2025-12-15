import streamlit as st
import random
import time

import gspread
from google.oauth2.service_account import Credentials
@st.cache_resource
def get_worksheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.sheet1

st.markdown("""
<style>
/* ===== 母音ボタン横並び（スマホ対応）===== */

div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 4px;              /* 余白を詰める */
}

div[data-testid="column"] {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}

/* ボタンサイズを制限 */
div[data-testid="column"] button {
    width: 100% !important;
    font-size: 14px;       /* ← 小さく */
    padding: 8px 0;        /* ← 高さを減らす */
    white-space: nowrap;  /* 折り返し防止 */
}
</style>
""", unsafe_allow_html=True)


# ===============================
# Google Sheets 接続
# ===============================

# スプレッドシート名
SPREADSHEET_ID = "1V8eSJwIuwHEWktTsU8VFZlSOzXuM0jUqa8jTjv1vbxQ"

def append_row(data):
    ws = get_worksheet()
    ws.append_row(data, value_input_option="USER_ENTERED")

# ===============================
# 母音抽出・マッチ・ソート（kai.py 準拠）
# ===============================


def is_chouon_word(romaji):
    return "-" in romaji


def match_pattern(word_vowels, input_pattern, romaji_word):
    if not input_pattern or not isinstance(input_pattern, str):
        return False

    chouon = is_chouon_word(romaji_word)
    wl = len(word_vowels)
    il = len(input_pattern)

    # 長音語：±1許容
    if chouon:
        if abs(wl - il) > 1:
            return False
        min_len = min(wl, il)
        w_cut = word_vowels[:min_len]
        i_cut = input_pattern[:min_len]

    # 非長音語
    else:
        if il > wl:
            return False
        w_cut = word_vowels[:il]
        i_cut = input_pattern

    for w, i in zip(w_cut, i_cut):
        if i == "u":
            if w not in ["u", "n"]:
                return False
        else:
            if w != i:
                return False

    return True


def sort_key(item, input_vowels):
    r, j, vowels = item
    wl = len(vowels)
    il = len(input_vowels)
    chouon = "-" in r

    if vowels == input_vowels:
        return (0, abs(wl - il))
    if wl == il:
        return (1, abs(wl - il))
    if chouon and abs(wl - il) == 1:
        return (2, abs(wl - il))
    return (3, abs(wl - il))

# ===============================
# 辞書読み込み（romaji_words.txt）
# ===============================
def load_dict():
    word_dict = {}
    with open("romaji_words.txt", encoding="utf-8") as f:
        for line in f:
            r, j = line.strip().split(",")
            word_dict[r] = j
    return word_dict

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

def is_chouon_word(romaji):
    return "-" in romaji

def match_pattern(word_vowels, input_pattern, romaji_word):
    if not input_pattern:
        return False   # ← 何も押していない時は候補を出さない


    chouon = is_chouon_word(romaji_word)
    wl, il = len(word_vowels), len(input_pattern)

    if chouon:
        if abs(wl - il) > 1:
            return False
        w_cut = word_vowels[:min(wl, il)]
        i_cut = input_pattern[:min(wl, il)]
    else:
        if il > wl:
            return False
        w_cut = word_vowels[:il]
        i_cut = input_pattern

    for w, i in zip(w_cut, i_cut):
        if i == "u":
            if w not in ["u", "n"]:
                return False
        else:
            if w != i:
                return False
    return True

word_dict = load_dict()


# ===============================
# session_state 初期化
# ===============================
if "phase" not in st.session_state:
    st.session_state.phase = "id_input"

if "experiment_id" not in st.session_state:
    st.session_state.experiment_id = ""

# ---------- 味覚 ----------
for key, default in {
    "taste_list": [],
    "taste_index": 0,
    "body_steps": 0,
    "taste_result": None,
    "taste_free_text": "",
    "taste_time_start": None,
    "taste_time_end": None,
    "taste_steps": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- 母音（味覚） ----------
for key, default in {
    "input_vowels": "",
    "vowel_result": None,
    "vowel_free_text": "",
    "vowel_time_start": None,
    "vowel_time_end": None,
    "vowel_steps": 0,
    "vowel_deletes": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- 体調 YES/NO ----------
for key, default in {
    "body_list": [],
    "body_index": 0,
    "body_yesno_result": None,
    "body_yesno_time_start": None,
    "body_yesno_time_end": None,
    "body_yesno_free_text": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- 体調 母音 ----------
for key, default in {
    "body_input_vowels": "",
    "body_vowel_result": None,
    "body_vowel_free_text": "",
    "body_vowel_time_start": None,
    "body_vowel_time_end": None,
    "body_vowel_steps": 0,
    "body_vowel_deletes": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default
if "vowel_active" not in st.session_state:
    st.session_state.vowel_active = False
if "body_vowel_active" not in st.session_state:
    st.session_state.body_vowel_active = False
if "saved" not in st.session_state:
    st.session_state.saved = False

# ===============================
# 1. ID入力
# ===============================
if st.session_state.phase == "id_input":
    st.title("入力実験")
    st.header("これから2つの質問に答えてください。")
    st.write("質問に対して一番最初に思ったものを選択してください。")
    st.write("ニックネーム、入力時間、選択結果などの情報は保存されます。ウイルスとかはありません")
    st.session_state.experiment_id = st.text_input("ニックネーム")

    if st.button("開始"):
        if st.session_state.experiment_id.strip():
            st.session_state.taste_list = random.sample(
                ["甘い", "辛い", "酸っぱい", "しょっぱい", "苦い","うまい","おなか一杯","甘酸っぱい"], 8
            )
            st.session_state.taste_index = 0
            st.session_state.taste_steps = 0
            st.session_state.phase = "taste_yesnoima"
            st.rerun()
        else:
            st.warning("ニックネームを入力してください")
# ===============================
# 2. 味覚 YES / NO
# ===============================
    # 新しいフェーズ追加：taste_question
elif st.session_state.phase == "taste_yesnoima":
    idx = st.session_state.taste_index
    tastes = st.session_state.taste_list

    # ★ ここがガード（重要）
    if idx >= len(tastes):
        st.session_state.phase = "taste_free_input"
        st.rerun()

    current = tastes[idx]

    st.header("第1問:今どんな味のものが食べたいですか？")
    st.write("当てはまるものでYES,どれでもなかったらどれでもないを押してください")
    st.write("例）あまい、からい、甘酸っぱい、あっさりなど")

    if st.button("開始"):
        st.session_state.taste_time_start = time.time()
        st.session_state.phase = "taste_checking"
        st.rerun()


elif st.session_state.phase == "taste_checking":
    idx = st.session_state.taste_index
    tastes = st.session_state.taste_list

    # ★ ここで完全終了を判定
    if idx >= len(tastes):
        st.session_state.taste_time_end = time.time()
        st.session_state.phase = "taste_free_input"
        st.rerun()

    current = tastes[idx]
    st.subheader(f"「{current}」は当てはまりますか？")

    col1, col2 = st.columns(2)

    if col1.button("YES"):
        st.session_state.taste_steps += 1
        st.session_state.taste_result = current
        st.session_state.taste_time_end = time.time()
        st.session_state.phase = "save_taste"
        st.rerun()

    if col2.button("NO"):
        st.session_state.taste_steps += 1
        st.session_state.taste_index += 1
        st.rerun()

# ===============================
# 2.5 味覚 YES 確定後
# ===============================
elif st.session_state.phase == "save_taste":
    # YES で確定した場合は自由入力をスキップして次へ
    st.session_state.phase = "taste_vowel_intro"
    st.rerun()

# ===============================
# 3. 味覚 自由入力
# ===============================
elif st.session_state.phase == "taste_free_input":
    st.header("では、どんな味の気分でしたか？")
    st.session_state.taste_free_text = st.text_input("自由に入力してください")

    if st.button("決定"):
        if st.session_state.taste_free_text.strip():
            st.session_state.phase = "taste_vowel_intro"
            st.rerun()
        else:
            st.warning("入力してください")




# ===============================
# 5. 味覚 母音入力 開始
# ===============================
elif st.session_state.phase == "taste_vowel_intro":
    st.header("同じ質問をもう一度します")
    st.write("今はどんな味のものが食べたい気分ですか？ただし母音のみで答えてください。")
    st.write("候補になかった場合は、候補になかったを押してください。")
    st.write("ただし、ん＝う、じゃ＝あ、としてください")
    st.write("例）あまい→ああい,しょっぱい→おあい,甘酸っぱい→ああうあい,パーフェクト→ああえうお")
    st.write("母音（あ い う え お）だけで入力してください")

    if st.button("母音入力を始める"):
        st.session_state.input_vowels = ""
        st.session_state.vowel_steps = 0
        st.session_state.vowel_deletes = 0
        st.session_state.vowel_time_start = time.time()
        st.session_state.phase = "vowel_input"
        st.rerun()

# ===============================
# 6. 味覚 母音入力 本体（kai.py方式）
# ===============================
elif st.session_state.phase == "vowel_input":
    st.header("母音入力")

    # ---------- 母音ボタン ----------
    cols = st.columns([1,1,1,1,1])
    for col, v in zip(cols, ["a", "i", "u", "e", "o"]):
        with col:
            if st.button(v, key=f"taste_vowel_{v}", use_container_width=True):
                st.session_state.input_vowels += v
                st.session_state.vowel_steps += 1
                st.rerun()


    # ---------- 削除 ----------
    if st.button("⌫ 削除", key="taste_vowel_delete"):
        if st.session_state.input_vowels:
            st.session_state.input_vowels = st.session_state.input_vowels[:-1]
            st.session_state.vowel_deletes += 1
        st.rerun()

    st.header(f"入力：{st.session_state.input_vowels}")

    # ---------- 候補生成（kai.py 完全準拠） ----------
    if st.session_state.input_vowels:
        candidates = []

        for r, j in word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.input_vowels, r):
                candidates.append((r, j, v))

        # 並び替え（kai.pyと同じ）
        candidates.sort(
            key=lambda x: sort_key(x, st.session_state.input_vowels)
        )

        # ---------- 最大6件だけ表示 ----------
        for idx, (r, j, v) in enumerate(candidates[:6]):
            if st.button(
                j,
                key=f"taste_vowel_candidate_{idx}_{r}"
            ):
                st.session_state.vowel_result = j
                st.session_state.vowel_time_end = time.time()
                st.session_state.vowel_active = False
                st.session_state.phase = "save_vowel"
                st.rerun()

    st.write("---")

    # ---------- 候補なし ----------
    if st.button("候補になかった", key="taste_vowel_none"):
        st.session_state.vowel_time_end = time.time()
        st.session_state.vowel_active = False
        st.session_state.phase = "vowel_free_input"
        st.rerun()



# ===============================
# 7. 味覚 母音 自由入力
# ===============================
elif st.session_state.phase == "vowel_free_input":
    st.header("どんな気分でしたか？")
    st.session_state.vowel_free_text = st.text_input("自由入力")

    if st.button("決定"):
        if st.session_state.vowel_free_text.strip():
            st.session_state.phase = "save_vowel"
            st.rerun()
        else:
            st.warning("入力してください")

# ===============================
# 8. 味覚 母音結果 保存
# ===============================
elif st.session_state.phase == "save_vowel":


    st.session_state.phase = "body_start"
    st.rerun()
# ===============================
# 9. 体調質問 開始（YES/NO）
# ===============================
elif st.session_state.phase == "body_start":
    st.header("第2問：今の体調はどうですか？")
    st.write("例）だるい、すっきり、あついなど")

    if st.button("開始"):
        st.session_state.body_list = random.sample(
            ["忙しい", "いたい", "ねむい", "すっきり", "つらい","元気","めんどう","あつい"], 8
        )
        st.session_state.body_index = 0
        st.session_state.body_steps = 0
        st.session_state.body_yesno_result = None
        st.session_state.body_yesno_time_start = time.time()
        st.session_state.phase = "body_yesno_check"
        st.rerun()

# ===============================
# 10. 体調 YES / NO 確認
# ===============================
elif st.session_state.phase == "body_yesno_check":
    idx = st.session_state.body_index
    body_list = st.session_state.body_list

    if idx < len(body_list):
        current = body_list[idx]
        st.subheader(f"「{current}」ですか？")

        col1, col2 = st.columns(2)
        if col1.button("YES"):
            st.session_state.body_steps += 1
            st.session_state.body_yesno_result = current
            st.session_state.body_yesno_time_end = time.time()
            st.session_state.phase = "body_vowel_start"
            st.rerun()

        if col2.button("NO"):
            st.session_state.body_steps += 1
            st.session_state.body_index += 1
            st.rerun()

    else:
        st.subheader("どれでもないですか？")
        if st.button("どれでもない"):
            st.session_state.body_yesno_time_end = time.time()
            st.session_state.phase = "body_free_input"
            st.rerun()

# ===============================
# 11. 体調 自由入力
# ===============================
elif st.session_state.phase == "body_free_input":
    st.header("どんな身体の状態、体調ですか？（自由入力）")
    st.session_state.body_yesno_free_text = st.text_input("自由入力")

    if st.button("決定"):
        if st.session_state.body_yesno_free_text.strip():
            st.session_state.phase = "body_vowel_start"
            st.rerun()
        else:
            st.warning("入力してください")

# ===============================
# 12. 体調 母音入力 開始
# ===============================
elif st.session_state.phase == "body_vowel_start":
    st.header("もう一度同じ質問をします。")
    st.write("身体の状態、体調はどんな感じですか？ただし今回は母音のみで答えてもらいます。候補に出なかった場合は、候補になかったを押してください。\nただし、ん＝う、じゃ＝あ、としてください\n例）だるい→あうい,すっきり→ういい,さむい→あうい,パーフェクト→ああうえお")
    st.write("母音（a i u e o）だけで入力してください")

    if st.button("母音入力を始める"):
        st.session_state.body_input_vowels = ""
        st.session_state.body_vowel_steps = 0
        st.session_state.body_vowel_deletes = 0
        st.session_state.body_vowel_time_start = time.time()
        st.session_state.body_vowel_active = True   # ← ★追加
        st.session_state.phase = "body_vowel_input"
        st.rerun()
# ===============================
# 13. 体調 母音入力 本体（kai.py方式）
# ===============================
elif st.session_state.phase == "body_vowel_input":
    st.header("体調 母音入力")

    # ---------- 母音ボタン ----------
    cols = st.columns([1,1,1,1,1])
    for col, v in zip(cols, ["a", "i", "u", "e", "o"]):
        with col:
            if st.button(v, key=f"body_vowel_{v}", use_container_width=True):
                st.session_state.body_input_vowels += v
                st.session_state.body_vowel_steps += 1
                st.rerun()


    # ---------- 削除 ----------
    if st.button("⌫ 削除", key="body_vowel_delete"):
        if st.session_state.body_input_vowels:
            st.session_state.body_input_vowels = st.session_state.body_input_vowels[:-1]
            st.session_state.body_vowel_deletes += 1
        st.rerun()

    st.header(f"入力：{st.session_state.body_input_vowels}")

    # ---------- 候補生成（kai.py 完全準拠） ----------
    if st.session_state.body_input_vowels:
        candidates = []

        for r, j in word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.body_input_vowels, r):
                candidates.append((r, j, v))

        # 並び替え（kai.pyと同一）
        candidates.sort(
            key=lambda x: sort_key(x, st.session_state.body_input_vowels)
        )

        # ---------- 最大6件表示 ----------
        for idx, (r, j, v) in enumerate(candidates[:6]):
            if st.button(
                j,
                key=f"body_vowel_candidate_{idx}_{r}"
            ):
                st.session_state.body_vowel_result = j
                st.session_state.body_vowel_time_end = time.time()
                st.session_state.phase = "save_body"
                st.rerun()

    st.write("---")

    # ---------- 候補なし ----------
    if st.button("候補になかった", key="body_vowel_none"):
        st.session_state.body_vowel_time_end = time.time()
        st.session_state.phase = "body_vowel_free_input"
        st.rerun()

# ===============================
# 13.5 体調 母音 自由入力
# ===============================
elif st.session_state.phase == "save_body":

    if not st.session_state.saved:   # ← ★追加
        st.session_state.saved = True

        # ---- 体調 YES/NO の所要時間 ----
        body_yesno_duration = round(
            st.session_state.body_yesno_time_end
            - st.session_state.body_yesno_time_start, 2
        )

        # ---- 体調 母音入力の所要時間 ----
        body_vowel_duration = round(
            st.session_state.body_vowel_time_end
            - st.session_state.body_vowel_time_start, 2
        )

        append_row([
            # ID
            st.session_state.experiment_id,

            # 味覚 YES/NO
            st.session_state.taste_result,
            st.session_state.taste_free_text,
            st.session_state.taste_steps,
            round(
                st.session_state.taste_time_end
                - st.session_state.taste_time_start, 2
            ),

            # 味覚 母音
            st.session_state.vowel_result,
            st.session_state.vowel_free_text,
            st.session_state.vowel_steps,
            st.session_state.vowel_deletes,
            round(
                st.session_state.vowel_time_end
                - st.session_state.vowel_time_start, 2
            ),

            # 体調 YES/NO
            st.session_state.body_yesno_result,
            st.session_state.body_yesno_free_text,
            st.session_state.body_steps,
            body_yesno_duration,

            # 体調 母音
            st.session_state.body_vowel_result,
            st.session_state.body_vowel_free_text,
            st.session_state.body_vowel_steps,
            st.session_state.body_vowel_deletes,
            body_vowel_duration,
        ])

    st.success("すべて完了しました！")
    st.write("ご協力ありがとうございました。\n最初に戻るを押してから終えてください！")


    if st.button("最初に戻る"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()














