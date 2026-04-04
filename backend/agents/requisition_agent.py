import json
from config.settings import get_llm
from instructions.prompts import HR_SYSTEM_PROMPT


class RequisitionAgent:

    def __init__(self):
        self.llm = get_llm()
        self.history = []             # 🧠 conversation history
        self.state = {}               # 🧠 accumulated data
        self.waiting_for_confirmation = False  # 🔑 track if JSON shown to HR

    async def run(self, message: str):

        # 1. Add user message
        self.history.append({"role": "user", "content": message})

        # 2. If waiting for confirmation, interpret yes/no
        if self.waiting_for_confirmation:
            if message.lower() in ["yes", "y"]:
                self.waiting_for_confirmation = False
                return "✅ Stored to DB (mock)"
            elif message.lower() in ["no", "n"]:
                self.waiting_for_confirmation = False
                return "Okay, let's continue editing the requisition."
            else:
                return "Please reply with 'yes' or 'no'."

        # 3. Build conversation string
        conversation = "\n".join([f"{m['role']}: {m['content']}" for m in self.history])

        prompt = f"""
        {HR_SYSTEM_PROMPT}

        Current Data:
        {json.dumps(self.state)}

        Conversation:
        {conversation}
        """

        # 4. Call Gemini
        response = self.llm.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw_output = response.text.strip()

        # 🔥 Remove markdown wrapping like ```json ... ```
        if raw_output.startswith("```"):
            raw_output = raw_output.replace("```json", "").replace("```", "").strip()

        # 5. Parse JSON safely
        try:
            parsed = json.loads(raw_output)
        except Exception:
            print("RAW OUTPUT:", response.text)
            return "⚠️ I couldn’t understand that properly. Can you rephrase?"

        # 6. Update state
        self.state = parsed.get("data", self.state)

        # 7. Save assistant message
        assistant_message = parsed.get("message", "")
        self.history.append({"role": "assistant", "content": assistant_message})

        # 8. If LLM says all fields collected, wait for confirmation
        if parsed.get("status") == "completed":
            self.waiting_for_confirmation = True
            # Show JSON for HR approval
            return (
                f"Here is the job description I generated:\n\n"
                f"{json.dumps(self.state, indent=2)}\n\n"
                f"Are you satisfied with this? (yes/no)"
            )

        # 9. Safe return for UI
        if not assistant_message:
            return "⚠️ I processed the request but couldn't generate a response. Please continue."

        return assistant_message