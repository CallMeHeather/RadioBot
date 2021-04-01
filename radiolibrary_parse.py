import requests
from bs4 import BeautifulSoup


def radiolibrary_parse(part_name: str):
    all_results = []

    print(f'Поиск "{part_name}" на radiolibrary.ru...\n')
    part_name = str(part_name.encode('ANSI')).replace('\\x', '%').upper()[2:-1]

    request = f'https://www.radiolibrary.ru/search.php?name={part_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    }
    response = requests.get(request, headers=headers)

    text = response.content
    soup = BeautifulSoup(text, features='lxml')
    results = soup.find_all('a')
    results = list(filter(lambda x: 'reference' in str(x), results))
    results = list(map(lambda x: str(x)[9:], results))[1:]
    results = list(map(lambda x: x[:x.find('"')], results))
    results = list(map(lambda x: 'https://www.radiolibrary.ru/' + x, results))

    print(f'Найдено {len(results)} результатов.')
    print(*results, sep='\n')
    #print()

    for i, result_url in enumerate(results):
        #print(f'Страница {i + 1}: '
        #      f'{result_url}')

        response = requests.get(result_url, headers=headers)
        text = response.content
        soup = BeautifulSoup(text, features='lxml')
        name = str(soup.h1)[4:-5]
        # print(name)

        data = soup.find_all('ul')
        if len(data) > 1:
            data = data[1]
            data = data.find_all('li')
            data = list(map(lambda x: x.get_text(), data))
        else:
            data = soup.find_all('table')
            data = data[4]
            data = str(data).split('<tr>')[1:]
            data = list(map(lambda x: x.replace('</td><td>', ': '), data))
            data = list(map(lambda x: x[x.find('>') + 1:x.find('<', 2)], data))

        # print(*data, sep='\n')

        images = soup.find_all('img')
        images = list(filter(lambda x: 'reference' in str(x), images))
        images = list(map(lambda x: str(x)[str(x).find('src') + 5:-3], images))
        images = list(map(lambda x: 'https://www.radiolibrary.ru' + x, images))

        if images or text:
            all_results.append({'url': None,
                                'images': [],
                                'text': None,
                                'name': None})
            all_results[-1]['url'] = result_url
            all_results[-1]['name'] = name

            if images:
                for i, url in enumerate(images):
                    response = requests.get(url, headers=headers)
                    with open(f'radiolibrary_imgs/{name}_img{i + 1}.{url[-3:]}', 'wb') as out_img:
                        out_img.write(response.content)
                        #print(f'Получено изображение {name}_img{i + 1}.{url[-3:]}')
                        all_results[-1]['images'].append(f'radiolibrary_imgs/{name}_img{i + 1}.{url[-3:]}')
                        out_img.close()
            if text:
                all_results[-1]['text'] = '\n\n'.join(data)

    #print()
    print('Поиск завершён.\n')
    return all_results


if __name__ == '__main__':
    part_name = 'кт3157'
    radiolibrary_parse(part_name)
