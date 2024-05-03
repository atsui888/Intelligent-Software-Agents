"""
notes:
    Space
    pip install -U pip setuptools wheel
    pip install -U spacy
    python -m spacy download en_core_web_lg
    # python -m spacy download en_core_web_sm
    pip install date-spacy
    https://pypi.org/project/date-spacy/

"""
import io
import librosa
import os
import gtts
import soundfile as sf
import spacy
import datetime as dt

from date_spacy import find_dates
from pydub import AudioSegment
from dotenv import load_dotenv
from typing import Final

# for aiogram
# from aiogram import Bot, Dispatcher, types, F
# from aiogram.filters import Command
# import asyncio
# import requests
# from gradio_client import Client, file

# for aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio

from convo_summariser import ChatBotLocal, ChatBotCloud
from asr import HuggingFaceASRPipeline, HuggingFaceASRGradio
from intent_classifier import HuggingFaceClfPipeline, HuggingFaceClfGradio
from audio_helper_v1 import mp3_to_ogg
from qa import QnALocal, QnAGradio
from Google_Calendar import GoogleCalendar
from slot_fillers_v4 import AddEventSlotFiller
from string_to_time_v2 import from_str_get_24hr_time_str
from dateutil import parser
from datetime import timedelta

load_dotenv()
TELEGRAM_TOKEN: Final = os.getenv("TELEGRAM_TOKEN")
bot = Bot(TELEGRAM_TOKEN)
BOT_USERNAME: Final = os.getenv('TELEGRAM_BOT_NAME')
USE_LOCAL_API = True if os.getenv('USE_LOCAL_API').lower() == "yes" else False

print(f"\nUSE_LOCAL_API = {USE_LOCAL_API}\n")

if USE_LOCAL_API:
    TS_CONVO = ChatBotLocal(model='http://127.0.0.1:10000')
    print("\t--> LOCAL: TS_CONVO loaded")
    TS_ASR = HuggingFaceASRPipeline(model="openai/whisper-small.en")
    print("\t--> LOCAL: TS_ASR loaded")
    TS_INTENT_CLASSIFIER = HuggingFaceClfPipeline(model="facebook/bart-large-mnli")
    print("\t--> LOCAL: TS_INTENT_CLASSIFIER loaded")
    TS_QnA = QnALocal('http://127.0.0.1:12000')
    print("\t--> LOCAL: TS_QnA loaded")
    TS_CALENDAR = GoogleCalendar()  # this can be replaced with any other calendar with future.
    print("\t--> LOCAL: TS_CALENDAR instantiated")
else:
    TS_CONVO = ChatBotCloud("Nous-Hermes-2-Mistral-7B-DPO-q4-0-gguf")
    print("\t--> CLOUD: TS_CONVO loaded")
    TS_ASR = HuggingFaceASRGradio(model="richardchai/isa_asr")
    print("\t--> CLOUD: TS_ASR loaded")
    TS_INTENT_CLASSIFIER = HuggingFaceClfGradio("richardchai/isa-intent-classifier-v2")
    print("\t--> CLOUD: TS_INTENT_CLASSIFIER loaded")
    TS_QnA = QnAGradio("richardchai/isa_qa")
    print("\t--> CLOUD: TS_QnA loaded")
    TS_CALENDAR = GoogleCalendar()  # this can be replaced with any other calendar with future.
    print("\t--> CLOUD: TS_CALENDAR instantiated")

TS_FIND_DATES = spacy.blank("en")
TS_FIND_DATES.add_pipe("find_dates")

dp = Dispatcher()

bot_intro =\
"""Hi! I am TaskSlinger, a Calendar Event Management bot. Let me know if you wish to add, list, delete events in your Google Calendar."""

INTENT_CLASSES = ["add task", "list tasks", "edit task", "delete task", "chatting", "greeting"]
INTENT_CLASSES_STR = "add task, list tasks, edit task, delete task, chatting, greeting"

CHOOSE_INTENT_PROMPT = """
You are only allowed to take the following actions ["add task", "list tasks", "edit task", "delete task", "chatting", "greeting"]. 
Given the following text, determine the primary action to be taken and return only that action and nothing else. 

### TEXT
{user_msg}
"""

