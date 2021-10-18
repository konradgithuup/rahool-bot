import sqlite3
import logging
import os
from APIrequests import get_manifest
from readJSON import process_weapon


# connect to Manifest.content and query all items named item_name
def query_weapon(item_name):
    if not os.path.isfile(r'Manifest.content'):
        # call API GET request for the game-manifest
        get_manifest()

    con = sqlite3.connect('Manifest.content')
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
        raise

    item_list = cur.fetchall()
    if len(item_list) == 0:
        logging.warning(f'"{item_name}" query did not yield db result')
    con.close()

    return process_weapon(item_list)


# connect to Manifest.content and query the plug set with the given hash
def query_plug_set(plug_hash):
    con = sqlite3.connect('Manifest.content')
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
    plug_set = cur.fetchone()
    if len(plug_set) == 0:
        logging.warning(f'"{plug_hash}" query did not yield db result')
    con.close()

    return plug_set[0]


# connect to Manifest.content and query the perk with the given hash
def query_perk(perk_hash, con):
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT
                json_extract(DestinyInventoryItemDefinition.json, '$')
            FROM
                DestinyInventoryItemDefinition, json_tree(DestinyInventoryItemDefinition.json, '$')
            WHERE
                json_tree.key = 'hash' AND json_tree.value = ?""", (perk_hash,))
    except sqlite3.Error as e:
        logging.error(f'"{perk_hash}" query caused {e}')
        raise
    perk = cur.fetchone()
    if len(perk) == 0:
        logging.warning(f'"{perk_hash}" query did not yield db result')

    return perk[0]


# query_weapon('Astral Horizon')
