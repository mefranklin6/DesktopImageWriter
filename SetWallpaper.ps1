Param(
    [Parameter(Mandatory=$true)]
    [string]$PC,

    [Parameter(Mandatory=$true)]
    [string]$RegularImagePath,

    [Parameter(Mandatory=$true)]
    [string]$LocalDestination,

    [Parameter(Mandatory=$true)]
    [string]$ImageTextWriterLoc,

    [Parameter(Mandatory=$true)]
    [string]$LogFileLocation,

    [Parameter(Mandatory=$true)]
    [string]$PythonVersion,

    [Parameter(Mandatory=$true)]
    [hashtable]$DepartmentKeywords,

    [Parameter(Mandatory=$true)]
    [string]$OwnershipFallback,

    [Parameter(Mandatory=$true)]
    [hashtable]$ContactStrings,

    [Parameter(Mandatory=$true)]
    [bool]$SpecialRoomDetection,

    [Parameter(Mandatory=$true)]
    [string]$NumberedBackgroundDir,

    [Parameter(Mandatory=$true)]
    [hashtable]$SpecialRooms,

    [Parameter(Mandatory=$true)]
    [string]$AssetTagHive,

    [Parameter(Mandatory=$true)]
    [string]$AssetTag_REG_SZ

)
Write-Output $LogFileLocation

function Log ($message) {
    $LogTime = Get-Date -DisplayHint Time
    $LogTime = $LogTime.ToString()
    Write-Output $message
    $LogStr = "$LogTimeStr  -  $PC  -  $message"
    $LogStr | Out-File "$LogFileLocation/$PC_Wallpaper.txt" -Append
    }


Log "INFO: STARTED Write Wallpaper for $PC"

if (!(Test-Connection -ComputerName $PC -Count 1)) {
    Log "FATAL: $PC IS NOT ONLINE OR WRONG NAME"
    Quit
}

# Form UNC path from $LocalDestination setting
$LocalDestParts = $LocalDestination.split(':').Replace('\', '')
$LocalDrive = $LocalDestParts[0]
$LocalPath = $LocalDestParts[1]
$LocalDestination_UNC = "\\$PC\$LocalDrive$\$LocalPath"

$PythonCommand = "python$PythonVersion"

$PC = $PC.ToUpper()


$MatchedDepartmentKey = $null
$Department = $null

foreach ($department_key in $DepartmentKeywords.Keys) {
    if ($PC -like $department_key) {
        $MatchedDepartmentKey = $department_key
        Write-Output "MATCHED KEY $MatchedDepartmentKey"
        Break
    }
}


try {
    $Department = $DepartmentKeywords[$MatchedDepartmentKey]
}
catch {
    $Department = 'ITSS'
}
Write-Output $Department

# Python script that adds text to .jpg image
# This .ps1 will write and call the .py if it's not already found
$ImageTextWriterCode = @'

from PIL import Image, ImageDraw, ImageFont
import sys

# Call '& python3.x' (your installed version) from powershell and pass these params:
# Params :
#    0 - This file name and location
#    1 - Path of base image to add text to (won't overwrite the original)
#    2 - here-string of text to add to the image (line breaks are preserved)
#    3 - location to save edited picture to 

image = Image.open(sys.argv[1]) 
draw = ImageDraw.Draw(image)

font = ImageFont.truetype('arial.ttf', 30)
text_position = (1500, 1050)
outline_color = 'black'
text_color = 'white'

# drops carriage return to handle encoding bug from powershell to python
text = str(sys.argv[2]).replace('\r\n', '\n')

# offset handles text outline since there's no built-in way to do that
x, y = text_position
for offset in [(1, 1), (-1, -1), (1, -1), (-1, 1)]:
    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=outline_color)
draw.text(text_position, text, font=font, fill=text_color)
image.save(sys.argv[3])

'@


