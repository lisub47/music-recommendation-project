
import streamlit as st
import requests
from dotenv import load_dotenv
import os

# ==========================================
# 讀取環境變數
# ==========================================
load_dotenv()

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8001"
).rstrip("/")

# 推薦設定
RECOMMENDATION_SEARCH_LIMIT = 100
RECOMMENDATION_DISPLAY_LIMIT = 10


# ==========================================
# 設定 Streamlit 頁面
# ==========================================
st.set_page_config(
    page_title="音樂推薦系統",
    layout="wide"
)

st.title("🎵 音樂推薦系統")


# ==========================================
# 共用函式：顯示歌曲卡片
# ==========================================
def display_song_cards(data):
    """
    使用 Streamlit 原生元件，
    將歌曲以 5 欄卡片形式顯示。
    """

    cols = st.columns(5)

    for idx, item in enumerate(data):

        song = item.get("song", {})
        artist_name = item.get("artist_name", "未知藝人")

        song_title = song.get(
            "song_title",
            "未知歌曲"
        )

        song_id = song.get(
            "song_id",
            "未知 ID"
        )

        col = cols[idx % 5]

        with col:
            with st.container(border=True):

                st.markdown(
                    f"**🎵 {song_title}**"
                )

                st.write(
                    f"**藝人：** {artist_name}"
                )

                st.caption(
                    f"歌曲 ID：{song_id}"
                )


# ==========================================
# 建立兩個分頁
# ==========================================
tab1, tab2 = st.tabs([
    "探索所有歌曲",
    "推薦與歌曲清單"
])


# ==========================================
# Tab 1：探索所有歌曲
# ==========================================
with tab1:

    st.subheader("🔍 探索所有歌曲")

    st.write("請輸入你想查詢的歌曲範圍：")

    # 輸入 Skip
    skip_input = st.number_input(
        "從第幾首開始 (Skip)：",
        min_value=0,
        value=0,
        step=1,
        help="輸入要跳過的歌曲數量，從 0 開始"
    )

    # 輸入 Limit
    limit_input = st.number_input(
        "顯示多少首歌曲 (Limit)：",
        min_value=1,
        value=10,
        step=1,
        help="輸入要顯示的歌曲數量，至少為 1"
    )

    # 儲存查詢結果，避免頁面重新整理後消失
    if "songs_data" not in st.session_state:
        st.session_state.songs_data = None

    if "songs_skip" not in st.session_state:
        st.session_state.songs_skip = 0

    # 取得歌曲按鈕
    if st.button(
        f"📂 取得歌曲 (跳過 {skip_input} 首，顯示 {limit_input} 首)"
    ):

        try:
            # 呼叫 FastAPI 歌曲 API
            songs_response = requests.get(
                f"{FASTAPI_URL}/songs/",
                params={
                    "skip": skip_input,
                    "limit": limit_input
                },
                timeout=15
            )

            if songs_response.status_code == 200:

                st.session_state.songs_data = (
                    songs_response.json()
                )

                st.session_state.songs_skip = skip_input

            else:
                st.error(
                    f"❌ 無法取得歌曲資料，"
                    f"HTTP 狀態碼：{songs_response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            st.error(
                f"❌ 無法連接 FastAPI 後端：{e}"
            )

    # 顯示歌曲查詢結果
    if st.session_state.songs_data is not None:

        data = st.session_state.songs_data

        if data:

            st.write(
                f"以下是從第 **{st.session_state.songs_skip}** 首開始，"
                f"共 **{len(data)}** 首歌曲："
            )

            display_song_cards(data)

        else:
            st.info(
                "ℹ️ 系統中目前沒有歌曲資料，"
                "或您輸入的範圍無結果。"
            )


# ==========================================
# Tab 2：推薦與歌曲清單
# ==========================================
with tab2:

    st.header("💡 使用者推薦與歌曲瀏覽")

    user_ids = []

    # --------------------------------------
    # 取得使用者 ID 列表
    # --------------------------------------
    try:

        user_list_resp = requests.get(
            f"{FASTAPI_URL}/users/",
            params={
                "skip": 0,
                "limit": 10
            },
            timeout=15
        )

        if user_list_resp.status_code == 200:

            user_ids = user_list_resp.json()[:10]

        else:
            st.warning(
                "⚠️ 無法取得使用者列表，"
                "推薦功能可能受限。"
                f"HTTP 狀態碼：{user_list_resp.status_code}"
            )

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ 無法連線到後端服務，"
            "請檢查網路或 FastAPI 狀態。"
        )

    except requests.exceptions.RequestException as e:
        st.error(
            f"❌ 取得使用者 ID 時發生錯誤：{e}"
        )

    # --------------------------------------
    # 選擇使用者
    # --------------------------------------
    selected_user = st.selectbox(
        "請選擇一位使用者來獲取推薦：",
        user_ids if user_ids else ["無可用使用者"]
    )

    # 儲存推薦結果
    if "recommendation_data" not in st.session_state:
        st.session_state.recommendation_data = None

    if "recommendation_user" not in st.session_state:
        st.session_state.recommendation_user = None

    # 切換使用者時清除舊結果
    if (
        st.session_state.recommendation_user is not None
        and st.session_state.recommendation_user != selected_user
    ):
        st.session_state.recommendation_data = None

    # --------------------------------------
    # 呼叫推薦 API
    # --------------------------------------
    if st.button(
        "🚀 取得推薦歌曲",
        disabled=not bool(user_ids)
    ):

        if selected_user and selected_user != "無可用使用者":

            try:

                with st.spinner("正在搜尋適合您的推薦歌曲..."):

                    # 呼叫 FastAPI 推薦 API
                    rec_response = requests.get(
                        f"{FASTAPI_URL}/users/"
                        f"{selected_user}/recommendations",
                        params={
                            "limit": RECOMMENDATION_SEARCH_LIMIT
                        },
                        timeout=120
                    )

                if rec_response.status_code == 200:

                    data = rec_response.json()

                    # 最多顯示 10 首推薦歌曲
                    st.session_state.recommendation_data = (
                        data[:RECOMMENDATION_DISPLAY_LIMIT]
                    )

                    st.session_state.recommendation_user = (
                        selected_user
                    )

                else:
                    st.error(
                        "❌ 無法取得推薦歌曲，"
                        f"HTTP 狀態碼：{rec_response.status_code}"
                    )

            except requests.exceptions.Timeout:
                st.error(
                    "❌ 推薦查詢逾時，請稍後再試。"
                )

            except requests.exceptions.RequestException as e:
                st.error(
                    f"❌ 無法連接推薦服務：{e}"
                )

    # --------------------------------------
    # 顯示推薦歌曲
    # --------------------------------------
    if st.session_state.recommendation_data is not None:

        data = st.session_state.recommendation_data

        if data:

            st.write(
                f"以下是為使用者 **{selected_user}** "
                f"推薦的 **{len(data)}** 首歌曲："
            )

            # 使用共用歌曲卡片函式
            display_song_cards(data)

        else:
            st.info(
                f"ℹ️ 目前沒有為使用者 `{selected_user}` "
                "找到推薦歌曲。"
            )
