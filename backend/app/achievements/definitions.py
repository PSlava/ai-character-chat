"""Predefined achievement definitions with i18n labels."""

ACHIEVEMENTS: dict[str, dict] = {
    "first_adventure": {
        "icon": "sword",
        "labels": {
            "en": {"name": "First Steps", "desc": "Start your first adventure"},
            "ru": {"name": "Первые шаги", "desc": "Начни свое первое приключение"},
            "es": {"name": "Primeros pasos", "desc": "Comienza tu primera aventura"},
            "fr": {"name": "Premiers pas", "desc": "Commence ta premiere aventure"},
            "de": {"name": "Erste Schritte", "desc": "Starte dein erstes Abenteuer"},
            "pt": {"name": "Primeiros passos", "desc": "Comece sua primeira aventura"},
            "it": {"name": "Primi passi", "desc": "Inizia la tua prima avventura"},
        },
    },
    "five_adventures": {
        "icon": "map",
        "labels": {
            "en": {"name": "Explorer", "desc": "Start 5 different adventures"},
            "ru": {"name": "Исследователь", "desc": "Начни 5 разных приключений"},
            "es": {"name": "Explorador", "desc": "Comienza 5 aventuras diferentes"},
            "fr": {"name": "Explorateur", "desc": "Commence 5 aventures differentes"},
            "de": {"name": "Entdecker", "desc": "Starte 5 verschiedene Abenteuer"},
            "pt": {"name": "Explorador", "desc": "Comece 5 aventuras diferentes"},
            "it": {"name": "Esploratore", "desc": "Inizia 5 avventure diverse"},
        },
        "target": 5,
    },
    "first_rating": {
        "icon": "star",
        "labels": {
            "en": {"name": "Critic", "desc": "Rate your first adventure"},
            "ru": {"name": "Критик", "desc": "Оцени свое первое приключение"},
            "es": {"name": "Critico", "desc": "Califica tu primera aventura"},
            "fr": {"name": "Critique", "desc": "Note ta premiere aventure"},
            "de": {"name": "Kritiker", "desc": "Bewerte dein erstes Abenteuer"},
            "pt": {"name": "Critico", "desc": "Avalie sua primeira aventura"},
            "it": {"name": "Critico", "desc": "Valuta la tua prima avventura"},
        },
    },
    "five_ratings": {
        "icon": "stars",
        "labels": {
            "en": {"name": "Connoisseur", "desc": "Rate 5 adventures"},
            "ru": {"name": "Знаток", "desc": "Оцени 5 приключений"},
            "es": {"name": "Conocedor", "desc": "Califica 5 aventuras"},
            "fr": {"name": "Connaisseur", "desc": "Note 5 aventures"},
            "de": {"name": "Kenner", "desc": "Bewerte 5 Abenteuer"},
            "pt": {"name": "Conhecedor", "desc": "Avalie 5 aventuras"},
            "it": {"name": "Intenditore", "desc": "Valuta 5 avventure"},
        },
        "target": 5,
    },
    "bookworm": {
        "icon": "book",
        "labels": {
            "en": {"name": "Bookworm", "desc": "Send 100 messages"},
            "ru": {"name": "Книжный червь", "desc": "Отправь 100 сообщений"},
            "es": {"name": "Raton de biblioteca", "desc": "Envia 100 mensajes"},
            "fr": {"name": "Rat de bibliotheque", "desc": "Envoie 100 messages"},
            "de": {"name": "Bucherwurm", "desc": "Sende 100 Nachrichten"},
            "pt": {"name": "Rato de biblioteca", "desc": "Envie 100 mensagens"},
            "it": {"name": "Topo di biblioteca", "desc": "Invia 100 messaggi"},
        },
        "target": 100,
    },
    "storyteller": {
        "icon": "feather",
        "labels": {
            "en": {"name": "Storyteller", "desc": "Send 500 messages"},
            "ru": {"name": "Рассказчик", "desc": "Отправь 500 сообщений"},
            "es": {"name": "Cuentacuentos", "desc": "Envia 500 mensajes"},
            "fr": {"name": "Conteur", "desc": "Envoie 500 messages"},
            "de": {"name": "Geschichtenerzahler", "desc": "Sende 500 Nachrichten"},
            "pt": {"name": "Contador de historias", "desc": "Envie 500 mensagens"},
            "it": {"name": "Narratore", "desc": "Invia 500 messaggi"},
        },
        "target": 500,
    },
    "dice_roller": {
        "icon": "dice",
        "labels": {
            "en": {"name": "Dice Roller", "desc": "Roll dice 20 times"},
            "ru": {"name": "Кубикомет", "desc": "Брось кубики 20 раз"},
            "es": {"name": "Tirador de dados", "desc": "Tira los dados 20 veces"},
            "fr": {"name": "Lanceur de des", "desc": "Lance les des 20 fois"},
            "de": {"name": "Wurfelwerfer", "desc": "Wurfle 20 Mal"},
            "pt": {"name": "Lancador de dados", "desc": "Lance os dados 20 vezes"},
            "it": {"name": "Lanciatore di dadi", "desc": "Lancia i dadi 20 volte"},
        },
        "target": 20,
    },
    "fate_rewriter": {
        "icon": "refresh",
        "labels": {
            "en": {"name": "Fate Rewriter", "desc": "Use Rewrite Fate 5 times"},
            "ru": {"name": "Вершитель судеб", "desc": "Используй Изменить судьбу 5 раз"},
            "es": {"name": "Reescritor del destino", "desc": "Usa Reescribir destino 5 veces"},
            "fr": {"name": "Reecriveur du destin", "desc": "Utilise Reecris le destin 5 fois"},
            "de": {"name": "Schicksalsschreiber", "desc": "Nutze Schicksal umschreiben 5 Mal"},
            "pt": {"name": "Reescritor do destino", "desc": "Use Reescrever destino 5 vezes"},
            "it": {"name": "Riscrittore del destino", "desc": "Usa Riscrivi il destino 5 volte"},
        },
        "target": 5,
    },
}


def get_all_definitions(language: str = "en") -> list[dict]:
    """Return all achievement definitions with labels for the given language."""
    result = []
    for aid, ach in ACHIEVEMENTS.items():
        lang_labels = ach["labels"].get(language, ach["labels"]["en"])
        result.append({
            "id": aid,
            "name": lang_labels["name"],
            "description": lang_labels["desc"],
            "icon": ach.get("icon", "trophy"),
            "target": ach.get("target"),
        })
    return result
