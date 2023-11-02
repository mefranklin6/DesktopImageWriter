import yaml


'''
Takes the Config.yml file and loads it into a Python file named pyconfig
This way you can simply import pyconfig in scripts

Just make sure to run this file every time the YAML changes'''

def main():

    with open('Config.yml', 'r') as YAMLFile:
        Config = yaml.safe_load(YAMLFile)
    
    with open('pyconfig.py', 'w') as f:
        f.write(f'config = {str(Config)}')

    print('Loaded Config.yml into pyconfig')



if __name__ == '__main__ ':
    main()
