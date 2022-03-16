import sqlite3
import logging
import os
from APIrequests import get_manifest
from readJSON import find_weapon, get_damage_type_link
from helperClasses import Weapon
from customExceptions import NoSuchWeaponError, NoGodRollError


# connect to Manifest.content and query all items named item_name
def query_weapon(item_name: str) -> Weapon:
    if not os.path.isfile(r'resources/Manifest.content'):
        # call API GET request for the game-manifest
        get_manifest()

    con = sqlite3.connect('resources/Manifest.content')
    cur = con.cursor()
    try:
        cur.execute("""
                SELECT
                    json_extract(DestinyInventoryItemDefinition.json, '$')
                FROM
                    DestinyInventoryItemDefinition, json_tree(DestinyInventoryItemDefinition.json, '$')
                WHERE
                    json_tree.key = 'name' AND UPPER(json_tree.value) LIKE UPPER(?)""", (item_name,))
    except sqlite3.Error as e:
        logging.error(f'"{item_name}" query caused {e}')
        raise IOError

    item_list: list[list[str]] = cur.fetchall()
    if len(item_list) == 0:
        logging.warning(f'"{item_name}" query did not yield db result')
        raise NoSuchWeaponError
    con.close()

    return find_weapon(item_list)


# connect to Manifest.content and query the plug set with the given hash
def query_plug_set(plug_hash: int) -> str:
    con = sqlite3.connect('resources/Manifest.content')
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT
                json_extract(DestinyPlugSetDefinition.json, '$')
            FROM
                DestinyPlugSetDefinition, json_tree(DestinyPlugSetDefinition.json, '$')
            WHERE
                json_tree.key = 'hash' AND json_tree.value = ?""", (plug_hash,))
    except sqlite3.Error as e:
        logging.error(f'"{plug_hash}" query caused {e}')
        raise
    plug_set: list[str] = cur.fetchone()
    if len(plug_set) == 0:
        logging.warning(f'"{plug_hash}" query did not yield db result')
    con.close()

    return plug_set[0]


# connect to Manifest.content and query the perk with the given hash
def query_perks(perk_hashes: list[int]) -> list[str]:
    con = sqlite3.connect('resources/Manifest.content')
    cur = con.cursor()
    try:
        if len(perk_hashes) > 1:
            cur.execute("""
                SELECT
                    json_extract(DestinyInventoryItemDefinition.json, '$')
                FROM
                    DestinyInventoryItemDefinition, json_tree(DestinyInventoryItemDefinition.json, '$')
                WHERE
                    json_tree.key = 'hash' AND json_tree.value IN {}""".format(tuple(map(int, perk_hashes))))
        else:
            cur.execute("""
                SELECT
                    json_extract(DestinyInventoryItemDefinition.json, '$')
                FROM
                    DestinyInventoryItemDefinition, json_tree(DestinyInventoryItemDefinition.json, '$')
                WHERE
                    json_tree.key = 'hash' AND json_tree.value = ?""", (perk_hashes[0], ))
    except sqlite3.Error as e:
        logging.error(f'perk query caused {e}')
        raise
    perks: list[str] = cur.fetchall()
    con.close()

    if len(perks) == 0:
        logging.warning(f'"perk query did not yield db result')

    return perks


def query_god_roll(weapon_hash: str) -> str:
    con = sqlite3.connect('resources/CurationRolls.db')
    cur = con.cursor()

    try:
        cur.execute("""
        SELECT
                    json_extract(Weapons.json, '$')
                FROM
                    Weapons, json_tree(Weapons.json, '$')
                WHERE
                    json_tree.key = 'hash' AND json_tree.value = ?""", (str(weapon_hash), ))
    except sqlite3.Error as e:
        logging.error(f'god roll query caused {e}')
        raise

    god_rolls: list[str] = cur.fetchone()

    if god_rolls is None or len(god_rolls[0]) == 0:
        raise NoGodRollError

    return god_rolls[0]


def query_damage_type(dmg_hash: str) -> str:
    con = sqlite3.connect('resources/Manifest.content')
    cur = con.cursor()

    try:
        cur.execute("""
                SELECT
                    json_extract(DestinyDamageTypeDefinition.json, '$')
                FROM
                    DestinyDamageTypeDefinition, json_tree(DestinyDamageTypeDefinition.json, '$')
                WHERE
                    json_tree.key = 'hash' AND json_tree.value = ?""", (dmg_hash,))
    except sqlite3.Error as e:
        logging.error(f'"{dmg_hash}" query caused {e}')
        raise IOError

    dmg_type: list[str] = cur.fetchone()
    if len(dmg_type) == 0:
        logging.warning(f'"{dmg_hash}" did not yield db result')

    return get_damage_type_link(dmg_type[0])
