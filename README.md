# artichokeee.github.io

Сайт Артема Русова на GitHub Pages: кто он, платформа для обучения тестировщиков [Rusau Learn](https://learn.rusau.net) и [тестовые задания для тестировщиков](https://artichokeee.github.io/zadaniya/) страницами.

Страницы заданий собираются из файлов репозитория [test-assignments](https://github.com/artichokeee/test-assignments):

```
python3 tools/extract.py /tmp/ta-text   # текст из doc, docx, pdf и txt
python3 tools/build.py /tmp/ta-text     # страницы, карта сайта, robots.txt, llms.txt
```

Почты, логины, пароли и адреса стендов компаний на страницы не попадают (`scrub` в `tools/build.py`).
