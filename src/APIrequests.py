import requests
import zipfile
import logging
import os


HEADERS = {"X-API-Key": os.environ.get('BUNGIE_API_KEY')}
BASE_URL = 'http://www.bungie.net/Platform/Destiny2/Manifest/'
HALF_HOUR = 1800


# get destiny 2 game Manifest from the Bungie api
def get_manifest():
    manifest_url = BASE_URL

    # get manifest location
    try:
        r = requests.get(manifest_url, headers=HEADERS)
    except requests.exceptions.RequestException as e:
        logging.error(f'request failed, reason {e}')
        raise

    manifest: dict = r.json()
    mani_url: str = 'https://www.bungie.net' + manifest['Response']['mobileWorldContentPaths']['en']

    # Download file and write it to MANZIP
    try:
        r = requests.get(mani_url)
    except requests.exceptions.RequestException as e:
        logging.error(f'request failed, reason {e}')
        raise
    with open('resources/MANZIP', 'wb') as zip:
        zip.write(r.content)
    logging.info('manifest downloaded')

    # Extract the file contents, rename extracted file
    with zipfile.ZipFile('resources/MANZIP') as zip:
        name = zip.namelist()
        zip.extractall()

    os.rename(name[0], 'resources/Manifest.content')
    logging.info('manifest ready')


# checks if a more recent Manifest exists, calls update if needed
def check_update():
    if not os.path.isfile(r'resources/Manifest.content'):
        get_manifest()
        return

    manifest_url: str = BASE_URL

    r = requests.get(manifest_url, headers=HEADERS)
    manifest_info: dict = r.json()

    md5_data: str = (manifest_info['Response']['mobileWorldContentPaths']['en']).split('_')
    new_md5: str = md5_data[4].replace('.content', '')

    manifest_md5_hash = open("resources/manifest_md5.txt", 'r')
    old_hash = manifest_md5_hash.read()
    manifest_md5_hash.close()

    logging.info(f'compare manifest md5 sum; old: {old_hash} new: {new_md5}')

    if not old_hash == new_md5:
        logging.info('md5 sums unequal; commence update')
        manifest_md5_hash = open("resources/manifest_md5.txt", "w")
        manifest_md5_hash.write(new_md5)
        manifest_md5_hash.close()
        update_manifest()


# updates the manifest
def update_manifest():
    os.remove("resources/Manifest.content")
    logging.info('old manifest removed')
    get_manifest()
