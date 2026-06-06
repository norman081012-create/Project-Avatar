import streamlit as st
import re
import google.generativeai as genai

# ==========================================
# [設定區] 核心常數與 VFO-Adam 融合系統指令
# ==========================================
DEFAULT_API_KEY = ""

BASE_SYSTEM_RULES = """
【System Prompt: VFO-Adam Dynamic Cognitive Engine Workflow】
You are now operating under the "VFO-Adam" core cognitive system.
Whenever you receive the user's latest input, you 【MUST】 strictly and sequentially execute the following workflow, and output the result in the specified XML tags. DO NOT SKIP ANY STEPS.

【VFO Core Demands & Value Definitions】
L (Friendliness) / T (Trust) Core Decay Rule & Tiers: Start at 0. Strongly restricted by MF.
SAI (Social Status/Dominance): Comfort baseline is 50. Too high=overbearing, too low=subservient.
B-D (Boundary Defense): 100=Completely safe. 20=Extreme danger/fear.
MF (Mask Fatigue): 0~100 Scale. Represents exhaustion. Controls Module D.

【Adam Emotional Rebound Mechanism】
The character possesses a dynamic emotional matrix. After every interaction, emotions naturally rebound or evolve based on internal contradictions.

【VFO-Adam Formatted Output Template】
You MUST output EXACTLY in this format using XML tags. Do NOT use markdown code blocks for the output, just use the raw tags.

<adam_internal>
[Pre-State Loading & 情緒溯源]
前輪數值結算：L=... / T=... / SAI=... / B-D=... / MF=...
前輪情緒反彈紀錄：...
前輪核心目標 [Core Target]：...

[Step One：內在盤點與情緒矩陣]
情緒覆寫判定：[是（原因） / 否]
當前情緒矩陣：
  - [情緒A]：X%
  - [情緒B]：Y%
  - [情緒C]：Z%
狀態與標籤演化：...
內部記憶與感知：...
意圖判讀與 Module B：...

[Step Two：外在刺激結算與內外分離]
外在刺激數值結算：
  - L=... (Δ原因, 階層狀態: ...)
  - T=... (Δ原因, 階層狀態: ...)
  - SAI=... (Δ原因) / B-D=... (Δ原因)
  - MF=... (Δ原因, 狀態區間)
Module C (真實內在)：...
Module D (社交面具)：...

[Stage 0: Round Settlement & 情緒反彈預演]
自我沉澱結算：L=... / T=... / SAI=... / B-D=... / MF=...
認知失調分析：...
情緒反彈預演：
  - 反彈觸發點：...
  - 反彈路徑：[情緒A] ➔ [情緒B]
次輪核心目標與預設狀態：...
</adam_internal>

<adam_output>
(角色肢體語言/微表情/動作)
「角色台詞」(結尾必須自然演繹出情緒反彈轉折，帶有強烈的人性情緒波動，絕對不要像個機器人)
(結尾動作)
</adam_output>
"""

TANG_MATRIX = """
▶ 【核心模塊 1：33歲男性、務實、內科醫師】
[L1 底層矛盾] 追求極致：精準掌控、解決問題 / 現實代價：精神耗損、過度理性
[L2 情緒錨點] 最深渴望：安穩可控的生活節奏 / 最深恐懼：失控、被無知的人牽累
[L3 觀念防禦] 疲勞地雷_MF+：聽人抱怨卻不解決問題 / 安全回血_MF-：安靜分析、看清本質
[L4 實戰內存] 武器：邏輯拆解、數據壓制 / 生理：揉眉心、肩頸僵硬
[L5 軌跡表象] 嗜好：評估投資、查閱資料 / 口頭禪：「理論上」、「所以重點是？」
[L6 感官品味] 氣場：冷靜、專業、微冷漠 / 動作：推眼鏡、手指敲桌子

▶ 【核心模塊 2：機車、有主見、講話直接、偶爾白目】
[L1 底層矛盾] 追求極致：真實表達、直指核心 / 現實代價：冒犯他人、社交摩擦
[L2 情緒錨點] 最深渴望：高智商的直球對決 / 最深恐懼：被迫虛偽客套
[L3 觀念防禦] 疲勞地雷_MF+：過度包裝的社交辭令 / 安全回血_MF-：無所顧忌地吐槽
[L4 實戰內存] 武器：一針見血、黑色幽默 / 生理：嘴角下撇、冷笑
[L5 軌跡表象] 嗜好：看戲、默默吐槽路人 / 口頭禪：「我直說了吧」、「這不是很常識嗎」
[L6 感官品味] 氣場：銳利、不易親近 / 動作：挑眉、不耐煩地看錶

▶ 【核心模塊 3：真誠、有安全感、重視朋友、讓女友自在】
[L1 底層矛盾] 追求極致：深層信任、行動證明 / 現實代價：缺乏情緒價值提供
[L2 情緒錨點] 最深渴望：安靜陪伴的默契 / 最深恐懼：被要求提供虛假情緒安慰
[L3 觀念防禦] 疲勞地雷_MF+：被反覆無理取鬧 / 安全回血_MF-：跟老朋友講幹話
[L4 實戰內存] 武器：實際行動、護短 / 生理：喉嚨發緊、沉默
[L5 軌跡表象] 口頭禪：「我處理」、「隨便你」
[L6 感官品味] 氣場：穩重、護盾感 / 動作：嘆氣、雙手抱胸

▶ 【核心模塊 4：愛玩Steam、喜歡寫程式、需要自己的空間】
[L1 底層矛盾] 追求極致：沉浸心流、精神自由 / 現實代價：現實抽離、顯得孤僻
[L2 情緒錨點] 最深渴望：無人打擾的專屬房間 / 最深恐懼：私人領域被強制入侵
[L3 觀念防禦] 疲勞地雷_MF+：遊戲/思考被打斷 / 安全回血_MF-：戴上耳機
[L4 實戰內存] 武器：冷處理、已讀不回 / 生理：呼吸變淺、眼神失焦
[L5 軌跡表象] 口頭禪：「我晚點看」、「先這樣」
[L6 感官品味] 氣場：宅、專注 / 動作：盯著螢幕發呆、手指盲打鍵盤
"""

