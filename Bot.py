import json
from random import randint
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import logging

import handlers
import setting
from setting import GROUP_ID, TOKEN

log = logging.getLogger('bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
    stream_handler.setLevel(logging.DEBUG)
    log.addHandler(stream_handler)

    file_handler = logging.FileHandler("bot.log", encoding='UTF8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    file_handler.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class UserState:
    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        self.context = context or {}


class Bot:
    def __init__(self, GROUP_ID, TOKEN):
        self.group_id = GROUP_ID
        self.token = TOKEN
        self.vk = vk_api.VkApi(token=TOKEN)
        self.long_paller = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()
        self.user_states = dict()


    def run(self):
        for event in self.long_paller.listen():
            try:
                self.on_event(event)
            except Exception:
                log.exception('Ошибка в обработке события')

    def on_event(self, event):
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Мы пока не умеем обрабатывать события такого типа', event.type)
            return

        user_id = event.object.peer_id
        text = event.object.text

        if user_id in self.user_states:
            text_to_send = self.continue_scenario(user_id, text)
        else:
            for intent in setting.IVENTS:
                if any(token in text.lower() for token in intent['tokens']):
                    if intent['answer']:
                        text_to_send = intent['answer']
                    else:
                        text_to_send = self.start_scenario(user_id, intent['scenario'])
                    break
            else:
                self.api.messages.send(
                    message=setting.DEFAULT_ANSWER,
                    random_id=randint(0, 2 ** 20),
                    peer_id=user_id,
                )
                self.api.messages.send(
                    message=setting.DEFAULT_ANSWER,
                    random_id=randint(0, 2 ** 20),
                    peer_id=user_id,
                    sticker_id=50895
                )

        self.api.messages.send(
            message=text_to_send,
            random_id=randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def start_scenario(self,user_id, scenario_name, ):
        scenario = setting.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_states[user_id] = UserState(scenario_name=scenario_name, step_name=first_step)
        return text_to_send

    def continue_scenario(self, user_id, text):
        state = self.user_states[user_id]
        steps = setting.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format()
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                self.user_states.pop(user_id)
        else:
            text_to_send = step['failure_text'].format()

        return text_to_send

    def keyboard(self):
        keyboard = {
            "one_time": False,
            "buttons": [
                [{
                    "action": {
                        "type": "text",
                        "payload": "{\"button\": \"1\"}",
                        "label": "Правила"
                    },
                    "color": "primary"
                },
                    {
                        "action": {
                            "type": "text",
                            "payload": "{\"button\": \"2\"}",
                            "label": "Поехали"
                        },
                        "color": "positive"
                    },
                ]
            ],
            'inline': False
        }

        keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
        keyboard = str(keyboard.decode('utf-8'))

        while True:
            for event in self.long_paller.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    if event.object.text.lower() == "начать":
                        self.vk.method("messages.send",
                                  {"peer_id": event.object.peer_id, "message": "Здравствуйте, Ваше величество! 👑\n \n "
                                                                               "Я ваш советник.\n"
                                                                               , "random_id": 0,
                                   "keyboard": keyboard}
                                       )
                        self.vk.method("messages.send",
                                       {"peer_id": event.object.peer_id, "message": "Привет, принцесса 👑", "random_id": 0,
                                        "keyboard": keyboard, 'sticker_id': 50906}
                                       )
                        self.vk.method("messages.send",
                                       {"peer_id": event.object.peer_id, "message": "Все уже давно готово, а вы только присоединились!\n\n"
                                                                                    "Давайте начинать игру! "
                                                                                    "(Советую сначала прочитать правила)", "random_id": 0,
                                        "keyboard": keyboard}
                                       )
                    if "Правила" in event.object.text:
                        self.vk.method("messages.send",
                                  {"peer_id": event.object.peer_id, "message": 'Это будет некий квест.\n\n'
                                  'В зависимости от задания, тебе нужно будет дать верный ответ.\n\n' 
                                  '‼ Ответом считается то, что ты найдешь ‼\n\n'
                                  'Отправляй сюда то, что ты считаешь верным, и, если все как надо, задания прдолжатся.\n', "random_id": 0
                                   }
                                       )
                    if "Поехали" in event.object.text:
                        keyboard = {
                            "one_time": True,
                            "buttons": [],
                            'inline': False
                        }
                        keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
                        keyboard = str(keyboard.decode('utf-8'))
                        self.vk.method("messages.send",
                                       {"peer_id": event.object.peer_id, "message": '⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐',
                                        "random_id": 0,
                                        "keyboard": keyboard})
                        self.vk.method("messages.send",
                                  {"peer_id": event.object.peer_id, "message": ' 1️⃣ Ваше Величество, нам нужно отгадать о чем тут речь!\n\n'
                                    'Здесь старики устраивают "съезд":\n'
                                    'На лавки сев как куры на насест,\n'
                                    'Власть предержащих яростно ругают,\n'
                                    'Страшилками войны внучат пугают,\n'
                                    'Хватаясь за обилье хворых мест,\n'
                                    'О всех всегда все по наслышке знают -\n'
                                    'Кто с кем чего-когда и кто что ест.\n'
                                    'Дверьми и домофоном нас встречает\n'
                                    'Уютный, чистый друг жильцов - ...\n'
                                      , "random_id": 0
                                  }
                                       )
                        bot.run()



if __name__ == "__main__":
    configure_logging()
    bot = Bot(GROUP_ID, TOKEN)
    bot.keyboard()


