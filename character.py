import mysql.connector
import requests
import re
import html2text
import sys
import json
from urllib.parse import urlparse

url = None
url_domain = None
url_protocol = None
url_base = None

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
            url_domain = urlparse(url).netloc
            url_protocol = urlparse(url).scheme
            url_base = url_protocol+'://'+url_domain
        case _:
            continue

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
    main_table = re.findall(r'<table class="genshin_table main_table">(.+?)</table>', html)
    main_info = {}
    if(len(main_table) > 0):
        main_table_rows = re.findall(r'<tr>(.+?)</tr>', main_table[0])
        for i in range(len(main_table_rows)):
            row = re.findall(r'<td>(.+?)</td>', main_table_rows[i])
            match row[0]:
                case "Rarity":
                    stars = re.findall(r'<img class="cur_icon" src="/img/icons/star_35.webp" />', row[1])     
                    main_info[row[0].lower()] = len(stars)
                case "Weapon":
                    weapon = re.findall(r'<img loading="lazy" class="cur_icon" src="/img/icons/weapon_types/(.+?)_35.webp">&nbsp;', row[1])     
                    if(len(weapon) > 0):
                        main_info['weapon_type'] = weapon[0].capitalize()
                    else:
                        main_info['weapon_type'] = 'unknown'
                case "Element":
                    element = re.findall(r'<img loading="lazy" class="cur_icon" src="/img/icons/element/(.+?)_35.webp">&nbsp;', row[1])     
                    if(len(element) > 0):
                        main_info[row[0].lower()] = element[0].capitalize()
                    else:
                        main_info[row[0].lower()] = 'unknown'
                case "Vision (Introduced)":
                    main_info['Vision'.lower()] = row[1]
                case "Constellation (Introduced)":
                    main_info['Constellation'.lower()] = row[1]
                case "Association":
                    main_info['Association'.lower()] = row[1].capitalize()
                case "Character Ascension Materials":
                    ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/', row[1]) 
                    main_info['ascension_materials'] = ascension_materials
                case "Skill Ascension Materials":
                    ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/', row[1]) 
                    main_info['skill_ascension_materials'] = ascension_materials
                case "Day of Birth":
                    main_info['day_of_birth'] = row[1]
                case "Month of Birth":
                    main_info['month_of_birth'] = row[1]
                case _:
                    if("seuyu" in row[0].lower()):
                        continue
                    main_info[row[0].lower()] = cleanHtml(row[1])
    return main_info

def getStatsTableInfo(html):
    stat_table = re.findall(r'<table class="genshin_table stat_table">(.+?)</table>', html)
    variable_stat = None
    stats = []
    if(len(stat_table) > 0):
        stat_table_header = re.findall(r'<thead>(.+?)</thead>', stat_table[0])
        if(len(stat_table_header) > 0):
            stat_table_heder_columns = re.findall(r'<td>(.+?)</td>', stat_table_header[0])
            if(len(stat_table_heder_columns) > 6): variable_stat = stat_table_heder_columns[6].replace("Bonus ", "")
        stat_table_content = re.findall(r'<tr>(.+?)</tr>', stat_table[0])
        if(len(stat_table_content) > 0):
            stat_table_row_ascension_materials = None
            for i in range(1, len(stat_table_content)):
                stat_table_content_columns = re.findall(r'<td>(.+?)</td>', stat_table_content[i])
                stat_table_content_advanced_columns = re.findall(r'<td rowspan="2" class="hmb">(.+?)</td>', stat_table_content[i])
                stat_data = {}
                stat_data['level'] = stat_table_content_columns[0]
                stat_data['hp'] = stat_table_content_columns[1]
                stat_data['atk'] = stat_table_content_columns[2]
                stat_data['def'] = stat_table_content_columns[3]
                stat_data['crit_rate'] = stat_table_content_columns[4].replace("%", "")
                stat_data['crit_dmg'] = stat_table_content_columns[5].replace("%", "")
                stat_data['variable_stat'] = variable_stat
                stat_data['variable_stat_value'] = stat_table_content_columns[6].replace("%", "")
                stat_data['materials'] = []
                
                if "+" in stat_data['level']:
                    for j in range(len(stat_table_row_ascension_materials)):
                        name = cleanHtml(stat_table_row_ascension_materials[j][0])
                        quantity = parseSufixes(cleanHtml(stat_table_row_ascension_materials[j][2]))
                        stat_data['materials'].append({ 'name': name, 'quantity': quantity})
                stats.append(stat_data)

                if(len(stat_table_content_advanced_columns) > 0):
                    stat_table_row_ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/(.+?).webp"><span>(.+?)</span>', stat_table_content_advanced_columns[0])
    return stats

