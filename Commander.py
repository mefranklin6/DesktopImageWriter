from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
import subprocess, yaml
#from concurrent import futures
#from time import sleep


with open('Config.yaml', 'r') as YAML_reader:
    config = yaml.safe_load(YAML_reader)

with open(config['TargetList'], 'r', encoding='utf-8') as target_list_file:
    target_list = target_list_file.readlines()


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
    return f'//{pc}/{drive}$/{path}'


# matches department and returns department contact string
def match_department( 
        pc : str,
        keywords : dict,
        department_strings : dict,
        fallback : str
    ) -> str:
    
    for key, value in keywords.items():
        if key in pc:
            return department_strings[value]
        else:
            return department_strings[fallback]
        


if specialNumberedWallpaper['SpecialRoomDetection'] == True:
    set_numbered_wallpaper = False #TODO: this



def read_registry(pc, registry_hive, registry_sz) -> str:
    # translate to microsoft style shashes
    registry_hive = registry_hive.replace('/', '\\') 

    cmd = subprocess.run(
        ['powershell.exe',
         f'Invoke-Command -ComputerName {pc} -ScriptBlock {{(Get-ItemProperty "{registry_hive}" -Name {registry_sz}).{registry_sz}}}'
        ],
        capture_output=True, 
        text=True
    )

    return str(cmd.stdout).upper().strip()


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

    return f'''
    Computer Name: {pc}
    Asset Tag: {asset_tag}
    {contact_string}
'''


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


def run_per_pc(pc):

    if ping(pc) == 0:
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


def main():
    for pc in target_list:
        pc = pc.replace('\n', '').upper()
        print(pc)
        run_per_pc(pc)


if __name__ == '__main__':
    main()

