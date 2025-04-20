import base64
from PIL import Image
from pathlib import Path
import streamlit as st # フロントエンドを扱うstreamlitの機能をインポート

#関数を定義
def ui_and_transcribe(client,key_name = "uicode"):

#関数の中身
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