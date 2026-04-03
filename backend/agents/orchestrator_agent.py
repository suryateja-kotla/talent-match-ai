from agents.requisition_agent import RequisitionAgent

class OrchestratorAgent:

    def __init__(self):
        self.requisition_agent = RequisitionAgent()

    def handle(self, message: str, role: str):  # ✅ make sync
        
        if role == "hr":
            return self.requisition_agent.run(message)

        return "Invalid role"