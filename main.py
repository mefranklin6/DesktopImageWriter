from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import subprocess, yaml
import logging as log
#from concurrent import futures
#from time import sleep


with open('Config.yaml', 'r') as YAML_reader:
    config = yaml.safe_load(YAML_reader)

log.basicConfig(
        filename=f'{config["BasicPaths"]["LogFileDirectory"]}/DesktopImageWriter_Log.log',
        encoding='utf-8',
        level=log.DEBUG
)

log.debug(f'Config: {str(config)}')


try:
    with open(config['TargetList'], 'r', encoding='utf-8') as target_list_file:
        target_list = target_list_file.readlines()
        log.debug(f'Target List: {target_list}')
except:
    log.fatal(f'Can not open target list at {config["TargetList"]}')
    exit(1)


# YAML Sections
basicPaths = config['BasicPaths']
ownership = config['Ownership']
specialNumberedWallpaper = config['SpecialNumberedWallpaper']


def ping(ip : str) -> int:
    return subprocess.call(f'powershell.exe ping -n 1 {ip}')
    # returns 0 for online, 1 for error


def local_to_UNC_path (pc : str, local_path : str) -> str:
    local_parts = local_path.replace('/', '').split(':')
    drive = local_parts[0]
    path = local_parts[1]
    format = f'//{pc}/{drive}$/{path}'
    
    log.debug(f'Local Path: {local_path}')
    log.debug(f'UNC Path: {format}')
    
    return format


# matches department and returns department contact string
def match_department( 
        pc : str,
        keywords : dict,
        department_strings : dict,
        fallback : str
    ) -> str:
    
    for key, value in keywords.items():
        if key in pc:
            log.info(f'Match! {pc} managed by {key}')
            return department_strings[value]
        else:
            log.warning(f'{pc} managed by {department_strings[fallback]} (fallback, no match)')
            return department_strings[fallback]
        

if specialNumberedWallpaper['SpecialRoomDetection'] == True:
    log.info('attempting to match special room')
    



    def detect_special_room(pc) -> bool:
        for room, max_number in specialNumberedWallpaper['SpecialRooms'].items():
            if room in pc:
                log.debug(f'{pc} detected as special room {room} with {max_number} of stations')
                return True
            log.debug(f'{pc} not in a special room')
            return False
    

    def match_special_room(pc):
        if detect_special_room(pc):
            pass

    match_special_room(pc)



    
    
    
    set_numbered_wallpaper = False #TODO: this




def read_registry(pc, registry_hive, registry_sz) -> str:
    # translate to microsoft style shashes
    registry_hive = registry_hive.replace('/', '\\') 

    invoke_command = f'Invoke-Command -ComputerName {pc} -ScriptBlock {{(Get-ItemProperty "{registry_hive}" -Name {registry_sz}).{registry_sz}}}'
    log.debug(f'Invoke-Command String: {invoke_command}')
    
    cmd = subprocess.run(
        [
        'powershell.exe',
         invoke_command
        ],
        capture_output=True, 
        text=True
    )

    log.debug(f'invoke command raw return: {str(cmd)}')

    asset_tag = str(cmd.stdout).upper().strip()
    log.info(f'{pc} asset tag: {asset_tag}')
    
    return asset_tag


def format_text(pc):
    
    asset_tag = read_registry(
        pc, 
        basicPaths['AssetTagHive'],
        basicPaths['AssetTag_REG_SZ']
    )

    contact_string = match_department (
        pc,
        ownership['DepartmentKeywords'],
        ownership['ContactStrings'],
        ownership['Fallback']
    )
    
    format = f'''
    Computer Name: {pc}
    Asset Tag: {asset_tag}
    {contact_string}
'''
    log.debug(f'format_text output {format}')
    
    return format


def write_image(image_location, text_to_write, out_file):
    image = Image.open(image_location) 
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype('arial.ttf', 30)
    text_position = (1400, 1125)
    outline_color = 'black'
    text_color = 'white'

    text = text_to_write

    # offset handles text outline since there's no built-in way to do that
    x, y = text_position
    for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
    draw.text(text_position, text, font=font, fill=text_color)
    image.save(out_file)


def confirm(pc):
    cmd = f'powershell.exe Test-Path -ComputerName {pc}'
    test_path = subprocess.call(cmd)
    log.debug(f'test-path for image raw {str(test_path)}')
    return test_path


def run_per_pc(pc):

    if ping(pc) == 0:
        log.debug(f'{pc} Online')
        text = format_text(pc)
        unc_path = local_to_UNC_path(
            pc,
            basicPaths['LocalDestination']
        )
        write_image(
            basicPaths['RegularImagePath'],
            text,
            unc_path
        )
        confirmation = confirm(pc)
        if confirmation == 0:
            log.info(f'ENDED on {pc}. Result 0')
        else:
            log.warning(f'Did not detect image on {pc}!')
    else:
        log.error(f'{pc} is offline, skipping')
        log.info(f'ENDED on {pc}. Result 1')


def main():
    for pc in target_list:
        pc = pc.replace('\n', '').upper()
        log.info(f'STARTED on {pc}')
        run_per_pc(pc)



if __name__ == '__main__':
    main()

