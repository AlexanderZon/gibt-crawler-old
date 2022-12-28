import mysql.connector
import requests
import re
import html2text
import sys

url = None

for i in range(1, len(sys.argv)):
    x = sys.argv[i].split("=", 1)
    option = x[0]
    value = None
    if(len(x) > 1):
        value = x[1]
    else:
        value = sys.argv[i+1]
        i = i+1
    match(option):
        case '--url':
            url = value
        case _:
            continue

def clean_html(html):
    text = html2text.html2text(html)
    text = text.replace('\n', '')
    text = text.replace('*', '')
    text = text.replace('#', '')
    text = text.replace('_', '')
    return text

def connect():
    conn = mysql.connector.connect(host="gibt_database", user="gibt", password="q1w2e3r4t5", database="gibt")
    cursor = conn.cursor()
    sql = """SELECT * FROM characters"""
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        print(result)
    except mysql.connector.errors.IntegrityError as e:
        print(e.msg)

def getMainTableInfo(html):
    main_table = re.findall(r'<table class="genshin_table main_table">(.+?)</table>', text)
    main_info = {}
    if(len(main_table) > 0):
        main_table_rows = re.findall(r'<tr>(.+?)</tr>', main_table[0])
        for i in range(len(main_table_rows)):
            row = re.findall(r'<td>(.+?)</td>', main_table_rows[i])
            match row[0]:
                case "Rarity":
                    stars = re.findall(r'<img class="cur_icon" src="/img/icons/star_35.webp" />', row[1])     
                    main_info[row[0]] = len(stars)
                case "Weapon":
                    weapon = re.findall(r'<img loading="lazy" class="cur_icon" src="/img/icons/weapon_types/(.+?)_35.webp">&nbsp;', row[1])     
                    if(len(weapon) > 0):
                        main_info[row[0]] = weapon[0].capitalize()
                    else:
                        main_info[row[0]] = 'unknown'
                case "Element":
                    element = re.findall(r'<img loading="lazy" class="cur_icon" src="/img/icons/element/(.+?)_35.webp">&nbsp;', row[1])     
                    if(len(element) > 0):
                        main_info[row[0]] = element[0].capitalize()
                    else:
                        main_info[row[0]] = 'unknown'
                case "Vision (Introduced)":
                    main_info['Vision'] = row[1]
                case "Constellation (Introduced)":
                    main_info['Constellation'] = row[1]
                case "Character Ascension Materials":
                    ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/', row[1]) 
                    main_info['Character Ascension Materials'] = ascension_materials
                case "Skill Ascension Materials":
                    ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/', row[1]) 
                    main_info['Skill Ascension Materials'] = ascension_materials
                case _:
                    main_info[row[0]] = clean_html(row[1])
    return main_info

def getStatsTableInfo(html):
    stat_table = re.findall(r'<table class="genshin_table stat_table">(.+?)</table>', text)
    variable_stat = None
    if(len(stat_table) > 0):
        stat_table_header = re.findall(r'<thead>(.+?)</thead>', stat_table[0])
        if(len(stat_table_header) > 0):
            stat_table_heder_columns = re.findall(r'<td>(.+?)</td>', stat_table_header[0])
            if(len(stat_table_heder_columns) > 6): variable_stat = stat_table_heder_columns[6].replace("Bonus ", "")
        stat_table_content = re.findall(r'<tr>(.+?)</tr>', stat_table[0])
        if(len(stat_table_content) > 0):
            for i in range(1, len(stat_table_content)):
                stat_table_content_columns = re.findall(r'<td>(.+?)</td>', stat_table_content[i])
                stat_table_content_columns = re.findall(r'<td>(.+?)</td>', stat_table_content[i])
                stat_data = {}
                stat_data['level'] = stat_table_content_columns[0]
                stat_data['hp'] = stat_table_content_columns[1]
                stat_data['atk'] = stat_table_content_columns[2]
                stat_data['def'] = stat_table_content_columns[3]
                stat_data['crit_rate'] = stat_table_content_columns[4].replace("%", "")
                stat_data['crit_dmg'] = stat_table_content_columns[5].replace("%", "")
                stat_data['variable_stat'] = variable_stat
                stat_data['variable_stat_value'] = stat_table_content_columns[6].replace("%", "")
                print(stat_data)

r = requests.get(url)
if(r.status_code == 200):
    text = r.text
    getMainTableInfo(text)
    getStatsTableInfo(text)
