import logging
import os
import disnake
from disnake.ext import commands, tasks
from APIrequests import check_update
from commandCallFunctions import generate_perk_information_image
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
    form.add_field(name='Disclaimer', value='The highlighted perks are simply suggestions.\nGod rolls are always subjective and depend on what you want to achieve.')

    form.set_footer(text='"Some of these files are older than the city itself..."')
    form.set_author(name='help',
                    icon_url=BOT_PFP)

    await inter.response.send_message(embed=form)


@rahool.slash_command()
async def perks(inter, weapon_name: str = commands.Param(name="weapon")):
    """
    Returns the random rolls for a specific weapon

    Parameters
    ----------
    weapon_name: :class:`str`
        The queried weapon
    """
    # temporary response to satisfy discord's response time limit
    await inter.response.defer()

    try:
        path_to_image: str = await generate_perk_information_image(weapon_name)
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

    image = disnake.File(path_to_image)

    await inter.followup.send(file=image)

    os.remove(path_to_image)

rahool.run(BOT_TOKEN)
