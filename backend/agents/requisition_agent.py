from config.settings import get_llm
from instructions.prompts import HR_SYSTEM_PROMPT

class RequisitionAgent:

    def __init__(self):
        self.llm = get_llm()

    async def run(self, message: str):

        prompt = f"""
        {HR_SYSTEM_PROMPT}

        User Input:
        {message}
        """

        response = self.llm.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
            )
        return response.text