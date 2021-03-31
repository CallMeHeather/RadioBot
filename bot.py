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


def photo_messages(vk, photos, peer_id=0):
    """ Загрузка изображений в сообщения
    :param photos: путь к изображению(ям) или file-like объект(ы)
    :type photos: str or list
    :param peer_id: peer_id беседы
    :type peer_id: int
    """

    url = vk.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']

    with FilesOpener(photos) as photo_files:
        response = requests.post(url, files=photo_files).json()

    return vk.photos.saveMessagesPhoto(photo=response['photo'],
                                       server=response['server'],
                                       hash=response['hash'])


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    group_id = 203010669
    longpoll = VkBotLongPoll(vk_session, group_id)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk = vk_session.get_api()
            sender = vk.users.get(user_id=event.obj.message['from_id'], fields='city')[0]
            text = event.obj.message['text']

            if not text:
                msg = f'Введите название элемента для поиска.'
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=msg,
                                 random_id=random.randint(0, 2 ** 64))
                continue
            if sender['id'] == 229756207:
                msg = f'Кирилл, ты персонально идёшь нахуй.'
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=msg,
                                 random_id=random.randint(0, 2 ** 64))
                continue

            msg = f'Выполняю поиск на radiolibrary.ru...'
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message=msg,
                             random_id=random.randint(0, 2 ** 64))
            results = radiolibrary_parse(text)

            # msg = f'Выполняю поиск на joyta.ru...'
            # vk.messages.send(user_id=event.obj.message['from_id'],
            #                  message=msg,
            #                  random_id=random.randint(0, 2 ** 64))
            # results = joyta_parse(text)

            if not results:
                msg = f'Выполняю поиск на shematok.ru...'
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=msg,
                                 random_id=random.randint(0, 2 ** 64))
                results = shematok_parse(text)

            if not results:
                msg = f'Ничего не найдено.'
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=msg,
                                 random_id=random.randint(0, 2 ** 64))
            else:
                msg = f'Результат поиска\n{results[0]["name"]}\nИсточник: {results[0]["url"]}\n'
                attachment = ''
                if results[0]['images']:
                    photos = []
                    for image in results[0]['images']:
                        photos.append(photo_messages(vk, open(image, 'rb'), 0))
                        os.remove(image)
                    attachment = ','.join([f'photo-{group_id}_{photo[0]["id"]}' for photo in photos])
                if results[0]['text']:
                    msg += '\n' + results[0]['text']

                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=msg,
                                 random_id=random.randint(0, 2 ** 64),
                                 attachment=attachment)



if __name__ == '__main__':
    main()
