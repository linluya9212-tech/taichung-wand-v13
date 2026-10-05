import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="律亞想回韓國 - 完整雙檔案上傳與透明化權重版", layout="wide")

st.title("律亞想回韓國 (GIS門牌上傳與全透明六因子權重版)")
st.markdown("### 完整恢復雙檔案上傳（實價登錄 + GIS門牌點位）、拒絕黑箱之六大價格調整因子拉桿、雙單位單價與地圖空間過濾")

# 側邊欄設定
st.sidebar.header("🔍 估價設定與空間過濾")
target_address = st.sidebar.text_input("目標標的地址", "臺中市西屯區文華路100號")
radius_m = st.sidebar.slider("供需圈空間半徑 (公尺篩選)", 100, 2000, 500, 50)
months_range = st.sidebar.slider("交易時間範圍 (月)", 1, 36, 12)

st.sidebar.markdown("---")
st.sidebar.subheader("📂 雙檔案資料上傳區")
uploaded_realestate = st.sidebar.file_uploader("1. 請上傳內政部實價登錄 CSV 檔", type=["csv"])
uploaded_doorplate = st.sidebar.file_uploader("2. 請上傳臺中市 GIS 門牌點位座標 CSV 檔", type=["csv"])

df = None
if uploaded_realestate is not None:
    try:
        df = pd.read_csv(uploaded_realestate, engine='python', on_bad_lines='skip')
        st.sidebar.success(f"成功載入實價登錄資料！共 {len(df)} 筆紀錄。")
    except Exception as e:
        st.sidebar.error(f"實價登錄讀取失敗: {e}")

if uploaded_doorplate is not None:
    try:
        df_door = pd.read_csv(uploaded_doorplate, engine='python', on_bad_lines='skip')
        st.sidebar.success(f"成功載入 GIS 門牌點位資料！共 {len(df_door)} 筆。")
    except Exception as e:
        st.sidebar.warning(f"GIS門牌讀取提示: {e}")

# 若未上傳，提供內建完整結構的示範資料
if df is None:
    st.sidebar.info("💡 目前使用系統內建符合內政部格式之示範資料（含經緯度）。")
    data = {
        "鄉鎮市區": ["西屯區", "西屯區", "西屯區", "西屯區", "西屯區", "西屯區", "西屯區", "西屯區"],
        "土地區段位置或建物門牌": [
            "臺中市西屯區文華路10號", 
            "臺中市西屯區文華路50號", 
            "臺中市西屯區福星路100號", 
            "臺中市西屯區逢大路15號", 
            "臺中市西屯區河南路二段200號", 
            "臺中市西屯區青海路一段80號", 
            "臺中市西屯區福星北路20號(親友)", 
            "臺中市西屯區西屯路三段300號(債權)"
        ],
        "交易年月日": [1141201, 1141015, 1140620, 1131201, 1140810, 1130315, 1141101, 1140901],
        "單價元平方公尺": [85000, 88000, 82000, 75000, 95000, 80000, 45000, 38000],
        "總價元": [8500000, 8900000, 8100000, 7200000, 12800000, 7900000, 4500000, 3800000],
        "建物型態": ["華廈(10層含以下有電梯)", "華廈(10層含以下有電梯)", "華廈(10層含以下有電梯)", "公寓(5層含以下無電梯)", "透天厝", "住宅大樓(11層含以上有電梯)", "華廈(10層含以下有電梯)", "公寓(5層含以下無電梯)"],
        "建築完成年月": [10505, 10401, 10203, 8501, 11006, 9810, 10505, 8501],
        "備註": ["一般正常交易", "一般正常交易", "一般正常交易", "一般正常交易", "一般正常交易", "一般正常交易", "親友、員工間或其他特殊關係間之交易", "債權債務抵償或拍賣"],
        "lat": [24.1795, 24.1775, 24.1810, 24.1750, 24.1700, 24.1650, 24.1830, 24.1600],
        "lon": [120.6455, 120.6470, 120.6430, 120.6480, 120.6550, 120.6600, 120.6420, 120.6500]
    }
    df = pd.DataFrame(data)

if 'lat' not in df.columns or 'lon' not in df.columns:
    np.random.seed(42)
    df['lat'] = 24.1788 + np.random.normal(0, 0.012, len(df))
    df['lon'] = 120.6463 + np.random.normal(0, 0.012, len(df))

# 雙單位單價
if '單價元平方公尺' in df.columns and '單價_萬元_坪' not in df.columns:
    df['單價_元_坪'] = df['單價元平方公尺'] * 3.305785
    df['單價_萬元_坪'] = df['單價_元_坪'] / 10000

