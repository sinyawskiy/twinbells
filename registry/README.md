# TwinBells registry

Публичный каталог упражнений, метрик и программ в формате TBF.

```text
registry/
├── exercises/   # *.tbf.json
├── metrics/     # *.tbf.json
├── programs/    # *.tbf.json
└── index.json   # генерируется CI
```

Правила для Pull Request:

- файл должен проходить JSON Schema TBF 1.0;
- `(type, id)` уникален в пределах реестра;
- все зависимости присутствуют в `objects`;
- checksum пересчитан и совпадает;
- личные журналы в реестр не добавляются;
- названия и описания должны быть оригинальными или иметь совместимую лицензию.

GitHub Actions проверяет файлы и генерирует `index.json`, который используют страницы `exercises.html` и `programs.html`.
