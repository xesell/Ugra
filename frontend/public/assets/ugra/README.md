# Ugra Character Assets

PNG-библиотека персонажа Ugra (снежная барыня) с прозрачным фоном.

## Структура

| Категория | Ключи | Кол-во |
|-----------|-------|--------|
| `hero/` | `desk` | 1 |
| `states/` | greeting, job-search, job-analysis, … | 17 |
| `turns/` | front, three-quarter, side, back | 4 |
| `emotions/` | joy, surprise, sadness, anger, tired, curious, delighted | 7 |

## Использование в React

```tsx
import { UgraCharacter } from "@/components/ugra/UgraCharacter";
import { ugraAsset, ugraPoseForEvent } from "@/assets/ugra";

<UgraCharacter pose="states/greeting" size={120} />
<UgraCharacter pose="VacancyFound" size={64} />  // по eventMap
<img src={ugraAsset("hero/desk")} alt="Ugra" />
```

## Пересборка из исходника

Исходный character sheet: `assets/ugra-character-sheet.png`

```bash
python scripts/split_character_assets.py
```

Скрипт обновит PNG в `frontend/public/assets/ugra/` и `manifest.json`.
