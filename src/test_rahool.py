import os

import pytest
from readDB import query_weapon, query_god_roll
from readJSON import get_weapon_plug_hashes, get_perks
from helperClasses import Weapon, PerkColumn, GodRollContainer
from customExceptions import NoSuchWeaponError, NoRandomRollsError
from commandCallFunctions import generate_perk_information_image
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
    weapon_perks: list[PerkColumn] = await get_weapon_plug_hashes(weapon.get_socket_set())
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
    await weapon_image_gen("Thoughtless")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_legendary_multiple_origin(event_loop):
    await weapon_image_gen("Reed's Regret")


@pytest.mark.perks
@pytest.mark.asyncio
async def test_image_generation_exotic(event_loop):
    await weapon_image_gen("Hawkmoon")


async def weapon_image_gen(weapon: str):
    image_name: str = await generate_perk_information_image(weapon)
    image = Image.open(image_name)
    image.show()

    os.remove(image_name)
