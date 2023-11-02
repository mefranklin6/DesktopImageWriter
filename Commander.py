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
                    str:basicPaths['RegularImagePath'],
                    str:basicPaths['LocalDestination'],
                    str:basicPaths['ImageTextWriterLocation'],
                    str:basicPaths['LogFileLocation'],
                    str:config['PythonVersion'],
                    dict:ownership['DepartmentKeywords'],
                    str:ownership['Fallback'],
                    dict:ownership['ContactStrings'],
                    bool:specialNumberedWallpaper['SpecialRoomDetection'],
                    str:specialNumberedWallpaper['NumberedBackgroundDirectory'],
                    dict:specialNumberedWallpaper['SpecialRooms'],
                    str:basicPaths['AssetTagHive'],
                    str:basicPaths['AssetTag_REG_SZ'],

                ]
    )


for pc_target in target_list:
    sleep(3)
    executor.submit(RunCommand, pc_target)


executor.shutdown()
print('Executor Shutdown')
