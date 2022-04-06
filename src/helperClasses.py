from __future__ import annotations
import json
import logging
from enum import IntEnum
from typing import Union

ORIGIN_TRAIT_HASH = 3993098925
ENHANCED_PERK = 'Enhanced Trait'


class GameModeFlag(IntEnum):
    """
    Represents the states of a weapon's possible curation status.
    """
    empty = 0
    pve = 1
    pvp = 2
    both = 3


class ManifestData:
    """
    wraps deserialization method to generate dictionary from a json-formatted string
    """
    # generate dictionary from db-json
    def deserialize(self, json_string: str) -> dict:
        """
        generates a dictionary from a json-formatted string

        :param json_string: str
        :return: dictionary containing key value pairs stored in the json
        """
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logging.error(f'db output could not be parsed: {e}')


class Weapon(ManifestData):
    """
    Contains relevant information of a weapon's InventoryItemDefinition's database entry.
    """
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
    def __init__(self, json_string: str):
        """
        :param json_string: json-formatted output of Destiny 2 database
        """
        weapon = self.deserialize(json_string=json_string)

        self.item_type = weapon['itemType']
        self.type = weapon['itemTypeAndTierDisplayName']
        self.name = weapon['displayProperties']['name']
        self.collectible_hash = str(weapon['collectibleHash'])
        self.hash = str(weapon['hash'])
        self.screenshot_url = weapon['screenshot']
        self.damage_type = weapon['defaultDamageTypeHash']
        self.socket_set = SocketSet(weapon['sockets'])

    def get_item_type(self) -> int:
        """
        :return: type of item encoded as Integer value
        """
        return self.item_type

    def get_name(self) -> str:
        """
        :return: weapon name as String value
        """
        return self.name

    def get_rarity(self) -> str:
        """
        :return: weapon rarity as :class: 'str' value
        """
        return self.type.split(" ")[0]

    def get_collectible_hash(self) -> str:
        """
        :return: hash of the weapon's CollectibleItemDefinition db-entry as String
        """
        return self.collectible_hash

    def get_hash(self) -> str:
        """
        :return: hash of the weapon's InventoryItemDefinition db-entry as String
        """
        return self.hash

    def get_screenshot(self) -> str:
        """
        gets weapon screenshot url; requires bungie.net base url

        :return: url for weapon jpg screenshot image as String
        """
        return self.screenshot_url

    def get_socket_set(self) -> SocketSet:
        """
        gets 'socket' subset of the weapon stored as SocketSet object

        :return: weapon specific instance of SocketSet
        """
        return self.socket_set

    def get_type(self) -> str:
        """
        gets weapon type and rarity as String

        :return: weapon type and rarity
        """
        return self.type

    def get_damage_type(self) -> str:
        """
        :return: weapon damage type hash as String. References DestinyDamageTypeDefinition db-entry
        """
        return self.damage_type

    def has_random_roll(self) -> bool:
        """
        iterates over all sockets to check for random Perks

        :return: True if at least 1 socket contains random Perks. False if no socket contains random perks.
        """
        for i in range(self.socket_set.get_size()):
            if self.socket_set.is_random_socket(i):
                return True
        return False


class SocketSet:
    """
    Subset of Weapon which represents values stored under an items 'sockets' key
    """
    sockets: list[dict[str, Union[list[int], str]]]
    perk_socket_indices: list[int]

    def __init__(self, sockets):
        """
        :param sockets: value of a weapon's 'sockets' key
        """
        socket_set = sockets

        self.sockets = socket_set['socketEntries']
        self.perk_socket_indices = socket_set['socketCategories'][1]['socketIndexes']

    def get_size(self) -> int:
        """
        :return: size of socket list
        """
        return len(self.sockets)

    def is_origin_socket(self, index: int) -> bool:
        """
        :param index: index of the socket entry
        :return: True if the socket contains at least one origin trait.
        False if socket does not contain any origin traits
        """
        if self.sockets[index]['socketTypeHash'] == ORIGIN_TRAIT_HASH:
            return True
        return False

    def is_random_socket(self, index: int) -> bool:
        """
        :param index: index of the socket entry
        :return: True if socket contains a random perk set, false if it doesn't
        """
        if 'randomizedPlugSetHash' in self.sockets[index]:
            return True
        return False

    def get_perk_socket_indices(self) -> list[int]:
        """
        :return: list of all sockets containing a static or a random perk set
        """
        return self.perk_socket_indices

    def get_plug_set_hash(self, index: int) -> int:
        """
        :param index: index of the socket entry
        :return: hash value of the static or random plug set stored in queried socket entry
        """
        set_type: str
        if 'randomizedPlugSetHash' in self.sockets[index]:
            return self.sockets[index].get('randomizedPlugSetHash', 0)
        return self.sockets[index].get('reusablePlugSetHash', 0)


