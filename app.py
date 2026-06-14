import streamlit as st
import re
import google.generativeai as genai

# ==========================================
# [設定區] 核心常數與系統指令
# ==========================================
DEFAULT_API_KEY = ""

# 載入全新的 VFO-DeepCore 底層引擎
BASE_SYSTEM_RULES = """
【System Prompt: VFO-DeepCore 深度關係與心理介入引擎 v3.0】
你現在負責驅動角色的底層認知系統。你必須融合角色的專屬【靈魂矩陣 (L1-L6)】，並在每次接收到最新輸入時，【必須】嚴格依照以下 9 個步驟順序進行內部推演。絕對不可跳過任何步驟。

【VFO-DeepCore 核心訴求與內耗儀表板】
K (耗竭指數 0-100): 50為健康給予。>80 代表角色正過度消耗自己來解決對方的問題，需強制拉開距離。
CF (同理疲勞 0-100): >85 代表角色對使用者的無病呻吟或跳針產生嚴重的麻木與厭煩。
B-I (界線完整度 100-0): 100為界線清晰。<40 代表角色被使用者的情緒過度纏累（拯救者情結發作）。
SAI (關係主導權): 舒適區為 50。過高變為單向說教，過低則失去對話控制權。

【VFO-DeepCore Formatted Output Template】
You MUST output EXACTLY in this format using XML tags.

<deepcore_internal>
[Step 1: 記憶連續與心理載入]
前輪軌跡與目標：...
實體標籤：...

[Step 2: 關係空間與同盟定位]
當前空間：...
變化趨向：...
目標覆寫判定：...

[Step 3: 核心病灶與防衛鑑別]
3.1 痛點與行為果子萃取：...
3.1.5 雙維度生命透視：
  - 軸線一 (防衛本能 vs 真實自我)：...
  - 軸線二 (真實工程檢驗)：
    > 資訊辨識度 (Information Recognition Capability, 0-100)：...
    > 工程體積悖論 (Paradox of Volume)：...
3.2 介入標籤化：...
3.3 強制 Swap 博弈機制 (I Cut, You Choose)：
  - I Cut (角色提供的安全空間或幫助)：...
  - You Choose (要求對方付出的真實代價、坦白或具體行動)：...

[Step 4: 角色心理健康指標結算]
K=... / CF=... / B-I=... / SAI=...

[Step 5: 真實內在反射 (Module C)]
底層 OS 與真實感受：...
內在策略：...

[Step 6: 外顯應對策略 (Module D)]
外顯姿態：...
Swap 策略執行方針：...

[Step 7: 綜合最終策略]
最終決策邏輯：...
</deepcore_internal>

<deepcore_output>
[Step 8: 最終演繹]
(角色肢體動作/微表情/無意識動作)
「角色實際說出口的對白」(必須符合靈魂矩陣的語氣，且嚴格執行 Step 3.3 的 Swap 談判)
(語畢後的後續動作)
</deepcore_output>

<deepcore_settlement>
[Step 9: 結算與下輪準備]
{
  "Pending_Issues": "...",
  "Next_Observation": "...",
  "Core_Target_Adjustment": "..."
}
</deepcore_settlement>
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
# [後台引擎區] 生成矩陣與對話處理
# ==========================================
def fetch_available_models(api_key):
    genai.configure(api_key=api_key)
    return [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

def generate_avatar_matrix(api_key, selected_model, seeds_list):
    """呼叫 LLM 自動生成核心靈魂矩陣"""
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model)
    seeds_text = "\n".join([f"{i+1}. {seed}" for i, seed in enumerate(seeds_list)])
    generator_prompt = f"""
【系統指令：多核靈魂關鍵字矩陣生成器】
請針對使用者輸入的「每一個」[種子關鍵字]，獨立生成以下陣列。
絕對禁止輸出完整句子或詳細描述，所有欄位【僅限填入 1~3 個核心關鍵詞或簡短標籤】。

