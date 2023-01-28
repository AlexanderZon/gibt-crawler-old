import html2text

def cleanHtml(html):
    text = html2text.html2text(html)
    text = text.replace('\n', '')
    text = text.replace('*', '')
    text = text.replace('#', '')
    text = text.replace('_', '')
    return text

def parseSufixes(quantity):
    if('K' in quantity):
        quantity = quantity.replace('K', '000')
    return quantity