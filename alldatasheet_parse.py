import requests
from bs4 import BeautifulSoup


def alldatasheet_parse(part_name: str, *args, **kwargs):
    all_results = []

    alphabet = {"а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м", "н", "о",
                "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ", "ы", "ь", "э", "ю", "я"}
    if bool(alphabet.intersection(set(part_name.lower()))):
        return None

    print(f'Поиск "{part_name}" на alldatasheet.com...')
    # part_name = str(part_name.encode('cp1251')).replace('\\x', '%').upper()[2:-1]

    request = f'https://www.alldatasheet.com/view_datasheet.jsp?Searchword={part_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    }
    response = requests.get(request, headers=headers)

    text = response.content
    soup = BeautifulSoup(text, features='lxml')

    table_match = soup.find_all('table', class_='main')[5]
    # print(table_match)
    rows = table_match.find_all('tr')[1:]
    # print(*rows, sep='\n----------------------------\n')
    print(f'Найдено {len(rows)} результатов.')

    all_text = ''
    for i, row in enumerate(rows):
        try:
            some_data = row.find_all('td')
            # print(*some_data, sep='\n----------\n')

            name = some_data[1].find('b').get_text()

            result_url = str(some_data[1])[str(some_data[1]).find('"') + 1:]
            result_url = result_url[2:result_url.find('"')]

            text = str(some_data[0].find('img'))[str(some_data[0].find('img')).find('alt') + 5:]
            text = 'Производитель: ' + text[:text.find('"')].strip()
            text += '\nОписание: ' + some_data[3].get_text().strip() + '\n\n'
            text = name + '\n' + result_url + '\n' + text
            all_text += text
        except Exception:
            continue

    all_results.append({'url': None,
                        'images': [],
                        'text': None,
                        'name': None})
    all_results[-1]['url'] = request
    all_results[-1]['name'] = part_name
    all_results[-1]['text'] = all_text

    print('Поиск завершён.\n')
    # print(all_text)
    return all_results


if __name__ == '__main__':
    part_name = 'irf9540'
    alldatasheet_parse(part_name)
