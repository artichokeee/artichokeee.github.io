# artichokeee.github.io

Сайт Артема Русова на GitHub Pages: кто он, платформа для обучения тестировщиков [Rusau Learn](https://learn.rusau.net) и [тестовые задания для тестировщиков](https://artichokeee.github.io/zadaniya/) страницами.

Страницы заданий собираются из файлов репозитория [test-assignments](https://github.com/artichokeee/test-assignments):

```
pip3 install pypdf                      # для pdf в extract.py; doc и docx читает textutil из macOS
python3 tools/extract.py /tmp/ta-text   # текст из doc, docx, pdf и txt
python3 tools/build.py /tmp/ta-text     # страницы, карта сайта, robots.txt, llms.txt
git push                                # GitHub Pages выкладывает сам
python3 tools/indexnow.py               # сообщить Яндексу и Bing об адресах из карты сайта
```

Почты, логины, пароли и адреса стендов компаний на страницы не попадают (`scrub` в `tools/build.py`).
