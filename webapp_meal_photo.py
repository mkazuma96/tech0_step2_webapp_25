#食べたものの画像をアップロードさせる
import streamlit as st
import base64
from PIL import Image

#関数を定義
def meal_and_transcribe(client, key_name = "meal_text"):
#関数の中身

    if "meal_text" not in st.session_state:
        st.session_state.meal_text = ""

    st.markdown("### 今日食べた画像をアップロードしてください")
    uploaded_file = st.file_uploader("食事の画像をアップロードしてください",type=["jpg","jpeg","png"])

    if uploaded_file is not None:
        # 画像表示
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた画像", use_container_width=False,width=300)

        #画像をバイトに変換
        image_bytes = uploaded_file.getvalue()

        if st.button("画像を解析する"):
            #過去コード（メモ用）
            # Base64にエンコード
            #image_bytes = uploaded_file.read()
            #base64_image = base64.b64encode(image_bytes).decode("utf-8")
            #mime_type = uploaded_file.type # 例）"image/jpeg" や "image/png"
            #data_url = f"data:{mime_type};base64,{base64_image}"

            with st.spinner("画像を解析中..."):
                response = client.chat.completions.create(
                    model = "gpt-4o",
                    messages = [
                        {
                            "role":"user",
                            "content":[
                                {"type":"text","text":"この画像に写っている食事の内容を簡潔に説明して、健康および栄養の観点から厳しく評価してください"},
                                {"type":"image_url","image_url":{
                                    "url":f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}",
                                    "detail":"auto"
                                }}
                            ]
                        }
                    ],
                    max_tokens = 500
                )
                st.session_state.meal_text = response.choices[0].message.content
                st.success("解析結果はこちら:")
                st.write(st.session_state.meal_text)
    return st.session_state.meal_text