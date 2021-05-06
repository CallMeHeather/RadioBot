import requests
from bs4 import BeautifulSoup

RESULTS_COUNT = 5


def eandc_parse(part_name: str, results_count: int = RESULTS_COUNT):
    all_results = []

    # print(f'Поиск "{part_name}" на eandc.ru...')
    part_name = str(part_name.encode('cp1251')).replace('\\x', '%').upper()[2:-1]

    request = f'https://eandc.ru/catalog/?q={part_name}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
    }
    response = requests.get(request, headers=headers)

    text = response.content
    soup = BeautifulSoup(text, features='lxml')

    if soup.find(text='Сожалеем, но ничего не найдено.'):
        # print('Найдено 0 результатов. Поиск завершён.')
        return []

    table = soup.find('div', class_='display_table')
    results = table.find_all('a', class_='desc_name')
    results = list(map(lambda x: str(x)[str(x).find('href') + 7:], results))
    results = list(map(lambda x: str(x)[:str(x).find('"')], results))

    # print(f'Найдено {len(results)} результатов.')

    for i, result_url in enumerate(results[:results_count] if results_count < len(results) else results):
        result_url = f'https://eandc.ru/{result_url}'
        # print(f'Страница {i + 1}: '
        #       f'{result_url}')

        response = requests.get(result_url, headers=headers)
        text = response.content
        soup = BeautifulSoup(text, features='lxml')

        name = soup.h1.get_text()

        image = str(soup.find('li', class_='current'))
        image = image[image.find('src') + 6:]
        image = image[:image.find('"')]

        text = soup.find('div', class_='description').get_text()

        pdf_link = str(soup.find('div', class_='pdf'))
        if pdf_link:
            pdf_link = pdf_link[pdf_link.find('href') + 7:]
            pdf_link = pdf_link[:pdf_link.find('"')]
            if pdf_link:
                text += f'\n\nСсылка на pdf с datasheetом: https://eandc.ru/{pdf_link}'

        if image or text:
            all_results.append({'url': None,
                                'images': [],
                                'text': None,
                                'name': None})
            all_results[-1]['url'] = result_url
            all_results[-1]['name'] = name

            if image:
                # response = requests.get(f'https://eandc.ru/{image}', headers=headers)
                # with open(f'data/images/eandc_imgs/{name.replace("/", "_")}_img.{image[-3:]}', 'wb') as out_img:
                #     out_img.write(response.content)
                #     # print(f'Получено изображение {name}_img{i + 1}.{url[-3:]}')
                #     all_results[-1]['images'].append(
                #         f'data/images/eandc_imgs/{name.replace("/", "_")}_img.{image[-3:]}')
                #     out_img.close()
                all_results[-1]["images"].append(f'https://eandc.ru/{image}')
            if text:
                all_results[-1]['text'] = text

    # print()
    # print('Поиск завершён.\n')
    return all_results


if __name__ == '__main__':
    part_name = 'кт501'
    eandc_parse(part_name)
