import streamlit as st
import random
import time
import streamlit.components.v1 as components
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
.vowel-row {
  display: flex;
  width: 100vw;          /* ← 画面幅基準 */
  max-width: 100%;
  gap: 6px;
  padding: 0 6px;
  box-sizing: border-box;
}

.vowel-btn {
  flex: 1 1 0;
  min-width: 0;
  height: 56px;
  font-size: 18px;
  border-radius: 12px;
  background-color: #1f2937;
  color: white;
  border: none;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.candidate-scroll {
    display: flex;
    overflow-x: auto;
    gap: 8px;
    padding: 6px 0;
}

.candidate-scroll button {
    white-space: nowrap;
    min-width: 110px;
    height: 48px;
    font-size: 16px;
    border-radius: 10px;
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
    st.title("入力実験(1分とかで終わる！）")
    st.header("これから2つの質問に答えてください。")
    st.write("質問に対して一番最初に思ったものを直感で選択してください。")
    st.write("ニックネーム、入力時間、選択結果などの情報は保存されます。研究に使うのでできるだけ真面目に答えてください！")
    st.session_state.experiment_id = st.text_input("ニックネーム")

    if st.button("スタート"):
        if st.session_state.experiment_id.strip():
            st.session_state.taste_list = random.sample(
                ["あまい", "からい", "すっぱい", "しょっぱい", "にがい"], 5
            )
            st.session_state.taste_index = 0
            st.session_state.taste_steps = 0
            st.session_state.phase = "taste_vowel_intro"
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

    st.header("また、同じ質問をします！")
    st.write("当てはまるものでYES,当てはまらなかったらNOを押してください")
    st.write("さっき答えた味覚と同じのが出るまでNOを押し続けて、ない場合その後入力してください！")

    if st.button("スタート"):
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
    st.subheader(f"「{current}」の味のものが食べたいですか？")

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
# save_taste フェーズ
elif st.session_state.phase == "save_taste":
    st.session_state.phase = "body_vowel_start"
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
    st.header("第1問:今どんな味のものが食べたいですか？今思っている直感です！")
    st.header("ただし母音のみで答えてください。")
    st.write("`母音を入力したうえで`候補になかった場合,下にある`候補になかった`を押してください。")
    st.write("ただし、ん＝う、じゃ＝あ、としてください")
    st.write("例）あまい→ああい,しょっぱい→おあい,あまずっぱい→ああうあい,パーフェクト→ああえうお")
    st.write("のように母音（a i u e o）だけで入力してください")

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
    st.write("どんな味が食べたい？")

    cols = st.columns(5, gap="small")
    for col, v, label in zip(
        cols,
        ["a", "i", "u", "e", "o"],
        ["あ", "い", "う", "え", "お"]
    ):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.input_vowels += v
                st.session_state.vowel_steps += 1
                st.rerun()

    # ---------- 削除 ----------
    if st.button("⌫ 削除", key="taste_vowel_delete"):
        if st.session_state.input_vowels:
            st.session_state.input_vowels = st.session_state.input_vowels[:-1]
            st.session_state.vowel_deletes += 1
        st.rerun()
    st.write("－－－－－－－－－－－－－ー－－－－－－－－－－－－－ー－－－－－－－－－－－－－ー")    
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

       # ---------- 最大6件を横並びで表示 ----------
        st.markdown('<div class="candidate-scroll">', unsafe_allow_html=True)

        for idx, (r, j, v) in enumerate(candidates[:6]):
            clicked = st.button(
                j,
                key=f"taste_vowel_candidate_{idx}_{r}"
            )
            if clicked:
                st.session_state.vowel_result = j
                st.session_state.vowel_time_end = time.time()
                st.session_state.phase = "save_vowel"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)


    st.header(f"入力：{st.session_state.input_vowels}")
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


    st.session_state.phase = "taste_yesnoima"
    st.rerun()
# ===============================
# 9. 体調質問 開始（YES/NO）
# ===============================
elif st.session_state.phase == "body_start":
    st.session_state.body_list = random.sample(
        ["ねむい", "つかれた","げんき","しんどい","いそがしい"], 5
    )
    st.session_state.body_index = 0
    st.session_state.body_steps = 0

    st.header("また、同じ質問をします！")

    st.write("当てはまるものでYES,当てはまらなかったらNOを押してください")
    st.write("さっき答えた体調と同じのが出るまでNOを押し続けて、ない場合その後入力してください！")

    if st.button("スタート"):
        st.session_state.body_list = random.sample(
            ["ねむい", "つかれた","げんき","しんどい","いそがしい"], 5
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
            st.session_state.phase = "save_body"
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
    st.header("第2問：今の体調はどうですか？これも今思う直感です！")
    st.header("ただし母音のみで答えてください。")
    st.write("`母音を入力したうえで`候補になかった場合,下にある`候補になかった`を押してください。")
    st.write("ただし、ん＝う、じゃ＝あ、としてください")
    st.write("例）だるい→あうい,すっきり→ういい,ねむい→えうい,パーフェクト→ああうえお")
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
    st.write("体調はどう？")

    # ---------- 母音ボタン ----------
    cols = st.columns([1,1,1,1,1])
    for col, v in zip(cols, ["a", "i", "u", "e", "o"]):
        with col:
            if st.button(v, key=f"body_vowel_{v}", use_container_width=True):
                st.session_state.body_input_vowels += v
                st.session_state.body_vowel_steps += 1
                st.rerun()

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

        # ---------- 最大6件を横並び ----------
        st.markdown('<div class="candidate-scroll">', unsafe_allow_html=True)
        
        for idx, (r, j, v) in enumerate(candidates[:6]):
            if st.button(
                j,
                key=f"body_vowel_candidate_{idx}_{r}"
            ):
                st.session_state.body_vowel_result = j
                st.session_state.body_vowel_time_end = time.time()
                st.session_state.phase = "body_start"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)




    # ---------- 削除 ----------
    if st.button("⌫ 削除", key="body_vowel_delete"):
        if st.session_state.body_input_vowels:
            st.session_state.body_input_vowels = st.session_state.body_input_vowels[:-1]
            st.session_state.body_vowel_deletes += 1
        st.rerun()
    st.write("－－－－－－－－－－－－－ー－－－－－－－－－－－－－ー－－－－－－－－－－－－－ー")   
    st.header(f"入力：{st.session_state.body_input_vowels}")

    # ---------- 候補なし ----------
    if st.button("候補になかった", key="body_vowel_none"):
        st.session_state.body_vowel_time_end = time.time()
        st.session_state.phase = "body_vowel_free_input"
        st.rerun()

# ===============================
# 13.5 体調 母音 自由入力
# ===============================

elif st.session_state.phase == "body_yesno_start":
    st.session_state.body_list = random.sample(
        ["ねむい", "つかれた", "げんき", "しんどい", "いそがしい"], 5
    )
    st.session_state.body_index = 0
    st.session_state.body_steps = 0
    st.session_state.body_yesno_time_start = time.time()
    st.session_state.phase = "body_yesno_check"
    st.rerun()

elif st.session_state.phase == "body_vowel_free_input":
    body_free = st.text_input("体調を自由入力してください")

    if st.button("決定"):
        st.session_state.body_vowel_free_text = body_free
        st.session_state.phase = "save_body"
        st.rerun()

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
        
elif st.session_state.phase == "save_body":
    append_row([
        st.session_state.experiment_id,
        st.session_state.taste_result,
        st.session_state.taste_free_text,
        st.session_state.taste_steps,
        round(
            st.session_state.taste_time_end
            - st.session_state.taste_time_start, 2
        ),
        st.session_state.vowel_result,
        st.session_state.vowel_free_text,
        st.session_state.vowel_steps,
        st.session_state.vowel_deletes,
        round(
            st.session_state.vowel_time_end
            - st.session_state.vowel_time_start, 2
        ),
        st.session_state.body_yesno_result,
        st.session_state.body_yesno_free_text,
        st.session_state.body_steps,
        round(
            st.session_state.body_yesno_time_end
            - st.session_state.body_yesno_time_start, 2
        ),
        st.session_state.body_vowel_result,
        st.session_state.body_vowel_free_text,
        st.session_state.body_vowel_steps,
        st.session_state.body_vowel_deletes,
        round(
            st.session_state.body_vowel_time_end
            - st.session_state.body_vowel_time_start, 2
        ),
    ])

    st.success("すべて完了しました！")
    st.write("ご協力ありがとうございました。\n最初に戻るを押してから終えてください！")


    if st.button("最初に戻る"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()