DAYS_OF_WEEK = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
D_OF_WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
MONTH_OF_YEAR = ("january", "february", "march", "april", "may", "june", "july", "august", "september",
                 "october", "november", "december")
MTH_OF_YEAR = ("jan", "feb", "mar", "apr", "may", "june", "july", "august", "september",
                 "october", "november", "december")

FAKE_EMAIL_ADDRESSES = {
    'james': 'james@abcdefghij.com',
    'lucy': 'lucy@abcdefghij.com'
}

CONVERSATION = []  # handle my own pruning or summarisation at this level


async def main():
    print(f"\n\nBot: '{BOT_USERNAME}' has started.\n")
    await dp.start_polling(bot)


@dp.message(Command('start'))
async def on_start(msg: types.Message):
    await msg.reply(bot_intro)


@dp.message(Command('replay'))
async def replay_memory(msg: types.Message):
    conversation = ''
    for c in CONVERSATION:
        conversation += str(c) + '\n'
        if 'assistant' in str(c):
            conversation += '\n'
    if conversation is None or len(conversation) < 1:
        await msg.reply('We have not yet began interacting. The conversation memory is empty.')
    else:
        await msg.reply(conversation)


@dp.message(Command('num_chars'))
async def num_chars(msg: types.Message):
    # num of words in CONVERSATION
    num_chars = 0
    for c in CONVERSATION:
        num_chars += len(str(c))
    await msg.reply(f"Number of Words in CONVERSATION Memory is: {str(num_chars)}")


def get_date_and_time_in_iso_format(input_date, input_time):
    """
    possible inputs for date:
    - 5th May 2024

    possible inputs for time:
    -  1130am to 1230pm

    :param input_date:
    :param input_time:
    :return:
    """
    return


