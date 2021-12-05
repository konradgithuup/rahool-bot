import pytest
from readDB import query_weapon
from readJSON import get_weapon_plug_hashes
from helperClasses import Weapon, PerkSet
from customExceptions import NoSuchWeaponError, NoRandomRollsError


def test_weapon_query():
    assert query_weapon("Bottom Dollar").get_name() == "Bottom Dollar"


async def get_first_perk(weapon_name: str) -> str:
    weapon: Weapon = query_weapon(weapon_name)
    weapon_perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)
    for col in weapon_perks:
        for perk in col:
            return perk


@pytest.mark.asyncio
async def test_perk_query(event_loop):
    assert await get_first_perk("Bottom Dollar") == "Arrowhead Brake"


@pytest.mark.asyncio
async def test_perk_query_filter_y1_version(event_loop):
    assert await get_first_perk("Shepherd's Watch") == "Arrowhead Brake"


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
    assert await get_first_perk("Hawkmoon") == "Arrowhead Brake"