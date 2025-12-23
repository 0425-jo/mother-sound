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
    

# =============================== Google Sheets 接続 ===============================
SPREADSHEET_ID = "1V8eSJwIuwHEWktTsU8VFZlSOzXuM0jUqa8jTjv1vbxQ"

def append_row(data):
    ws = get_worksheet()
    ws.append_row(data, value_input_option="USER_ENTERED")

# =============================== 母音処理関数（変更なし）===============================
def is_chouon_word(romaji):
    return "-" in romaji

def match_pattern(word_vowels, input_pattern, romaji_word):
    if not input_pattern:
        return False
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

word_dict = load_dict()

# =============================== session_state 初期化（変更なし）===============================
if "phase" not in st.session_state:
    st.session_state.phase = "id_input"

if "experiment_id" not in st.session_state:
    st.session_state.experiment_id = ""
if "age_group" not in st.session_state:
    st.session_state.age_group = ""
if "vowel_ui_eval" not in st.session_state:
    st.session_state.vowel_ui_eval = ""

# 味覚系
for key, default in {
    "taste_list": [], "taste_index": 0, "body_steps": 0, "taste_result": None,
    "taste_free_text": "", "taste_time_start": None, "taste_time_end": None, "taste_steps": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 母音（味覚）
for key, default in {
    "input_vowels": "", "vowel_result": None, "vowel_free_text": "", "vowel_time_start": None,
    "vowel_time_end": None, "vowel_steps": 0, "vowel_deletes": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 体調 YES/NO
for key, default in {
    "body_list": [], "body_index": 0, "body_yesno_result": None,
    "body_yesno_time_start": None, "body_yesno_time_end": None, "body_yesno_free_text": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# 体調 母音
for key, default in {
    "body_input_vowels": "", "body_vowel_result": None, "body_vowel_free_text": "",
    "body_vowel_time_start": None, "body_vowel_time_end": None,
    "body_vowel_steps": 0, "body_vowel_deletes": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if "saved" not in st.session_state:
    st.session_state.saved = False

# =============================== 1. ID入力 ===============================
if st.session_state.phase == "id_input":
    st.title("１分で終わる入力実験です")
    st.header("これから2つの質問に答えてもらいます")
    st.header("思ったものを**「考えすぎず直感で」**選んでください")
    st.write("ニックネーム、入力時間、選択結果などは研究目的で保存されます")
    st.session_state.experiment_id = st.text_input("ニックネーム")
    st.session_state.age_group = st.selectbox("年齢", ["", "10代", "20代", "30代", "40代", "50代", "60代以上"])

    if st.button("スタート"):
        if st.session_state.experiment_id.strip() and st.session_state.age_group:
            st.session_state.taste_list = random.sample(["あまい", "からい", "すっぱい", "しょっぱい", "にがい"], 5)
            st.session_state.taste_index = 0
            st.session_state.taste_steps = 0
            st.session_state.phase = "taste_vowel_intro"
            st.rerun()
        else:
            st.warning("ニックネームと年齢を入力してください")

# =============================== 味覚 母音入力 開始 ===============================
elif st.session_state.phase == "taste_vowel_intro":
    st.header("第1問:今、どんな味のものが食べたい？")
    st.header("**母音だけ**で答えてください。")
    st.write("画面左の「あいうえお」を押して入力します")
    st.markdown("例:あまい→ああい　/ しょっぱい→おあい / あまずっぱい→ああうあい / こってり→おえい")
    st.write("※「ん」=「う」/「じゃ」= 「あ」として入力してください")

    if st.button("母音入力を始める"):
        st.session_state.input_vowels = ""
        st.session_state.vowel_steps = 0
        st.session_state.vowel_deletes = 0
        st.session_state.vowel_time_start = time.time()
        st.session_state.phase = "vowel_input"
        st.rerun()

# =============================== 味覚 母音入力 本体（スマホでも横並び！）===============================
elif st.session_state.phase == "vowel_input":
    st.write("どんな味が食べたい？")
    st.caption("※「ん」=「う」 / 「じゃ」=「あ」")

    # ① 母音ボタン
    for v, label in zip(["a", "i", "u", "e", "o"], ["あ", "い", "う", "え", "お"]):
        if st.button(label, use_container_width=True):
            st.session_state.input_vowels += v
            st.session_state.vowel_steps += 1
            st.rerun()

    # ② 削除
    if st.button("⌫削除", use_container_width=True):
        if st.session_state.input_vowels:
            st.session_state.input_vowels = st.session_state.input_vowels[:-1]
            st.session_state.vowel_deletes += 1
        st.rerun()

    st.markdown("---")

    # ③ 入力確認表示
    st.subheader(f"入力：{st.session_state.input_vowels}")

    # ④ 候補群
    if st.session_state.input_vowels:
        candidates = []
        for r, j in word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.input_vowels, r):
                candidates.append((r, j, v))

        candidates.sort(key=lambda x: sort_key(x, st.session_state.input_vowels))

        for idx, (r, j, v) in enumerate(candidates[:6]):
            if st.button(j, key=f"taste_cand_{idx}_{r}", use_container_width=True):
                st.session_state.vowel_result = j
                st.session_state.vowel_time_end = time.time()
                st.session_state.phase = "save_vowel"
                st.rerun()

    # ⑤ 候補になかった
    if st.button("候補になかった", use_container_width=True):
        st.session_state.vowel_time_end = time.time()
        st.session_state.phase = "vowel_free_input"
        st.rerun()

# =============================== 味覚 母音 自由入力 ===============================
elif st.session_state.phase == "vowel_free_input":
    st.header("では、どんな味が食べたい気分でしたか？")
    st.session_state.vowel_free_text = st.text_input("自由入力")
    if st.button("決定"):
        if st.session_state.vowel_free_text.strip():
            st.session_state.phase = "save_vowel"
            st.rerun()
        else:
            st.warning("入力してください")

# =============================== 味覚 保存 → 次のフェーズ ===============================
elif st.session_state.phase == "save_vowel":
    st.session_state.phase = "taste_yesnoima"
    st.rerun()

# =============================== 味覚 YES/NO ===============================
elif st.session_state.phase == "taste_yesnoima":
    idx = st.session_state.taste_index
    tastes = st.session_state.taste_list
    if idx >= len(tastes):
        st.session_state.phase = "taste_free_input"
        st.rerun()
    current = tastes[idx]
    st.header("また、同じ質問をします！")
    st.write("当てはまれば YES,違えば NO を押してください")
    st.write("さっき答えた味覚と同じのが出るまでNOを押し続けてください")
    if st.button("スタート"):
        st.session_state.taste_time_start = time.time()
        st.session_state.phase = "taste_checking"
        st.rerun()

elif st.session_state.phase == "taste_checking":
    idx = st.session_state.taste_index
    tastes = st.session_state.taste_list
    if idx >= len(tastes):
        st.session_state.taste_time_end = time.time()
        st.session_state.phase = "taste_free_input"
        st.rerun()
    current = tastes[idx]
    st.subheader(f"「{current}」味を食べたいですか？")
    c1, c2 = st.columns(2)
    if c1.button("YES"):
        st.session_state.taste_steps += 1
        st.session_state.taste_result = current
        st.session_state.taste_time_end = time.time()
        st.session_state.phase = "save_taste"
        st.rerun()
    if c2.button("NO"):
        st.session_state.taste_steps += 1
        st.session_state.taste_index += 1
        st.rerun()

elif st.session_state.phase == "save_taste":
    st.session_state.phase = "body_vowel_start"
    st.rerun()

elif st.session_state.phase == "taste_free_input":
    st.header("では、どんな味の気分でしたか？")
    st.session_state.taste_free_text = st.text_input("自由に入力してください")
    if st.button("決定"):
        if st.session_state.taste_free_text.strip():
            st.session_state.phase = "body_vowel_start"
            st.rerun()
        else:
            st.warning("入力してください")

# =============================== 体調 母音入力 開始 ===============================
elif st.session_state.phase == "body_vowel_start":
    st.header("第2問：今の体調はどうですか？")
    st.header("さっきと同じく「母音のみ」で答えてください。")
    st.write("例）だるい→あうい / すっきり→ういい / ねむい→えうい / パーフェクト→ああうえお")
    st.write("※「ん」=「う」/「じゃ」= 「あ」として入力してください")

    if st.button("母音入力を始める"):
        st.session_state.body_input_vowels = ""
        st.session_state.body_vowel_steps = 0
        st.session_state.body_vowel_deletes = 0
        st.session_state.body_vowel_time_start = time.time()
        st.session_state.phase = "body_vowel_input"
        st.rerun()

# =============================== 体調 母音入力 本体（スマホでも横並び！）===============================
elif st.session_state.phase == "body_vowel_input":
    st.write("今の体調に一番近いものを、母音で入力してください")
    st.caption("※「ん」=「う」 / 「だるい」→「あうい」など")

    # ① 母音ボタン
    for v, label in zip(["a", "i", "u", "e", "o"], ["あ", "い", "う", "え", "お"]):
        if st.button(label, key=f"body_vowel_{v}", use_container_width=True):
            st.session_state.body_input_vowels += v
            st.session_state.body_vowel_steps += 1
            st.rerun()

    # ② 削除
    if st.button("⌫削除", key="body_delete", use_container_width=True):
        if st.session_state.body_input_vowels:
            st.session_state.body_input_vowels = st.session_state.body_input_vowels[:-1]
            st.session_state.body_vowel_deletes += 1
        st.rerun()

    st.markdown("---")

    # ③ 入力確認
    st.subheader(f"入力：{st.session_state.body_input_vowels}")

    # ④ 候補表示
    body_word_dict = word_dict
    if st.session_state.body_input_vowels:
        candidates = []
        for r, j in body_word_dict.items():
            v = extract_vowels(r)
            if match_pattern(v, st.session_state.body_input_vowels, r):
                candidates.append((r, j, v))

        candidates.sort(
            key=lambda x: sort_key(x, st.session_state.body_input_vowels)
        )

        if len(candidates) == 0:
            st.info("該当する候補がありません")

        for idx, (r, j, v) in enumerate(candidates[:6]):
            if st.button(
                j,
                key=f"body_cand_{idx}_{r}",
                use_container_width=True
            ):
                st.session_state.body_result = j
                st.session_state.body_time_end = time.time()
                st.session_state.phase = "body_start"
                st.rerun()

    # ⑤ 候補になかった
    if st.button("候補になかった", key="body_not_found", use_container_width=True):
        st.session_state.body_time_end = time.time()
        st.session_state.phase = "body_free_input"
        st.rerun()


# =============================== 体調 母音 自由入力 ===============================
elif st.session_state.phase == "body_vowel_free_input":
    st.session_state.body_vowel_free_text = st.text_input("体調を自由入力してください")
    if st.button("決定"):
        st.session_state.phase = "body_start"
        st.rerun()

# =============================== 体調 YES/NO ===============================
elif st.session_state.phase == "body_start":
    st.session_state.body_list = random.sample(["ねむい", "つかれた","げんき","しんどい","いそがしい"], 5)
    st.session_state.body_index = 0
    st.session_state.body_steps = 0

    st.header("また、同じ質問をします！")
    st.write("当てはまれば YES,違えば NO を押してください")
    st.write("さっき答えた味覚と同じのが出るまでNOを押し続けてください")
    if st.button("スタート"):
        st.session_state.body_yesno_time_start = time.time()
        st.session_state.phase = "body_yesno_check"
        st.rerun()

elif st.session_state.phase == "body_yesno_check":
    idx = st.session_state.body_index
    if idx < len(st.session_state.body_list):
        current = st.session_state.body_list[idx]
        st.subheader(f"「{current}」ですか？")
        c1, c2 = st.columns(2)
        if c1.button("YES"):
            st.session_state.body_steps += 1
            st.session_state.body_yesno_result = current
            st.session_state.body_yesno_time_end = time.time()
            st.session_state.phase = "save_body"
            st.rerun()
        if c2.button("NO"):
            st.session_state.body_steps += 1
            st.session_state.body_index += 1
            st.rerun()
    else:
        st.subheader("どれでもないですか？")
        if st.button("どれでもない"):
            st.session_state.body_yesno_time_end = time.time()
            st.session_state.phase = "body_free_input"
            st.rerun()

elif st.session_state.phase == "body_free_input":
    st.header("どんな身体の状態、体調ですか？（自由入力）")
    st.session_state.body_yesno_free_text = st.text_input("自由入力")
    if st.button("決定"):
        if st.session_state.body_yesno_free_text.strip():
            st.session_state.phase = "save_body"
            st.rerun()
        else:
            st.warning("入力してください")

# =============================== 最終 保存 & リセット ===============================
elif st.session_state.phase == "save_body":
    st.success("すべて完了しました！")
    st.write("ご協力ありがとうございました。\n最初に戻るを押してから終えてください！")
    st.markdown("---")
    st.subheader("最後に、操作について教えてください")
    st.session_state.vowel_ui_eval = st.radio(
        "母音入力はわかりやすかったですか？",
        ["説明を読まずとも直感的に使えた", "例を見ればすぐ理解できた", "試しながら使い方が分かった", "最後までよくわからなかった"],
        index=None
    )

    if st.button("最初に戻る"):
        if not st.session_state.vowel_ui_eval:
            st.warning("アンケートへの回答をお願いします")
        else:
            if not st.session_state.saved:
                body_yesno_start = st.session_state.body_yesno_time_start or time.time()
                body_yesno_end   = st.session_state.body_yesno_time_end or time.time()
                body_yesno_duration = round(body_yesno_end - body_yesno_start, 2)

                body_vowel_start = st.session_state.body_vowel_time_start or time.time()
                body_vowel_end   = st.session_state.body_vowel_time_end or time.time()
                body_vowel_duration = round(body_vowel_end - body_vowel_start, 2)

                append_row([
                    st.session_state.experiment_id,
                    st.session_state.taste_result,
                    st.session_state.taste_free_text,
                    st.session_state.taste_steps,
                    round(st.session_state.taste_time_end - st.session_state.taste_time_start, 2) if st.session_state.taste_time_start else "",
                    st.session_state.vowel_result,
                    st.session_state.vowel_free_text,
                    st.session_state.vowel_steps,
                    st.session_state.vowel_deletes,
                    round(st.session_state.vowel_time_end - st.session_state.vowel_time_start, 2) if st.session_state.vowel_time_start else "",
                    st.session_state.body_yesno_result,
                    st.session_state.body_yesno_free_text,
                    st.session_state.body_steps,
                    body_yesno_duration,
                    st.session_state.body_vowel_result,
                    st.session_state.body_vowel_free_text,
                    st.session_state.body_vowel_steps,
                    st.session_state.body_vowel_deletes,
                    body_vowel_duration,
                    st.session_state.age_group,
                    st.session_state.vowel_ui_eval,
                ])
                st.session_state.saved = True

            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()










