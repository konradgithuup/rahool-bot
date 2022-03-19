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
    weapon: dict[str,
                 Union[int,
                       str,
                       dict[str,
                            dict[Union[str,
                                       int,
                                       dict[str,
                                            int]
                                       ],
                                 dict[str,
                                      Union[list[int],
                                            str]
                                      ]
                                 ]
                            ]
                       ]
                 ]

    # weapon constructor
    def __init__(self, json_string):
        # this is the part where I regret using Python
        self.weapon = self.deserialize(json_string=json_string)

    def get_item_type(self) -> int:
        return self.weapon['itemType']

    def get_name(self) -> str:
        return self.weapon['displayProperties']['name']

    def get_rarity(self) -> str:
        return self.weapon['itemTypeAndTierDisplayName'].split(" ")[0]

    def get_collectible_hash(self) -> str:
        return self.weapon['collectibleHash']

    def get_hash(self) -> str:
        return self.weapon['hash']

    def get_screenshot(self) -> str:
        return self.weapon['screenshot']

    def get_socket_set(self):
        return self.weapon['sockets']

    def get_type(self) -> str:
        return self.weapon['itemTypeAndTierDisplayName']

    def get_description(self) -> str:
        return self.weapon['flavorText']

    def get_damage_type(self) -> str:
        return self.weapon['defaultDamageTypeHash']

    def has_random_roll(self) -> bool:
        for socket in self.weapon['sockets']['socketEntries']:
            if 'randomizedPlugSetHash' in socket:
                return True
        return False


class SocketSet:
    socket_set: dict[str, dict[Union[str, int], dict[str, Union[list[int], str]]]]

    def __init__(self, weapon: Weapon):
        self.socket_set = weapon.get_socket_set()

    def get_socket_perk_indices(self) -> list[int]:
        return self.socket_set['socketCategories'][1]['socketIndexes']

    def is_origin_socket(self, index: int) -> bool:
        if self.socket_set['socketEntries'][index]['socketTypeHash'] == ORIGIN_TRAIT_HASH:
            return True
        return False

    def is_random_socket(self, index: int) -> bool:
        if 'randomizedPlugSetHash' in self.socket_set['socketEntries'][index]:
            return True

        return False

    def get_perk_sockets(self):
        return self.socket_set['socketCategories'][1]['socketIndexes']

    def get_plug_set_hash(self, index: int) -> int:
        set_type: str
        if 'randomizedPlugSetHash' in self.socket_set['socketEntries'][index]:
            return self.socket_set['socketEntries'][index].get('randomizedPlugSetHash', 0)
        return self.socket_set['socketEntries'][index].get('reusablePlugSetHash', 0)


class PlugSet(ManifestData):
    plug_set: dict[str, Union[int, dict[int, Union[str, bool]]]]

    def __init__(self, json_string: str):
        self.plug_set = self.deserialize(json_string=json_string)

    def get_perk_hashes(self) -> list[int]:
        column: list[int] = []

        for plug_item in self.plug_set['reusablePlugItems']:
            if plug_item['currentlyCanRoll'] is True:
                column.append(plug_item['plugItemHash'])

        return column


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
    perk: dict[str, Union[str, dict[str, str]]]
    curation: GameModeFlag

    def __init__(self, json_string):
        self.perk = self.deserialize(json_string)
        self.curation = GameModeFlag(GameModeFlag.empty)

    def set_curation(self, god_rolls: GodRollContainer):
        if self.perk['hash'] in god_rolls.get_rolls('PVP'):
            self.curation += GameModeFlag.pvp
        if self.perk['hash'] in god_rolls.get_rolls('PVE'):
            self.curation += GameModeFlag.pve

    def get_hash(self) -> str:
        return str(self.perk['hash'])

    def get_name(self) -> str:
        return self.perk['displayProperties']['name']

    def get_icon_url(self) -> str:
        return self.perk['displayProperties']['icon']

    def is_enhanced(self) -> bool:
        return self.perk['itemTypeDisplayName'] == ENHANCED_PERK


class DamageType(ManifestData):
    damage_type: dict[Union[str, dict[str, str]], Union[dict[str, str], str]]

    def __init__(self, json_string):
        self.damage_type = self.deserialize(json_string=json_string)

    def get_icon(self) -> str:
        return self.damage_type['displayProperties']['icon']


class GodRollContainer(ManifestData):
    god_rolls: dict[str, list[list[int]]]

    def __init__(self, json_string):
        self.god_rolls = self.deserialize(json_string=json_string)

    def get_rolls(self, game_mode: str) -> list[list[int]]:
        return self.god_rolls[game_mode]

    def apply_to_perk_set(self, perk_set: list[PerkColumn]):
        iter_len: int = len(self.god_rolls['PVP'])
        if len(perk_set) < iter_len:
            iter_len = len(perk_set)

        for i in range(iter_len):
            for perk in perk_set[i]:
                if perk.get_hash() in self.god_rolls['PVP'][i]:
                    perk.curation += GameModeFlag.pvp
                if perk.get_hash() in self.god_rolls['PVE'][i]:
                    perk.curation += GameModeFlag.pve
