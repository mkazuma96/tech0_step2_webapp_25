#音声で今日1日の感想を録音してもらう
import streamlit as st
import uuid
import wave
from audio_recorder_streamlit import audio_recorder
import os # OSが持つ環境変数OPENAI_API_KEYにAPIを入力するためにosにアクセスするためのライブラリをインポート


def record_and_transcribe(client, key_name = "recorder_day"):
    st.markdown("### 今日はどんな1日だったか教えて下さい！")

    # ★ここで最初に初期化する
    if "day_contents" not in st.session_state:
        st.session_state.day_contents = None
    if "recording" not in st.session_state:
        st.session_state.recording = False


    if st.button("🎙️ 録音を開始する"):
        st.session_state.recording = True

    if st.session_state.recording:
        day_contents = audio_recorder(
            energy_threshold = 300,
            text="クリックして音声を録音しよう！",
            pause_threshold= 30,
            sample_rate = 48_000,
            key="recorder_day"
        )

        if day_contents is not None:
            st.session_state.day_contents = day_contents
            st.session_state.recording = False #録音したら録音モードをオフに

# 録音データが存在するなら、音声を再生＋文字起こしボタン表示
    if st.session_state.day_contents is not None:
        st.audio(st.session_state.day_contents)


        if st.button("📝 文字起こしを開始する"):
            # 一意のファイル名を生成
            filename_day = f"audio_day_{uuid.uuid4()}.wav"

            #waveライブラリで音声を.wavファイルとして保存。
            with wave.open(filename_day,"wb") as f:
                f.setnchannels(1)
                f.setsampwidth(2) # サンプル幅（2バイト = 16bit）
                f.setframerate(48000) # サンプリングレート
                f.writeframes(st.session_state.day_contents)

            with open(filename_day,"rb") as f:
                day_transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="ja",
                )
                recognized_day_text = day_transcription.text

            st.write("🎙️ 音声の文字起こし結果：")
            st.write(recognized_day_text)

            if "edited_day_text" not in st.session_state:
                st.session_state.edited_day_text = recognized_day_text

            st.session_state.edited_day_text = st.text_area(
                label="文字起こし内容を修正できます：",
                value=st.session_state.edited_day_text,
                height=300
            )

            # ファイル削除
            os.remove(filename_day)

            return st.session_state.edited_day_text
