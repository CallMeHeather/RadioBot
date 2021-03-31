import requests
from bs4 import BeautifulSoup


def joyta_parse(part_name):
    all_results = []

    print(f'Поиск "{part_name}" на joyta.ru...\n')
    request = f'https://cse.google.com/cse/element/v1?rsz=filtered_cse&num=10&hl=ru&source=gcsc&gss=.ru&cselibv=323d4b81541ddb5b&cx=partner-pub-9745464714517329:1789442533&q={part_name}&safe=off&cse_tok=AJvRUv1-ejzm9I1Ub3yl1W_drWBP:1617032136759&sort=&exp=csqr,cc&oq=кт817&gs_l=partner-generic.12...0.0.0.9733.0.0.0.0.0.0.0.0..0.0.csems,nrl=13...0.0....34.partner-generic..0.0.0.&callback=google.search.cse.api4405'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0',
        'Cookie': 'NID=212=puq2oeDsCWnggJOYSz-0uJmyKj6J-nt7I-w_1clN6HMNLYUJJvm_Td6LFxfkgI0KU6M4VA-gT5jbVcJIseaUs9-jfjgK8EKmzQxspG8EP3fjXaNvCUbPwcFCcxgTsqA_2jSDvPSjNS7MMei9cv1Qn3eRhoiD9f995U0jQhbAjym-16C8kD1irf6ck4h9WQ4O8tkRUkOApGKwKKCENWroMWtsiexp3ZgZaM3VwF1QZi_h; SID=7gf4ssXcnonq82ASMqbIHzUoLneYHl2ef_A_Y6tkNasRIcDVUJaSuo-Bz8r9dhgqLEaCyA.; __Secure-3PSID=7gf4ssXcnonq82ASMqbIHzUoLneYHl2ef_A_Y6tkNasRIcDV46PNlKLnRF_Z1zSdMzBjig.; HSID=A_aDe2vi8A9ZPQXSi; SSID=AbuR3tS4w3er3zadt; APISID=MZCeFn34ugWn8UGg/A1L_NcpcWYTjcCosC; SAPISID=HE2BU8AXFYYH7j9q/AklQoGTrlb9C40b-4; __Secure-3PAPISID=HE2BU8AXFYYH7j9q/AklQoGTrlb9C40b-4; SIDCC=AJi4QfEgxq6WoSMA-Oqf7BuaCxFUjdxRkk5g2mTiSaU_QMkqgXsUkkTzDY1_5qcgTxUFZ5i7wa0; __Secure-3PSIDCC=AJi4QfFLY8dPE5Pt5nIG4lO0vKxv4xcVLBCpAEfWBHdsbtg9h6z6AC_AaAAvHTTCQfOkAOZkeQ; 1P_JAR=2021-03-29-15; OGPC=19022519-1:; ANID=AHWqTUn1xxcBF4f0sb59cCWUCCDJOzZk5cVKzEP5PJ0b5H9M5roKKP2PjWEJaFjb; OGP=-19022519:',
        'Host': 'cse.google.com',
        'Accept-Language':'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip,deflate,br',
        'Connection': 'keep-alive',
        'Referer': 'https://cse.google.ru/'
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
