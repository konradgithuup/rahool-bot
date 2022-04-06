import logging
import threading
from helperClasses import Weapon, SocketSet, PlugSet, PerkColumn, DamageType
from customExceptions import NoRandomRollsError
from typing import Optional

ITEM_TYPE_WEAPON = 3


class ColumnThread(threading.Thread):
    """
    threading class for parallelized perk queries
    """
    def __init__(self, thread_id, name, column, out):
        """
        :param thread_id: ID of the thread
        :param name: name of the thread
        :param column: perk hashes to query
        :param out: list of Perks to write results to
        """
        threading.Thread.__init__(self)
        self.thread_id: int = thread_id
        self.name: str = name
        self.column: list[int] = column
        self.out: list[PerkColumn] = out

    def run(self):
        logging.info(f"Starting {self.name}")
        col: PerkColumn = perk_set_from_hashes(self.column)
        # acts as a "return value"
        self.out[self.thread_id-1] = col
        logging.info(f"Exiting {self.name}")


def find_weapon(weapon_db: list[list[str]]) -> Weapon:
    """
    recursively filter database weapon query for random rolled weapon

    :param weapon_db: database query result
    :return: random rolled weapon
    :raises NoRandomRollsError: when database query doesn't contain a random rolled weapon
    """
    if len(weapon_db) == 0:
        raise NoRandomRollsError

    weapon_string: list[str] = weapon_db[0]
    try:
        weapon: Weapon = Weapon(json_string=weapon_string[0])
    except KeyError:
        weapon_db.pop(0)
        return find_weapon(weapon_db)

    if weapon.get_item_type() != ITEM_TYPE_WEAPON:
        weapon_db.pop(0)
        return find_weapon(weapon_db)

    if weapon.has_random_roll():
        return weapon

    weapon_db.pop(0)
    return find_weapon(weapon_db)


def get_damage_type_icon_url(dmg_type_string: str) -> str:
    """
    get icon url for a damage type

    :param dmg_type_string: damage type data as json-formatted String
    :return: damage type icon url, requires bungie.net base url
    """
    damage_type: DamageType = DamageType(dmg_type_string)
    return damage_type.get_icon()


async def get_weapon_plug_hashes(perk_socket_set: SocketSet) -> list[PerkColumn]:
    """
    get perks for all random and origin perk sockets

    :param perk_socket_set: weapon's perk sockets
    :return: weapon perks as List of PerkColumn
    """
    from readDB import query_plug_set
    plug_sets: list[PlugSet] = []
    i: int = 1

    while i < perk_socket_set.get_size():

        if perk_socket_set.is_random_socket(index=i) or perk_socket_set.is_origin_socket(index=i):
            plug_set: int = perk_socket_set.get_plug_set_hash(index=i)
            plug_sets.append(PlugSet(query_plug_set(plug_set)))
        i += 1

    return await get_plug_set_perk_hashes(plug_sets)


async def get_plug_set_perk_hashes(plug_sets: list[PlugSet]) -> list[PerkColumn]:
    """
    get perks from plug sets

    :param plug_sets:
    :return:
    """

    total_perk_hashes: list[list[int]] = []
    for plug_set in plug_sets:
        column: list[int] = plug_set.get_perk_hashes()

        total_perk_hashes.append(column)

    return await get_perks(total_perk_hashes)


# called upon by each ColumnThread
def perk_set_from_hashes(column: list[int]) -> PerkColumn:
    from readDB import query_perks
    col: PerkColumn = PerkColumn()
    perks = query_perks(column)
    for perk in perks:
        col.add_perk(perk[0])

    return col


# handle multithreaded db lookup for weapon-perks
async def get_perks(perk_hashes: list[list[int]]) -> list[PerkColumn]:
    """
    gets perk data from set of perk hash lists running each column on a different thread
    :param perk_hashes:
    :return: perk data ordered by column as List of PerkColumn
    """
    total_perks: list[Optional[PerkColumn]] = []

    i: int = 0
    threads: list[ColumnThread] = []
    # create new thread for each perk row
    for column in perk_hashes:
        i += 1
        total_perks.append(None)
        threads.append(ColumnThread(thread_id=i, name=f"Thread_{i}", column=column, out=total_perks))

    # execute the threads
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    return total_perks
