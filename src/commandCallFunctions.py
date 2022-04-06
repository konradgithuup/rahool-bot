from helperClasses import Weapon, PerkColumn, GodRollContainer
from readDB import query_weapon, query_god_roll
from readJSON import get_weapon_plug_hashes
from createImages import create_perk_image
from customExceptions import NoGodRollError
import os


async def generate_perk_information_image(weapon_name: str) -> str:
    """
    generates and locally stores perk information image

    :param weapon_name: name of the weapon for which to generate the image
    :return: name of the locally stored image
    """
    weapon: Weapon
    god_rolls: GodRollContainer

    weapon = query_weapon(weapon_name)
    weapon_perks: list[PerkColumn] = await get_weapon_plug_hashes(weapon.get_socket_set())

    try:
        god_rolls = GodRollContainer(query_god_roll(weapon.get_hash()))
        god_rolls.apply_to_perk_set(perk_set=weapon_perks)
    except NoGodRollError:
        pass

    create_perk_image(weapon, weapon_perks)
    os.remove(f'{weapon.get_damage_type()}.png')

    return f'{weapon.get_collectible_hash()}.png'

