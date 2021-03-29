import requests
from bs4 import BeautifulSoup


def joyta_parse(part_name):
    all_results = []

    print(f'Поиск "{part_name}" на joyta.ru...\n')
    request = f'https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=ru&source=gcsc&gss=.ru&cselibv=323d4b81541ddb5b&cx=partner-pub-9745464714517329:1789442533&q={part_name}&safe=off&cse_tok=AJvRUv1-ejzm9I1Ub3yl1W_drWBP:1617032136759&sort=&exp=csqr,cc&oq=кт817&gs_l=partner-generic.12...0.0.0.9733.0.0.0.0.0.0.0.0..0.0.csems,nrl=13...0.0....34.partner-generic..0.0.0.&callback=google.search.cse.api4405'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    }
    response = requests.get(request, headers=headers)
    # print(response)

    a = eval(response.content[34:-2], {'true': True})
    if 'results' in a.keys():
        results = a['results']
    else:
        print('Ничего не найдено.')
        return None
    print(f'Найдено {len(results)} результатов.')

    for i, result in enumerate(results):
        result_url, result_title = result['url'], result['titleNoFormatting']
        print(f'Страница {i + 1}:'
              f' {result_title} - {result_url}')

        response = requests.get(result_url, headers=headers)
        text = response.content
        soup = BeautifulSoup(text, features='lxml')

        name = str(soup.h1)[4:-5]

        images = soup.find('article')
        images = images.find_all('img')
        images = list(filter(lambda x: 'uploads' in str(x), images))
        images = list(map(lambda x: str(x), images))
        images = list(map(lambda x: x[x.find('src="') + 5:], images))
        images = list(map(lambda x: x[:x.find('"')], images))

        data = soup.find_all('p')[2]

        # print(*images, sep='\n')
        if images or text:
            all_results.append({'url': None,
                                'images': [],
                                'text': None,
                                'name': None})
            all_results[-1]['url'] = result_url
            all_results[-1]['name'] = name

            if images:
                for i, url in enumerate(images):
                    response = requests.get(url)
                    with open(f'joyta_imgs/{name}_img{i + 1}.{url[-3:]}', 'wb') as out_img:
                        out_img.write(response.content)
                        print(f'Получено изображение {name}_img{i + 1}.{url[-3:]}')
                        all_results[-1]['images'].append(f'joyta_imgs/{name}_img{i + 1}.{url[-3:]}')
            if text:
                all_results[-1]['text'] = str(data)

            print()
            print('Поиск завершён.\n')
            return all_results


if __name__ == '__main__':
    joyta_parse('кт817')
