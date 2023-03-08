import requests
import re
import sys
import json
from urllib.parse import urlparse
from utils import cleanHtml, parseSufixes

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

def cleanText(text):
    text = text.replace('"', '')
    return text

def getMainTableInfo(html):
    main_table = re.findall(r'<table class="genshin_table main_table">(.+?)</table>', html)
    main_info = {
        'name': None,
        'rarity': None,
        'description': None,
        'weapon_type': None,
        'ascension_materials': [],
    }
    if(len(main_table) > 0):
        main_table_rows = re.findall(r'<tr>(.+?)</tr>', main_table[0])
        for i in range(len(main_table_rows)):
            row = re.findall(r'<td>(.+?)</td>', main_table_rows[i])
            match row[0]:
                case "Name":
                    main_info['Name'.lower()] = cleanHtml(row[1])
                case "Rarity":
                    stars = re.findall(r'<img alt=Raritystr class=cur_icon src=(.+?)?x53470>', row[1])
                    main_info[row[0].lower()] = len(stars)
                case "Family":
                    weapon_type = re.findall(r'\[(.+?)\]', cleanHtml(row[1]))
                    for j in range(len(weapon_type)):
                        match(weapon_type[j]):
                            case "Sword":
                                main_info['weapon_type'] = 'Sword'
                            case "Claymore":
                                main_info['weapon_type'] = 'Claymore'
                            case "Polearm":
                                main_info['weapon_type'] = 'Polearm'
                            case "Bow":
                                main_info['weapon_type'] = 'Bow'
                            case "Catalyst":
                                main_info['weapon_type'] = 'Catalyst'
                case "Description":
                    main_info['Description'.lower()] = cleanHtml(row[1])
                case "Affix Description":
                    main_info['Description'.lower()] = cleanHtml(row[1])
                case "Weapon Ascension Materials":
                    ascension_materials = re.findall(r'<img loading=lazy alt="(.+?)" src=', row[1]) 
                    main_info['ascension_materials'] = ascension_materials
    return main_info

def getStatsTableInfo(html, weapon):
    stat_table = re.findall(r'<table class="genshin_table stat_table">(.+?)</table>', html)
    variable_stat = None
    stats = []
    if(len(stat_table) > 0):
        stat_table_header = re.findall(r'<thead>(.+?)</thead>', stat_table[0])
        if(len(stat_table_header) > 0):
            stat_table_heder_columns = re.findall(r'<td>(.+?)</td>', stat_table_header[0])
            if(len(stat_table_heder_columns) > 4): 
                variable_stat = stat_table_heder_columns[2].replace("Bonus ", "")
                variable_stat = variable_stat.replace("Bonuse ", "")
        stat_table_content = re.findall(r'<tr>(.+?)</tr>', stat_table[0])
        if(len(stat_table_content) > 0):
            stat_table_row_ascension_materials = None
            for i in range(1, len(stat_table_content)):
                stat_table_content_columns = re.findall(r'<td>(.+?)</td>', stat_table_content[i])
                stat_table_content_advanced_columns = re.findall(r'<td rowspan=2>(.+?)</td>', stat_table_content[i])
                stat_data = {}
                stat_data['level'] = stat_table_content_columns[0]
                stat_data['atk'] = stat_table_content_columns[1]
                if(weapon['rarity'] > 2):
                    stat_data['variable_stat'] = variable_stat
                    stat_data['variable_stat_value'] = stat_table_content_columns[2].replace("%", "")
                stat_data['materials'] = []
                
                if "+" in stat_data['level']:
                    for j in range(len(stat_table_row_ascension_materials)):
                        name = cleanText(cleanHtml(stat_table_row_ascension_materials[j][0]))
                        quantity = parseSufixes(cleanHtml(stat_table_row_ascension_materials[j][4]))
                        stat_data['materials'].append({ 'name': name, 'quantity': quantity})
                stats.append(stat_data)

                if(len(stat_table_content_advanced_columns) > 0):
                    stat_table_row_ascension_materials = re.findall(r'<img loading=lazy alt=(.+?) src=(.+?)?x53470 width=(.+?) height=(.+?)><span>(.+?)</span>', stat_table_content_advanced_columns[0])
    return stats

def getFileFullURL(endpoint):
    return url_base+endpoint

def getGallerySectionInfo(html):
    gallery_section = re.findall(r'<section id="item_gallery" class="tab-panel tab-panel-1">(.+?)</section>', html)
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
                    case 'Awakened Icon':
                        gallery.append({ 'type': 'awakened_icon', 'url': file_url})
                    case 'Gacha Icon':
                        gallery.append({ 'type': 'gacha_card', 'url': file_url})
                    case 'Gacha Card':
                        gallery.append({ 'type': 'gacha_card', 'url': file_url})
    return gallery

def requestWeapon():
    r = requests.get(url)
    if(r.status_code == 200):
        text = r.text
        weapon = getMainTableInfo(text)
        weapon['weapon_stats'] = getStatsTableInfo(text, weapon)
        weapon['gallery'] = getGallerySectionInfo(text)
    return weapon

def saveWeaponrJSONFile(weapon):
    json_file = open('.data/weapons/'+weapon['weapon_type'].lower()+'/'+weapon['name']+'.json', "w")
    json_file.write(json.dumps(weapon))
    json_file.close()

def storeWeaponrData(weapon):
    r = requests.post('http://gibt/api/crawler/weapons', json = weapon)
    if(r.status_code == 200):
        text = r.text
        print('Response: ', r.status_code, text)
    else: 
        print('Error: ', r.status_code, r.text)

def main():
    weapon = requestWeapon()
    saveWeaponrJSONFile(weapon)
    storeWeaponrData(weapon)
    
main()