def detect_intent_and_act(user_msg: str) -> str:
    global CONVERSATION
    clf_labels, clf_scores = TS_INTENT_CLASSIFIER(input_sequence=user_msg, class_labels=INTENT_CLASSES_STR,
                                                  multi_label=True, top_k=3)

    # todo: comment out debug lines when not required.
    print()
    for lbl, score in zip(clf_labels, clf_scores):
        print(f"label: '{lbl}' ->\t {score}")

    if clf_scores[0] >= 0.8 and clf_scores[1] >= 0.8:
        user_intent = TS_CONVO(prompt=CHOOSE_INTENT_PROMPT.format(user_msg=user_msg))
    elif clf_scores[0] >= 0.8:
        user_intent = clf_labels[0]
    else:
        user_intent = 'chatting'

    # todo: to add timezone info later
    # now
    now_dt = dt.datetime.now()
    now_date_str = str(now_dt.year).zfill(4) + '-' + str(now_dt.month).zfill(2) + '-' + str(now_dt.day).zfill(2)
    now_time_str = str(now_dt.hour).zfill(2) + ':' + str(now_dt.minute).zfill(2)
    day_name = DAYS_OF_WEEK[dt.datetime.weekday(now_dt)]
    month_name = MONTH_OF_YEAR[now_dt.month + 1]

    # todo: comment out debug lines when not required.
    print(f"\nTaskSlinger decided that the task to perform is: '{user_intent}'\n")

    assistant_response = ''
    # see bug listed in case "list my tasks" below, to fix in next release
    user_intent = "list my tasks" if user_intent == "list tasks" else user_intent
    match user_intent:
        case "add task":
            add_event_slot_filler = AddEventSlotFiller(
                user_msg=user_msg,
                qa_model=TS_QnA
            )
            attributes = add_event_slot_filler.add_event_attributes
            print(f"\nattributes detected: \n{attributes}\n")

            # todo: the attendees are fake, just for demo purpose, otherwise we need to create a fn
            # todo: allow user to enter a list of friends/colleagues and their email address
            # todo: To do in next release
            attendees = []
            print()
            names = attributes.get('people_involved').lower()
            print(names)
            if 'james' in names:
                print('james is found')
                attendees.append({"email": FAKE_EMAIL_ADDRESSES.get('james')})
            if 'lucy' in names:
                print('lucy is found')
                attendees.append({"email": FAKE_EMAIL_ADDRESSES.get('lucy')})
            print(attendees)

            doc = TS_FIND_DATES(attributes.get('event_start_date'))
            dt_str = ''
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    dt_str = str(ent._.date)
                    break  # for this demo, we only take the first date. for next practice module, work on NLU
            # for time_str, we don't want the seconds, from HH:MM:SS to HH:MM is sufficient
            date_str, _ = dt_str.split()[0], dt_str.split()[1]
            datetime_str = date_str  # we want this format, str 'YYYY-mm-dd'

            if attributes.get('event_start_time') is not None and len(attributes.get('event_start_time')) > 0:
                start_time = from_str_get_24hr_time_str(attributes.get('event_start_time')) + ':00' + '+08:00'
                start_date_time = datetime_str + 'T' + start_time
                # for now, end_time default to 1 hour for start_date_time
                end_date_time_dt = parser.parse(start_date_time) + timedelta(hours=1)
                end_date_time = end_date_time_dt.isoformat()
            else:
                start_time = "00:00:00+0800"
                start_date_time = datetime_str + 'T' + start_time
                end_time = "23:59:59+0800"
                end_date_time = datetime_str + 'T' + end_time

            print(f"\ndate_str -> {date_str}")
            print(f"start_time -> {start_time}")
            print(f"start_date_time -> {start_date_time}")
            print(f"start_date_time -> {end_date_time}\n")


            # -----------------
            # if attributes.get('event_start_date') == '5th May 2024' and attributes.get('event_start_time') == '1130am':
            #     start_date_time = "2024-05-05T11:30:00+08:00"
            #     end_date_time = "2024-05-05T12:30:00+08:00"
            #     # end_date_time cannot be None
            # else:
            #     # if None, set it to today start at 00:00:00 and end at 23:59:00
            #     start_date_time = None
            #     end_date_time = None

            print("attributes:")
            print(str(attributes.get('event')))
            print(str(attributes.get('location')))
            print(str(start_date_time))
            print(str(end_date_time))
            print(attendees)
            print()
            print()
            res = TS_CALENDAR.add_event(
                summary=str(attributes.get('event')),
                location=str(attributes.get('location')),
                start_date_time=str(start_date_time),  # ""2024-03-28T18:15:00+08:00"
                end_date_time=str(end_date_time),
                start_time_zone="Asia/Singapore",
                end_time_zone="Asia/Singapore",
                details="",
                attendees=attendees
            )
            print(f"Response for Google Calendar: {res}")
            if res is None:
                assistant_response = 'Error: Failed to add task to calendar.'
            else:
                assistant_response = 'A task has been added to your calendar.'
        case "list tasks":
            assistant_response = 'list task is called.'
        case "list my tasks":
            # todo: bug: remove the hardcoded "list my tasks" in intent_classifier later
            # todo: it should follow the classes that are passed into intent_classifier
            # todo: get the date from user_msg
            events = None
            doc = TS_FIND_DATES(user_msg)
            dt_str = ''
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    dt_str = str(ent._.date)
                    break  # for this demo, we only take the first date. for next practice module, work on NLU

            # step 1
            print(f"\n\ndt_str: {type(dt_str)}\n\n\n")
            if dt_str is not None and len(dt_str) > 1:
                date_str, _ = dt_str.split()[0], dt_str.split()[1]
                datetime_str = date_str  # we want this format, str 'YYYY-mm-dd'
                events = TS_CALENDAR.get_upcoming_events_by_date(desired_date_str=datetime_str)
            else:
                events = TS_CALENDAR.get_n_upcoming_events(num_events=5)

            event_details = ''
            if events is None:
                print("No tasks found on this day.")
            else:
                # for evt in EVENTS:
                #     for k, v in evt.to_dict().items():
                #         print(k, v)
                # print('*'*50)
                # step 2
                for evt in events:
                    event_details += 'Task #: ' + str(evt.idx) + '\n' + TS_CALENDAR.get_event_details(evt.idx) + '\n\n'
            print(event_details)
            assistant_response = f'Here is the task list:\n{event_details}'
        case "view task details":
            # not implemented yet
            # assistant_response = 'Here are the details of this task.'
            pass
        case "edit task":
            # not implemented yet
            # assistant_response = 'The task has been modified.'
            pass
        case "delete task":
            question = "what is the task number?"
            context = "please remove task 1"
            res_str = TS_QnA(context=context, question=question)
            event_id = TS_CALENDAR.with_idx_get_event_id(int(res_str))
            print(event_id)
            if event_id is None:
                """
                nb: if tasks has not be listed to the user yet, there is no event_idx and hence no event_id exists
                """
                res = 'Unable to obtain event id, task is not deleted.'
                assistant_response = res
            else:
                TS_CALENDAR.delete_event(event_id)
                assistant_response = f'Task #{res_str} is deleted.'
        case "chatting":
            chat_prompt = f"""You are an AI Calendar Management bot. Respond to the following USER text concisely in less then 50 words. Remember to answer in less than 50 words.
                ### USER
                {user_msg}
                """.format(user_msg=user_msg)
            assistant_response = TS_CONVO(prompt=chat_prompt)
        case "greeting":
            assistant_response = f"{bot_intro}"
        case _:
            # todo, chg to list wht bot can is and do
            assistant_response = "Hi, I am an AI Bot that can help you add task, list task, view task, delete task from your google calendar. Please let me know how I can help you."

    CONVERSATION.append({'assistant': assistant_response})
    # todo: prune/summarise convo here if req.
    # todo: for now, we just drop the first 2 lines coz my laptop is too slow to do summarisation.
    # todo: for future, use appropriate tokeniser to get the correct number of tokens to make a decision
    number_of_chars = 0
    for c in CONVERSATION:
        number_of_chars += len(str(c))
    if number_of_chars > 1200:  # assuming 1 word is 5 chars on ave, 1200 chars is 256 words
        CONVERSATION = CONVERSATION[2:]

    # notes: assistant_response for this turn is not affected and should not be affected by
    # convo pruning or summarization because only convo memory is changed.
    return assistant_response