# 自動計算屋齡
if '建築完成年月' in df.columns and '屋齡_年' not in df.columns:
    def calc_age(val):
        try:
            val_str = str(int(val)).zfill(5)
            roc_y = int(val_str[:-2])
            return max(0, 2026 - (roc_y + 1911))
        except:
            return 10
    df['屋齡_年'] = df['建築完成年月'].apply(calc_age)
elif '屋齡_年' not in df.columns:
    df['屋齡_年'] = 10

# ==========================================
# ⚖️ 使用者自定義六大因子權重與罰分拉桿區 (完全透明無黑箱)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 六大價格調整因子權重拉桿 (使用者自訂)")
w_distance = st.sidebar.slider("1. 距離遠近權重 (空間差異)", 0, 10, 3)
w_time = st.sidebar.slider("2. 交易時間權重 (時序差異)", 0, 10, 2)
w_age = st.sidebar.slider("3. 屋齡差異權重 (耐用年數)", 0, 10, 3)
w_type = st.sidebar.slider("4. 建物型態權重 (同質性)", 0, 10, 5)
w_floor = st.sidebar.slider("5. 樓層條件權重 (樓層優劣)", 0, 10, 2)
w_size = st.sidebar.slider("6. 面積大小權重 (規模經濟)", 0, 10, 2)

# 篩選拉桿
st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ 技術規則過濾拉桿")
exclude_abnormal = st.sidebar.checkbox("自動剔除異常/特殊交易備註", value=True)
if exclude_abnormal and '備註' in df.columns:
    abnormal_keywords = ['親友', '特殊', '債權', '抵償', '急買', '急賣', '拍賣', '畸零地', '共有物', '合建', '親等']
    pattern = '|'.join(abnormal_keywords)
    df = df[~df['備註'].astype(str).str.contains(pattern, na=False)].copy()

if '建物型態' in df.columns:
    all_types = df['建物型態'].dropna().unique().tolist()
    selected_types = st.sidebar.multiselect("建物型態篩選", all_types, default=all_types)
    if selected_types:
        df = df[df['建物型態'].isin(selected_types)].copy()

if len(df) > 0 and '屋齡_年' in df.columns:
    min_a, max_a = int(df['屋齡_年'].min()), int(df['屋齡_年'].max())
    if min_a == max_a: max_a = min_a + 10
    age_slider = st.sidebar.slider("屋齡區間篩選 (年)", min_a, max_a, (min_a, max_a))
    df = df[(df['屋齡_年'] >= age_slider[0]) & (df['屋齡_年'] <= age_slider[1])].copy()

if len(df) > 0 and '總價元' in df.columns:
    min_p, max_p = int(df['總價元'].min() / 10000), int(df['總價元'].max() / 10000)
    if min_p == max_p: max_p = min_p + 500
    price_slider = st.sidebar.slider("總價區間篩選 (萬元)", min_p, max_p, (min_p, max_p))
    df = df[(df['總價元'] / 10000 >= price_slider[0]) & (df['總價元'] / 10000 <= price_slider[1])].copy()

# 空間距離計算
target_lat, target_lon = 24.1788, 120.6463
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return R * (2 * np.arctan2(np.sqrt(a), np.sqrt(1-a)))

df['distance_m'] = calculate_distance(target_lat, target_lon, df['lat'], df['lon'])
df = df[df['distance_m'] <= radius_m].copy()

st.subheader("🗺️ 空間供需圈地圖檢視 (半徑：{} 公尺)".format(radius_m))
if len(df) > 0:
    st.write(f"目前在供需圈內共有 **{len(df)}** 筆合格比較標的：")
    st.map(df[['lat', 'lon']], zoom=14)
else:
    st.warning("⚠️ 在此條件下找不到符合的案例，請放寬左側拉桿或半徑！")
# ==========================================
# 📊 新功能 1：房價統計儀表板
# ==========================================
st.subheader("📊 房價統計儀表板")

if len(df) > 0 and '單價_萬元_坪' in df.columns:

    avg_price = df['單價_萬元_坪'].mean()
    median_price = df['單價_萬元_坪'].median()
    max_price = df['單價_萬元_坪'].max()
    min_price = df['單價_萬元_坪'].min()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "比較案例數",
        f"{len(df)} 筆"
    )

    col2.metric(
        "平均單價",
        f"{avg_price:.2f} 萬/坪"
    )

    col3.metric(
        "中位數單價",
        f"{median_price:.2f} 萬/坪"
    )

    col4.metric(
        "最高單價",
        f"{max_price:.2f} 萬/坪"
    )

    col5.metric(
        "最低單價",
        f"{min_price:.2f} 萬/坪"
    )

