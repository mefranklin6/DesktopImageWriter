import subprocess
from concurrent import futures
from time import sleep
import pyyaml





Executor = futures.ThreadPoolExecutor()


def RunCommand (pc):
    subprocess.run(
                    [
                    'powershell.exe',
                    'C:/Users/mefranklin/Documents/Github/DeploymentScripts/PC-ConfigurationScript/./GatherFacts.ps1', 
                    pc,
                    Config['Sqlite3_exe'],
                    Config['DB_Path']
                    ]
    )


for PC in InvList:
    sleep(3)
    Executor.submit(RunCommand, PC)


Executor.shutdown()

print('Scan Executor Shutdown')