@dp.message(F.text)
async def on_text(msg: types.Message):
    """
    1. get intent of user's message

    n. since we received text, we return text only
    :param msg:
    :return:
    """
    user_msg = msg.text
    CONVERSATION.append({'user': user_msg})
    assistant_response = detect_intent_and_act(user_msg=user_msg)
    await msg.reply(assistant_response)

    # result = client.predict(
    #     param_0=msg.text,
    #     api_name="/predict"
    # )

    # await msg.reply(result)
    # print(r.text)
    # await msg.reply(f"you said: {msg.text}''")


# content_types=types.ContentType.VOICE
# @dp.message_handler(content_types=types.ContentType.VOICE)
# @dp.message_handler(content_types=types.ContentType.VOICE)

@dp.message(F.voice)
async def process_voice_message(msg: types.Message):
    # https://docs.aiogram.dev/en/dev-3.x/api/download_file.html
    voice_file = await bot.get_file(msg.voice.file_id)
    voice_path_file = voice_file.file_path
    voice_file = io.BytesIO()
    await bot.download_file(voice_path_file, destination=voice_file)

    # https://librosa.org/doc/latest/index.html
    y, sr = librosa.load(voice_file, sr=16000)
    voice_file.close()
    # hf asr can work with .wav, but I would like to save as mp3 to get smaller file size
    wav_file = 'user_voice_msg.wav'
    sf.write(wav_file, y, samplerate=int(sr), format='WAV', subtype='PCM_16')
    # sf.write('test_2.mp3', y, samplerate=int(sr), format='MP3', subtype='PCM_16')  # failed coz endian is wrong??

    # so I use another method to convert wav to mp3
    # https://realpython.com/playing-and-recording-sound-python/
    # if required, realpython post shows how to convert from .wav to .mp3
    sound = AudioSegment.from_wav(wav_file)
    mp3_file = 'user_voice_msg.mp3'
    sound.export(mp3_file, format='mp3')
    # asr
    transcribed_text = TS_ASR.transcribe(mp3_file)
    # await msg.reply(f"You said: '{transcribed_text}'")

    CONVERSATION.append({'user': transcribed_text})
    assistant_response = detect_intent_and_act(user_msg=transcribed_text)

    voice = gtts.gTTS(assistant_response, lang='en')

    # Use a buffered file stream - converts mp3 to OGG
    voice.save('assistant_response_voice.mp3')
    voice = types.BufferedInputFile(mp3_to_ogg('assistant_response_voice'), 'bot_voice')
    await msg.answer_voice(voice)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Bot: '{BOT_USERNAME}' has shutdown.")
