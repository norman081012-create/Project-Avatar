# multiagent.py
import streamlit as st

def render_multi_agent_page(api_key, selected_model, base_system_rules, process_avatar_turn_func):
    col_nav1, col_nav2 = st.columns([1, 8])
    with col_nav1:
        if st.button("⬅️ 返回", use_container_width=True):
            st.session_state.current_page = "manager"
            st.rerun()
    with col_nav2:
        st.title("⚔️ VFO 雙核心動態交鋒 (Agent vs Agent)")
    
    avatar_list = list(st.session_state.avatars.keys())
    
    # 檢查是否有足夠的 Avatar
    if len(avatar_list) < 2:
        st.warning("⚠️ 請先到「人格容器庫」收容至少兩位不同的 Avatar 才能進行雙人交鋒！")
        return

    # 1. 設定區塊
    with st.container(border=True):
        st.subheader("⚙️ 交鋒參數設定")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            avatar_a = st.selectbox("🔴 選擇 Avatar A (先手)", avatar_list, index=0)
        with col2:
            # 預設選取清單中的第二個
            avatar_b = st.selectbox("🔵 選擇 Avatar B (後手)", avatar_list, index=1 if len(avatar_list) > 1 else 0)
        with col3:
            n_rounds = st.number_input("🔁 模擬回合數", min_value=1, max_value=10, value=3)

        scene_setup = st.text_area("🎬 共同場景設定", value="你們兩人在一間狹小且安靜的會議室裡，因為一個未解的爭議被迫對話。雙方都不想退讓。")
        initial_spark = st.text_input("🔥 初始對話/破冰句 (由 Avatar A 先發難)", placeholder="例如：你到底想怎樣？把話說清楚。")

    st.divider()

    # 2. 執行區塊
    if st.button("🚀 啟動 N 輪動態交鋒", type="primary", use_container_width=True):
        if not api_key or not selected_model:
            st.error("請先在左側邊欄輸入 API 金鑰並選擇運算核心！")
            return
            
        if avatar_a == avatar_b:
            st.warning("請選擇兩位【不同】的 Avatar 進行交鋒！")
            return

        data_a = st.session_state.avatars[avatar_a]
        data_b = st.session_state.avatars[avatar_b]

        # 視角交叉綁定 (A 眼中的 B, B 眼中的 A)
        perception_a = f"對方是 {data_b['name']}。({data_b.get('core_seed_label', '未知身分')})"
        perception_b = f"對方是 {data_a['name']}。({data_a.get('core_seed_label', '未知身分')})"
        
        target_a = "在對話中佔據主導權，並試圖看穿對方的底牌。"
        target_b = "維持自己的防禦邊界，不輕易妥協與退讓。"

        # 建立專屬的暫存對話紀錄 (不影響一般單人對話的歷史)
        history_a = []
        history_b = []
        
        chat_container = st.container()
        current_input = initial_spark
        
        # 3. 自動推演迴圈
        with st.spinner(f"正在啟動 {avatar_a} 與 {avatar_b} 的 VFO 引擎，開始交鋒..."):
            for round_num in range(n_rounds):
                with chat_container:
                    st.markdown(f"#### 🏁 Round {round_num + 1}")
                
                # ==========================================
                # [上半場] Avatar A 的回合
                # ==========================================
                history_a.append({"role": "user", "content": current_input})
                sys_prompt_a = (
                    base_system_rules + "\n\n" + data_a['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_a} 眼中的使用者狀態：\n{perception_a}\n\n"
                    f"🎯 3. {avatar_a} 當下的核心目標：\n{target_a}\n"
                )
                
                api_hist_a = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in history_a[:-1]]
                forced_input_a = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<adam_internal>` for reasoning and `<adam_output>` for the highly emotional final reply."
                
                res_a = process_avatar_turn_func(api_key, selected_model, sys_prompt_a, api_hist_a, forced_input_a)
                history_a.append({"role": "assistant", "raw_text": res_a["raw_full_text"], "content": res_a["output"], "parsed_dash": res_a["parsed_dash"]})
                
                with chat_container:
                    with st.chat_message("assistant", avatar="🔴"):
                        st.markdown(f"**{avatar_a}**:\n{res_a['output']}")
                        with st.expander(f"⚙️ {avatar_a} 的 VFO 內部參數"):
                            st.json(res_a["parsed_dash"])

                # 將 A 的輸出轉為 B 的輸入
                current_input = res_a["output"]

                # ==========================================
                # [下半場] Avatar B 的回合
                # ==========================================
                history_b.append({"role": "user", "content": current_input})
                sys_prompt_b = (
                    base_system_rules + "\n\n" + data_b['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_b} 眼中的使用者狀態：\n{perception_b}\n\n"
                    f"🎯 3. {avatar_b} 當下的核心目標：\n{target_b}\n"
                )
                
                api_hist_b = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in history_b[:-1]]
                forced_input_b = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<adam_internal>` for reasoning and `<adam_output>` for the highly emotional final reply."
                
                res_b = process_avatar_turn_func(api_key, selected_model, sys_prompt_b, api_hist_b, forced_input_b)
                history_b.append({"role": "assistant", "raw_text": res_b["raw_full_text"], "content": res_b["output"], "parsed_dash": res_b["parsed_dash"]})
                
                with chat_container:
                    with st.chat_message("user", avatar="🔵"):
                        st.markdown(f"**{avatar_b}**:\n{res_b['output']}")
                        with st.expander(f"⚙️ {avatar_b} 的 VFO 內部參數"):
                            st.json(res_b["parsed_dash"])

                # 將 B 的輸出再次轉回給下一輪的 A
                current_input = res_b["output"]
                
        st.balloons()
        st.success("🏁 N 輪交鋒推演完畢！")
