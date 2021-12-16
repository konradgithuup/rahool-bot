from __future__ import annotations
import json
import logging
from typing import Union


class ManifestData:
    # generate dictionary from db-json
    def deserialize(self, json_string: str) -> dict:
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logging.error(f'db output could not be parsed: {e}')


class Weapon(ManifestData):
    weapon: dict[str, Union[int, str, dict[str, dict[Union[str, int], dict[str, Union[list[int], str]]]]]]

    # weapon constructor
    def __init__(self, json_string):
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

    def is_random_socket(self, index: int) -> bool:
        if 'randomizedPlugSetHash' not in self.socket_set['socketEntries'][index]:
            return True

        return False

    def get_perk_sockets(self):
        return self.socket_set['socketCategories'][1]['socketIndexes'];

    def get_plug_set_hash(self, index: int) -> int:
        return self.socket_set['socketEntries'][index].get('randomizedPlugSetHash', 0)


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
    perk_set: PerkSet
    index: int

    def __init__(self, perk_set: PerkSet):
        self.perk_set = perk_set
        self.index = 0

    def __next__(self):
        if self.index < (len(self.perk_set)):
            result = self.perk_set[self.index]
            self.index += 1
            return result

        raise StopIteration


class PerkSet(ManifestData):
    perk_set: list[dict[str, Union[str, dict[str, str]]]]

    def __init__(self):
        self.perk_set = []

    def __len__(self):
        return len(self.perk_set)

    def __iter__(self):
        return PerkIterator(self)

    def __getitem__(self, item):
        return self.perk_set[item]['displayProperties']['name']

    def add_perk(self, json_string):
        self.perk_set.append(self.deserialize(json_string))
