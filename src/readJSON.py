import logging
import threading
from helperClasses import Weapon, SocketSet, PlugSet, PerkColumn, DamageType, GodRollContainer
from customExceptions import NoRandomRollsError
from typing import Optional

ITEM_TYPE_WEAPON = 3


# run queries for each perk column on an individual thread to speed up the process
class ColumnThread(threading.Thread):
    def __init__(self, thread_id, name, column, out):
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


# search database output for random rolled weapon
def find_weapon(weapon_db: list[list[str]]) -> Weapon:
    if len(weapon_db) == 0:
        raise NoRandomRollsError

    weapon_string: list[str] = weapon_db[0]
    weapon: Weapon = Weapon(json_string=weapon_string[0])

    if weapon.get_item_type() != ITEM_TYPE_WEAPON:
        weapon_db.pop(0)
        return find_weapon(weapon_db)

    if weapon.has_random_roll():
        return weapon

    weapon_db.pop(0)
    return find_weapon(weapon_db)


def get_damage_type_link(dmg_type_string: str) -> str:
    damage_type: DamageType = DamageType(dmg_type_string)
    return damage_type.get_icon()


# prepare the weapon dictionary to get plug hashes
async def get_weapon_plug_hashes(weapon: Weapon) -> list[PerkColumn]:
    from readDB import query_plug_set
    perk_socket_set: SocketSet = SocketSet(weapon)
    plug_sets: list[str] = []
    i: int = 1
    perk_sockets = perk_socket_set.get_perk_sockets()

    # get plug hash for all columns that store randomized weapon perks
    while i < perk_sockets[len(perk_sockets)-1]:

        if perk_socket_set.is_random_socket(index=i) or perk_socket_set.is_origin_socket(index=i):
            plug_set: int = perk_socket_set.get_plug_set_hash(index=i)
            plug_sets.append(query_plug_set(plug_set))
        i += 1

    return await get_plug_set_perk_hashes(plug_sets)


# retrieve each plug sets perks
async def get_plug_set_perk_hashes(plug_sets: list[str]) -> list[PerkColumn]:
    # store all perk hashes
    total_perk_hashes: list[list[int]] = []
    for plug_string in plug_sets:
        plug: PlugSet = PlugSet(plug_string)
        # retrieve perk hashes of column i
        column: list[int] = plug.get_perk_hashes()

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