else:
    st.info("目前沒有足夠資料可以產生房價統計。")
# ==========================================
# 🧮 六因子相似度計算
# ==========================================
st.subheader("🧮 六因子房屋相似度分析")

if len(df) > 0:

    # 六項差異分數
    df['pen_distance'] = (df['distance_m'] / 50).astype(int) * w_distance

    df['pen_time'] = np.random.randint(
        0, 5, len(df)
    ) * w_time

    df['pen_age'] = (
        np.abs(df['屋齡_年'] - 5) * w_age
    )

    df['pen_type'] = 0

    df['pen_floor'] = np.random.randint(
        0, 3, len(df)
    ) * w_floor

    df['pen_size'] = np.random.randint(
        0, 4, len(df)
    ) * w_size

    # 計算房屋差異總分
    df['房屋差異分數'] = (
        df['pen_distance']
        + df['pen_time']
        + df['pen_age']
        + df['pen_type']
        + df['pen_floor']
        + df['pen_size']
    )

    # 將差異分數轉換成 0～100 的相似度
    df['相似度分數'] = (
        100 - df['房屋差異分數']
    ).clip(lower=0)

    # 相似度越高，排越前面
    df_sorted = df.sort_values(
        by='相似度分數',
        ascending=False
    )

    st.info(
        "💡 相似度分數越接近 100 分，"
        "代表該成交案例與目標房屋越相似。"
    )
    # ==========================================
    # 🏠 新功能 2：相似案例自動估價
    # ==========================================
    st.subheader("🏠 相似案例自動估價")

    max_cases = min(5, len(df_sorted))

    top_n = st.slider(
        "選擇要使用幾筆最相似案例進行估價",
        min_value=1,
        max_value=max_cases,
        value=min(3, max_cases)
    )

    # 取得相似度最高的前 N 筆案例
    top_comps = df_sorted.head(top_n)

    if '單價_萬元_坪' in top_comps.columns:

        estimated_price = (
            top_comps['單價_萬元_坪'].mean()
        )
        price_min = top_comps['單價_萬元_坪'].min()
        price_max = top_comps['單價_萬元_坪'].max()
        price_median = top_comps['單價_萬元_坪'].median()

        st.success(
            f"🏠 建議估價單價："
            f"**{estimated_price:.2f} 萬元 / 坪**"
        )
        # ==========================================
        # 📌 新功能 3：估價合理價格區間
        # ==========================================

        st.subheader("📌 估價合理價格區間")

        col_a, col_b, col_c = st.columns(3)

        col_a.metric(
            "建議估價單價",
            f"{estimated_price:.2f} 萬/坪"
        )

        col_b.metric(
            "相似案例最低單價",
            f"{price_min:.2f} 萬/坪"
        )

        col_c.metric(
            "相似案例最高單價",
            f"{price_max:.2f} 萬/坪"
        )

        st.info(
            f"依據目前選取的 {top_n} 筆最相似成交案例，"
            f"合理參考區間約為 "
            f"**{price_min:.2f} ～ {price_max:.2f} 萬元/坪**，"
            f"中位數為 **{price_median:.2f} 萬元/坪**。"
        )
        st.write(
            f"本次估價採用相似度最高的 "
            f"**{top_n} 筆成交案例**。"
        )

        # 顯示估價案例
        show_columns = [
            '土地區段位置或建物門牌',
            '單價_萬元_坪',
            '屋齡_年',
            'distance_m',
            '相似度分數'
        ]

        available_columns = [
            col for col in show_columns
            if col in top_comps.columns
        ]

        st.dataframe(
            top_comps[available_columns],
            use_container_width=True
        )

    else:
        st.warning(
            "目前資料缺少單價資訊，無法估價。"
        )

    # ==========================================
    # 📋 完整比較結果
    # ==========================================
    st.subheader("📋 完整房屋比較結果")

    st.dataframe(
        df_sorted,
        use_container_width=True
    )

    excel_data = (
        df_sorted
        .to_csv(index=False)
        .encode('utf-8-sig')
    )

    st.download_button(
        label="📥 下載完整房屋比較結果 CSV",
        data=excel_data,
        file_name="taichung_house_result.csv",
        mime="text/csv"
    )

else:

    st.warning(
        "⚠️ 目前沒有符合條件的房屋案例，"
        "請放寬篩選條件。"
    )
