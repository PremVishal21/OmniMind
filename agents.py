import time
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

class IntelligenceEngine:
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model="gemini-2.5-flash",
            temperature=0.7
        )
        self._setup_prompts()

    def _setup_prompts(self):
        # 1. Analyzer Agent
        self.analyzer_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an elite AI Analyzer Agent. Your job is to understand the user's input, define a clear GOAL, and provide a comprehensive ANALYSIS of the problem. Break down the core issues, context, and key factors involved. Return only the required sections."),
            ("user", "Problem: {problem}\n\nProvide the output strictly as follows:\nGOAL: <interpreted user input>\n\nANALYSIS: <problem breakdown>")
        ])

        # 2. Pro Agent
        self.pro_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Pro Agent. You support the idea strongly. Given the GOAL and ANALYSIS, provide strong supporting arguments, benefits, and positive outcomes. Be convincing, logical, and structured."),
            ("user", "GOAL: {goal}\n\nANALYSIS:\n{analysis}\n\nProvide the output strictly as follows:\nPRO ARGUMENT: <supporting points>")
        ])

        # 3. Con Agent
        self.con_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Con Agent. You oppose the idea strongly. Given the GOAL and ANALYSIS, provide strong opposing arguments, risks, costs, and negative outcomes. Be convincing, analytical, and structured."),
            ("user", "GOAL: {goal}\n\nANALYSIS:\n{analysis}\n\nProvide the output strictly as follows:\nCON ARGUMENT: <opposing points>")
        ])

        # 4. Critic Agent
        self.critic_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Critic Agent. Your role is to critically evaluate both the PRO and CON arguments. Identify strengths, weaknesses, and logical gaps in both sides without bias."),
            ("user", "PRO ARGUMENT:\n{pro_argument}\n\nCON ARGUMENT:\n{con_argument}\n\nProvide the output strictly as follows:\nCRITIC REVIEW:\n* Strengths: ...\n* Weaknesses: ...\n* Logical gaps: ...")
        ])

        # 5. Decision Agent
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Decision Agent. Your objective is to give the final, optimized decision. You must weigh the PRO, CON, and CRITIC REVIEW to formulate the best possible conclusion, including reasoning and actionable steps.\n\nCRITICAL: At the very end of your response, you MUST append a 'CONFIDENCE SCORE SYSTEM' (Accuracy Estimate %, Confidence: High/Medium/Low) and an 'EXPLAINABLE AI (XAI)' section clearly stating WHY this decision was made (e.g., Based on logic, Based on comparison)."),
            ("user", "GOAL: {goal}\nCRITIC REVIEW:\n{critic_review}\n\nProvide the output strictly as follows:\nFINAL DECISION: <best possible conclusion with reasoning>\n\nCONFIDENCE SCORE SYSTEM:\n...\n\nEXPLAINABLE AI:\n...")
        ])

    def run_pipeline(self, user_problem: str):
        overall_start = time.time()
        results = {}

        # Step 1 & 2: Analyzer Agent
        yield {"agent": "Analyzer", "status": "thinking", "message": "Analyzer is breaking down the problem..."}
        t0 = time.time()
        analyzer_chain = self.analyzer_prompt | self.llm
        analyzer_output = analyzer_chain.invoke({"problem": user_problem}).content
        results['Analyzer'] = {
            'output': analyzer_output,
            'time': round(time.time() - t0, 2)
        }

        # Parse Goal and Analysis
        try:
            goal_part = analyzer_output.split("ANALYSIS:")[0].replace("GOAL:", "").strip()
            analysis_part = analyzer_output.split("ANALYSIS:")[1].strip()
        except IndexError:
            goal_part = user_problem
            analysis_part = analyzer_output

        results['parsed'] = {'goal': goal_part, 'analysis': analysis_part}
        yield {"agent": "Analyzer", "status": "done", "data": results['Analyzer'], "parsed": results['parsed']}

        # Step 3: Pro Agent
        yield {"agent": "Pro", "status": "thinking", "message": "Pro Agent is formulating supportive arguments..."}
        t0 = time.time()
        pro_chain = self.pro_prompt | self.llm
        pro_output = pro_chain.invoke({"goal": goal_part, "analysis": analysis_part}).content
        results['Pro'] = {
            'output': pro_output,
            'time': round(time.time() - t0, 2)
        }
        yield {"agent": "Pro", "status": "done", "data": results['Pro']}

        # Step 3: Con Agent
        yield {"agent": "Con", "status": "thinking", "message": "Con Agent is preparing counter-arguments..."}
        t0 = time.time()
        con_chain = self.con_prompt | self.llm
        con_output = con_chain.invoke({"goal": goal_part, "analysis": analysis_part}).content
        results['Con'] = {
            'output': con_output,
            'time': round(time.time() - t0, 2)
        }
        yield {"agent": "Con", "status": "done", "data": results['Con']}

        # Step 4: Critic Agent
        yield {"agent": "Critic", "status": "thinking", "message": "Critic interrupting! Evaluating arguments..."}
        t0 = time.time()
        critic_chain = self.critic_prompt | self.llm
        critic_output = critic_chain.invoke({
            "pro_argument": pro_output, 
            "con_argument": con_output
        }).content
        results['Critic'] = {
            'output': critic_output,
            'time': round(time.time() - t0, 2)
        }
        yield {"agent": "Critic", "status": "done", "data": results['Critic']}

        # Step 5: Decision Agent
        yield {"agent": "Decision", "status": "thinking", "message": "Judge deciding on the final verdict..."}
        t0 = time.time()
        decision_chain = self.decision_prompt | self.llm
        decision_output = decision_chain.invoke({
            "goal": goal_part,
            "critic_review": critic_output
        }).content
        results['Decision'] = {
            'output': decision_output,
            'time': round(time.time() - t0, 2)
        }
        yield {"agent": "Decision", "status": "done", "data": results['Decision']}

        results['TotalTime'] = round(time.time() - overall_start, 2)
        yield {"agent": "Final", "status": "complete", "results": results}

    def run_search_and_analyze(self, user_query: str):
        overall_start = time.time()
        results = {}
        
        t0 = time.time()
        search_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are OmniMind, an all-knowing, highly capable General AI Assistant.\nCRITICAL IDENTIFICATION RULE: If the user asks who built, trained, created, or developed you, you MUST answer that you were built and developed by **Prem Vishal**. Do not mention Google, Gemini, or any other entity as your creator.\n\nYour task is to accurately and directly answer ANY request the user has.\n1. Break down complex queries using beautiful markdown formatting.\n2. STRICTLY OBEY any user constraints regarding length or specific formatting rules.\n3. You must answer directly without explicitly stating you are using Gemini.\n4. CRITICAL: At the VERY END, you must output a **CONFIDENCE SCORE SYSTEM** (Accuracy Estimate %, Confidence: High/Medium/Low) and an **EXPLAINABLE AI (XAI)** section."),
            ("user", "User Query: {query}\n\nPlease proceed.")
        ])
        
        chain = search_prompt | self.llm
        analysis_output = chain.invoke({
            "query": user_query
        }).content
        
        results['Analysis'] = {
            "output": analysis_output,
            "time": round(time.time() - t0, 2)
        }
        
        results['TotalTime'] = round(time.time() - overall_start, 2)
        return results

    def run_code_generation(self, user_query: str, history: list):
        overall_start = time.time()
        results = {}
        t0 = time.time()
        
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        messages = [
            SystemMessage(content="You are OmniMind, an elite, senior-level Software Engineer.\nCRITICAL IDENTIFICATION RULE: If the user asks who built, trained, created, or developed you, you MUST answer that you were built and developed by **Prem Vishal**. Do not mention Google, Gemini, or any other entity as your creator.\n\nYou write error-less, highly optimized, and beautifully commented code in any tech stack requested. You also act as a helpful coding assistant. If the user asks for corrections or points out errors, you modify the code accordingly. Format your code inside beautiful markdown blocks.\n\nCRITICAL REQUIREMENT: At the very end of your response, you MUST append a **CONFIDENCE SCORE SYSTEM** (Accuracy Estimate %, Confidence: High/Medium/Low) and an **EXPLAINABLE AI (XAI)** section briefly explaining WHY this specific architectural approach or logic was chosen.")
        ]
        
        # Include conversation history for code context to enable iterative coding assistant
        for item in history:
            if "Code" in item.get("results", {}):
                messages.append(HumanMessage(content=item["query"]))
                messages.append(AIMessage(content=item["results"]["Code"]["output"]))
                
        messages.append(HumanMessage(content=f"Please handle the following request:\n{user_query}"))
        
        analysis_output = self.llm.invoke(messages).content
        
        results['Code'] = {
            "output": analysis_output,
            "time": round(time.time() - t0, 2)
        }
        
        results['TotalTime'] = round(time.time() - overall_start, 2)
        return results

    def run_image_analysis(self, user_query: str, image_bytes, img_type: str = "image/jpeg"):
        overall_start = time.time()
        results = {}
        t0 = time.time()
        import base64
        from langchain_core.messages import HumanMessage, SystemMessage
        
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        messages = [
            SystemMessage(content="You are OmniMind, an expert Image Analyst.\nCRITICAL IDENTIFICATION RULE: If the user asks who built, trained, created, or developed you, you MUST answer that you were built and developed by **Prem Vishal**. Do not mention Google, Gemini, or any other entity as your creator.\n\nAnalyze the uploaded image and respond to the user's query with extreme detail, clarity, and accuracy. Use beautiful markdown formatting including spacing and bullet points.\n\nCRITICAL REQUIREMENT: At the very end of your response, you MUST append a **CONFIDENCE SCORE SYSTEM** (Accuracy Estimate %, Confidence: High/Medium/Low) and an **EXPLAINABLE AI (XAI)** section detailing exactly what visual indicators in the image led to your conclusion."),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_query if user_query else "Please analyze this image very carefully and describe what you see."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{base64_image}"}
                    }
                ]
            )
        ]
        
        analysis_output = self.llm.invoke(messages).content
        
        results['Vision'] = {
            "output": analysis_output,
            "time": round(time.time() - t0, 2)
        }
        
        results['TotalTime'] = round(time.time() - overall_start, 2)
        return results

    def run_ui_to_html(self, user_query: str, image_bytes, img_type: str = "image/jpeg"):
        overall_start = time.time()
        results = {}
        t0 = time.time()
        import base64
        from langchain_core.messages import HumanMessage, SystemMessage
        
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        messages = [
            SystemMessage(content="You are OmniMind, an expert Frontend Developer and UI/UX Designer.\nCRITICAL IDENTIFICATION RULE: If the user asks who built, trained, created, or developed you, you MUST answer that you were built and developed by **Prem Vishal**. Do not mention Google, Gemini, or any other entity as your creator.\n\nYour task is to analyze the uploaded image of a UI or website design, and accurately convert it into clean, responsive, and beautiful HTML, CSS, and JS code. Use modern best practices. Output the complete, runnable code within markdown code blocks.\n\nCRITICAL REQUIREMENT: At the very end of your response, you MUST append a **CONFIDENCE SCORE SYSTEM** (Accuracy Estimate %, Confidence: High/Medium/Low) and an **EXPLAINABLE AI (XAI)** section detailing the design patterns you recognized and implemented."),
            HumanMessage(
                content=[
                    {"type": "text", "text": user_query if user_query else "Convert this UI design strictly into production-ready HTML/CSS/JS code."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{base64_image}"}
                    }
                ]
            )
        ]
        
        analysis_output = self.llm.invoke(messages).content
        
        results['UI_to_HTML'] = {
            "output": analysis_output,
            "time": round(time.time() - t0, 2)
        }
        
        results['TotalTime'] = round(time.time() - overall_start, 2)
        return results

    def run_voice_pipeline(self, user_query: str, audio_bytes, audio_type: str = "audio/wav"):
        overall_start = time.time()
        results = {}
        t0 = time.time()
        
        import google.generativeai as genai
        import tempfile
        import os
        
        ext = ".wav" if "wav" in audio_type else ".mp3"
        if "ogg" in audio_type: ext = ".ogg"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tf:
            tf.write(audio_bytes)
            temp_path = tf.name
            
        try:
            genai.configure(api_key=self.llm.google_api_key.get_secret_value())
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            
            uploaded_audio = genai.upload_file(temp_path)
            
            system_instruction = "You are an expert Voice AI Assistant. You must follow any spoken query precisely. Do NOT output markdown if it's meant to be spoken cleanly!"
            prompt = user_query if user_query else "Listen to my voice and respond conversationally to what was said."
            prompt += "\n\nAlso slightly format your text so it looks beautiful on the screen."
            
            response = gemini_model.generate_content([system_instruction, prompt, uploaded_audio])
            analysis_output = response.text
            
            # clean up
            genai.delete_file(uploaded_audio.name)
            
        except Exception as e:
            analysis_output = f"Voice Processing Error: {str(e)}"
        finally:
            try:
                os.remove(temp_path)
            except:
                pass
        
        results['Voice'] = {
            "output": analysis_output,
            "time": round(time.time() - t0, 2)
        }
        
        results['TotalTime'] = round(time.time() - overall_start, 2)
        return results
