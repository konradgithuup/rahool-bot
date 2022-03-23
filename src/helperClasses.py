from __future__ import annotations
import json
import logging
from enum import IntEnum
from typing import Union

ORIGIN_TRAIT_HASH = 3993098925
ENHANCED_PERK = 'Enhanced Trait'


class GameModeFlag(IntEnum):
    empty = 0
    pve = 1
    pvp = 2
    both = 3


class ManifestData:
    # generate dictionary from db-json
    def deserialize(self, json_string: str) -> dict:
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logging.error(f'db output could not be parsed: {e}')


class Weapon(ManifestData):
    item_type: int
    name: str
    rarity: str
    collectible_hash: str
    hash: str
    screenshot_url: str
    socket_set: SocketSet
    type: str
    damage_type: str

    # weapon constructor
    def __init__(self, json_string):
        # this is the part where I regret using Python
        weapon = self.deserialize(json_string=json_string)

        self.item_type = weapon['itemType']
        self.type = weapon['itemTypeAndTierDisplayName']
        self.name = weapon['displayProperties']['name']
        self.collectible_hash = str(weapon['collectibleHash'])
        self.hash = str(weapon['hash'])
        self.screenshot_url = weapon['screenshot']
        self.socket_set = SocketSet(self.get_socket_set())

    def get_item_type(self) -> int:
        return self.item_type

    def get_name(self) -> str:
        return self.name

    def get_rarity(self) -> str:
        return self.type.split(" ")[0]

    def get_collectible_hash(self) -> str:
        return self.collectible_hash

    def get_hash(self) -> str:
        return self.hash

    def get_screenshot(self) -> str:
        return self.screenshot_url

    def get_socket_set(self):
        return self.socket_set

    def get_type(self) -> str:
        return self.type

    def get_damage_type(self) -> str:
        return self.damage_type

    def has_random_roll(self) -> bool:
        for i in range(self.socket_set.get_size()):
            if self.socket_set.is_random_socket(i):
                return True
        return False


class SocketSet:
    sockets: list[dict[str, Union[list[int], str]]]
    perk_socket_indices: list[int]

    def __init__(self, sockets):
        socket_set = sockets

        self.sockets = socket_set['socketEntries']
        self.perk_socket_indices = socket_set['socketCategories'][1]['socketIndexes']

    def get_size(self) -> int:
        return len(self.sockets)

    def is_origin_socket(self, index: int) -> bool:
        if self.sockets[index]['socketTypeHash'] == ORIGIN_TRAIT_HASH:
            return True
        return False

    def is_random_socket(self, index: int) -> bool:
        if 'randomizedPlugSetHash' in self.sockets[index]:
            return True
        return False

    def get_perk_socket_indices(self):
        return self.perk_socket_indices

    def get_plug_set_hash(self, index: int) -> int:
        set_type: str
        if 'randomizedPlugSetHash' in self.sockets[index]:
            return self.sockets[index].get('randomizedPlugSetHash', 0)
        return self.sockets[index].get('reusablePlugSetHash', 0)


class PlugSet(ManifestData):
    perk_hashes: list[int]

    def __init__(self, json_string: str):
        plug_set = self.deserialize(json_string=json_string)
        self.perk_hashes = []

        for plug_item in plug_set['reusablePlugItems']:
            if plug_item['currentlyCanRoll'] is True:
                self.perk_hashes.append(plug_item['plugItemHash'])

    def get_perk_hashes(self) -> list[int]:
        return self.perk_hashes


class PerkIterator:
    perk_set: PerkColumn
    index: int

    def __init__(self, perk_set: PerkColumn):
        self.perk_set = perk_set
        self.index = 0

    def __next__(self):
        if self.index < (len(self.perk_set)):
            result = self.perk_set[self.index]
            self.index += 1
            return result

        raise StopIteration


class PerkColumn:
    normal_perks: list[Perk]
    enhanced_perks: list[Perk]

    def __init__(self):
        self.normal_perks = []
        self.enhanced_perks = []

    def __len__(self):
        return len(self.normal_perks)

    def __iter__(self):
        return PerkIterator(self)

    def __getitem__(self, item):
        return self.normal_perks[item]

    def add_perk(self, json_string):
        perk = Perk(json_string)
        if perk.is_enhanced():
            self.enhanced_perks.append(perk)
            return
        self.normal_perks.append(perk)

    def has_enhanced_perk(self) -> bool:
        return len(self.enhanced_perks) > 0


class Perk(ManifestData):
    hash: str
    name: str
    icon_url: str
    item_type: str
    curation: GameModeFlag

    def __init__(self, database_result):
        perk = self.deserialize(database_result)

        self.curation = GameModeFlag.empty
        self.hash = str(perk['hash'])
        self.name = perk['displayProperties']['name']
        self.icon_url = perk['displayProperties']['icon']
        self.item_type = perk['itemTypeDisplayName']

    def set_curation(self, gamemode: GameModeFlag):
        self.curation += gamemode

    def get_hash(self) -> str:
        return self.hash

    def get_name(self) -> str:
        return self.name

    def get_icon_url(self) -> str:
        return self.icon_url

    def is_enhanced(self) -> bool:
        return self.item_type == ENHANCED_PERK


class DamageType(ManifestData):
    icon_url: str

    def __init__(self, database_result):
        damage_type = self.deserialize(json_string=database_result)
        self.icon_url = damage_type['displayProperties']['icon']

    def get_icon(self) -> str:
        return self.icon_url


class GodRollContainer(ManifestData):
    pvp_rolls: list[list[int]]
    pve_rolls: list[list[int]]
    weapon_hash: str

    def __init__(self, database_result):
        god_rolls = self.deserialize(json_string=database_result)

        self.pvp_rolls = god_rolls['PVP']
        self.pve_rolls = god_rolls['PVE']
        self.weapon_hash = str(god_rolls['hash'])

    def apply_to_perk_set(self, perk_set: list[PerkColumn]):
        iter_len: int = len(self.pvp_rolls)
        if len(perk_set) < iter_len:
            iter_len = len(perk_set)

        for i in range(iter_len):
            for perk in perk_set[i]:
                if perk.get_hash() in self.pvp_rolls[i]:
                    perk.set_curation(GameModeFlag.pvp)
                if perk.get_hash() in self.pve_rolls[i]:
                    perk.set_curation(GameModeFlag.pve)
