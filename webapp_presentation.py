import streamlit as st # フロントエンドを扱うstreamlitの機能をインポート
import requests # リクエストするための機能をインポート
from datetime import date # 現在時刻などの時間を扱う機能をインポート
from openai import OpenAI # openAIのchatGPTのAIを活用するための機能をインポート
import os # OSが持つ環境変数OPENAI_API_KEYにAPIを入力するためにosにアクセスするためのライブラリをインポート
from webapp_record import record_and_transcribe
from webapp_meal_photo import meal_and_transcribe
from webapp_ui_code import ui_and_transcribe
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from dotenv import load_dotenv
from firebase_auth import firebase_login, firebase_signup
import json


#.envを呼び出せるようにする
load_dotenv()

#FirebaseのAPIキーを設定
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

#Firebaseの初期化（1回だけ）
if not firebase_admin._apps:
    try: #まずSecret Managerから読み込む（クラウド環境用）
        service_account_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
        cred = credentials.Certificate(service_account_info)
    except Exception:#ローカル環境用（サービスアカウントのJSONファイルパスから読む）
        cred_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred)

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
db = firestore.client()

#OpenAI設定
api_key =os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#ログイン/新規登録UI
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
def sidebar_auth():
    st.sidebar.title("ログイン・新規登録")

    if "user" not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        email = st.sidebar.text_input("メールアドレス")
        password = st.sidebar.text_input("パスワード", type="password")

        login_col,signup_col = st.sidebar.columns(2)

        with login_col:
            if st.button("ログインする"):
                if email and password:
                    result = firebase_login(email,password)
                    if "idToken" in result:
                        st.session_state.user = result
                        st.success("✅ ログイン成功しました！")
                        st.rerun() # ログイン後すぐ画面を更新
                    else:
                        st.error(f"ログインに失敗しました:{result.get('error', {}).get('message', '不明なエラー')}")
                else:
                    st.warning("メールアドレスとパスワードを入力してください")

        with signup_col:
            if st.button("新規登録する"):
                if email and password:
                    result = firebase_signup(email,password)
                    if "idToken" in result:
                        st.session_state.user = result
                        st.success("✅ 新規登録＆ログインに成功しました！")
                        st.rerun() # ログイン後すぐ画面を更新
                    else:
                        st.error(f"新規登録に失敗しました:{result.get('error', {}).get('message', '不明なエラー')}")
                else:
                    st.warning("メールアドレスとパスワードを入力してください。")

        # ログイン・新規登録待ちの間はストップ
        st.stop()
    else:
        st.sidebar.success(f"ようこそ！")

# ログイン機能の呼び出し
sidebar_auth()

#ーーーーーーーーーーーーーーーーーーーーーーーーーー
#UI変更
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#webapp_ui_codeの関数を呼び出し
ui_and_transcribe(client)


#ーーーーーーーーーーーーーーーーーーーーーーーーーーー

st.sidebar.title("メニュー")
mode = st.sidebar.selectbox(
    "操作を選んでください",
    ("今日の記録を入力する","過去の記録を確認する")
)

if mode == "今日の記録を入力する":
    # タイトルと画像を横並びで両脇に配置
    col1, col2 ,col3 = st.columns([1, 3, 1])  # 左画像1：タイトル5 : 右画像1
    with col1:
        st.image("dog.png", width=100)  # 右側の画像（小さく表示）
    with col2:
        st.title("今日も1日おつかれさま")  # 中央のタイトル
    with col3:
        st.image("dog2.png", width=100)  # 右側の画像（小さく表示）


#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#カレンダーで記録日の日付を入力させる
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    st.markdown("### 今日の日付を教えて下さい")
    selected_date = st.date_input(
        label="今日は",
        value=date(2025,4,1),
        min_value=date(2025,4,1),
        max_value=date(2099,3,31),
        )

#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#今日一日の点数をスライダーで選ばせる
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
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

#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#音声で今日1日の感想を録音してもらう
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #webapp_record.pyの関数を呼び出し
    record_and_transcribe(client)

#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#今日歩いた歩数を入力させる
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    st.markdown("### 今日の歩数を教えて下さい")
    step_count = st.number_input(
        label="今日の歩数は",
        min_value= 0,
        max_value= 50000,
        value=0,
        step=100,
        format="%d"
    )

#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#食べたものの画像をアップロードさせる
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    #webapp_meal_photo.pyの関数を呼び出し
    st.session_state.meal_text = meal_and_transcribe(client)

#ーーーーーーーーーーーーーーーーーーーーーーーーー
#Chatgptに情報を渡す
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    prompt = f"""
    以下は、今日1日の健康状態に関する情報です。この情報を元に、プロの健康管理アドバイザーとして、まず入力内容のサマリを簡単に記載した上で、明日1日を健康的に過ごすためのアドバイスを日本語でください。
    - 日付:{selected_date.strftime('%Y年%m月%d日')}
    - 今日の1日の点数（自己評価）:{day_value}点
    - 今日の感想（本人による音声の文字起こし）：{st.session_state.edited_day_text}
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


#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
#記録を保存する
#ーーーーーーーーーーーーーーーーーーーーーーーーーーー
    if st.button("今日の記録を保存する"):
        db.collection("daily_logs").add({
            "date":selected_date.strftime('%Y年%m月%d日'),
            "score":day_value,
            "emotion_text":st.session_state.edited_day_text,
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