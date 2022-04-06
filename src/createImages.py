import os

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from enum import Enum
from helperClasses import Weapon, PerkColumn
from readDB import query_damage_type
import urllib.request

COL_WIDTH: int = 500
ENHANCED_PERK_DISCLAIMER: str = '(this weapon has enhanced perks obtainable through the relic on Mars)'
curation_color = {
    0: (200, 200, 200),
    1: (77, 148, 255),
    2: (255, 77, 77),
    3: (255, 219, 77)
}


def create_perk_image(weapon: Weapon, perk_set: list[PerkColumn]) -> str:
    """
    creates image with weapon information

    :param weapon: the weapon for which to create the image
    :param perk_set: the weapon's perk_set
    """
    # open/create required images
    urllib.request.urlretrieve(f'https://bungie.net{weapon.get_screenshot()}',
                               f'{weapon.get_collectible_hash()}.png')
    urllib.request.urlretrieve(f'https://bungie.net{query_damage_type(weapon.get_damage_type())}',
                               f'{weapon.get_damage_type()}.png')

    weapon_img = Image.open(f'{weapon.get_collectible_hash()}.png')
    dmg_type_img = Image.open(f'{weapon.get_damage_type()}.png')
    dmg_type_img = dmg_type_img.convert(mode='RGBA', palette=Image.ADAPTIVE, colors=32)
    dmg_type_img = dmg_type_img.resize((100, 100))
    overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 96))
    glow = Image.open(f'resources/image_assets/weapon_glow_{weapon.get_rarity()}.png')

    # open required fonts
    title = ImageFont.truetype('resources/fonts/FUTURA.ttf', 100)
    base_text = ImageFont.truetype('resources/fonts/futur.ttf', 40)

    weapon_img = weapon_img.filter(ImageFilter.BoxBlur(5))

    # add text on overlay-layer
    overlay_edit = ImageDraw.Draw(overlay)
    overlay_edit.text((130, 15),
                      weapon.get_name(),
                      (255, 255, 255),
                      title)

    draw_perks(overlay, weapon, perk_set, base_text)

    # composite all layers
    enhance = ImageEnhance.Brightness(dmg_type_img)
    mask = enhance.enhance(1)
    overlay.paste(dmg_type_img, (15, 15), mask)
    enhance = ImageEnhance.Brightness(glow)
    mask = enhance.enhance(0.3)
    overlay.paste(glow, (0, 540), mask)
    enhance = ImageEnhance.Brightness(overlay)
    mask = enhance.enhance(0.3)
    weapon_img.paste(overlay, (0, 0), mask)

    weapon_img.save(f"{weapon.get_collectible_hash()}.png")
    os.remove(f'{weapon.get_collectible_hash()}_icon.png')

    return weapon.get_collectible_hash()


def draw_perks(overlay: Image, weapon: Weapon, perk_set: list[PerkColumn], base_text: ImageFont):
    """
    adds perks to the image

    :param overlay: layer to draw on
    :param weapon: weapon for which to draw perks
    :param perk_set: perks to draw
    :param base_text: font for perk names
    """
    overlay_edit = ImageDraw.Draw(overlay)
    disclaimer = ""

    n_cols: int = 0
    perk_block_x: int = 20
    perk_block_y: int = 150
    col_count = 0

    for column in perk_set:
        if column.has_enhanced_perk():
            disclaimer = ENHANCED_PERK_DISCLAIMER

        if col_count > 3:
            perk_block_y = 870
            perk_block_x = 250

        col_count += 1
        depth: int = 0
        icon_urls: list[str] = []
        column_width: int = 0

        for perk in column:
            icon_urls.append(perk.get_icon_url())
            perk_text_width = base_text.getbbox(text=perk.get_name())[2]

            overlay_edit.text((50 + perk_block_x, perk_block_y + depth * 52),
                              text=perk.get_name(),
                              font=base_text,
                              fill=curation_color[perk.curation])

            if perk_text_width > column_width:
                column_width = perk_text_width
            depth += 1

        overlay_edit.line((perk_block_x, perk_block_y, perk_block_x, perk_block_y + depth * 50),
                          width=5,
                          fill=255)

        for i in range(depth):
            urllib.request.urlretrieve(f'https://bungie.net{icon_urls[i]}',
                                       f'{weapon.get_collectible_hash()}_icon.png')
            icon = Image.open(f'{weapon.get_collectible_hash()}_icon.png')
            icon = icon.convert(mode='RGBA', palette=Image.ADAPTIVE, colors=32)
            icon = icon.resize((40, 40))
            enhance = ImageEnhance.Brightness(icon)
            mask = enhance.enhance(1)
            overlay.paste(icon, (5 + perk_block_x, perk_block_y + i * 52), mask)

        perk_block_x += 70 + column_width
        n_cols += 1

        # add origin perk ui elements
        overlay_edit.line((0, 850, 1920, 850), width=10, fill=255)
        overlay_edit.text((15, 870), spacing=20, text="Origin Perks", font=base_text, fill=(255, 255, 255))

        # add disclaimer
        overlay_edit.text((15, 800), spacing=20, text=disclaimer, font=base_text, fill=(255, 230, 128), alpha=0.8)
