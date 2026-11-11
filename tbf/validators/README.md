# TBF validator

Валидатор проверяет документы TwinBells Format 1.0:

- JSON Schema;
- наличие корневого объекта;
- уникальность `(type, id)`;
- ссылки между объектами;
- checksum каждого объекта.

## Установка

```bash
python3 -m pip install -r tbf/validators/requirements.txt
```

## Проверка

```bash
python3 tbf/validators/validate.py tbf/examples
```

Пример успешного вывода:

```text
OK   tbf/examples/metric-weight.json
OK   tbf/examples/exercise-squat.json
OK   tbf/examples/program-strength-5x5.json
OK   tbf/examples/journal-minimal.json
```

## Обновление checksums

Если вы правите пример или добавляете новый объект:

```bash
python3 tbf/validators/validate.py --write-checksums tbf/examples
```

Команда пересчитает `checksum` по смысловой проекции и затем проверит файлы.

## Проверка отдельного файла

```bash
python3 tbf/validators/validate.py path/to/file.tbf.json
```

## Ограничения

Валидатор не загружает внешние URL и не импортирует данные в приложение. Он только проверяет структуру и целостность документа.
