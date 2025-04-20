import streamlit as st # フロントエンドを扱うstreamlitの機能をインポート
import requests # リクエストするための機能をインポート
from datetime import date # 現在時刻などの時間を扱う機能をインポート
from openai import OpenAI # openAIのchatGPTのAIを活用するための機能をインポート
import os # OSが持つ環境変数OPENAI_API_KEYにAPIを入力するためにosにアクセスするためのライブラリをインポート
from webapp_record import record_and_transcribe
from webapp_meal_photo import meal_and_transcribe
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dotenv import load_dotenv
import pyrebase
import base64
from PIL import Image
from pathlib import Path

#.envを呼び出せるようにする
load_dotenv()

#Firebaseの初期化（1回だけ）
if not firebase_admin._apps:
    cred_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
#サービスアカウントキーの読み込み
    cred = credentials.Certificate(cred_path)
#参考ページ：https://docs.kanaries.net/ja/topics/Streamlit/firebase-streamlit
    firebase_admin.initialize_app(cred)

#firebaseクライアントを取得
db = firestore.client()

# Firebase Authentication用の設定
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()


api_key =os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

#ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
#UI変更
#フォント変更
def apply_custom_font():
    font_path = "static/1.otf"
    with open(font_path, "rb") as font_file:
        font_data = font_file.read()
        encoded_font = base64.b64encode(font_data).decode()
    
    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'CustomFont';
            src: url(data:font/otf;base64,{encoded_font});
        }}
        * {{
            font-family: 'CustomFont', sans-serif !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_font()

# 背景画像をBase64形式でエンコード
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# CSSに背景画像を適用
background_image_path = "background.png"  # ローカル画像のパス
encoded_image = get_base64_encoded_image(background_image_path)

screencast_bg_css = f"""
<style>
    [data-testid="stApp"] {{
        background-image: url("data:image/jpeg;base64,{encoded_image}");
        background-size: contain;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
</style>
"""
st.markdown(screencast_bg_css, unsafe_allow_html=True)

# メッセージ枠のスタイルを変更するCSSを追加
custom_style = """
<style>
    div[data-testid="stAlertContainer"] {
        background-color: #fad67d; /* 背景色（薄いオレンジに変更） */ 
        padding: 10px; /* 内側の余白 */
        border-radius: 5px; /* 角を丸める */
        textColor: #090547; # 紺色
    }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)



#ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
#サイドバー　メニュー
#初期化
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.sidebar.title("ログイン")

    email = st.sidebar.text_input("メールアドレス")
    password = st.sidebar.text_input("パスワード", type="password")

    login_col,signup_col = st.sidebar.columns(2)

    with login_col:
        if st.button("ログインする"):
            try:
                user = auth.sign_in_with_email_and_password(email,password)
                st.session_state.user = user
                st.success("✅ ログイン成功しました！")
                st.rerun() # ログイン後すぐ画面を更新
            except Exception as e:
                st.error(f"ログインに失敗しました：{e}")

    with signup_col:
        if st.button("新規登録する"):
            try:
                user = auth.create_user_with_email_and_password(email,password)
                st.session_state.user = user
                st.success("✅ 新規登録＆ログインに成功しました！")
                st.rerun() # ログイン後すぐ画面を更新
            except Exception as e:
                st.error(f"新規登録に失敗しました：{e}")
    st.stop() #ログインするまでこの先を実行しない


st.sidebar.title("メニュー")
mode = st.sidebar.selectbox(
    "操作を選んでください",
    ("今日の記録を入力する","過去の記録を確認する")
)

if mode == "今日の記録を入力する":

    st.title("今日も1日お疲れさまでした")

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #カレンダーで記録日の日付を入力させる
    st.markdown("### 今日の日付を教えて下さい")
    selected_date = st.date_input(
        label="今日は",
        value=date(2025,4,1),
        min_value=date(2025,4,1),
        max_value=date(2099,3,31),
        )

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー

    #今日一日の点数をスライダーで選ばせる
    st.markdown("### 今日1日の点数を教えて下さい")
    day_value = st.slider(
        label="今日の点数は",
        min_value= 0,
        max_value= 100,
        value= 0,
    )

    if day_value == 100:
        st.balloons()
        st.success("素晴らしい！今日は最高の1日だったんですね👏🎉")
    elif day_value == 99:
        st.success("惜しい！あと一歩！明日は100点💯の１日にできるといいですね！👏")
    elif 80 <= day_value <= 98:
        st.success("良かったです！今日はいい１日だったんですね！！👏👏")
    elif 1<= day_value < 80:
        st.success("明日はいい１日にしましょう！！")
    else:
        pass

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #音声で今日1日の感想を録音してもらう
    #webapp_record.pyのモジュールを呼び出す
    edited_day_text = record_and_transcribe(client)

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #今日歩いた歩数を入力させる
    st.markdown("### 今日の歩数を教えて下さい")
    step_count = st.number_input(
        label="今日の歩数は",
        min_value= 0,
        max_value= 50000,
        value=0,
        step=100,
        format="%d"
    )

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #食べたものの画像をアップロードさせる
    #webapp_meal_photo.pyのモジュールを呼び出す
    st.session_state.meal_text = meal_and_transcribe(client)

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #Chatgptに情報を投げる
    prompt = f"""
    以下は、今日1日の健康状態に関する情報です。この情報を元に、プロの健康管理アドバイザーとして、まず入力内容のサマリを簡単に記載した上で、明日1日を健康的に過ごすためのアドバイスを日本語でください。
    - 日付:{selected_date.strftime('%Y年%m月%d日')}
    - 今日の1日の点数（自己評価）:{day_value}点
    - 今日の感想（本人による音声の文字起こし）：{edited_day_text}
    - 今日の歩数:{step_count}歩
    - 本日の食事:{st.session_state.meal_text}
    """

    if "advice" not in st.session_state:
        st.session_state.advice = ""

    if st.button("明日1日の過ごし方についてのアドバイスをもらう"):
        with st.spinner("アドバイスを取得中..."):
            response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":"あなたは優しく丁寧な、プロの健康管理アドバイザーで、いつも的確にアドバイスをしてくれます。"},
                {"role":"user","content":prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        st.session_state.advice = response.choices[0].message.content
        st.markdown("### 明日に向けた健康アドバイスです")
        st.write(st.session_state.advice)


    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #記録を保存する
    if st.button("今日の記録を保存する"):
        db.collection("daily_logs").add({
            "date":selected_date.strftime('%Y年%m月%d日'),
            "score":day_value,
            "emotion_text":edited_day_text,
            "steps":step_count,
            "meal_summary":st.session_state.meal_text,
            "advice": st.session_state.advice
        })
        st.success("✅ 今日の記録を保存しました！")


elif mode == "過去の記録を確認する":
    st.title("過去の記録を探す")

    #サイドバーで日付表示
    search_date = st.sidebar.date_input(
    label="表示したい日付を選んでください",
    value=date(2025,4,1),
    min_value=date(2025,4,1),
    max_value=date(2099,3,31),
    )

    # 日付を文字列に変換
    date_str = search_date.strftime("%Y年%m月%d日")

    # Firestoreからデータ取得
    docs = db.collection("daily_logs").where("date","==", date_str).stream()

    found = False
    for doc in docs:
        data = doc.to_dict()
        with st.container():
            st.subheader(f"🗓️ {data.get('date', '日付なし')}")
            st.write(f"🔵 スコア：{data.get('score', '不明')}点")
            st.write(f"🗣️ 今日の感想：{data.get('emotion_text', 'なし')}")
            st.write(f"🚶‍♂️ 歩数：{data.get('steps', '不明')}歩")
            st.write(f"🍽️ 食事まとめ：{data.get('meal_summary', 'なし')}")
            st.write(f"💡 アドバイス：{data.get('advice', 'なし')}")
        found = True

    if not found:
        st.warning("この日付のデータは存在しません。")