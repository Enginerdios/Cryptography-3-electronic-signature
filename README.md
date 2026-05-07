# Электронная подпись ГОСТ Р 34.10-2012

Практическая работа 3 по дисциплине "Криптографические методы защиты информации"

## Что в папке

- `gost_sign.html` - веб-интерфейс (открывается в браузере)
- `gost_sign.py` - консольная версия (Python 3)
- `README.md` - этот файл

## Как запустить GUI

Открыть файл `gost_sign.html` двойным кликом в браузере (Chrome, Firefox, Edge)

## Как запустить консольную версию

Нужен Python 3.6 или новее. Внешние библиотеки не нужны

### Тесты

```
python gost_sign.py test
```

### Генерация ключей

```
python gost_sign.py keygen
```

### Подписать файл

```
python gost_sign.py sign document.txt gost_private.key
```

### Проверить подпись

```
python gost_sign.py verify document.txt document.txt.sig gost_public.key
```
