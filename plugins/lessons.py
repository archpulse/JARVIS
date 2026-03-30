def open_school_lesson(subject_name: str):
    """
    AI DESCRIPTION: Поиск и открытие ссылки на школьный урок.
    Поддерживает сокращения (збд, укр мова, матем).
    Аргумент subject_name — название предмета.
    """
    import webbrowser
    import json

    # База уроков
    lessons = [
        {"subject": "Познание природы Малюта Світлана Олександрівна", "link": "https://us04web.zoom.us/j/72339583058?pwd=M3FCSEVtaC9KOGpLZkY0OXphdkR1UT09"},
        {"subject": "Информатика Сівіцкий Володимир", "link": "https://us04web.zoom.us/j/3606255925?pwd=MDFhb3AwWVpTN2lZWnRvcEJZTWV4UT09"},
        {"subject": "География Марина Василівна Колеснікова", "link": "https://us05web.zoom.us/j/5291127746?pwd=NUIwS3FYOVBBOWF5Z0N0K0drdThmUT09"},
        {"subject": "Музыка Валентина Пожидаева", "link": "https://us04web.zoom.us/j/5261265435?pwd=K0ZkYm1wbGVYeDZhcFMxRkR1TCtlUT09"},
        {"subject": "Английский язык", "link": "https://us04web.zoom.us/j/7187152206?pwd=d0YxWU9QWHdJU1F0NkY2SXA1cGl1Zz09"},
        {"subject": "Математика Олена Кожевникова", "link": "https://us05web.zoom.us/j/82444893091?pwd=P13fANoaXpI2f8yO0pdPcWu81Nc08G.1"},
        {"subject": "ЗБД Искусство Валентина", "link": "https://us05web.zoom.us/j/6746572124?pwd=9nBVqLzOg9Vaa5oavAJfsRjY2wb0IQ.1"},
        {"subject": "Укр мова Алла Свєтлична", "link": "https://us04web.zoom.us/j/9682150103?pwd=Ui9KVnA0clZzNzAycTZSVmtRNjNhdz09"},
        {"subject": "История Мінєєва Євгенія Петрівна", "link": "https://us05web.zoom.us/j/6783267881?pwd=eElxcUVlbmwxaWF3dllPZmJ1VmEwdz09"},
        {"subject": "Физкультура Татьяна (Nataha Kylikovskay)", "link": "https://us05web.zoom.us/j/9990471804?pwd=ZzRFT1dyUysyaFl4RW02VVNFNEg2dz09"},
        {"subject": "Технология Олена Макарова", "link": "https://us05web.zoom.us/j/2960579220?pwd=a2NPMWlzbE1xOGttSEpLSjIzZXNnQT09"},
        {"subject": "Зарубежная литература", "link": "https://us05web.zoom.us/j/5557117207?pwd=zcHoUgGNwCMNqm6AbfaBcasFCDelwE.1"}
    ]

    # Словарь синонимов для сложных названий
    synonyms = {
        "збд": "збд искусство валентина",
        "искусство": "збд искусство валентина",
        "природа": "познание природы",
        "укр": "укр мова",
        "зарубежка": "зарубежная литература",
        "физра": "физкультура"
    }

    # Очищаем запрос: убираем лишние пробелы и переводим в нижний регистр
    raw_query = subject_name.lower().strip().replace(" ", "")

    # Проверяем синонимы
    final_query = raw_query
    for short_name, full_name in synonyms.items():
        if short_name in raw_query:
            final_query = full_name
            break

    # Ищем совпадение
    for lesson in lessons:
        # Убираем пробелы из названия в базе для более точного сравнения
        clean_subject = lesson["subject"].lower().replace(" ", "")
        if final_query.replace(" ", "") in clean_subject:
            webbrowser.open(lesson["link"])
            return f"Урок {lesson['subject']}. Открываю Zoom."

    return f"Миша, я не смог найти урок по запросу '{subject_name}'."

def register_plugin():
    return [open_school_lesson], {"open_school_lesson": open_school_lesson}
