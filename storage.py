from datetime import datetime
import json
from pathlib import Path


def save_raw(records, raw_dir, query):
    #Сохранение сырых данных сбора в JSON: data/raw/vacancies_2026-10-30_1530.json
    path = Path(raw_dir) / f"vacancies_{datetime.now():%Y-%m-%d_%H%M}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        'query': query,
        'collected_at': datetime.now().isoformat(timespec='seconds'),
        'count': len(records),
        'vacancies': records,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def load_raw(path):
    #Чтение сохранённого сбора: (запрос, список сырых вакансий)
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return payload.get('query', ''), payload.get('vacancies', [])
