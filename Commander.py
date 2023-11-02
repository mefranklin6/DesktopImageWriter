import subprocess, yaml
from concurrent import futures
from time import sleep


with open('Config.yaml', 'r') as YAML_reader:
    config = yaml.safe_load(YAML_reader)

with open(config['TargetList'], 'r') as target_list_file:
    target_list = target_list_file.readlines()


basicPaths = config['BasicPaths']
ownership = config['Ownership']
specialNumberedWallpaper = config['SpecialNumberedWallpaper']

executor = futures.ThreadPoolExecutor()


def RunCommand (pc):
    subprocess.run(
                [
                    'powershell.exe',
                    './SetWallpaper.ps1', 
                    pc,
                    basicPaths['RegularImagePath'],
                    basicPaths['LocalDestination'],
                    basicPaths['ImageTextWriterLocation'],
                    basicPaths['LogFileLocation'],
                    config['PythonVersion'],
                    ownership['DepartmentKeywords'],
                    ownership['Fallback'],
                    ownership['ContactStrings'],
                    specialNumberedWallpaper['SpecialRoomDetection'],
                    specialNumberedWallpaper['NumberedBackgroundDirectory'],
                    specialNumberedWallpaper['SpecialRooms'],
                    basicPaths['AssetTagHive'],
                    basicPaths['AssetTag_REG_SZ'],

                ]
    )


for pc_target in target_list:
    sleep(3)
    print(pc_target)
    RunCommand(pc_target)


executor.shutdown()
print('Executor Shutdown')
