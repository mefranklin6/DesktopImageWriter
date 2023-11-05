import re

def match_special_room(pc):
    room, max_number = ('THMA116', 7)
        
    if room is None:
        return None
        
    else:
        cleaned = pc.replace(str(room), '').replace('-','')
        print(cleaned)
        try: 
            digits_only = re.search(r'(\d+)', cleaned)[1]
            print(digits_only)

        except:
            print('no match')
            return None
        
        if int(digits_only) > max_number:
            print('too many')

match_special_room('SC-THMA116-7a')