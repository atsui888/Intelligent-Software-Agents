# local is not dockerised, cloud is using hf spaces

from abc import ABC, abstractmethod
from transformers import pipeline
from gradio_client import Client, file


class ASR(ABC):
    def __init__(self, model: str):
        self.model_name = model

    @abstractmethod
    def transcribe(self, **kwargs):
        pass


class HuggingFaceASRPipeline(ASR):
    def __init__(self, model: str):
        super().__init__(model)
        self._model = pipeline('automatic-speech-recognition', model=model)

    def transcribe(self, speech_file):
        """
        :param speech_file:
        :return:
        """
        transcribed = self._model(speech_file)
        transcribed_text = transcribed.get('text').strip()

        if isinstance(transcribed_text, str):
            search_term = 'text='
            if search_term in transcribed_text:
                user_msg_text = (
                    transcribed_text[transcribed_text.find(search_term) + len(search_term) + 1:
                                     transcribed_text.rfind(',')]
                    .strip())
            else:
                user_msg_text = transcribed_text
        elif isinstance(transcribed_text, dict):
            if 'text' in transcribed_text.keys():
                user_msg_text = transcribed_text.get('text')
                if user_msg_text is not None and isinstance(user_msg_text, str):
                    user_msg_text = user_msg_text.strip()
            else:
                user_msg_text = transcribed_text
        else:
            user_msg_text = 'Unknown'
        return user_msg_text

    def __call__(self, speech_file):
        """

        :param speech_file:
        :return:
        """
        return self.transcribe(speech_file)


class HuggingFaceASRGradio(ASR):
    def __init__(self, model: str):
        super().__init__(model)
        self._model = Client(model)

    def transcribe(self, speech_file):
        """

        :param speech_file:
        :return:
        """
        result = self._model.predict(
            param_0=file(speech_file),
            api_name="/predict"
        )
        text = result[result.find('"')+1:result.rfind('"')].strip()
        return text

    def __call__(self, speech_file):
        """

        :param speech_file:
        :return:
        """
        return self.transcribe(speech_file)


if __name__ == "__main__":
    # # asr_bot_local = HuggingFaceASRPipeline(model="openai/whisper-small.en")
    # asr_bot_cloud = HuggingFaceASRGradio(model="richardchai/isa_asr")
    #
    # input("press to start.")
    # test_file = "test_voice.mp3"
    #
    # # print("testing local")
    # # print(asr_bot_local(test_file))
    # print("\nTesting HF Gradio")
    # print(asr_bot_cloud(test_file))

    pass
