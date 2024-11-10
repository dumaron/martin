from openai import OpenAI


class OpenAIService:
    def get_pairing_suggestions(self):
        self._init_openai_client()
        pass


    def suggest_next_task(self, input):
        self._init_openai_client()
        pass


    def _init_openai_client(self):
        self.client = OpenAI()


openai = OpenAIService()