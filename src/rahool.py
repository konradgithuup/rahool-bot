import logging
import os
import disnake
from disnake.ext import commands, tasks
from readDB import query_weapon
from readJSON import get_weapon_plug_hashes
from APIrequests import check_update
from createImages import create_perk_image
from helperClasses import Weapon, PerkSet
from customExceptions import NoSuchWeaponError, NoRandomRollsError

BOT_PFP = 'https://cdn.discordapp.com/app-icons/725485079438032916/8cfe42f2a6930a82300aba44ef390306.png?size=512'
BOT_TOKEN = os.environ.get('BOT_TOKEN')

rahool = commands.Bot(command_prefix='e/')

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s|%(module)s|%(funcName)s|%(message)s|%(asctime)s',
                    datefmt='%Y-%m-%d|%H:%m:%S')


# triggers on bot start
@rahool.event
async def on_ready():
    update_loop.start()
    logging.info("Bot online")
    await rahool.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name="Weapon Rolls"))


@tasks.loop(hours=1)
async def update_loop():
    logging.info("checking for updates")
    check_update()


# override help function
@rahool.slash_command(description="command syntax help")
async def help(inter):
    form = disnake.Embed(
        title='Rahool/help',
        url='https://discord.gg/7kvXr4zhY3',
        description="Can't find what you are looking for?\nWant to suggest a feature or report a bug?\n"
                    "Follow the link in the title to join the support discord server",
        colour=disnake.Colour.green()
    )

    form.add_field(name='Shows all possible Weapon Perks', value='/perks <Weapon>')
    form.add_field(name='Examples', value='/perks Gridskipper\n'
                                          '/perks Astral Horizon')

    form.set_footer(text='"Some of these files are older than the city itself..."')
    form.set_author(name='help',
                    icon_url=BOT_PFP)

    await inter.response.send_message(embed=form)


# get weapon random rolls
@rahool.slash_command(description="show a weapon's possible perks")
async def perks(inter, weapon_name: str = commands.Param(name="weapon")):
    # temporary response to satisfy discord's response time limit
    await inter.response.defer()

    try:
        weapon: Weapon = query_weapon(weapon_name)
    except NoSuchWeaponError:
        error = disnake.Embed(
            title="Error",
            description="This weapon does not exist.\n"
                        "Please check for typos or check /help",
            colour=disnake.Colour.red()
        )
        await inter.followup.send(content=None, embed=error)
        return
    except NoRandomRollsError:
        error = disnake.Embed(
            title="Error",
            description="This weapon does not have any random rolls\n"
                        "/perks only works for weapons with random perks",
            colour=disnake.Colour.red()
        )
        await inter.followup.send(content=None, embed=error)
        return

    weapon_perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)
    image = disnake.File(f'{create_perk_image(weapon, weapon_perks)}.png')

    await inter.followup.send(file=image)
    os.remove(f'{weapon.get_collectible_hash()}.png')


@perks.error
async def perks_error(inter, error):
    form = disnake.Embed(
        title='Error',
        description='An error occurred using the perks command.\n'
                    'See /help for more information',
        colour=disnake.Colour.red()
    )

    await inter.response.send_message(content=None, embed=form)

rahool.run(BOT_TOKEN)