class PlugSet(ManifestData):
    """
    Contains relevant information of a plug set's PlugSetDefinition's database entry.
    """
    perk_hashes: list[int]

    def __init__(self, json_string: str):
        """
        :param json_string: json-formatted output of Destiny 2 database
        """
        plug_set = self.deserialize(json_string=json_string)
        self.perk_hashes = []

        for plug_item in plug_set['reusablePlugItems']:
            if plug_item['currentlyCanRoll'] is True:
                self.perk_hashes.append(plug_item['plugItemHash'])

    def get_perk_hashes(self) -> list[int]:
        """
        :return: hashes of all perks contained in plug set
        """
        return self.perk_hashes


class PerkIterator:
    """
    Iterator for lists of Perk objects
    """
    perk_set: PerkColumn
    index: int

    def __init__(self, perk_set: PerkColumn):
        """
        :param perk_set: perk column over which to iterate
        """
        self.perk_set = perk_set
        self.index = 0

    def __next__(self):
        if self.index < (len(self.perk_set)):
            result = self.perk_set[self.index]
            self.index += 1
            return result

        raise StopIteration


class PerkColumn:
    """
    Container for all Perks of a column.
    """
    normal_perks: list[Perk]
    enhanced_perks: list[Perk]

    def __init__(self):
        self.normal_perks = []
        self.enhanced_perks = []

    def __len__(self):
        """
        :return: length of the 'normal_perks' list
        """
        return len(self.normal_perks)

    def __iter__(self):
        return PerkIterator(self)

    def __getitem__(self, item):
        return self.normal_perks[item]

    def add_perk(self, json_string):
        """
        :param json_string: json-formatted perk query output of Destiny 2 database
        """
        perk = Perk(json_string)
        if perk.is_enhanced():
            self.enhanced_perks.append(perk)
            return
        self.normal_perks.append(perk)

    def has_enhanced_perk(self) -> bool:
        """
        :return: True if the corresponding weapon has at least 1 enhanced perk. False if not.
        """
        return len(self.enhanced_perks) > 0


class Perk(ManifestData):
    """
    Contains relevant information of a perks InventoryItemDefiniton's database entry.
    """
    hash: str
    name: str
    icon_url: str
    item_type: str
    curation: GameModeFlag

    def __init__(self, database_result):
        """
        :param database_result: json-formatted perk query output of Destiny 2 database
        """
        perk = self.deserialize(database_result)

        self.curation = GameModeFlag.empty
        self.hash = str(perk['hash'])
        self.name = perk['displayProperties']['name']
        self.icon_url = perk['displayProperties']['icon']
        self.item_type = perk['itemTypeDisplayName']

    def set_curation(self, gamemode: GameModeFlag):
        """
        Updates curation to either pvp, pve or both.

        :param gamemode: game mode for which the perk was curated
        """
        self.curation += gamemode

    def get_hash(self) -> str:
        """
        :return: hash value as String
        """
        return self.hash

    def get_name(self) -> str:
        """
        :return: perk name as String
        """
        return self.name

    def get_icon_url(self) -> str:
        """
        gets perk icon url; requires bungie.net base url

        :return: url for perk icon jpg image as String
        """
        return self.icon_url

    def is_enhanced(self) -> bool:
        """
        :return: True if perk is enhanced, False if it is not
        """
        return self.item_type == ENHANCED_PERK


class DamageType(ManifestData):
    """
    Contains relevant information of damage types DamageTypeDefinition's database entry.
    """
    icon_url: str

    def __init__(self, database_result):
        damage_type = self.deserialize(json_string=database_result)
        self.icon_url = damage_type['displayProperties']['icon']

    def get_icon(self) -> str:
        """
        gets damage type icon url; requires bungie.net base url

        :return: url for damage type icon image as String
        """
        return self.icon_url


class GodRollContainer(ManifestData):
    """Contains a weapon's pvp and pve recommendations"""
    pvp_rolls: list[list[int]]
    pve_rolls: list[list[int]]
    weapon_hash: str

    def __init__(self, database_result):
        god_rolls = self.deserialize(json_string=database_result)

        self.pvp_rolls = god_rolls['PVP']
        self.pve_rolls = god_rolls['PVE']
        self.weapon_hash = str(god_rolls['hash'])

    def apply_to_perk_set(self, perk_set: list[PerkColumn]):
        """
        Takes a weapon's Perks and updates their curation status according to the information
        stored in the GodRollContainer in O(n^2)

        :param perk_set: weapon's Perks
        """
        iter_len: int = len(self.pvp_rolls)
        if len(perk_set) < iter_len:
            iter_len = len(perk_set)

        for i in range(iter_len):
            for perk in perk_set[i]:
                if perk.get_hash() in self.pvp_rolls[i]:
                    perk.set_curation(GameModeFlag.pvp)
                if perk.get_hash() in self.pve_rolls[i]:
                    perk.set_curation(GameModeFlag.pve)
