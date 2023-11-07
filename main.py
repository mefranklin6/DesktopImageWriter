from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import subprocess
import yaml
import re
import logging as log
from os import mkdir, path
from concurrent import futures
from time import sleep


with open('Config.yaml', 'r') as YAML_reader:
    config = yaml.safe_load(YAML_reader)

# YAML Sections
BASIC_PATHS = config['BasicPaths']
OWNERSHIP = config['Ownership']


LOG_PATH = config["BasicPaths"]["LogFileDirectory"]


def confirm_log_path(local_directory) -> None:
    if not path.exists(local_directory):
        print(f'Creating directory for logs at {local_directory}')
        mkdir(local_directory)
    else:
        print(f'logging to {local_directory}')


confirm_log_path(LOG_PATH)


log.basicConfig(
    filename=f'{LOG_PATH}/DesktopImageWriter_Log.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    level=log.INFO,
)


log.debug(f'Config: {str(config)}')


try:
    with open(config['TargetList'], 'r', encoding='utf-8') as target_list_file:
        target_list = target_list_file.read().splitlines()
        log.debug(f'Target List: {target_list}')
except:
    log.fatal(f'Can not open target list at {config["TargetList"]}')
    exit(1)


def ping(ip: str) -> int:
    return subprocess.call(f'powershell.exe ping -n 1 {ip}')
    # returns 0 for online, 1 for error


def local_to_UNC_path(pc: str, local_path: str) -> str:
    local_parts = local_path.replace('/', '').split(':')
    drive = local_parts[0]
    path = local_parts[1]
    format = f'//{pc}/{drive}$/{path}'

    log.debug(f'{pc} Local Path: {local_path}')
    log.debug(f'{pc} UNC Path: {format}')

    return format


def matching_strict(pc: str, department_regex_patterns: dict) -> str:
    if department_regex_patterns:
        for pattern, department in department_regex_patterns.items():
            if re.match(pattern, pc):
                return department
    log.warning(f'{pc} No department regex patterns detected')
    return None


def matching_loose(pc: str, department_keywords: dict) -> str:
    if department_keywords:
        for key, department in department_keywords.items():
            if key in pc:
                return department
    log.warning(f'{pc} No department keywords detected')
    return None


def matching_AD(pc: str, department_ou: dict) -> str:
    AD_query_base = 'Get-ADComputer -Filter '
    AD_query_filter = f'Name -like "{pc}"'
    AD_Query = f"({AD_query_base}'{AD_query_filter}').DistinguishedName"

    AD_Return = subprocess.run(
        [
            'powershell.exe',
            AD_Query
        ],
        capture_output=True
    )

    if AD_Return.returncode == 0:
        log.debug(f'{pc} AD Return raw: {str(AD_Return)}')
        for ou, ou_department in department_ou.items():
            if f'OU={ou}' in str(AD_Return):
                return ou_department
    return None

# order of matching is up for debate:
# I like regex (strict) matching first because CTS has 'special' numbered rooms.
# Arguably AD matching is more accurate but slower, stresses the domain controllers
# ... and harder to do 'special room' matching


def ownership_match(pc):
    matched = matching_strict(pc, OWNERSHIP['DepartmentRegexPatterns'])
    if matched:
        log.info(f'{pc} Matched {matched} with STRICT matching')
        return matched

    matched = matching_loose(pc, OWNERSHIP['DepartmentKeywords'])
    if matched:
        log.info(f'{pc} Matched {matched} with LOOSE matching')
        return matched

    matched = matching_AD(pc, OWNERSHIP['DepartmentOU'])
    if matched:
        log.info(f'{pc} Matched {matched} with Active Directory matching')
        return matched

    log.error(f'{pc} FAILED ALL MATCHING!')
    log.info(f'{pc} falling back to {OWNERSHIP["Fallback"]}')
    return None


def pair_contact_string(department: str, contact_strings: dict) -> str:
    if ',' in department:
        contact_key = department.split(',')[0]
    else:
        contact_key = department

    contact_string = contact_strings[contact_key]
    return contact_string


