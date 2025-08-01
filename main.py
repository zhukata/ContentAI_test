import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv('URL')
LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')
DBNAME = os.getenv('DBNAME')
DBTABLE = os.getenv('DBTABLE')

session = requests.Session()

login_page = session.get(URL)
login_page.raise_for_status()

soup = BeautifulSoup(login_page.text, "html.parser")
form = soup.find("form", {"id": "login_form"})
hidden_inputs = form.find_all("input", {"type": "hidden"})

payload = {
    "pma_username": LOGIN,
    "pma_password": PASSWORD,
}

for input_tag in hidden_inputs:
    name = input_tag.get("name")
    value = input_tag.get("value", "")
    if name:
        payload[name] = value


login_resp = session.post(URL, data=payload)
login_resp.raise_for_status()


if 'name="login_form"' in login_resp.text or "Access denied" in login_resp.text:
    print("Авторизация не удалась")
    exit(1)

print("Авторизация успешна")


soup = BeautifulSoup(login_resp.text, "html.parser")
token = None
for input_tag in soup.find_all("input", {"type": "hidden"}):
    if input_tag.get("name") == "token":
        token = input_tag.get("value")
        break

if not token:
    print("Не найден токен авторизации")
    exit(1)

params = {
    "route": "/sql",
    "db": "testDB",
    "table": "users",
    "server": 1,
    "ajax_request": "true",
    "token": token,
}

browse_resp = session.get(URL, params=params,
                          headers={"X-Requested-With": "XMLHttpRequest"})
browse_resp.raise_for_status()

data = browse_resp.json()
html_fragment = data.get("message", "")
if not html_fragment:
    print("В ответе нет HTML-фрагмента в поле message")
    exit(1)

soup = BeautifulSoup(html_fragment, "html.parser")
table = soup.find("table", class_="table_results")
if not table:
    print("Таблица не найдена")
    exit(1)

print("Таблица users:")

for tr in table.find("tbody").find_all("tr"):
    cells = [
        td.get_text(strip=True)
        for td in tr.find_all("td", class_="data")
    ]
    if cells:
        print(cells)
