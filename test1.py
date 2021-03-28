import requests

part_name = 'кт819'


def rudatasheet_search(name):
    request = f'https://rudatasheet.ru/?s={name}'

    response = requests.get(request)
    print(response)

    with open('test1.html', 'wb') as html_out:
        html_out.write(response.content)
        html_out.close()


def radiolibrary_search(name):
    request = f'https://www.radiolibrary.ru/search.php?name={name}'

    response = requests.get(request)
    print(response)


def eandc_search(name):
    request = f'https://eandc.ru/catalog/?q={name}'

    response = requests.get(request)
    print(response)

    with open('test2.html', 'wb') as html_out:
        html_out.write(response.content)
        html_out.close()


def hardelectronics_search(name):
    request = f'http://hardelectronics.ru/?s={name}'

    response = requests.get(request)
    print(response)

    with open('test_hardelectronics.html', 'wb') as html_out:
        html_out.write(response.content)
        html_out.close()


# rudatasheet_search(part_name)
# radiolibrary_search(part_name)
# eandc_search(part_name)
hardelectronics_search(part_name)