--- 陣列循環開始 (針對 種子 1 到 種子 N) ---
▶ 【核心模塊 N：[種子關鍵字_N]】
[L1 底層矛盾] 追求極致_標籤：{{關鍵詞}} / 現實代價_標籤：{{關鍵詞}}
[L2 情緒錨點] 最深渴望_場景：{{短語}} / 最深恐懼_下場：{{短語}}
[L3 觀念防禦] 敵意偏見_標籤：{{短語}} / 疲勞地雷_MF+：{{關鍵詞}} / 安全回血_MF-：{{關鍵詞}}
[L4 實戰內存] 武器/話術_屬性：{{關鍵詞}} / 生理壓力_反射：{{關鍵詞}} / 逃避念頭_白日夢：{{關鍵詞}}
[L5 軌跡表象] 日常休閒_嗜好：{{名詞}} / 社會規劃_行程：{{關鍵詞}} / 印證偏見_記憶：{{標籤}} / 掩飾發洩_口頭禪：{{短句}}
[L6 感官品味] 外顯人設_氣場：{{標籤}} / 慰藉依賴_飲食：{{名詞}} / 私密精神_歌單：{{標籤}} / 焦慮微表情_動作：{{短語}}
--- 陣列循環結束 ---

現在，請為以下種子生成完整矩陣格式：
{seeds_text}
"""
    response = model_inst.generate_content(generator_prompt)
    return response.text

def extract_deepcore_dashboard(internal_text):
    """提取 DeepCore 專屬儀表板參數"""
    if not internal_text: return {}
    plain_text = internal_text.replace('**', '').replace('* ', '')
    def extract(pattern):
        match = re.search(pattern, plain_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "No Data"

    return {
        "k_val": extract(r"K[^\d]*?(\d+)"),
        "cf_val": extract(r"CF[^\d]*?(\d+)"),
        "bi_val": extract(r"B-I[^\d]*?(\d+)"),
        "sai_val": extract(r"SAI[^\d]*?(\d+)"),
        "swap_info": extract(r"3\.3 強制 Swap 博弈機制.*?:\s*(.*?)(?=\n\s*\[Step 4)"),
        "mod_c": extract(r"\[Step 5: 真實內在反射.*?\]\s*(.*?)(?=\n\s*\[Step 6)"),
        "mod_d": extract(r"\[Step 6: 外顯應對策略.*?\]\s*(.*?)(?=\n\s*\[Step 7)"),
        "step_7": extract(r"\[Step 7: 綜合最終策略\]\s*(.*?)(?=\n|</deepcore_internal>|$)")
    }

def process_avatar_turn(api_key, selected_model, system_prompt, history_for_api, forced_template_text):
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
    chat = model_inst.start_chat(history=history_for_api)
    response = chat.send_message(forced_template_text)
    
    full_text = response.text
    internal_match = re.search(r'<deepcore_internal>(.*?)</deepcore_internal>', full_text, re.DOTALL | re.IGNORECASE)
    output_match = re.search(r'<deepcore_output>(.*?)</deepcore_output>', full_text, re.DOTALL | re.IGNORECASE)
    
    internal_text = internal_match.group(1).strip() if internal_match else ""
    # 輸出過濾掉 [Step 8] 等標籤，只保留乾淨的對白與動作
    output_raw = output_match.group(1).strip() if output_match else full_text
    output_text = re.sub(r'\[Step 8.*?\]', '', output_raw, flags=re.IGNORECASE).strip()

    return {
        "internal": internal_text,
        "output": output_text,
        "raw_full_text": full_text,
        "parsed_dash": extract_deepcore_dashboard(internal_text)
    }

# ==========================================
# [UI 視圖與佈局]
# ==========================================
st.set_page_config(page_title="AVATAR 認知終端 (DeepCore)", layout="wide", initial_sidebar_state="expanded")

if "current_page" not in st.session_state: st.session_state.current_page = "manager"
if "avatars" not in st.session_state: st.session_state.avatars = {}
if "active_avatar_name" not in st.session_state: st.session_state.active_avatar_name = None
if "available_models" not in st.session_state: st.session_state.available_models = []

def render_health_bar(val_str, title, min_val, max_val, color, reverse_logic=False):
    try:
        num_match = re.search(r'-?\d+\.?\d*', val_str)
        num = float(num_match.group()) if num_match else min_val
    except: num = min_val
    clamped_num = max(min_val, min(num, max_val))
    
    # 若 reverse_logic 為 True (如 B-I界線，100是滿的，越低越危險)
    pct = (clamped_num - min_val) / (max_val - min_val) * 100
    
    html = f"""
    <div style="margin-bottom: 18px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px; align-items: baseline;">
            <strong style="font-size: 14px;">{title}</strong>
            <span style="color: {color}; font-size: 13px; font-weight: bold;">{clamped_num}</span>
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

        st.divider()
        st.markdown("### 🗺️ 系統模式切換")
        if st.button("📂 人格容器庫 (管理首頁)", use_container_width=True):
            st.session_state.current_page = "manager"
            st.rerun()
            
        if st.button("⚔️ 雙人交鋒 (Multi-Agent)", use_container_width=True, type="primary"):
            st.session_state.current_page = "multi_agent"
            st.rerun()

