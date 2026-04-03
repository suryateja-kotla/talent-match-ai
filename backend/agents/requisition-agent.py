import json
from backend.schemas.job_schema import JobPostingSchema

class RequisitionAgent:
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=(
                "You are an HR assistant. Extract or update job descriptions into JSON using EXACT keys: "
                "job_title, department, location, job_type, experience_required, technical_skills. "
                "Return ONLY JSON."
            )
        )

        # 🧠 state (POC)
        self.pending_job = None
        self.awaiting_confirmation = False

    # -----------------------------
    # STEP 1: Initial generation
    # -----------------------------
    def generate(self, raw_prompt: str):
        response = self.model.generate_content(
            raw_prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        job = JobPostingSchema.model_validate_json(response.text)

        self.pending_job = job
        self.awaiting_confirmation = True

        return {
            "message": "Here is the generated job description. You can suggest changes or type 'yes' to approve.",
            "data": job.model_dump()
        }

    # -----------------------------
    # STEP 2: Refinement loop
    # -----------------------------
    def refine_or_confirm(self, user_input: str):

        if not self.awaiting_confirmation:
            return {"message": "No active job to refine."}

        # ✅ FINAL APPROVAL
        if user_input.lower() in ["yes", "approve", "ok"]:
            self.save_to_db(self.pending_job.model_dump())

            self.pending_job = None
            self.awaiting_confirmation = False

            return {"message": "✅ Job successfully saved to DB"}

        # 🔁 REFINEMENT
        else:
            refinement_prompt = f"""
            Existing Job JSON:
            {self.pending_job.model_dump_json()}

            User wants following changes:
            {user_input}

            Update the JSON accordingly.
            Return ONLY JSON.
            """

            response = self.model.generate_content(
                refinement_prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            updated_job = JobPostingSchema.model_validate_json(response.text)

            self.pending_job = updated_job

            return {
                "message": "Here is the updated job description. More changes or type 'yes' to approve.",
                "data": updated_job.model_dump()
            }

    # -----------------------------
    # DB SAVE
    # -----------------------------
    def save_to_db(self, job_data: dict):
        print("💾 Saving to DB:", job_data)


if __name__ == "__main__":
    agent = RequisitionAgent(api_key="api_key")

    while True:
        user_input = input("\nHR: ")

        if agent.awaiting_confirmation:
            response = agent.refine_or_confirm(user_input)
        else:
            response = agent.generate(user_input)

        print("\nAI:", response["message"])

        if "data" in response:
            print(json.dumps(response["data"], indent=4))