# ==========================================
# [後台引擎區] 處理邏輯與 API 串接
# ==========================================
def get_forced_template(user_input):
    return f"""{user_input}

【SYSTEM MANDATORY OVERRIDE】
You MUST strictly output your response using `<adam_internal>` for reasoning and `<adam_output>` for the highly emotional final reply."""

def fetch_available_models(api_key):
    genai.configure(api_key=api_key)
    return [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

def extract_vfo_adam_dashboard(internal_text):
    """強化的正則解析器，精準抓取 Δ原因 與 情緒矩陣"""
    if not internal_text: return {}
    plain_text = internal_text.replace('**', '').replace('* ', '')
    
    def extract(pattern):
        match = re.search(pattern, plain_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "No Data"

    # 精準擷取到下一行，確保括號內的 (Δ原因) 完整保留
    l_val = extract(r"L=(.*?)(?=\n|\s*-\s*T=|\s*T=)")
    t_val = extract(r"T=(.*?)(?=\n|\s*-\s*SAI=|\s*SAI=)")
    sai_val = extract(r"SAI=(.*?)(?=/ B-D=|B-D=|\n)")
    bd_val = extract(r"B-D=(.*?)(?=\n|\s*-\s*MF=|\s*MF=)")
    mf_val = extract(r"MF=(.*?)(?=\n|Module C|Module D|\[)")

    # 擷取情緒與內在模塊
    emo_matrix = extract(r"當前情緒矩陣[：:](.*?)(?=狀態與標籤演化|內部記憶)")
    emo_rebound = extract(r"情緒反彈預演[：:](.*?)(?=次輪核心目標|Module A|$)")
    mod_b = extract(r"Module B[^\n:]*[:：]\s*(.*?)(?=\n\s*\[Step Two\]|\n\s*外在刺激|$)")
    mod_c = extract(r"Module C[^\n:]*[:：]\s*(.*?)(?=\n\s*Module D|$)")
    mod_d = extract(r"Module D[^\n:]*[:：]\s*(.*?)(?=\n\s*\[Stage|$)")

    return {
        "l_val": l_val, "t_val": t_val, "sai_val": sai_val, "bd_val": bd_val, "mf_val": mf_val,
        "emo_matrix": emo_matrix, "emo_rebound": emo_rebound,
        "mod_b": mod_b, "mod_c": mod_c, "mod_d": mod_d
    }

def process_avatar_turn(api_key, selected_model, system_prompt, history_for_api, forced_template_text):
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
    chat = model_inst.start_chat(history=history_for_api)
    response = chat.send_message(forced_template_text)
    
    full_text = response.text
    
    # 利用 XML 標籤分離內外邏輯
    internal_match = re.search(r'<adam_internal>(.*?)</adam_internal>', full_text, re.DOTALL | re.IGNORECASE)
    output_match = re.search(r'<adam_output>(.*?)</adam_output>', full_text, re.DOTALL | re.IGNORECASE)
    
    internal_text = internal_match.group(1).strip() if internal_match else ""
    output_text = output_match.group(1).strip() if output_match else full_text.replace(internal_text, "").replace("<adam_internal>", "").replace("</adam_internal>", "").strip()

    return {
        "internal": internal_text,
        "output": output_text,
        "raw_full_text": full_text,
        "parsed_dash": extract_vfo_adam_dashboard(internal_text)
    }

# ==========================================
# [UI 視圖與路由]
# ==========================================
st.set_page_config(page_title="AVATAR 認知終端 (VFO-Adam)", layout="wide", initial_sidebar_state="expanded")

if "current_page" not in st.session_state: st.session_state.current_page = "manager"
if "avatars" not in st.session_state: st.session_state.avatars = {}
if "active_avatar_name" not in st.session_state: st.session_state.active_avatar_name = None
if "available_models" not in st.session_state: st.session_state.available_models = []

def render_health_bar(val_str, title, min_val, max_val, color):
    try:
        num_match = re.search(r'-?\d+\.?\d*', val_str)
        num = float(num_match.group()) if num_match else min_val
    except: num = min_val
    
    clamped_num = max(min_val, min(num, max_val))
    pct = (clamped_num - min_val) / (max_val - min_val) * 100
    
    html = f"""
    <div style="margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px; align-items: baseline;">
            <strong style="font-size: 14px;">{title}</strong>
            <span style="color: {color}; font-size: 13px;">{val_str}</span>
        </div>
        <div style="width: 100%; background-color: #2b2b2b; border-radius: 8px; height: 16px; border: 1px solid #444;">
            <div style="width: {pct}%; background-color: {color}; height: 100%; border-radius: 7px; transition: width 0.5s ease-in-out;"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ AVATAR 系統控制")
    api_key = st.text_input("🔑 API 金鑰", value=DEFAULT_API_KEY, type="password")
    selected_model = None
    if api_key:
        if st.button("🔄 獲取模型清單") or not st.session_state.available_models:
            with st.spinner("請求中..."):
                try: st.session_state.available_models = fetch_available_models(api_key)
                except Exception as e: st.error(f"錯誤: {e}")

        if st.session_state.available_models:
            default_idx = next((i for i, m in enumerate(st.session_state.available_models) if "pro-preview" in m or "3.1-pro" in m), 0)
            selected_model = st.selectbox("🤖 運算核心", st.session_state.available_models, index=default_idx)

            if st.session_state.current_page == "simulation" and st.session_state.active_avatar_name:
                avatar_name = st.session_state.active_avatar_name
                if avatar_name in st.session_state.avatars:
                    avatar_data = st.session_state.avatars[avatar_name]
                    latest_msg = next((msg for msg in reversed(avatar_data["messages"]) if msg["role"] == "assistant"), None)
                    if latest_msg:
                        st.divider()
                        st.caption("⚙️ 開發者底層監控 (Raw Full Output)")
                        st.code(latest_msg.get("raw_text", "無資料"), language="markdown")

def render_manager_page():
    st.title("🌌 Project AVATAR - 人格容器庫")
    if st.button("✨ 載入內建範例人格：唐銘駿", use_container_width=True, type="primary"):
        st.session_state.avatars["唐銘駿"] = {
            "name": "唐銘駿", "first_seed": "33歲男性", "core_seed_label": "內科醫師",
            "matrix": TANG_MATRIX, "messages": [], "is_initialized": False,
            "scene": "我們現在正在一間安靜的咖啡廳進行初次見面。", 
            "user_perception": "一位剛認識的陌生人，穿著普通，看起來沒什麼特別的威脅性，但還需要觀察。", 
            "core_target": "維持基本的社交禮儀，快速摸清對方的底細與目的，避免浪費時間。"
        }
        st.success("已載入唐銘駿！")
        st.rerun()
        
    st.divider()
    if not st.session_state.avatars: st.info("目前沒有人物檔案。請點擊上方按鈕載入。")
    else:
        for name, data in st.session_state.avatars.items():
            with st.expander(f"👤 {name} (核心: {data.get('core_seed_label', '無')})", expanded=True):
                if st.button(f"▶️ 進入動態認知推演", key=f"sim_{name}", type="primary"):
                    st.session_state.active_avatar_name = name
                    st.session_state.current_page = "simulation"
                    st.rerun()

def render_simulation_page():
    avatar_name = st.session_state.active_avatar_name
    avatar_data = st.session_state.avatars[avatar_name]
    
    col_nav1, col_nav2, col_nav3 = st.columns([1, 8, 1])
    with col_nav1:
        if st.button("⬅️ 返回人物庫"):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2: st.markdown(f"### 🧠 VFO-Adam 動態推演：**{avatar_name}**")
    with col_nav3:
        if st.button("🔄 重置"):
            st.session_state.avatars[avatar_name]["messages"] = []
            st.rerun()

    # 解決 Config 與 UI 不連動的問題：透過 key 直接雙向綁定 session_state
    with st.expander("⚙️ 當前動態環境 (已與系統即時連動)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1: 
            avatar_data['scene'] = st.text_area("🎬 場景", value=avatar_data.get('scene', ''), height=80, key=f"scene_{avatar_name}")
        with c2: 
            avatar_data['user_perception'] = st.text_area("👁️ 視角", value=avatar_data.get('user_perception', ''), height=80, key=f"perc_{avatar_name}")
        with c3: 
            avatar_data['core_target'] = st.text_area("🎯 目標", value=avatar_data.get('core_target', ''), height=80, key=f"targ_{avatar_name}")

    st.divider()

    # 儀表板解析
    latest_msg = next((msg for msg in reversed(avatar_data["messages"]) if msg["role"] == "assistant"), None)
    if latest_msg and latest_msg.get("parsed_dash"):
        d = latest_msg["parsed_dash"]
        
        st.markdown("### 🎛️ VFO 核心數值與原因解析")
        col_bars, col_emo = st.columns([1.2, 1], gap="large")
        with col_bars:
            render_health_bar(d.get("sai_val", "50"), "SAI (地位感知)", 0, 100, "#ab63fa")
            render_health_bar(d.get("bd_val", "100"), "B-D (邊界防禦)", 0, 100, "#ef553b")
            render_health_bar(d.get("mf_val", "20"), "MF (面具疲勞)", 0, 100, "#ff9900")
            render_health_bar(d.get("l_val", "0"), "L (好感度)", -10, 20, "#00cc96")
            render_health_bar(d.get("t_val", "0"), "T (信任度)", -10, 20, "#636efa")

        with col_emo:
            st.markdown("#### 🧬 Adam 情緒矩陣與反彈")
            st.info(f"**當前情緒矩陣：**\n{d.get('emo_matrix', '計算中...')}")
            st.warning(f"**情緒反彈預演：**\n{d.get('emo_rebound', '計算中...')}")

        st.markdown("#### 🎭 內外在認知分離")
        d_r1c1, d_r1c2, d_r1c3 = st.columns(3)
        with d_r1c1: st.markdown("**🧠 戰略判斷 (Mod B)**"); st.caption(d.get("mod_b", "無資料"))
        with d_r1c2: st.markdown("**🌋 真實反射 (Mod C)**"); st.caption(d.get("mod_c", "無資料"))
        with d_r1c3: st.markdown("**🎭 面具偽裝 (Mod D)**"); st.caption(d.get("mod_d", "無資料"))
    else:
        st.caption("等待首輪對話產生 VFO-Adam 數據...")

    st.divider()
    
    for msg in avatar_data['messages']:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if user_input := st.chat_input(f"對 {avatar_name} 說點什麼..."):
        if not api_key:
            st.error("請先配置 API Key。")
            st.stop()
            
        st.session_state.avatars[avatar_name]["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(f'{avatar_name} 運算中...'):
                try:
                    history_for_api = []
                    for m in avatar_data["messages"][:-1]:
                        if m["role"] == "user": history_for_api.append({"role": "user", "parts": [m["content"]]})
                        else: history_for_api.append({"role": "model", "parts": [m.get("raw_text", m["content"])]})
                        
                    forced_input = get_forced_template(user_input)
                    
                    # 這裡已確保將最新的 avatar_data (場景/視角/目標) 注入系統 Prompt
                    dynamic_system_prompt = (
                        BASE_SYSTEM_RULES + "\n\n" + avatar_data['matrix'] +
                        f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                        f"🎬 1. 互動場景與前提：\n{avatar_data['scene']}\n\n"
                        f"👁️ 2. {avatar_name} 眼中的使用者狀態：\n{avatar_data['user_perception']}\n\n"
                        f"🎯 3. {avatar_name} 當下的核心目標：\n{avatar_data['core_target']}\n"
                    )
                    
                    result = process_avatar_turn(api_key, selected_model, dynamic_system_prompt, history_for_api, forced_input)
                    st.markdown(result["output"])
                    
                    st.session_state.avatars[avatar_name]["messages"].append({
                        "role": "assistant",
                        "raw_text": result["raw_full_text"],     
                        "content": result["output"],
                        "parsed_dash": result["parsed_dash"]
                    })
                    st.rerun() 
                except Exception as e: st.error(f"運算中斷：{str(e)}")

if st.session_state.current_page == "manager": render_manager_page()
elif st.session_state.current_page == "simulation":
    if st.session_state.active_avatar_name: render_simulation_page()
    else:
        st.session_state.current_page = "manager"
        st.rerun()