def getSkillsTableInfo(html):
    asc_table = re.findall(r'<table class="genshin_table asc_table">(.+?)</table>', html)
    skills = []
    if(len(asc_table) > 0):
        asc_table_content = re.findall(r'<tr>(.+?)</tr>', asc_table[0])
        for i in range(2, len(asc_table_content)):
            asc_table_content_columns = re.findall(r'<td>(.+?)</td>', asc_table_content[i])
            asc_table_row_ascension_materials = re.findall(r'<img loading="lazy" alt="(.+?)" src="/img/(.+?).webp"><span>(.+?)</span></div></a>', asc_table_content_columns[1])
            asc_data = {}
            asc_data['level'] = asc_table_content_columns[0]
            asc_data['materials'] = []
            for j in range(len(asc_table_row_ascension_materials)):
                name = cleanHtml(asc_table_row_ascension_materials[j][0])
                quantity = parseSufixes(cleanHtml(asc_table_row_ascension_materials[j][2]))
                asc_data['materials'].append({ 'name': name, 'quantity': quantity})
            skills.append(asc_data)
    return skills

def getFileFullURL(endpoint):
    return url_base+endpoint
            
def getGallerySectionInfo(html):
    gallery_section = re.findall(r'<section id="char_gallery" class="tab-panel tab-panel-1">(.+?)</section>', html)
    gallery = []
    if(len(gallery_section) > 0):
        gallery_section_content = re.findall(r'<div class="gallery_cont">(.+?)</div>', gallery_section[0])
        for i in range(len(gallery_section_content)):
            gallery_element = re.findall(r'<a target="_blank" href="(.+?)"><span class="gallery_cont_span">(.+?)</span>', gallery_section_content[i])
            if(len(gallery_element) > 0 and len(gallery_element[0]) > 1):
                file_url = getFileFullURL(gallery_element[0][0])
                match(gallery_element[0][1]):
                    case 'Icon':
                        gallery.append({ 'type': 'icon', 'url': file_url})
                    case 'Side Icon':
                        gallery.append({ 'type': 'side_icon', 'url': file_url})
                    case 'Gacha Card':
                        gallery.append({ 'type': 'gacha_card', 'url': file_url})
                    case 'Gacha Splash':
                        gallery.append({ 'type': 'gacha_splash', 'url': file_url})
    return gallery
                
    

def requestCharacter():
    r = requests.get(url)
    if(r.status_code == 200):
        text = r.text
        character = getMainTableInfo(text)
        character['character_stats'] = getStatsTableInfo(text)
        character['character_skills'] = getSkillsTableInfo(text)
        character['gallery'] = getGallerySectionInfo(text)
    return character

def saveCharacterJSONFile(character):
    json_file = open(".data/"+character['name']+'.json', "w")
    json_file.write(json.dumps(character))
    json_file.close()

def storeCharacterData(character):
    r = requests.post('http://gibt/api/crawler/characters', json = character)
    if(r.status_code == 200):
        text = r.text
        print('Response: ', text)
    else: 
        print('Error: ', r.status_code, r.text)

def main():
    character = requestCharacter()
    saveCharacterJSONFile(character)
    storeCharacterData(character)
    
main()