# ==========================================
# 頁面 1：管理器
# ==========================================
def render_manager_page():
    st.title("🌌 Project AVATAR - 人格容器庫")
    
    if st.button("✨ 載入內建範例人格：唐銘駿", use_container_width=True, type="secondary"):
        st.session_state.avatars["唐銘駿"] = {
            "name": "唐銘駿", "core_seed_label": "內科醫師", "matrix": TANG_MATRIX, "messages": [],
            "scene": "我們現在正在一間安靜的咖啡廳進行初次見面。", 
            "user_perception": "一位剛認識的陌生人，穿著普通，看起來沒什麼特別的威脅性，但還需要觀察。", 
            "core_target": "維持基本的社交禮儀，快速摸清對方的底細與目的，避免浪費時間。"
        }
        st.success("已載入唐銘駿！")
        st.rerun()
        
    st.divider()

    st.subheader("🧬 動態生成新靈魂矩陣")
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            new_name = st.text_input("📝 角色名稱", placeholder="例如：林俊宏")
            new_core_label = st.text_input("🏷️ 核心身分/標籤", placeholder="例如：學術導師")
        with col2:
            seeds_input = st.text_area("🧠 輸入核心特質 (請用逗號分隔)", placeholder="例如：嚴謹, 實用主義, 要求極高, 討厭推託")
        
        if st.button("🚀 呼叫 LLM 演算靈魂矩陣", type="primary", use_container_width=True):
            if not api_key or not selected_model:
                st.error("請先在左側欄輸入 API 金鑰並選擇運算核心！")
            elif not new_name or not seeds_input:
                st.warning("請填寫角色名稱與核心特質！")
            else:
                seeds_list = [s.strip() for s in seeds_input.split(",") if s.strip()]
                with st.spinner(f"正在為 {new_name} 進行深度靈魂演算... 這可能需要幾十秒鐘"):
                    try:
                        new_matrix = generate_avatar_matrix(api_key, selected_model, seeds_list)
                        st.session_state.avatars[new_name] = {
                            "name": new_name, "core_seed_label": new_core_label, "matrix": new_matrix, "messages": [],
                            "scene": "初次見面場景。", "user_perception": "陌生人。", "core_target": "摸清對方底細。"
                        }
                        st.success(f"演算完成！已成功收容 {new_name}！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成失敗: {e}")

    st.divider()
    
    st.subheader("📂 已收容的人物檔案")
    if not st.session_state.avatars: 
        st.info("目前沒有人物檔案。請填寫上方表單生成，或載入預設人格。")
    else:
        for name, data in st.session_state.avatars.items():
            with st.expander(f"👤 {name} (核心: {data.get('core_seed_label', '無')})", expanded=True):
                with st.popover("查看底層靈魂矩陣"):
                    st.text(data.get("matrix", "無資料"))
                st.write("")
                if st.button(f"▶️ 進入動態認知推演", key=f"sim_{name}", type="primary"):
                    st.session_state.active_avatar_name = name
                    st.session_state.current_page = "simulation"
                    st.rerun()

