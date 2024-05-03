from abc import ABC, abstractmethod
import requests

"""
local is from docker running local
cloud is from huggingface spaces running fastapi
"""


class ChatBot(ABC):
    def __init__(self, model: str):
        self.model_name = model

    @abstractmethod
    def chat(self, **kwargs):
        pass


class ChatBotCloud(ChatBot):
    def __init__(self, model: str):
        super().__init__(model)
        self._chat_url = 'https://richardchai-isa-convo-summariser.hf.space/chat'
        self._replay_url = "https://richardchai-isa-convo-summariser.hf.space/replay"
        # don't use _summarise_url, it tends to run out of context, better to manage the memory at the main app
        # self._summarise_url = "https://richardchai-isa-convo-summariser.hf.space/summarise"

    def chat(self, prompt: str):
        args = {'input_string': prompt}
        r = requests.post(self._chat_url, json=args).json()
        return r.get('completion')

    def replay(self):
        r = requests.get(self._replay_url)
        return r.json()

    def __call__(self, prompt: str):
        return self.chat(prompt)


class ChatBotLocal(ChatBot):
    def __init__(self, model: str):
        super().__init__(model)
        self._chat_url = model + '/chat'
        self._replay_url = model + '/replay'
        print(self._chat_url)
        print(self._replay_url)

    def chat(self, prompt: str):
        args = {'input_string': prompt}
        r = requests.post(self._chat_url, json=args).json()
        return r.get('completion')

    def replay(self):
        r = requests.get(self._replay_url)
        return r.json()

    def __call__(self, prompt: str):
        return self.chat(prompt)


if __name__ == "__main__":
    # cbot = ChatBotCloud("Nous-Hermes-2-Mistral-7B-DPO-q4-0-gguf")
    cbot = ChatBotLocal('http://127.0.0.1:10000')

    print(cbot("what are you"))
    # cbot("do you have other hobbies?")
    # cbot("what about sports?")
    # res = cbot.replay()  # todo: too troublesome to use .replay(). Store the user/assistant convo at main.py
    # print(type(res))
    # for line in res:
    #     print(type(line))
    #     print(line)




