import re, yaml, subprocess


with open('Config.yaml', 'r') as YAML_reader:
    config = yaml.safe_load(YAML_reader)

patterns = config['Ownership']['DepartmentRegexPatterns']

with open('C:/Temp/alltargets.txt', 'r', encoding='utf-8') as f:
    inv_list = f.read().splitlines()



def strict_matching(pc:str, department_regex_patterns:dict):
    for pattern, department in department_regex_patterns.items():
        if re.match(pattern, pc):
            return (pc, department)
    return None

def loose_matching(pc:str, department_keywords:dict):
    for key, department in department_keywords.items():
        if key in pc:
            return (pc, department)
    return None
        
def AD_QueryMatching(pc:str, ou_keywords:dict):
    AD_query_base = 'Get-ADComputer -Filter '
    AD_query_filter = f'Name -like "{pc}"'
    AD_Query = f"{AD_query_base}'{AD_query_filter}'"
            
    AD_Return = subprocess.run(
                [
                    'powershell.exe',
                     AD_Query
                ],
                capture_output=True
    )

    if AD_Return.returncode == 0:
        for ou, ou_department in ou_keywords.items():
            if f'OU={ou}' in str(AD_Return):
                return (pc, ou_department)
    return None


            
        


for i in inv_list:
    matched = False
    for pattern, name in patterns.items():
        if re.match(pattern, i):
            print(f'{i} -- {name} -- Strong')
            matched = True
            break
    if not matched:
        if 'SC-' in i:
            print(f'{i} -- CTS Classroom -- WEAK!')
        elif 'CONF-' in i:
            print(f'{i} -- CTS Conf -- WEAK!')
        else:
            # build the query in parts to be compatiable with powershell quotes
            AD_query_base = 'Get-ADComputer -Filter '
            AD_query_filter = f'Name -like "{i}"'
            AD_Query = f"{AD_query_base}'{AD_query_filter}'"
            
            AD_Return = subprocess.run(
                [
                    'powershell.exe',
                     AD_Query
                ],
                capture_output=True
            )

            if AD_Return.returncode == 0:

                for ou, ou_department in config['Ownership']['DepartmentOU'].items():
                    if f'OU={ou}' in str(AD_Return):
                        print(f'AD MATCHED {i} -- {ou_department}')

            else:
                print('TOTAL AND COMPLETE FAILURE')


        

