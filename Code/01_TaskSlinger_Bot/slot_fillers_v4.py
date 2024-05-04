from typing import Any


class AddEventSlotFiller:
    def __init__(self, user_msg: str, qa_model: Any):
        self._add_event_questions = {
            "event": "What is the event?",
            "location": "Where is the location of the event?",
            "event_start_date": "What is the start date of the event?",
            "event_start_time": "What time does the event start?",
            # "duration": "How long does the event last?",
            # 'event_end_date': "What is the end date of the event?",
            # 'event_end_time': "What time does the event end?",
            "people_involved": "Who is attending this event? Reply with only the names.",
        }
        self._add_event_attributes = {
            'event': None,     # summary
            'location': None,  # location
            'event_start_date': None,
            'event_start_time': None,
            # "duration": None,
            # 'event_end_date': None,
            # 'event_end_time': None,
            'people_involved': None,
        }

        self._user_msg = user_msg
        self._qa_model = qa_model
        self._response = None

        self.get_add_event_attributes()

    @property
    def add_event_attributes(self):
        return self._add_event_attributes

    def get_add_event_attributes(self):
        self._response = self._qa_model.fill_slots(
            context=self._user_msg,
            questions=self._add_event_questions,
            event_attributes=self._add_event_attributes
        )
        for k, v in self._response.items():
            if v is not None:
                self._add_event_attributes[k] = v

        # todo: for future, create a way to spin a process to ask user questions
        # Bot to ask questions for those which QA Bot couldn't answer
        # for q in self._add_event_questions:
        #     if self._add_event_attributes[q] is None or self._add_event_attributes[q].lower() == 'unknown':
        #         r = str(input(f"{self._add_event_questions.get(q)}: "))
        #         self._add_event_attributes[q] = r

        # Bot to ask questions that QA Bot was not meant / not capable enough to get good answers
        # todo: finetune QnA Bot to improve extraction of task/meeting related types of data
        # for q in self._add_event_questions:
        #     if self._add_event_attributes[q] is None or self._add_event_attributes[q].lower() == 'unknown':
        #         r = str(input(f"{self._add_event_questions.get(q)}: "))
        #         self._add_event_attributes[q] = r

        return self._add_event_attributes


if __name__ == "__main__":
    from qa import QnALocal, QnAGradio

    QnABot = QnALocal('http://127.0.0.1:12000')
    # QnABot = QnAGradio("richardchai/isa_qa")

    # original_user_prompt = "My meeting with James is this Friday at his office. Please add this to my calendar."
    original_user_prompt = "I am meeting James and Lucy at the hilton hotel on 2nd Jan 2024 from 1130am to 1230pm. Please mark it in my calendar."

    add_event_slot_filler = AddEventSlotFiller(
        user_msg=original_user_prompt,
        qa_model=QnABot
    )
    add_event_attributes = add_event_slot_filler.add_event_attributes
    print()
    print(add_event_attributes)

    # # todo: step 1 -> ask QA bot
    # R = QnABot.fill_slots(context=original_user_prompt,
    #                       questions=ADD_EVENT_QUESTIONS,
    #                       event_attributes=ADD_EVENT_ATTRIBUTES)  # return dict
    # print()
    # for K, V in R.items():
    #     print(K, '\t->', V)
    #     if V is not None or len(V) > 0:
    #         ADD_EVENT_ATTRIBUTES[K] = V
    #
    # print('\n**********\n\n')

    # todo: step 2: If any "unknown", just ask directly, don't use the QnA bot (it does not work well)
    # for q in ADD_EVENT_QUESTIONS:
    #     if ADD_EVENT_ATTRIBUTES[q] is None or ADD_EVENT_ATTRIBUTES[q].lower() == 'unknown':
    #         res = str(input(f"{ADD_EVENT_QUESTIONS.get(q)}: "))
    #         print(q, ' ------>')
    #         print(f"\t{res}\n")
    #         ADD_EVENT_ATTRIBUTES[q] = res

    # todo: step 3 - always ask for "details" because it is not asked for above
    # todo: also ask for duration because QnA Bot does not handle it well.
    # ADD_EVENT_ADDITIONAL_ATTRIBUTES = {
    #     'duration': 'How much time will this take (minutes)? ',
    #     'details': 'Any other details to add? '
    # }
    # for k, v in ADD_EVENT_ADDITIONAL_ATTRIBUTES.items():
    #     res = str(input(v))
    #     if res is not None:
    #         ADD_EVENT_ATTRIBUTES[k] = res
    #
    # # check what are the valeus
    # for k, v in ADD_EVENT_ATTRIBUTES.items():
    #     print(k, '\t->', v)

    # todo: somewhere need to convert start and end times to ISO format
    #

    # from Google_Calendar import GoogleCalendar
    # g_cal = GoogleCalendar()
    #
    # print('*' * 50)
    # RES = g_cal.add_event(
    #     summary="my new event 111",
    #     location="Hilton Hotel",
    #     start_date_time="2024-04-29T16:00:00+08:00",  # ""2024-03-28T18:15:00+08:00"
    #     end_date_time="2024-04-29T17:00:00+08:00",
    #     start_time_zone="Asia/Singapore",
    #     end_time_zone="Asia/Singapore",
    #     details="This is a test description.",  # OK
    #     attendees=[  # OK
    #         {"email": "atsuishisen@yahoo.com"},
    #         {"email": "richard.chai@outlook.sg"},
    #     ]
    # )
    # print(RES)