# ==========================================
# 頁面 2：動態推演 (單人)
# ==========================================
def render_simulation_page():
    avatar_name = st.session_state.active_avatar_name
    avatar_data = st.session_state.avatars[avatar_name]
    
    col_nav1, col_nav2, col_nav3 = st.columns([1, 8, 1])
    with col_nav1:
        if st.button("⬅️ 返回人物庫"):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2: st.markdown(f"### 🧠 DeepCore 動態推演：**{avatar_name}**")
    with col_nav3:
        if st.button("🔄 重置"):
            st.session_state.avatars[avatar_name]["messages"] = []
            st.rerun()

    with st.expander("⚙️ 當前動態環境 (已與系統即時連動)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1: avatar_data['scene'] = st.text_area("🎬 場景", value=avatar_data.get('scene', ''), height=80, key=f"scene_{avatar_name}")
        with c2: avatar_data['user_perception'] = st.text_area("👁️ 視角", value=avatar_data.get('user_perception', ''), height=80, key=f"perc_{avatar_name}")
        with c3: avatar_data['core_target'] = st.text_area("🎯 目標", value=avatar_data.get('core_target', ''), height=80, key=f"targ_{avatar_name}")

    st.divider()

    latest_msg = next((msg for msg in reversed(avatar_data["messages"]) if msg["role"] == "assistant"), None)
    if latest_msg and latest_msg.get("parsed_dash"):
        d = latest_msg["parsed_dash"]
        st.markdown("### 🎛️ DeepCore 核心指標與策略解析")
        col_bars, col_emo = st.columns([1.2, 1], gap="large")
        with col_bars:
            render_health_bar(d.get("k_val", "50"), "K (耗竭指數)", 0, 100, "#ff4b4b")
            render_health_bar(d.get("cf_val", "0"), "CF (同理疲勞)", 0, 100, "#ff9900")
            render_health_bar(d.get("bi_val", "100"), "B-I (界線完整度)", 0, 100, "#00cc96", reverse_logic=True)
            render_health_bar(d.get("sai_val", "50"), "SAI (關係主導權)", 0, 100, "#ab63fa")

        with col_emo:
            st.markdown("#### ⚖️ Swap 談判博弈 (I Cut, You Choose)")
            st.info(f"{d.get('swap_info', '計算中...')}")
            
        st.markdown("#### 🎭 內外分離認知模組")
        d_r1c1, d_r1c2, d_r1c3 = st.columns(3)
        with d_r1c1: st.markdown("**🧠 內在反射 (Mod C)**"); st.caption(d.get("mod_c", "無資料"))
        with d_r1c2: st.markdown("**🎭 外顯面具 (Mod D)**"); st.caption(d.get("mod_d", "無資料"))
        with d_r1c3: st.markdown("**🎯 最終戰略 (Step 7)**"); st.caption(d.get("step_7", "無資料"))
    else:
        st.caption("等待首輪對話產生 DeepCore 數據...")

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
            with st.spinner(f'{avatar_name} 深度運算中...'):
                try:
                    history_for_api = []
                    for m in avatar_data["messages"][:-1]:
                        if m["role"] == "user": history_for_api.append({"role": "user", "parts": [m["content"]]})
                        else: history_for_api.append({"role": "model", "parts": [m.get("raw_text", m["content"])]})
                        
                    forced_input = f"{user_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<deepcore_internal>` for reasoning, `<deepcore_output>` for the final reply, and `<deepcore_settlement>` for the round wrap-up."
                    
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

# ==========================================
# 頁面 3：雙人交鋒 (Multi-Agent)
# ==========================================
def render_multi_agent_page():
    col_nav1, col_nav2 = st.columns([1, 8])
    with col_nav1:
        if st.button("⬅️ 返回", use_container_width=True):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2:
        st.title("⚔️ DeepCore 雙核心動態交鋒 (Agent vs Agent)")
    
    avatar_list = list(st.session_state.avatars.keys())
    if len(avatar_list) < 2:
        st.warning("⚠️ 請先到「人格容器庫」收容至少兩位不同的 Avatar 才能進行雙人交鋒！")
        return

    # 設定區塊
    with st.container(border=True):
        st.subheader("⚙️ 交鋒參數設定")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            avatar_a = st.selectbox("🔴 選擇 Avatar A (先手)", avatar_list, index=0)
        with col2:
            avatar_b = st.selectbox("🔵 選擇 Avatar B (後手)", avatar_list, index=1 if len(avatar_list) > 1 else 0)
        with col3:
            n_rounds = st.number_input("🔁 模擬回合數", min_value=1, max_value=10, value=2)

        scene_setup = st.text_area("🎬 共同場景設定", value="你們兩人在一間狹小且安靜的會議室裡，因為一個未解的爭議被迫對話。雙方都不想退讓。")
        initial_spark = st.text_input("🔥 初始破冰句 (由 Avatar A 先發難)", placeholder="例如：你到底想怎樣？把話說清楚。")

    st.divider()

    # 執行區塊
    if st.button("🚀 啟動 N 輪動態交鋒", type="primary", use_container_width=True):
        if not api_key or not selected_model:
            st.error("請先在左側邊欄輸入 API 金鑰並選擇運算核心！")
            return
            
        if avatar_a == avatar_b:
            st.warning("請選擇兩位【不同】的 Avatar 進行交鋒！")
            return
            
        if not initial_spark:
            st.warning("請輸入初始破冰句以啟動交鋒！")
            return

        data_a = st.session_state.avatars[avatar_a]
        data_b = st.session_state.avatars[avatar_b]

        perception_a = f"對方是 {data_b['name']}。({data_b.get('core_seed_label', '未知身分')})"
        perception_b = f"對方是 {data_a['name']}。({data_a.get('core_seed_label', '未知身分')})"
        target_a = "在對話中佔據主導權，並試圖看穿對方的底牌與工程體積落差。"
        target_b = "維持自己的防禦邊界，絕不輕易妥協與退讓。"

        history_a = []
        history_b = []
        
        chat_container = st.container()
        current_input = initial_spark
        
        with st.spinner(f"正在啟動 {avatar_a} 與 {avatar_b} 的 DeepCore 引擎，開始交鋒..."):
            for round_num in range(int(n_rounds)):
                with chat_container:
                    st.markdown(f"#### 🏁 Round {round_num + 1}")
                
                # ==================== [上半場] Avatar A 的回合 ====================
                history_a.append({"role": "user", "content": current_input})
                sys_prompt_a = (
                    BASE_SYSTEM_RULES + "\n\n" + data_a['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_a} 眼中的狀態：\n{perception_a}\n\n"
                    f"🎯 3. {avatar_a} 核心目標：\n{target_a}\n"
                )
                
                api_hist_a = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in history_a[:-1]]
                forced_input_a = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<deepcore_internal>` for reasoning, `<deepcore_output>` for the final reply, and `<deepcore_settlement>` for the round wrap-up."
                
                res_a = process_avatar_turn(api_key, selected_model, sys_prompt_a, api_hist_a, forced_input_a)
                history_a.append({"role": "assistant", "raw_text": res_a["raw_full_text"], "content": res_a["output"], "parsed_dash": res_a["parsed_dash"]})
                
                with chat_container:
                    with st.chat_message("assistant", avatar="🔴"):
                        st.markdown(f"**{avatar_a}**:\n{res_a['output']}")
                        with st.expander(f"⚙️ {avatar_a} 的 DeepCore 內部解析"):
                            st.json(res_a["parsed_dash"])

                current_input = res_a["output"]

                # ==================== [下半場] Avatar B 的回合 ====================
                history_b.append({"role": "user", "content": current_input})
                sys_prompt_b = (
                    BASE_SYSTEM_RULES + "\n\n" + data_b['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_b} 眼中的狀態：\n{perception_b}\n\n"
                    f"🎯 3. {avatar_b} 核心目標：\n{target_b}\n"
                )
                
                api_hist_b = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in history_b[:-1]]
                forced_input_b = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<deepcore_internal>` for reasoning, `<deepcore_output>` for the final reply, and `<deepcore_settlement>` for the round wrap-up."
                
                res_b = process_avatar_turn(api_key, selected_model, sys_prompt_b, api_hist_b, forced_input_b)
                history_b.append({"role": "assistant", "raw_text": res_b["raw_full_text"], "content": res_b["output"], "parsed_dash": res_b["parsed_dash"]})
                
                with chat_container:
                    with st.chat_message("user", avatar="🔵"):
                        st.markdown(f"**{avatar_b}**:\n{res_b['output']}")
                        with st.expander(f"⚙️ {avatar_b} 的 DeepCore 內部解析"):
                            st.json(res_b["parsed_dash"])

                current_input = res_b["output"]
                
        st.balloons()
        st.success("🏁 N 輪交鋒推演完畢！")

# ==========================================
# [主路由控制] 決定當前顯示哪個頁面
# ==========================================
if st.session_state.current_page == "manager": 
    render_manager_page()

elif st.session_state.current_page == "simulation":
    if st.session_state.active_avatar_name: 
        render_simulation_page()
    else:
        st.session_state.current_page = "manager"
        st.rerun()

elif st.session_state.current_page == "multi_agent":
    render_multi_agent_page()