if (!(Test-Path $ImageTextWriterLoc)) {
    Set-Content $ImageTextWriterLoc $ImageTextWriterCode
    Log "INFO: Writing ImageTextWriter.py to $ImageTextWriterLoc"
}


###################################################################################################


$SpecialErrorMsg = @"
ERROR: PC in special room should be named like 'SC-THMA116-11'
Defaulting to regular background for $PC
"@ 


$SetNumberedBackground = $false # reset

if ($SpecialRoomDetection -eq $true) {
    foreach ($key in $SpecialRooms.Keys) {
        if ($PC -like "$key*") {
            Log "$key detected, attempting to set numbered backgound"
            $SetNumberedBackground = $true
            $Room = $key
            Break
        }
    }
}


$AssetTag = Invoke-Command -ComputerName $PC -ScriptBlock {
    (Get-ItemProperty "$AssetTagHive" -Name $AssetTag_REG_SZ).$AssetTag_REG_SZ
}

$AssetTag = $AssetTag.ToUpper()


$BackgroundText = @"
Computer Name: $PC
Asset Tag: $AssetTag
$ContactStrings[$Department]
"@


# for special rooms:
while ($SetNumberedBackground -eq $true) {

    $PCStationNumber = $null

    # while there's anything but a number at the end...
    # strip the end of the string until it hits a number
    $PCMatchStr = $PC
    while (!($PCMatchStr -match "\d+$")) {
        $PCMatchStr = $PCMatchStr -replace ".$" 
    }

    $DashCount = [Regex]::Matches($PCMatchStr, '-').count
    if ($DashCount -lt 2) {
        Log "No station numbering detected"
        $SetNumberedBackground = $false
        Break
    }

    $PCStationNumber = $PCMatchStr.Split('-')[-1]
    $PCStationNumber = [int]$PCStationNumber
    Log "INFO: Station $PCStationNumber detected for $PC"

    if ($PCStationNumber -gt $SpecialRooms[$Room]) {
        $MaxValue = $SpecialRooms[$Room]
        Log "ERROR: $MaxValue is maximum amount of stations in this room"
        $SetNumberedBackground = $false
        Break
    }

    if ($PCStationNumber -eq $null) {
        Log $SpecialErrorMsg
        $SetNumberedBackground = $false
        Break
        
        if (!(Test-Path $NumberedBackgroundFolder)) {
            Log "ERROR: CAN NOT ACCESS NUMBERED BACKGROUND FOLDER"
            $SetNumberedBackground = $false
            Break
        }
    }

    # enumerate folder contents
    $NumBgDirChild = Get-ChildItem $NumberedBackgroundDir

    # format string for matching.  Based on ex: 'Background Numbered 12.jpg'
    $MatchString = ' ' + $PCStationNumber + '.jpg'
    
    # match the .jpg
    $DirChildItem = $NumBgDirChild -match $MatchString
    
    # format path to matched .jpg
    $SelectedNumberedBackgroundLoc = $DirChildItem

    # write the file
    $params = 
        "$ImageTextWriterLoc",
        "$SelectedNumberedBackgroundLoc",
        "$BackgroundText",
        "$LocalDestination_UNC"

    & $PythonCommand @params

    Break # only want to run the loop once
          # it's only a loop so we can quickly fallback to setting non-numbered backgrounds
} 

# for standard rooms
if ($SetNumberedBackground -eq $false) {
    Log "INFO: Writing Regular Background to $PC"

    $params = 
        "$ImageTextWriterLoc",
        "$RegularImagePath",
        "$BackgroundText",
        "$LocalDestination_UNC"
    
        & $PythonCommand @params
}

Start-Sleep -Seconds 2 # allow extra time for file copy


if (Test-Path $LocalDestination_UNC) {
    Log "INFO: Success!  Image has been saved to $LocalDestination_UNC"

}
else {
    Log "ERROR: Image not detected at $LocalDestination_UNC"
}

