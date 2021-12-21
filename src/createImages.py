from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from helperClasses import Weapon, PerkSet
from readDB import query_damage_type
import urllib.request

COL_WIDTH: int = 500


def create_perk_image(weapon: Weapon, perk_set: list[PerkSet]) -> str:
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
    overlay_edit.text((15, 145),
                      f'"{weapon.get_description()}"',
                      (255, 255, 255),
                      base_text)

    # add perks
    n_cols: int = 0
    for column in perk_set:
        depth: int = 0
        perk_string: str = ''
        for perk in column:
            perk_string += f'{perk}\n'
            depth += 1

        overlay_edit.line((35 + COL_WIDTH*n_cols, 230, 35 + COL_WIDTH*n_cols, 230 + depth*50),
                          width=5,
                          fill=255)
        overlay_edit.multiline_text((45+COL_WIDTH*n_cols, 230),
                                    spacing=20,
                                    text=perk_string,
                                    font=base_text,
                                    fill=(200, 200, 200))
        n_cols += 1

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

    return weapon.get_collectible_hash()
