from storage import save_raw, load_raw


def test_save_and_load_raw(tmp_path):
    records = [{'id': '1', 'title': 'Аналитик данных', 'skills': ['SQL', 'Python']}]

    path = save_raw(records, tmp_path / 'raw', 'аналитик данных')

    assert path.exists()
    assert path.parent == tmp_path / 'raw'
    query, loaded = load_raw(path)
    assert query == 'аналитик данных'
    assert loaded == records
