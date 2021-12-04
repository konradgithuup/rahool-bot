import logging
import os
import disnake
from disnake.ext import commands, tasks
from readDB import query_weapon
from readJSON import get_weapon_plug_hashes
from APIrequests import check_update
from helperClasses import Weapon, PerkSet

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
        title='Help',
        description='Get information on possible weapon perk rolls',
        colour=disnake.Colour.green()
    )

    form.add_field(name='Syntax', value='e/perks <description>')
    form.add_field(name='Examples', value='e/perks Gridskipper\n'
                                          'weapon names with >1 word must be encased in "":\n'
                                          'e/perks "Astral Horizon"')

    form.set_footer(text='"Some of these files are older than the city itself..."')
    form.set_author(name='help',
                    icon_url=BOT_PFP)

    await inter.inter.response.send_message(embed=form)


# get weapon random rolls
@rahool.slash_command(description="show a weapon's possible perks")
async def perks(inter, weapon_name: str):
    # temporary response to satisfy discord's response time limit
    await inter.response.send_message("processing your request...")

    weapon: Weapon = query_weapon(weapon_name)

    form = disnake.Embed(
        title=weapon.get_name(),
        description=weapon.get_type(),
        url=f'''https://data.destinysets.com/i/InventoryItem:{weapon.get_hash()}''',
        colour=disnake.Colour.dark_gold()
    )
    weapon_perks: list[PerkSet] = await get_weapon_plug_hashes(weapon)

    form.set_author(name=f'info',
                    icon_url=BOT_PFP)
    form.set_footer(text='"Some of these files are older than the city itself..."')

    form.set_thumbnail(url=f'''https://bungie.net{weapon.get_icon()}''')
    form.add_field(name='_____', value=f'''"{weapon.get_description()}"''', inline=False)

    i = 1
    for column in weapon_perks:
        perk_string: str = ''
        for perk in column:
            perk_string += f'{perk}\n'
        form.add_field(name=f'column {i}', value=perk_string, inline=True)
        i += 1

    await inter.edit_original_message(content=None, embed=form)


@perks.error
async def perks_error(ctx, error):
    form = disnake.Embed(
        title='Error',
        description='An error occurred using the perks command',
        colour=disnake.Colour.red()
    )

    if isinstance(error, commands.MissingRequiredArgument):
        form.add_field(name="Missing Required Argument", value='When using the perks command you'
                                                               'must provide the name of the weapon'
                                                               'you are searching.\n'
                                                               'Check help for more information.')

    await ctx.send(embed=form)

rahool.run(BOT_TOKEN)
