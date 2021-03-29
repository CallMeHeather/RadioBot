import requests
from bs4 import BeautifulSoup
import re


def shematok_parse(part_name):
    all_results = []

    # Все результаты поиска
    print(f'Поиск "{part_name}" на shematok.ru...\n')

    url = f'https://shematok.ru/?s={part_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    # print('GET', url)
    response = requests.get(url, headers=headers)
    # print(response)

    # with open('shematok.html', 'wb') as output_file:
    #     output_file.write(response.content)
    #     output_file.close()
    #
    # with open('shematok.html', encoding='utf-8') as input_file:
    #     text = input_file.read()

    text = response.content

    # Парсинг
    soup = BeautifulSoup(text, features='lxml')
    results = soup.find_all('div', {'class': "post-card__title"})
    results = list(filter(lambda x: 'драг' not in str(x), results))
    results = list(map(lambda x: str(x)[str(x).find('href='):], results))
    results = list(map(lambda x: x[x.find('"') + 1:x.find('"', x.find('"') + 1)], results))
    print(f'Найдено {len(results)} резултатов.')
    print(*results, sep='\n')
    print()

    # Страница элемента
    for i, url in enumerate(results):
        print(f'Страница №{i + 1} - {url}')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        # print('GET', url)
        response = requests.get(url, headers=headers)
        # print(response)

        # with open('shematok.html', 'wb') as output_file:
        #     output_file.write(response.content)
        #     output_file.close()
        #
        # with open('shematok.html', encoding='utf-8') as input_file:
        #     text = input_file.read()

        text = response.content

        # Парсинг
        soup = BeautifulSoup(text, features='lxml')

        name = str(soup.find('h1'))
        name = name[name.find('>') + 1:name.find('</')]
        print(name)

        article = soup.find('article')
        images = article.find_all('img')
        # images = soup.find_all('img')
        # images = list(filter(lambda x: 'параметры' in str(x), images))
        images = list(map(lambda x: str(x)[str(x).find('https'):], images))
        images = list(map(lambda x: x[:x.find('"')], images))
        images = images[::2]

        data = soup.find_all('li')
        data = list(map(lambda x: str(x), data))
        data = list(filter(lambda x: 'напряж' in str(x.lower()) or 'предел' in str(x.lower()) or 'ток' in str(
            x.lower()) or 'темп' in str(x.lower()) or 'коэфф' in str(x.lower()) or 'мощ' in str(x.lower()),
                           data))
        data = list(map(lambda x: x[x.find('li') + 3:], data))
        data = list(map(lambda x: x[:x.find('li') - 2], data))
        data = list(map(lambda x:
                        x.replace('<sub>', '').replace('</sub>', '').replace('<sup>', '').replace('</sup>', '')
                        .replace('<ma>', '').replace('</ma>', ''),
                        data))
        data = list(map(lambda x: x.capitalize(), data))

        if not images and not data:
            print('На странице ничего не найдено.\n')
            continue
        else:
            all_results.append({'url': None,
                                'images': [],
                                'text': None,
                                'name': None})
            all_results[-1]['url'] = url
            all_results[-1]['name'] = name
            if images:
                for i, url in enumerate(images):
                    # print(f'GET {url}')
                    response = requests.get(url)
                    # print(response)

                    with open(f'shematok_imgs/{name}_img{i + 1}.{url[-3:]}', 'wb') as out_img:
                        out_img.write(response.content)
                        print(f'Получено изображение {name}_img{i + 1}.{url[-3:]}')
                        all_results[-1]['images'].append(f'shematok_imgs/{name}_img{i + 1}.{url[-3:]}')

            if data:
                all_results[-1]['text'] = '\n\n'.join(data)

            print()
            print('Поиск завершён.')
            return all_results

    if not all_results:
        return None


if __name__ == '__main__':
    part_name = 'д2'
    shematok_parse(part_name)
