# DesktopImageWriter
Tool that embeds computer-specific and department-specific support information onto the Windows Desktop Background/Wallpaper

Written for and at CSU Chico to reduce confusion over what office/department supports each computer.

## How-To:
1. Edit values in the Config.yaml file
2. Run main.py
3. Set desktop background to the path you set in 'LocalDestination' in the yaml.
    Note: this can be done via Group Policy at User Configuration > Policies > Admin Templates > Control Panel > Desktop > Desktop > DesktopWallpaper

## Requires:
- Windows 10+ on your machine and target machines
- Python 3.10+ on your machine (Written in Python 3.11.6)
- Pillow lib for Python on your machine.  (pip3 install Pillow, written with 10.0.0)
- PowershellRemoting enabled in your domain.
- Run by a user who is in the admin group on target machines.

# Config.yaml
TargetList: full path to text file containing a list of target PC's.  One PC per line, no spaces please.

## Basic Paths:
  ImageSourcePaths: full path(s) to an image to be used as desktop background.
  
  LocalDestination: this is where the modified image gets saved to each machine in the target list.  Please note that Windows will not check if this image has been changed unless the name of the image has been changed.

  LogFileDirectory: Location that the log file gets saved to.  A file called 'DesktopImageWriter_Log.log' will be saved here.  This can be anywhere you have write and modify rights to.  There is only one log file for all computers.

  AssetTagKey: Full path to key where the asset tag is stored in the registry.  Example: 'REGISTRY::HKEY_LOCAL_MACHINE/SOFTWARE/Chico'

  AssetTag_REG_SZ: String within the above key containing the asset tag.  Example 'Chico_AssetTag'

  
## Ownership:
  DepartmentRegexPatterns: if your org has a consistent naming pattern that ownership can be determined from, you can enter multiple key:value pairs here where the key is the regex pattern and the value is the owning department.

  DepartmentKeywords: same as above, but just using keywords.  This works at CSU Chico but may not work elsewhere.

  DepartmentOU: queries an Active Directory Domain Controller with Get-ADComputer and searches 'OU=' membership.

  Fallback: If all matching fails, this is the default department/office that you'll want people to call

  ContactStrings:  Key=Department/Office Value=Text to be written.  Ex: 'CTS' : 'Classroom Technology Services xxx-xxx-xxxx'

## TextPosition: This may take some trial and error to find an aesthetically pleasing location
  X: X-Axis, in pixels, that the text is written to
  Y: Y-Axis, in pixels, that the text is written to

  

  
