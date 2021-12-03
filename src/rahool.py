import logging
import os
import disnake
from disnake.ext import commands, tasks
from readDB import query_weapon
from readJSON import prepare_weapon
from APIrequests import check_update

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


# logs for command invocation, completion and error
@rahool.event
async def on_command(ctx):
    logging.info(f'{ctx.prefix}{ctx.command} request by {ctx.author.name}, {ctx.author.id}: requested')


@rahool.event
async def on_command_completion(ctx):
    logging.info(f'{ctx.prefix}{ctx.command} request by {ctx.author.name}, {ctx.author.id}: completed')


@rahool.event
async def on_command_error(ctx, error):
    logging.error(f'{ctx.prefix}{ctx.command} request by {ctx.author.name}, {ctx.author.id}: {error}')


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
    await inter.response.send_message("processing your request...")
    # retrieve weapon information
    weapon = query_weapon(weapon_name)
    # assemble discord form containing information on the requested weapon

    form = disnake.Embed(
        title=weapon['displayProperties']['name'],
        description=weapon['itemTypeAndTierDisplayName'],
        url=f'''https://data.destinysets.com/i/InventoryItem:{weapon['hash']}''',
        colour=disnake.Colour.dark_gold()
    )
    weapon_perks = await prepare_weapon(weapon)

    form.set_author(name=f'info',
                    icon_url=BOT_PFP)
    form.set_footer(text='"Some of these files are older than the city itself..."')

    form.set_thumbnail(url=f'''https://bungie.net{weapon['displayProperties']['icon']}''')
    form.add_field(name='_____', value=f'''"{weapon['flavorText']}"''', inline=False)

    i = 1
    for column in weapon_perks:
        perk_string = ''
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
