import os

import pytest
from readDB import query_weapon, query_god_roll
from readJSON import get_weapon_plug_hashes, get_perks
from helperClasses import Weapon, PerkColumn, GodRollContainer
from customExceptions import NoSuchWeaponError, NoRandomRollsError, NoGodRollError
from createImages import create_perk_image, create_god_roll_image
from PIL import Image


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "perks: marks test as perks command"
    )
    config.addinivalue_line(
        "markers", "godroll: marks test as godroll command"
    )


def test_weapon_query():
    assert query_weapon("Bottom Dollar").get_name() == "Bottom Dollar"


async def get_first_perk(weapon_name: str) -> str:
    weapon: Weapon = query_weapon(weapon_name)
    weapon_perks: list[PerkColumn] = await get_weapon_plug_hashes(weapon)
    for col in weapon_perks:
        for perk in col:
            return perk.get_name()


@pytest.mark.perks
@pytest.mark.asyncio
async def test_perk_query(event_loop):
    assert await get_first_perk("Bottom Dollar") == "Hammer-Forged Rifling"


@pytest.mark.perks
@pytest.mark.asyncio
async def test_perk_query_filter_y1_version(event_loop):
    assert await get_first_perk("Shepherd's Watch") == "Hammer-Forged Rifling"


@pytest.mark.perks
@pytest.mark.asyncio
async def test_perk_query_test_db_exception(event_loop):
    with pytest.raises(NoSuchWeaponError):
        assert await get_first_perk("DummyWeapon")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_perk_query_y1_weapon(event_loop):
    with pytest.raises(NoRandomRollsError):
        assert await get_first_perk("Midnight Coup")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_perk_query_exotic(event_loop):
    assert await get_first_perk("Hawkmoon") == "Hammer-Forged Rifling"


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_legendary_no_origin(event_loop):
    await weapon_image_gen("Bottom Dollar")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_legendary_single_origin(event_loop):
    await weapon_image_gen("Hung Jury SR4")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_legendary_multiple_origin(event_loop):
    await weapon_image_gen("Herod-C")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_exotic(event_loop):
    await weapon_image_gen("Hawkmoon")


@pytest.mark.godroll
@pytest.mark.asyncio
async def test_god_roll_pve(event_loop):
    await god_roll_gen("Hung Jury SR4", "PVE")


async def weapon_image_gen(weapon: str):
    weapon: Weapon = query_weapon(weapon)
    perks: list[PerkColumn] = await get_weapon_plug_hashes(weapon)

    try:
        god_rolls = GodRollContainer(query_god_roll(weapon.get_hash()))
        god_rolls.apply_to_perk_set(perk_set=perks)
    except NoGodRollError:
        pass

    img: Image = Image.open(f'{create_perk_image(weapon, perks)}.png')
    img.show()

    os.remove(f'{weapon.get_damage_type()}.png')
    os.remove(f'{weapon.get_collectible_hash()}.png')


async def god_roll_gen(weapon: str, mode: str):
    weapon: Weapon = query_weapon(weapon)
    god_rolls: list[list[int]] = GodRollContainer(query_god_roll(weapon.get_hash())).get_rolls(game_mode=mode)
    perks: list[PerkColumn] = await get_perks(perk_hashes=god_rolls)

    img: Image = Image.open(f'{create_god_roll_image(weapon, perks, mode)}.png')
    img.show()
    os.remove(f'{weapon.get_hash()}.png')
