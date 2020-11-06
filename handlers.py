import re
re_name = re.compile(r'^[\w\-\s]{3,40}$')
re_email = re.compile(r"\b(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)\b")


def handle_name(text, context):
    match = ('рафаэло','рафа','raffaello','раффа')
    if any(match in text.lower() for match in match):
        return True
    else:
        return False


def handle_email(text, context):
    match = ('чуп','chup')
    if any(match in text.lower() for match in match):
        return True
    else:
        return False

def milka(text, context):
    match = ('milka','милка','шоко')
    if any(match in text.lower() for match in match):
        return True
    else:
        return False

def beer(text, context):
    match = ('медве','мишк','игрушка','подар', 'коро')
    if any(match in text.lower() for match in match):
        return True
    else:
        return False

def more(text, context):
    match = ('фывфволдстрдлсфщыйцу', 'мишвыфпавраповаок', 'игрувапрвпофывашка', 'подапврарваор')
    if any(match in text.lower() for match in match):
        return True
    else:
        return False