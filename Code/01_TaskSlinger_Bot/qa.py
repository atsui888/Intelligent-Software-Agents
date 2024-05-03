# Class for QA to be called from TaskSlinger bot

from abc import ABC, abstractmethod
# from transformers import pipeline
from gradio_client import Client
from typing import Dict, Any
import requests


class QnA(ABC):
    def __init__(self, model: str):
        self.model_name = model

    @abstractmethod
    def ask(self, **kwargs):
        pass


class QnAGradio(QnA):
    def __init__(self, model: str):
        super().__init__(model)
        self._ask_url = Client(model)
        self._fill_slots_url = None

    def ask(self, context: str, question: str) -> str:
        """

        :param context:
        :param question:
        :return: Returns tuple of 2 elements
            [0] str
                i.e. The output value that appears in the "Answer" Textbox component.

            [1] Dict(
                label: str | int | float | None,
                confidences: List[Dict(label: str | int | float | None, confidence: float | None)] | None)
                i.e. The output value that appears in the "Score" Label component.
        """
        result = self._ask_url.predict(
            param_0=question,
            param_1=context,
            api_name="/predict"
        )
        # ('Berlin', {'label': 'Berlin', 'confidences': [{'label': 'Berlin', 'confidence': 0.9834203124046326}]}),
        return result

    def fill_slots(self, context, questions: Dict[str, str], event_attributes: Dict[str, Any]) -> dict:
        for k, v in event_attributes.items():
            if v is None or v == '':
                response = self.ask(context=context, question=questions.get(k))
                # ('Berlin', {'label': 'Berlin', 'confidences': [{'label': 'Berlin', 'confidence': 0.983420312404}]})
                event_attributes[k] = response[0]
        return event_attributes

    def __call__(self, context: str, question: str):
        result = self.ask(context=context, question=question)
        # ('Berlin', {'label': 'Berlin', 'confidences': [{'label': 'Berlin', 'confidence': 0.9834203124046326}]})
        return result[0]


class QnALocal(QnA):
    def __init__(self, model: str):
        super().__init__(model)
        self._ask_url = model + '/ask'
        self._fill_slots_url = model + '/fill-slots'
        print(self._ask_url)
        print(self._fill_slots_url)

    def ask(self, context: str, question: str):
        args = {
            'context': context,
            'question': question
        }
        return requests.post(self._ask_url, json=args).json()

    def __call__(self, context: str, question: str):
        res = self.ask(context, question)
        return res.get('answer')

    def fill_slots(self, context: str, questions: Dict[str, str], event_attributes: Dict[str, Any]):
        args = {
            'context': context,
            'questions': questions,
            'event_attributes': event_attributes
        }
        r = requests.post(self._fill_slots_url, json=args).json()
        return r


if __name__ == "__main__":
    QnABot = QnALocal('http://127.0.0.1:12000')
    # QnABot = QnAGradio("richardchai/isa_qa")

    # 01 - simple QA
    # QUESTION = "What is the event?"
    # CONTEXT = "My meeting is with James this Friday at his office. Please add this to my calendar."

    QUESTION = "what is the task number?"
    CONTEXT = "please remove task 1"
    RES = QnABot(context=CONTEXT, question=QUESTION)
    print(f'res:\n\t{RES} \n type: {type(RES)}\n**********************')

    # 02 - Slot Fill
    # # CONTEXT = 'I am having lunch at the hilton hotel on 2nd Jan 2024 at 1130am with Jane and Henry. Please mark it in my calendar.'
    # CONTEXT = 'I am meeting James at the hilton hotel on 2nd Jan 2024 at 1130am. Please mark it in my calendar.'
    # QUESTIONS = {
    #     "event": "What is the event?",
    #     "location": "Where is the event held?",
    #     "date": "What is the date of the event?",
    #     "time": "What time is the event held?",
    #     "people_involved": "Who else will be at the event?",
    #     "action": "What action do I need to take for my calendar?"
    # }
    # EVENT_ATTRIBUTES = {
    #     'event': None,
    #     'location': None,
    #     'date': None,
    #     'time': None,
    #     'people_involved': None,
    #     'action': None
    # }
    #
    # R = QnABot.fill_slots(context=CONTEXT, questions=QUESTIONS, event_attributes=EVENT_ATTRIBUTES)  # return dict
    # print()
    # for K, V in R.items():
    #     print(K, '\t->', V)

    pass


