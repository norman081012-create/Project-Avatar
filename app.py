import streamlit as st
import re
import google.generativeai as genai
import avatar_engine
import avatar_presets

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
    
    # [1] 預設角色載入區塊 (改由 avatar_presets 取出)
    if st.button("✨ 載入內建範例人格：唐銘駿", use_container_width=True, type="primary"):
        preset_tang = avatar_presets.PRESETS.get("唐銘駿")
        if preset_tang:
            st.session_state.avatars["唐銘駿"] = preset_tang.copy()
            st.success("已載入唐銘駿！")
            st.rerun()
        else:
            st.error("找不到預設角色檔案！")
            
    st.divider()
    
    # [2] 動態矩陣生成區塊 (全新接回)
    st.subheader("🧬 動態生成新靈魂矩陣")
    with st.container(border=True):
        col_gen1, col_gen2 = st.columns([1, 2])
        with col_gen1:
            new_name = st.text_input("角色名稱", placeholder="例如：林俊宏")
            new_core_label = st.text_input("核心身分/標籤", placeholder="例如：學術導師")
        with col_gen2:
            seeds_input = st.text_area("輸入核心特質 (請用逗號分隔)", placeholder="例如：嚴謹, 實用主義, 學術派, 要求極高, 討厭推託")
        
        if st.button("🚀 呼叫 LLM 演算靈魂矩陣", type="secondary"):
            if not api_key or not selected_model:
                st.error("請先在左側欄輸入 API 金鑰並選擇運算核心！")
            elif not new_name or not seeds_input:
                st.warning("請填寫角色名稱與核心特質！")
            else:
                seeds_list = [s.strip() for s in seeds_input.split(",") if s.strip()]
                with st.spinner(f"正在為 {new_name} 進行深度靈魂演算... 這可能需要幾十秒鐘"):
                    try:
                        # 呼叫你寫好的 engine 生成矩陣
                        new_matrix = avatar_engine.generate_avatar_matrix(api_key, selected_model, seeds_list)
                        
                        st.session_state.avatars[new_name] = {
                            "name": new_name, 
                            "first_seed": seeds_list[0] if seeds_list else "未知", 
                            "core_seed_label": new_core_label,
                            "matrix": new_matrix, 
                            "messages": [], 
                            "is_initialized": False,
                            "scene": "我們現在正在一間安靜的咖啡廳進行初次見面。", 
                            "user_perception": "一位剛認識的陌生人，穿著普通，看起來沒什麼特別的威脅性，但還需要觀察。", 
                            "core_target": "維持基本的社交禮儀，快速摸清對方的底細與目的，避免浪費時間。"
                        }
                        st.success(f"演算完成！已成功收容 {new_name}！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成失敗: {e}")

    st.divider()
    
    # [3] 已收容檔案清單
    st.subheader("📂 已收容的人物檔案")
    if not st.session_state.avatars: 
        st.info("目前沒有人物檔案。請點擊上方按鈕載入或生成。")
    else:
        for name, data in st.session_state.avatars.items():
            with st.expander(f"👤 {name} (核心: {data.get('core_seed_label', '無')})", expanded=True):
                # 加入彈出視窗讓你可以查看剛生成的矩陣
                with st.popover("查看底層靈魂矩陣"):
                    st.text(data.get("matrix", "無資料"))
                
                st.write("") # 小排版空間
                
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
