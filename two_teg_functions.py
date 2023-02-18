from add_log_file import add_log
from data.category import Category


def fix_html_problems(text: str):
    list_of_bad_characters = [("&", "&AMP;"), ("<", "&lt;"),
                              (">", "&gt;"), ("\t", "&Tab;"), ("\r", ''), ('\n', '<br>'), ("{", "&lcub;"),
                              ("}", "&rcub;")]
    for ch, rch in list_of_bad_characters:
        text = text.replace(ch, rch)
    return text


# Выделяем теги из текста и преобразуем их в ссылки
def with_cats_show(text):
    res = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '#':
            j = 1
            teg = ["#"]
            while i + j < n:
                if not (text[i + j].isalpha() or text[i + j].isdigit() or text[i + j] in "_."):
                    break
                teg.append(text[i + j])
                j += 1
            if teg:
                res.append(f"<a href='/***/***/год/{''.join(teg)}'>#{''.join(teg)}</a>")
            if i + j < n:
                res.append(text[i + j])
            i += j
        else:
            res.append(text[i])
            i += 1
    return ''.join(res)


def good_show(text):
    return with_cats_show(fix_html_problems(text))


# Проверяем, что у публикации категории в базе данных совпадают с теми, что в её тексте(заголовке, тексте, комментариях...)
def fix_cats(publ, db_sess):
    names = publ.get_needed_cats()
    publ_name = str(type(publ)) + str(publ.id)
    add_log(f"У публикации {publ_name} были теги {[teg.name for teg in publ.categories]}", db_sess=db_sess)
    for name in names:
        if not db_sess.query(Category).filter(Category.name == name).first():
            category = Category()
            category.name = name
            publ.categories.append(category)
        else:
            category = db_sess.query(Category).filter(Category.name == name).first()
            if category not in publ.categories:
                publ.categories.append(category)
    for category in publ.categories:
        if category.name not in names:
            publ.categories.remove(category)
    add_log(f"Теперь у публикации {publ_name} теги {[teg.name for teg in publ.categories]}", db_sess=db_sess)
    db_sess.commit()


def add_links(text, how='normal'):
    if how=='latex':
        return text
    else:
        return text

def fix_tegs(publ, db_sess):
    pass