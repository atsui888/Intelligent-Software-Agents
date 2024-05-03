
# from fastapi import FastAPI
# from pydantic import BaseModel
# # from pathlib import Path
# from transformers import pipeline
from abc import ABC, abstractmethod
import requests
from typing import Dict, List, Union, Optional, Tuple
from gradio_client import Client, file


class Classifier(ABC):
    def __init__(self, model: str):
        self.model_name = model

    @abstractmethod
    def classify(self, **kwargs):
        pass


class HuggingFaceClfGradio(Classifier):
    def __init__(self, model: str):
        super().__init__(model)
        self._client = Client(model)  # "richardchai/isa-intent-classifier-v2"

    def classify(self, input_sequence: str, class_labels: str, multi_label=False, top_k=0):
        res = self._client.predict(
            param_0=input_sequence,
            param_1=class_labels,
            param_2=multi_label,
            api_name="/predict"
        )
        # res is a dict with 2 keys 'label' and 'confidences'
        # 'label' is top_k = 1
        # 'confidences' is a list of {'label': str, 'confidence': float}
        r_labels = []
        r_scores = []
        for pred in res.get('confidences'):
            r_labels.append(pred.get('label'))
            r_scores.append(pred.get('confidence'))

        if top_k > 0:
            r_labels = r_labels[0:top_k]
            r_scores = r_scores[0:top_k]
        r_labels = [lbl.strip() for lbl in r_labels]

        return r_labels, r_scores

    def __call__(self, input_sequence: str, class_labels: str, multi_label=False, top_k=0):
        return self.classify(input_sequence, class_labels, multi_label, top_k)


class HuggingFaceClfPipeline(Classifier):
    def __init__(self, model: str = "facebook/bart-large-mnli", model_url: str = 'http://127.0.0.1:11000/classify'):
        super().__init__(model)
        self._model_url = model_url
        self._results = None

    def classify(self, input_sequence: str, class_labels=None, multi_label=True, top_k=0):
        # for pipline version, multi_label is set at pipeline() instantiation, os it is not used here
        # but it is in the signature above to keep the syntax compatible with the Gradio version
        # to be refactored in future.
        if class_labels is None or not isinstance(class_labels, list):
            args = {'sequence': input_sequence, 'labels': []}
        else:
            args = {'sequence': input_sequence, 'labels': class_labels}
        self._results = requests.post(self._model_url, json=args)
        if self._results is None:
            return
        else:
            self._results = self._results.json()

        r_labels = self._results.get('labels')
        r_scores = self._results.get('scores')

        if top_k > 0:
            r_labels = r_labels[0:top_k]
            r_scores = r_scores[0:top_k]
        r_labels = [lbl.strip() for lbl in r_labels]

        return r_labels, r_scores

    def __call__(self, input_sequence: str, class_labels: Union[None, str, List[str]], multi_label=True, top_k=0):
        return self.classify(input_sequence, class_labels, multi_label, top_k)


if __name__ == "__main__":
    print("hello inside main")
    INTENT_CLASSES = ["add task", "list my tasks", "edit task", "delete task", "chatting"]
    INTENT_CLASSES_STR = "add task, list my tasks, edit task, delete task, chatting"
    MULTI_LABEL = True  # The model in docker is pipeline as multi-label = True

    INPUT_SEQ = "I am no longer having lunch with Tom today. Please remove it from my calendar."

    # testing local HF Pipeline
    print("test local")
    intent_clf_pipeline = HuggingFaceClfPipeline(model="facebook/bart-large-mnli")
    # clf_labels, clf_scores = intent_clf_pipeline.classify(input_sequence=INPUT_SEQ, class_labels=INTENT_CLASSES_STR,
    #                                                       multi_label=True, top_k=3)
    clf_labels, clf_scores = intent_clf_pipeline(input_sequence=INPUT_SEQ, class_labels=INTENT_CLASSES_STR,
                                                 multi_label=True, top_k=3)
    for lbl, score in zip(clf_labels, clf_scores):
        print(lbl, ':\t', score)

    # # testing Gradio
    print("\ntest gradio")
    intent_clf_gradio = HuggingFaceClfGradio("richardchai/isa-intent-classifier-v2")
    input('press enter to start)')
    clf_labels, clf_scores = intent_clf_gradio(input_sequence=INPUT_SEQ, class_labels=INTENT_CLASSES_STR,
                                               multi_label=True, top_k=3)
    for lbl, score in zip(clf_labels, clf_scores):
        print(lbl, ':\t', score)

    # todo: to add in main.py
    """
    If two or more of the top_3k each have scores > 0.9, do the next step
    ask the convo/summariser bot to confirm:
    """

    prompt = """
    You are only allowed to take these two actions ["edit task", "delete task"]. Given the following text, determine the primary action to be taken and return only that action and nothing else. 
    
    ### TEXT
    I am no longer having lunch with Tom today. Please remove it from my calendar.
    """

    # todo: it answered "delete task" which was correct.
