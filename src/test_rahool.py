import os

import pytest
from readDB import query_weapon
from readJSON import get_weapon_plug_hashes
from helperClasses import Weapon, PerkSet
from customExceptions import NoSuchWeaponError, NoRandomRollsError
from createImages import create_perk_image
from PIL import Image


def test_weapon_query():
    assert query_weapon("Bottom Dollar").get_name() == "Bottom Dollar"


async def get_first_perk(weapon_name: str) -> str:
    weapon: Weapon = query_weapon(weapon_name)
    weapon_perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)
    for col in weapon_perks:
        for perk in col:
            return perk['name']


@pytest.mark.asyncio
async def test_perk_query(event_loop):
    assert await get_first_perk("Bottom Dollar") == "Hammer-Forged Rifling"


@pytest.mark.asyncio
async def test_perk_query_filter_y1_version(event_loop):
    assert await get_first_perk("Shepherd's Watch") == "Hammer-Forged Rifling"


@pytest.mark.asyncio
async def test_perk_query_test_db_exception(event_loop):
    with pytest.raises(NoSuchWeaponError):
        assert await get_first_perk("DummyWeapon")


@pytest.mark.asyncio
async def test_perk_query_y1_weapon(event_loop):
    with pytest.raises(NoRandomRollsError):
        assert await get_first_perk("Midnight Coup")


@pytest.mark.asyncio
async def test_perk_query_exotic(event_loop):
    assert await get_first_perk("Hawkmoon") == "Hammer-Forged Rifling"


@pytest.mark.asyncio
async def test_image_generation_legendary(event_loop):
    weapon: Weapon = query_weapon("Shayura's Wrath")
    perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)

    img: Image = Image.open(f'{create_perk_image(weapon, perks)}.png')
    img.show()

    os.remove(f'{weapon.get_damage_type()}.png')
    os.remove(f'{weapon.get_collectible_hash()}.png')


@pytest.mark.asyncio
async def test_image_generation_exotic(event_loop):
    weapon: Weapon = query_weapon("Hawkmoon")
    perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)

    img: Image = Image.open(f'{create_perk_image(weapon, perks)}.png')
    img.show()

    os.remove(f'{weapon.get_damage_type()}.png')
    os.remove(f'{weapon.get_collectible_hash()}.png')
