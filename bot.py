import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import os
import requests
from vk_api.upload import FilesOpener

from shematok_parse import shematok_parse
from joyta_parse import joyta_parse
from radiolibrary_parse import radiolibrary_parse

TOKEN = 'd034eacf55b685f35ec2b825304d1e705080c129359983d40ce469629f66c0eb20eaef6833987876315ba'
group_id = 203010669

parsers = {1: (1, radiolibrary_parse, 'radiolibrary.ru'),
           2: (2, shematok_parse, 'shematok.ru')}


def photo_messages(vk, photo, peer_id=0):
    """ Загрузка изображений в сообщения
    :param photos: путь к изображению(ям) или file-like объект(ы)
    :type photos: str or list
    :param peer_id: peer_id беседы
    :type peer_id: int
    """

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
                         message=f'''Привет.
                                     Я - радиобот, могу искать характеристики электронных компонентов по их названиям.
                                     На данный момент в базе {len(parsers)} сайтов.
                                     Отправьте название для поиска.

                                     BETA 0.0.0.0.0000001 НИЧЁ НЕ РАБОТАЕТ НОРМАЛЬНО''',
                         random_id=random.randint(0, 2 ** 64))

    def reset_search(self):
        self.state = 'wait_for_request'
        self.current_parser = 1
        self.current_result = 0

    def parse(self, vk):
        self.results = []
        _, parser, site_url = parsers.get(self.current_parser)
        vk.messages.send(user_id=self.user_id,
                         message=f'Поиск  "{self.search_text}"  на {site_url}...',
                         random_id=random.randint(0, 2 ** 64))
        self.results = parser(self.search_text)

        # Если результатов нет, то идёт на другой сайт
        if not self.results:
            vk.messages.send(user_id=self.user_id,
                             message=f'''На сайте ничего не найдено.''',
                             random_id=random.randint(0, 2 ** 64))
            return False

        return True

    def send_result(self, vk):
        if self.results:
            result = self.results.pop(0)
        else:
            return False

        msg = f'''Результат поиска: {result["name"]}
                  Источник: {result["url"]}\n'''
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

        vk.messages.send(user_id=self.user_id,
                         message=msg,
                         random_id=random.randint(0, 2 ** 64),
                         attachment=attachment)

        # Просит ответа у пользователя
        vk.messages.send(user_id=self.user_id,
                         message=f'''1 - Следующий результат
                                     2 - Продолжить поиск на другом сайте
                                     3 - Закончить поиск по запросу  "{self.search_text}"''',
                         random_id=random.randint(0, 2 ** 64))
        self.state = 'wait_for_response'
        return True

    def handle_message(self, text, vk):
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
                    break

            if self.results:
                self.send_result(vk)

        elif self.state == 'wait_for_response':
            if text == '3':
                vk.messages.send(user_id=self.user_id,
                                 message=f'''Поиск по запросу  "{self.search_text}"  завершён.
                                             Введите название элемента, чтобы начать поиск.''',
                                 random_id=random.randint(0, 2 ** 64))
                self.reset_search()
            elif text == '1':
                a = self.send_result(vk)
                if not a:
                    vk.messages.send(user_id=self.user_id,
                                     message=f'''Результаты кончились.
                                                 2 - Продолжить поиск на другом сайте
                                                 3 - Закончить поиск по запросу  "{self.search_text}"''',
                                     random_id=random.randint(0, 2 ** 64))
            elif text == '2':
                self.current_parser += 1
                if self.current_parser > len(parsers):
                    vk.messages.send(user_id=self.user_id,
                                     message=f'''Сайты кончились.
                                                 Поиск по запросу  "{self.search_text}"  завершён.''',
                                     random_id=random.randint(0, 2 ** 64))
                    self.reset_search()
                else:
                    while not self.parse(vk):
                        self.current_parser += 1
                        if self.current_parser > len(parsers):
                            vk.messages.send(user_id=self.user_id,
                                             message=f'''Сайты кончились.
                                                         Поиск по запросу  "{self.search_text}"  завершён.''',
                                             random_id=random.randint(0, 2 ** 64))
                            self.reset_search()

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
            text = event.obj.message['text']

            if sender['id'] not in dialogs:
                dialogs[sender['id']] = UserDialog(sender['id'], vk)
            else:
                dialogs[sender['id']].handle_message(text, vk)

            # if not text:
            #     msg = f'Введите название элемента для поиска.'
            #     vk.messages.send(user_id=event.obj.message['from_id'],
            #                      message=msg,
            #                      random_id=random.randint(0, 2 ** 64))
            #     continue
            # if sender['id'] == 229756207:
            #     msg = f'Кирилл, ты персонально идёшь нахуй.'
            #     vk.messages.send(user_id=event.obj.message['from_id'],
            #                      message=msg,
            #                      random_id=random.randint(0, 2 ** 64))
            #     continue

            # msg = f'Выполняю поиск на radiolibrary.ru...'
            # vk.messages.send(user_id=event.obj.message['from_id'],
            #                  message=msg,
            #                  random_id=random.randint(0, 2 ** 64))
            # results = radiolibrary_parse(text)

            # msg = f'Выполняю поиск на joyta.ru...'
            # vk.messages.send(user_id=event.obj.message['from_id'],
            #                  message=msg,
            #                  random_id=random.randint(0, 2 ** 64))
            # results = joyta_parse(text)

            # if not results:
            #     msg = f'Выполняю поиск на shematok.ru...'
            #     vk.messages.send(user_id=event.obj.message['from_id'],
            #                      message=msg,
            #                      random_id=random.randint(0, 2 ** 64))
            #     results = shematok_parse(text)
            #
            # if not results:
            #     msg = f'Ничего не найдено.'
            #     vk.messages.send(user_id=event.obj.message['from_id'],
            #                      message=msg,
            #                      random_id=random.randint(0, 2 ** 64))
            #
            # else:
            #     msg = f'Результат поиска\n{results[0]["name"]}\nИсточник: {results[0]["url"]}\n'
            #     attachment = ''
            #     if results[0]['images']:
            #         photos = []
            #         for image in results[0]['images']:
            #             with open(image, 'rb') as img:
            #                 a = photo_messages(vk, img, 0)
            #                 if a:
            #                     photos.append(a)
            #                 img.close()
            #             os.remove(image)
            #         attachment = ','.join([f'photo-{group_id}_{photo[0]["id"]}' for photo in photos])
            #     if results[0]['text']:
            #         msg += '\n' + results[0]['text']
            #
            #     vk.messages.send(user_id=event.obj.message['from_id'],
            #                      message=msg,
            #                      random_id=random.randint(0, 2 ** 64),
            #                      attachment=attachment)


if __name__ == '__main__':
    main()