def read_registry(pc, registry_key, registry_sz) -> str:
    # translate to microsoft style shashes
    registry_key = registry_key.replace('/', '\\')

    invoke_command = f'Invoke-Command -ComputerName {pc} -ScriptBlock {{(Get-ItemProperty "{registry_key}" -Name {registry_sz}).{registry_sz}}}'
    log.debug(f'{pc} Invoke-Command String: {invoke_command}')

    cmd = subprocess.run(
        [
            'powershell.exe',
            invoke_command
        ],
        capture_output=True,
        text=True
    )

    log.debug(f'{pc} invoke command raw return: {str(cmd)}')

    asset_tag = str(cmd.stdout).upper().strip()
    log.info(f'{pc} asset tag: {asset_tag}')

    return asset_tag


def format_text(pc, asset_tag, contact_string):
    format = f'''
    Computer Name: {pc}
    Asset Tag: {asset_tag}
    {contact_string}
'''
    log.debug(f'{pc} format_text output {format}')
    return format


def write_image(image_location, text_to_write, out_file) -> None:
    image = Image.open(image_location)
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('arial.ttf', 30)
    text_position_x = config['TextPosition']['X']
    text_position_y = config['TextPosition']['Y']
    text_position = (text_position_x, text_position_y)
    outline_color = 'black'
    text_color = 'white'

    text = text_to_write

    # offset handles text outline since there's no built-in way to do that
    x, y = text_position
    for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
        draw.text((x + offset[0], y + offset[1]),
                  text, font=font, fill=outline_color)
    draw.text(text_position, text, font=font, fill=text_color)
    image.save(out_file)


def decide_image_source(department: str, options: dict):
    if ',' in department:
        department = department.split(',')[0].strip()

    for department_key, path_value in options.items():
        if department in department_key:
            log.debug(f'Image Path set to {path_value}')
            return path_value
    return None


def confirm(unc_path) -> int:
    cmd = f'powershell.exe Test-Path {unc_path}'
    test_path = subprocess.call(cmd)
    log.debug(f'test-path for image raw {str(test_path)}')
    return int(test_path)


# the main single-threaded function
def run_per_pc(pc) -> None:

    if ping(pc) != 0:
        log.error(f'{pc} OFFLINE!')
        return None

    asset_tag = read_registry(
        pc,
        BASIC_PATHS['AssetTagKey'],
        BASIC_PATHS['AssetTag_REG_SZ']
    )
    if not asset_tag:
        log.error(f'{pc} FAILED AT ASSET TAG')
        return None

    department = ownership_match(pc)
    if not department:
        department = OWNERSHIP['Fallback']

    contact_string = pair_contact_string(
        department,
        OWNERSHIP['ContactStrings'],
    )
    if not contact_string:
        log.error(f'{pc} FAILED AT CONTACT STRING')
        return None

    formatted_text = format_text(
        pc,
        asset_tag,
        contact_string
    )
    if not formatted_text:
        log.error(f'{pc} FAILED AT FORMATTING TEXT')
        return None

    unc_save_path = local_to_UNC_path(
        pc,
        BASIC_PATHS['LocalDestination']
    )
    if not unc_save_path:
        log.error(f'{pc} FAILED AT UNC PATH CONVERSION')
        return None

    image_source = decide_image_source(
        department,
        BASIC_PATHS['ImageSourcePaths']
    )
    if not image_source:
        log.error(f'{pc} FAILED AT DECIDE IMAGE SOURCE')
        return None

    write_image(
        image_source,
        formatted_text,
        unc_save_path
    )

    log.debug(f'{pc} wrote image')

    sleep(1)

    confirmation = confirm(unc_save_path)

    if confirmation == 0:
        log.info(f'{pc} Confirmed Success!')
    else:
        log.warning(f'{pc} NOT confirmed')


EXECUTOR = futures.ThreadPoolExecutor()
log.debug('Executor init')

# handles async


def main():
    for pc in target_list:
        pc = pc.upper()
        sleep(3)
        log.info(f'STARTED on {pc}')
        EXECUTOR.submit(run_per_pc, pc)
    log.debug('Executor Shutdown')
    EXECUTOR.shutdown()


if __name__ == '__main__':
    main()
