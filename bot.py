import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import os
import requests
from vk_api.upload import FilesOpener
import json

from shematok_parse import shematok_parse
from joyta_parse import joyta_parse
from radiolibrary_parse import radiolibrary_parse
from eandc_parse import eandc_parse

TOKEN = 'd034eacf55b685f35ec2b825304d1e705080c129359983d40ce469629f66c0eb20eaef6833987876315ba'
group_id = 203010669

parsers = {2: (2, radiolibrary_parse, 'radiolibrary.ru'),
           1: (1, eandc_parse, 'eandc.ru'),
           # 2: (2, shematok_parse, 'shematok.ru')
           }

keyboard = {
    "keyboard": {
        "one_time": True,
        "buttons":
            [
                {
                    "action":
                        {
                            "type": "text",
                            "label": "Red",
                            "payload": "1",
                        },
                    "color": "negative"
                }
            ],
        "inline": False
    }
}
keyboard = str(keyboard["keyboard"]). \
    replace('True', 'true').replace('False', 'false').replace("'", '"').replace(' ', '')


def photo_messages(vk, photo, peer_id=0):
    try:
        url = vk.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']

        with FilesOpener(photo) as photo_files:
            response = requests.post(url, files=photo_files).json()

        return vk.photos.saveMessagesPhoto(photo=response['photo'],
                                           server=response['server'],
                                           hash=response['hash'])
    except Exception as exc:
        pass


class UserDialog:
    def __init__(self, user_id, vk):
        self.user_id = user_id
        self.current_parser = 1
        self.current_result = -1
        self.search_text = ''
        self.results = []
        self.state = 'wait_for_request'  # 'wait_for_response'

        vk.messages.send(user_id=self.user_id,
                         message=f'Привет.\n'
                                 f'Я - радиобот, могу искать характеристики электронных компонентов по их названиям.\n'
                                 f'На данный момент в базе {len(parsers)} сайтов.\n'
                                 f'Отправьте название для поиска.\n'
                                 f'\n'
                                 f'Для более точного и быстрого поиска вводите маркировку вместе с буквенным индексом (Пример: КТ315Г)\n'
                                 f'Поиск может занять какое-то время, наберитесь терпения.\n'
                                 f'Если результаты поиска некорректны, попробуте поиск на другом сайте.\n'
                                 f'\n'
                                 f'BETA 0.0.0.2 НИЧЁ НЕ РАБОТАЕТ НОРМАЛЬНО',
                         random_id=random.randint(0, 2 ** 64))

    def reset_search(self, vk):
        self.state = 'wait_for_request'
        self.current_parser = 1
        self.current_result = 0
        self.results = []
        vk.messages.send(user_id=self.user_id,
                         message=f'Поиск по запросу  "{self.search_text}"  завершён.\n'
                                 f'Введите название элемента, чтобы начать поиск.',
                         random_id=random.randint(0, 2 ** 64))

    def parse(self, vk):
        try:
            self.results = []
            _, parser, site_url = parsers.get(self.current_parser)
            vk.messages.send(user_id=self.user_id,
                             message=f'Поиск  "{self.search_text}"  на {site_url}...',
                             random_id=random.randint(0, 2 ** 64),
                             dont_parse_links=True)
            self.results = parser(self.search_text)

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
                                     f'Произошла непредвиденная ошибка при поиске.\n',
                             random_id=random.randint(0, 2 ** 64))
            return False
        return True

    def send_result(self, vk):
        if self.results:
            result = self.results.pop(0)
        else:
            return False

        msg = f'Результат поиска: {result["name"]}\n' \
              f'Источник: {result["url"]}\n'
        attachment = ''
        if result['images']:
            photos = []
            for image in result['images']:
                with open(image, 'rb') as img:
                    a = photo_messages(vk, img, 0)
                    if a:
                        photos.append(a)
                    img.close()
                os.remove(image)
            attachment = ','.join([f'photo-{group_id}_{photo[0]["id"]}' for photo in photos])
        if result['text']:
            msg += '\n' + result['text']

            # for i, text in enumerate(msg):
            vk.messages.send(user_id=self.user_id,
                             message=msg,
                             random_id=random.randint(0, 2 ** 64),
                             attachment=attachment)

        # Просит ответа у пользователя
        vk.messages.send(user_id=self.user_id,
                         message=f'1 - Следующий результат\n'
                                 f'2 - Продолжить поиск на другом сайте\n'
                                 f'3 - Закончить поиск по запросу  "{self.search_text}"',
                         random_id=random.randint(0, 2 ** 64))

        self.state = 'wait_for_response'
        return True

    def handle_message(self, message, vk):
        text = message['text']

        # Пустое сообщение
        if not text:
            vk.messages.send(user_id=self.user_id,
                             message='Отправьте мне корректное название радиоэлемента для поиска.',
                             random_id=random.randint(0, 2 ** 64))
            return None
        if self.state == 'wait_for_request':
            self.search_text = text

            while not self.parse(vk):
                self.current_parser += 1
                if self.current_parser > len(parsers):
                    self.reset_search(vk)
                    break

            if self.results:
                self.send_result(vk)

        elif self.state == 'wait_for_response':
            if text == '3':

                self.reset_search(vk)
            elif text == '1':
                a = self.send_result(vk)
                if not a:
                    vk.messages.send(user_id=self.user_id,
                                     message=f'Результаты кончились.\n'
                                             f'2 - Продолжить поиск на другом сайте\n'
                                             f'3 - Закончить поиск по запросу  "{self.search_text}"',
                                     random_id=random.randint(0, 2 ** 64))
            elif text == '2':
                self.current_parser += 1
                if self.current_parser > len(parsers):
                    vk.messages.send(user_id=self.user_id,
                                     message=f'Сайты кончились.\n',
                                     random_id=random.randint(0, 2 ** 64))
                    self.reset_search(vk)
                else:
                    while not self.parse(vk):
                        self.current_parser += 1
                        if self.current_parser > len(parsers):
                            vk.messages.send(user_id=self.user_id,
                                             message=f'Сайты кончились.\n',
                                             random_id=random.randint(0, 2 ** 64))
                            self.reset_search(vk)

                    if self.results:
                        self.send_result(vk)
            else:
                self.reset_search(vk)
                self.search_text = text

                while not self.parse(vk):
                    self.current_parser += 1
                    if self.current_parser > len(parsers):
                        break

                if self.results:
                    self.send_result(vk)


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    longpoll = VkBotLongPoll(vk_session, group_id)
    dialogs = {}

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            sender = vk.users.get(user_id=event.obj.message['from_id'], fields='city')[0]
            message = event.obj.message

            if sender['id'] not in dialogs:
                dialogs[sender['id']] = UserDialog(sender['id'], vk)
            else:
                dialogs[sender['id']].handle_message(message, vk)


if __name__ == '__main__':
    main()
