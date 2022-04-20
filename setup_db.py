from uuid import uuid4
from re import match

import django
import requests

django.setup()

from app.models import Item, ItemGroup, ProcessItem, Process  # noqa

base_url = 'https://prices.runescape.wiki/api/v1/osrs'
agent = f'agent{uuid4().hex[:4]}'
barrows_regex = '^.*(Karil|Ahrim|Dharok|Verac|Torag|Guthan).+[^0]$'
HEAD, BODY, LEGS, WEAPON = range(4)
types = {HEAD: {'name': 'head', 'cost': 38100},
         BODY: {'name': 'body', 'cost': 57150},
         LEGS: {'name': 'legs', 'cost': 50800},
         WEAPON: {'name': 'weapon', 'cost': 60000}}
barrows = {
    "Ahrim's hood": HEAD, "Ahrim's robeskirt": LEGS,
    "Ahrim's robetop": BODY, "Ahrim's staff": WEAPON,

    "Dharok's greataxe": WEAPON, "Dharok's helm": HEAD,
    "Dharok's platebody": BODY, "Dharok's platelegs": LEGS,

    "Guthan's chainskirt": LEGS, "Guthan's helm": HEAD,
    "Guthan's platebody": BODY, "Guthan's warspear": WEAPON,

    "Karil's coif": HEAD, "Karil's crossbow": WEAPON,
    "Karil's leatherskirt": LEGS, "Karil's leathertop": BODY,

    "Torag's hammers": WEAPON, "Torag's helm": HEAD,
    "Torag's platebody": BODY, "Torag's platelegs": LEGS,

    "Verac's brassard": BODY, "Verac's flail": WEAPON,
    "Verac's helm": HEAD, "Verac's plateskirt": LEGS
}


def main():
    mapping = requests.get(f'{base_url}/mapping',
                           headers={'User-Agent': agent}).json()

    try:
        group = ItemGroup.objects.get(name='barrows')
    except ItemGroup.DoesNotExist:
        group = ItemGroup(name='barrows')
        group.save()

    try:
        gp = Item.objects.get(osrs_id=-1)
    except Item.DoesNotExist:
        gp = Item(osrs_id=-1, name='gold pieces')
        gp.save()

    for item in mapping:
        try:
            _ = Item.objects.get(osrs_id=item['id'])
        except Item.DoesNotExist:
            db_item = Item(osrs_id=item['id'], name=item['name'])
            db_item.save()

    for item in mapping:
        if not match(barrows_regex, item['name']):
            continue
        if item['name'].endswith('armour set'):
            continue

        brother = match(barrows_regex, item['name']).group(1)
        type_ = barrows[item['name']]
        name = types[type_]['name']
        processing_fee = types[type_]['cost']
        db_item = Item.objects.get(osrs_id=item['id'])
        db_item_broken = Item.objects.get(name=f'{db_item.name} 0')
        
        process_name = f'fix {brother} {name}'
        try:
            process = Process.objects.get(name=process_name)
        except Process.DoesNotExist:
            process = Process(
                name=process_name, description='fix barrows armour',
                group=group)
            process.save()

        try:
            process_input1 = ProcessItem.objects.get(
                item=db_item_broken, process=process)
        except ProcessItem.DoesNotExist:
            process_input1 = ProcessItem(
                item=db_item_broken, process=process,
                quantity=1, is_input=True)
            process_input1.save()

        try:
            process_input2 = ProcessItem.objects.get(
                item=gp, process=process)
        except ProcessItem.DoesNotExist:
            process_input2 = ProcessItem(
                item=gp, process=process,
                quantity=processing_fee, is_input=True)
            process_input2.save()

        try:
            process_output = ProcessItem.objects.get(
                item=db_item, process=process)
        except ProcessItem.DoesNotExist:
            process_output = ProcessItem(
                item=db_item, process=process,
                quantity=1, is_input=False)
            process_output.save()

        print(
            f'Created process: {process_name} = '
            f'{process_input1.item.name} x {process_input1.quantity}'
            f' + {process_input2.item.name} x {process_input2.quantity}'
            f' -> {process_output.item.name} x {process_output.quantity}')


if __name__ == '__main__':
    main()
