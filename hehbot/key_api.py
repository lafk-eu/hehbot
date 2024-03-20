import os

class APIHolder:
    def __init__(self):
        self.bot = self.read_api_from_env("TG_BOT_API")
        self.chatgpt = self.read_api_from_env("OPENAI_API")

    def read_api_from_env(self, env_variable):
        return os.getenv(env_variable)
    
api = APIHolder()
    