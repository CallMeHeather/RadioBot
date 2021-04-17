import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import os
import requests
from vk_api.upload import FilesOpener

from radiolibrary_parse import radiolibrary_parse
from eandc_parse import eandc_parse
from alldatasheet_parse import alldatasheet_parse

TOKEN = 'd034eacf55b685f35ec2b825304d1e705080c129359983d40ce469629f66c0eb20eaef6833987876315ba'
group_id = 203010669

parsers = {
    2: (2, radiolibrary_parse, 'radiolibrary.ru'),
    1: (1, eandc_parse, 'eandc.ru'),
    3: (3, alldatasheet_parse, 'www.alldatasheet.com')
}

keyboard = {
    "keyboard": {
        "one_time": True,
        "buttons":
            [
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Следующий результат",
                            "payload": "1"
                        },
                    "color": "primary"

                }],
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Поиск на другом сайте",
                            "payload": "2"
                        },
                    "color": "primary"
                }],
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Закончить поиск",
                            "payload": "3"
                        },
                    "color": "negative"
                }]

            ],
        "inline": False
    },
    "start": {
        "one_time": True,
        "buttons":
            [
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Настройки",
                            "payload": "4"
                        },
                    "color": "secondary"

                }],
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Помощь",
                            "payload": "7"
                        },
                    "color": "secondary"

                }]
            ],
        "inline": False
    },
    "settings": {
        "one_time": True,
        "buttons":
            [
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Кол-во результатов поиска",
                            "payload": "5"
                        },
                    "color": "secondary"
                }],
                [{
                    "action":
                        {
                            "type": "text",
                            "label": "Назад",
                            "payload": "6"
                        },
                    "color": "primary"

                }]
            ],
        "inline": False
    },
    "empty": {
        "one_time": True,
        "buttons": [],
        "inline": False
    },
}

greeting_message = f'Привет.\n' \
                   f'Я - радиобот, могу искать характеристики электронных компонентов по их маркировке.\n' \
                   f'На данный момент в базе {len(parsers)} сайтов.\n' \
                   f'Отправьте название для поиска.\n' \
                   f'\n' \
                   f'Для более точного и быстрого поиска вводите маркировку вместе с буквенным индексом (Пример: КТ315Г)\n' \
                   f'Поиск может занять какое-то время.\n' \
                   f'Если результаты поиска некорректны, попробуте поиск на другом сайте или проверьте, правильно ли введена маркировка компонента.\n'


def make_keyboard_json(keyboard):
    return str(keyboard).replace('True', 'true').replace('False', 'false').replace("'", '"')


def photo_messages(vk, photo, peer_id=0):
    try:
        url = vk.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']

        with FilesOpener(photo) as photo_files:
            response = requests.post(url, files=photo_files).json()

        return vk.photos.saveMessagesPhoto(photo=response['photo'],
                                           server=response['server'],
                                           hash=response['hash'])
    except Exception:
        pass


