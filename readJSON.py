import json
import logging

ITEM_TYPE_WEAPON = 3


# generate dictionary from db-json
def deserialize(db_output):
    data_json = db_output
    try:
        return json.loads(data_json)
    except json.JSONDecodeError as e:
        logging.error(f'db output could not be parsed: {e}')


# convert weapon db entry into dictionary
def process_weapon(weapon_db):
    weapon = weapon_db[0]
    weapon_dict = deserialize(weapon[0])

    if weapon_dict['itemType'] != ITEM_TYPE_WEAPON:
        weapon_db.remove(0)
        return process_weapon(weapon_db)

    return weapon_dict


# prepare the weapon dictionary to get plug hashes
async def prepare_weapon(weapon_json):
    from readDB import query_plug_set
    socket_dict = weapon_json['sockets']
    socket_sets = []
    i = 1

    # get plug hash for all columns that store non-intrinsic weapon perks
    while i in socket_dict['socketCategories'][1]['socketIndexes']:
        # socket_sets.append(query_plug_set(socket_dict['socketEntries'][i]['randomizedPlugSetHash']))

        if 'randomizedPlugSetHash' not in socket_dict['socketEntries'][i]:
            i += 1
            continue

        plug_set = socket_dict['socketEntries'][i].get('randomizedPlugSetHash', 0)
        socket_sets.append(query_plug_set(plug_set))
        i += 1

    return await process_plugs(socket_sets)


# retrieve each plug sets perks
async def process_plugs(socket_sets):
    # store all perk hashes
    total_perk_hashes = []
    for plug in socket_sets:
        # stores perk hashes from current column
        column = []
        plug = deserialize(plug)

        # retrieve perk hashes of column i
        for plug_item in plug['reusablePlugItems']:
            if plug_item['currentlyCanRoll'] is True:
                column.append(plug_item['plugItemHash'])
        # print(column)

        total_perk_hashes.append(column)

    return await process_perks(total_perk_hashes)


# retrieve each perk
async def process_perks(perk_hashes):
    from readDB import query_perk
    total_perks = []
    tasks = []

    for column in perk_hashes:
        col = []

        for perk in column:
            db_output = await query_perk(perk)
            col.append(deserialize(db_output)['displayProperties']['name'])

        total_perks.append(col)

    for i in total_perks:
        print(i)
    return total_perks
