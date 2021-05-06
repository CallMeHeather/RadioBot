import requests
from bs4 import BeautifulSoup

RESULTS_COUNT = 5


def tec_parse(part_name: str, results_count: int = RESULTS_COUNT):
    all_results = []

    # print(f'Поиск "{part_name}" на tec.org.ru...')

    request = f'http://tec.org.ru/search/?q={part_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    }
    response = requests.get(request, headers=headers)

    text = response.content
    soup = BeautifulSoup(text, features='lxml')
    results = soup.find_all('table', class_='eBlock')
    results = list(filter(lambda x: 'prochee_oborudovanie' not in str(x), results))
    results = list(map(lambda x: x.find('a'), results))
    results = list(map(lambda x: x.get('href'), results))
    # print(f'Найдено {len(results)} результатов.')
    # print(*results, sep='\n')
    # print()

    for i, result_url in enumerate(results[:results_count] if results_count < len(results) else results):
        try:
            # print(f'Страница {i + 1}: '
            #      f'{result_url}')

            response = requests.get(result_url, headers=headers)
            text = response.content
            soup = BeautifulSoup(text, features='lxml')
            name = soup.find('div', class_='eTitle').get_text().split(':')[-1]
            # print(name)

            data = soup.find('td', class_='eText')

            images = data.find_all('img')
            images = list(map(lambda x: x.get('src'), images))
            images = list(map(lambda x: 'http://tec.org.ru' + str(x) if not 'http' in str(x) else str(x), images))
            # print(images)

            text = data.find_all('p')
            text = list(map(lambda x: x.get_text(), text))
            text = '\n'.join(text)

            tables = data.find_all('td', style='TEXT-ALIGN: center; VERTICAL-ALIGN: top')
            for table in tables:
                header = ' '.join(list(map(lambda x: x.get_text().strip(), table.find_all('div')[:-1]))).split(':')[0]
                rows = table.find_all('tr')
                rows = list(map(lambda x: x.get_text().strip().split('\n'), rows))
                rows = list(map(lambda x: ': '.join(x), rows))
                if rows and header:
                    text += '\n\n' + header + '\n\n' + '\n'.join(rows)

            pdf = soup.find_all('a', target='_blank')[-1].get('href')
            if pdf:
                pdf = 'http://tec.org.ru' + pdf
                text += '\n\n' + pdf

            # print(text)
            # print('\n\n')
            if images or text:
                all_results.append({'url': None,
                                    'images': [],
                                    'text': None,
                                    'name': None})
                all_results[-1]['url'] = result_url
                all_results[-1]['name'] = name

                if images:
                    all_results[-1]['images'] = images
                if text:
                    all_results[-1]['text'] = text
        except Exception as exception:
            # print('Ощибка')
            # print(exception)
            # print('\n\n')
            pass

    # print('Поиск завершён.\n')
    return all_results


if __name__ == '__main__':
    part_name = 'гу-50'
    tec_parse(part_name)