class UserDialog:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_parser = 1
        self.current_result = -1
        self.results_count = 5
        self.search_text = ''
        self.results = []
        self.next_call = None
        self.state = 'idle'  # 'wait_for_response'

    def set_results_count(self, vk, message):
        try:
            a = int(message["text"])
            if a == -1:
                self.results_count = 999
                vk.messages.send(user_id=self.user_id,
                                 message=f'Будут выводиться все результаты.',
                                 random_id=random.randint(0, 2 ** 64))
                return True
            elif a < 1:
                raise ValueError
            else:
                self.results_count = a
                vk.messages.send(user_id=self.user_id,
                                 message=f'Установлено число выводимых результатов поиска: {self.results_count}',
                                 random_id=random.randint(0, 2 ** 64))
                return True
        except ValueError:
            vk.messages.send(user_id=self.user_id,
                             message=f'Число результатов должно быть int >= 1',
                             random_id=random.randint(0, 2 ** 64))
            return False

    def reset_search(self, vk):
        self.state = 'idle'
        self.current_parser = 1
        self.current_result = 0
        self.results = []
        if self.search_text:
            vk.messages.send(user_id=self.user_id,
                             message=f'Поиск по запросу  "{self.search_text}"  завершён.\n',
                             # f'Введите название элемента, чтобы начать поиск.',
                             random_id=random.randint(0, 2 ** 64),
                             keyboard=make_keyboard_json(keyboard.get("start")))
        self.search_text = ''

    def parse(self, vk):
        try:
            self.results = []
            _, parser, site_url = parsers.get(self.current_parser)
            vk.messages.send(user_id=self.user_id,
                             message=f'Поиск  "{self.search_text}"  на {site_url}...',
                             random_id=random.randint(0, 2 ** 64),
                             dont_parse_links=True)
            self.results = parser(self.search_text, self.results_count)

            # Если результатов нет, то идёт на другой сайт
            if not self.results:
                vk.messages.send(user_id=self.user_id,
                                 message=f'''На сайте ничего не найдено.''',
                                 random_id=random.randint(0, 2 ** 64))
                return False
        except Exception as exc:
            vk.messages.send(user_id=self.user_id,
                             message=f'{exc}\n'
                                     f'\n'
                                     f'Произошла непредвиденная ошибка.\n'
                                     f'Отправьте скриншот переписки сюда: https://vk.com/topic-203010669_47477651',
                             random_id=random.randint(0, 2 ** 64))
            return False
        return True

    def send_result(self, vk):
        if self.results:
            result = self.results.pop(0)
        else:
            return False
        try:
            msg = f'Результат поиска: {result["name"]}\n' \
                  f'Источник: {result["url"]}\n'
            attachment = ''

            if result['images']:
                photos = []
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
                }
                for image in result['images']:
                    response = requests.get(image, headers=headers)

                    with open(f'temp.{image[-3:]}', 'wb') as out_img:
                        out_img.write(response.content)
                    with open(f'temp.{image[-3:]}', 'rb') as img:
                        a = photo_messages(vk, img, 0)
                        if a:
                            photos.append(a)
                    os.remove(f'temp.{image[-3:]}')
                attachment = ','.join([f'photo-{group_id}_{photo[0]["id"]}' for photo in photos])
            if result['text']:
                msg += '\n' + result['text']

            kbd = eval(str(keyboard.get("keyboard")))
            kbd["buttons"][2][0]["action"]["label"] = f'Закончить поиск по запросу {self.search_text}' \
                if len(f'Закончить поиск по запросу {self.search_text}') <= 40 else \
                f'Закончить поиск по запросу {self.search_text}'[:37] + '...'

            kbd["buttons"][0][0]["action"]["label"] = f'Следующий результат ({len(self.results)})'
            if self.current_parser + 1 > len(parsers):
                kbd["buttons"].pop(1)
            if not self.results:
                kbd["buttons"].pop(0)

            kbd = make_keyboard_json(kbd)
            vk.messages.send(user_id=self.user_id,
                             message=msg,
                             random_id=random.randint(0, 2 ** 64),
                             attachment=attachment,
                             keyboard=kbd,
                             dont_parse_links=True)

            self.state = 'wait_for_response'
        except Exception as exc:
            vk.messages.send(user_id=self.user_id,
                             message=f'{exc}\n'
                                     f'\n'
                                     f'Произошла непредвиденная ошибка.\n'
                                     f'Отправьте скриншот переписки сюда: https://vk.com/topic-203010669_47477651',
                             random_id=random.randint(0, 2 ** 64))
            return False
        return True

    def first_parse(self, vk):
        while not self.parse(vk):
            self.current_parser += 1
            if self.current_parser > len(parsers):
                vk.messages.send(user_id=self.user_id,
                                 message=f'Сайты кончились.\n',
                                 random_id=random.randint(0, 2 ** 64))
                self.reset_search(vk)
                break

        if self.results:
            self.send_result(vk)

    def handle_message(self, message, vk):
        text = message['text']

        # Пустое сообщение
        if not text:
            vk.messages.send(user_id=self.user_id,
                             message='Отправьте мне корректную маркировку радиоэлемента для поиска.',
                             random_id=random.randint(0, 2 ** 64))
            return None
        if self.state in ('idle', 'wait_for_response'):
            if "payload" in message:
                if message["payload"] == '{"command":"start"}':
                    vk.messages.send(user_id=self.user_id,
                                     message=greeting_message,
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=make_keyboard_json(keyboard.get("start")))
                elif message["payload"] == '3':
                    self.reset_search(vk)
                elif message["payload"] == '1':
                    a = self.send_result(vk)
                    if not a:
                        vk.messages.send(user_id=self.user_id,
                                         message=f'Результаты кончились.\n'
                                                 f'2 - Продолжить поиск на другом сайте\n'
                                                 f'3 - Закончить поиск по запросу  "{self.search_text}"',
                                         random_id=random.randint(0, 2 ** 64))
                elif message["payload"] == '2':
                    self.current_parser += 1
                    if self.current_parser > len(parsers):
                        vk.messages.send(user_id=self.user_id,
                                         message=f'Сайты кончились.\n',
                                         random_id=random.randint(0, 2 ** 64))
                        self.reset_search(vk)
                    else:
                        self.first_parse(vk)
                elif message["payload"] == "4":  # Настройки
                    kbd = eval(str(keyboard.get("settings")))
                    kbd["buttons"][0][0]["action"][
                        "label"] = f'Кол-во результатов поиска (текущ.: {self.results_count})'
                    vk.messages.send(user_id=self.user_id,
                                     message=f'Вы вошли в настройки.',
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=make_keyboard_json(kbd))
                elif message["payload"] == "5":  # Кол-во результатов
                    vk.messages.send(user_id=self.user_id,
                                     message=f'Текущее количество выводимых результатов: {self.results_count}\n'
                                             f'Введите необходимое значение или -1, чтобы выводить все.',
                                     random_id=random.randint(0, 2 ** 64))
                    self.state = 'waiting_for_results_count'
                elif message["payload"] == "6":  # Выход из настроек
                    vk.messages.send(user_id=self.user_id,
                                     message=f'Вы вышли из настроек.',
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=make_keyboard_json(keyboard.get("start")))
                elif message["payload"] == "7":  # Помощь
                    vk.messages.send(user_id=self.user_id,
                                     message='Для начала поиска введите маркировку радиоэлемента.\n'
                                             'Для более точного и быстрого поиска вводите маркировку вместе с буквенным индексом (Пример: КТ315Г, КТ819ГМ, Д226Б).\n'
                                             'Поиск может занять какое-то время. Если поиск идёт слишком долго, попробуйте уменьшить кол-во выводимых результатов в настройках.\n'
                                             'Если результаты поиска некорректны, попробуте поиск на другом сайте или проверьте, правильно ли введена маркировка компонента.\n',
                                     random_id=random.randint(0, 2 ** 64),
                                     keyboard=make_keyboard_json(keyboard.get("start")))

            else:
                self.reset_search(vk)
                self.search_text = text
                self.first_parse(vk)
        elif self.state == 'waiting_for_results_count':
            if self.set_results_count(vk, message):
                self.state = 'idle'
                kbd = eval(str(keyboard.get("settings")))
                kbd["buttons"][0][0]["action"][
                    "label"] = f'Кол-во результатов поиска (текущ.: {self.results_count})'
                vk.messages.send(user_id=self.user_id,
                                 message=f'Вы в настройках.',
                                 random_id=random.randint(0, 2 ** 64),
                                 keyboard=make_keyboard_json(kbd))


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, group_id)
    dialogs = {}

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            sender = vk.users.get(user_id=event.obj.message['from_id'])[0]
            message = event.obj.message

            if sender['id'] not in dialogs:
                dialogs[sender['id']] = UserDialog(sender['id'])
                dialogs[sender['id']].handle_message(message, vk)
            else:
                dialogs[sender['id']].handle_message(message, vk)


if __name__ == '__main__':
    main()
