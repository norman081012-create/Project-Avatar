def render_multi_agent_page():
    st.title("⚔️ VFO 雙核心動態交鋒 (Agent vs Agent)")
    
    avatar_list = list(st.session_state.avatars.keys())
    if len(avatar_list) < 2:
        st.warning("請先到人物庫收容至少兩位 Avatar！")
        return

    # 1. 設定區塊
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        avatar_a = st.selectbox("🔴 選擇 Avatar A (先手)", avatar_list, index=0)
    with col2:
        avatar_b = st.selectbox("🔵 選擇 Avatar B (後手)", avatar_list, index=1 if len(avatar_list) > 1 else 0)
    with col3:
        n_rounds = st.number_input("🔁 模擬回合數 (N)", min_value=1, max_value=10, value=3)

    scene_setup = st.text_area("🎬 共同場景設定", value="你們兩人在一間狹小且安靜的會議室裡，因為一個未解的問題被迫對話。")
    initial_spark = st.text_input("🔥 初始對話/破冰句 (由 Avatar A 針對此句開局)", placeholder="例如：你到底想怎樣？")

    st.divider()

    if st.button("🚀 啟動 N 輪交鋒", type="primary"):
        if not api_key:
            st.error("請先配置 API Key。")
            return
            
        if avatar_a == avatar_b:
            st.warning("請選擇兩位不同的 Avatar 進行交鋒！")
            return

        # 取出雙方資料
        data_a = st.session_state.avatars[avatar_a]
        data_b = st.session_state.avatars[avatar_b]

        # 2. 視角交叉綁定 (A 看 B, B 看 A)
        perception_a = f"對方是 {data_b['name']}。({data_b.get('core_seed_label', '未知身分')})"
        perception_b = f"對方是 {data_a['name']}。({data_a.get('core_seed_label', '未知身分')})"
        
        target_a = "在對話中佔據主導權，並試圖看穿對方底牌。"
        target_b = "維持自己的防禦邊界，不輕易妥協。"

        # 清空雙方歷史紀錄以利全新交鋒
        data_a["messages"] = []
        data_b["messages"] = []

        chat_container = st.container()
        
        # 將初始破冰句作為 A 的第一個 User Input
        current_input = initial_spark
        
        # 3. N 輪自動推演迴圈
        with st.spinner("雙方 VFO 引擎已啟動，開始動態交鋒..."):
            for round_num in range(n_rounds):
                with chat_container:
                    st.markdown(f"### 🏁 Round {round_num + 1}")
                
                # ==========================================
                # [回合前半] Avatar A 思考與發言
                # ==========================================
                data_a["messages"].append({"role": "user", "content": current_input})
                
                sys_prompt_a = (
                    BASE_SYSTEM_RULES + "\n\n" + data_a['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_a} 眼中的使用者狀態：\n{perception_a}\n\n"
                    f"🎯 3. {avatar_a} 當下的核心目標：\n{target_a}\n"
                )
                
                history_a = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in data_a["messages"][:-1]]
                forced_input_a = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<adam_internal>` for reasoning and `<adam_output>` for the highly emotional final reply."
                
                res_a = process_avatar_turn(api_key, selected_model, sys_prompt_a, history_a, forced_input_a)
                
                # 紀錄 A 的輸出
                data_a["messages"].append({
                    "role": "assistant", "raw_text": res_a["raw_full_text"], "content": res_a["output"], "parsed_dash": res_a["parsed_dash"]
                })
                
                with chat_container:
                    with st.chat_message("assistant", avatar="🔴"):
                        st.markdown(f"**{avatar_a}**:\n" + res_a["output"])
                        with st.expander("查看 VFO 內部參數"):
                            st.json(res_a["parsed_dash"])

                # 將 A 的輸出轉換為 B 的 Input
                current_input = res_a["output"]

                # ==========================================
                # [回合後半] Avatar B 思考與發言
                # ==========================================
                data_b["messages"].append({"role": "user", "content": current_input})
                
                sys_prompt_b = (
                    BASE_SYSTEM_RULES + "\n\n" + data_b['matrix'] +
                    f"\n\n【System Absolute Override - 當前動態環境與狀態】\n"
                    f"🎬 1. 互動場景與前提：\n{scene_setup}\n\n"
                    f"👁️ 2. {avatar_b} 眼中的使用者狀態：\n{perception_b}\n\n"
                    f"🎯 3. {avatar_b} 當下的核心目標：\n{target_b}\n"
                )
                
                history_b = [{"role": "user", "parts": [m["content"]]} if m["role"] == "user" else {"role": "model", "parts": [m.get("raw_text", m["content"])]} for m in data_b["messages"][:-1]]
                forced_input_b = f"{current_input}\n\n【SYSTEM MANDATORY OVERRIDE】\nYou MUST strictly output your response using `<adam_internal>` for reasoning and `<adam_output>` for the highly emotional final reply."
                
                res_b = process_avatar_turn(api_key, selected_model, sys_prompt_b, history_b, forced_input_b)
                
                # 紀錄 B 的輸出
                data_b["messages"].append({
                    "role": "assistant", "raw_text": res_b["raw_full_text"], "content": res_b["output"], "parsed_dash": res_b["parsed_dash"]
                })
                
                with chat_container:
                    with st.chat_message("user", avatar="🔵"):
                        st.markdown(f"**{avatar_b}**:\n" + res_b["output"])
                        with st.expander("查看 VFO 內部參數"):
                            st.json(res_b["parsed_dash"])

                # 將 B 的輸出再轉回給 A 的下一次 Input
                current_input = res_b["output"]
                
        st.success("🏁 N 輪交鋒推演完畢！")
