class APIHolder:
    def __init__(self):
        self.chatgpt_api_key = self.read_api_key("chatgpt_key.txt")
        self.bot_api_key = self.read_api_key("bot_key.txt")

    def read_api_key(self, filename):
        try:
            with open(filename, "r") as file:
                return file.read().strip()
        except FileNotFoundError:
            print(f"Файл {filename} не знайдено. Будь ласка, створіть файл та помістіть туди ключ API.")
            return ""

    def get_chatgpt_api_key(self):
        return self.chatgpt_api_key

    def get_bot_api_key(self):
        return self.bot_api_key