import json
import os
import re
import subprocess

import xlsxwriter

root_dir = os.path.join(os.path.dirname(__file__), "..")
os.chdir(os.path.join(root_dir, "WebBasedData"))

contents = json.load(open("screenshot-database-v2.json"))

def getwingetPackages():
    packageList = []
    p = subprocess.Popen(["mode", "400,30&", "winget", "search", ""], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
    output = []
    counter = 0
    idSeparator = 0
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            if(counter > 0):
                if not b"---" in line:
                    output.append(str(line, encoding='utf-8', errors="ignore"))
            else:
                l = str(line, encoding='utf-8', errors="ignore").replace("\x08-\x08\\\x08|\x08 \r","")
                l = l.split("\r")[-1]
                if("Id" in l):
                    idSeparator = len(l.split("Id")[0])
                    verSeparator = idSeparator+2
                    i=0
                    while l.split("Id")[1].split(" ")[i] == "":
                        verSeparator += 1
                        i += 1
                    counter += 1
    counter = 0
    for element in output:
        try:
            verElement = element[idSeparator:].strip()
            verElement.replace("\t", " ")
            while "  " in verElement:
                verElement = verElement.replace("  ", " ")
            iOffset = 0
            id = verElement.split(" ")[iOffset+0]
            if len(id)==1:
                iOffset + 1
                id = verElement.split(" ")[iOffset+0]
            if not "  " in element[0:idSeparator].strip():
                packageList.append(id)
            else:
                print(f"🟡 package {element[0:idSeparator].strip()} failed parsing, going for method 2...")
                element = bytes(element, "utf-8")
                print(element, verSeparator)
                export = (element[0:idSeparator], str(element[idSeparator:], "utf-8").strip().split(" ")[0], )
                packageList.append(export[1])
        except Exception as e:
            try:
                print(e)
                try:
                    element = str(element, "utf-8")
                except Exception as e:
                    print(e)
                packageList.append(element[idSeparator:verSeparator].strip())
            except Exception as e:
                print(e)
                print()
    return sorted(packageList)


def getScoopPackages():
    pkgs = []
    print("🟢 Starting scoop search...")
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    p = subprocess.Popen(' '.join(["powershell", "-NoProfile", "-Command", "scoop", "search"]), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
    output = []
    counter = 0
    while p.poll() is None:
        line = p.stdout.readline()
        line = line.strip()
        if line:
            if(counter > 1 and not b"---" in line):
                output.append(ansi_escape.sub('', str(line, encoding='utf-8', errors="ignore")))
            else:
                counter += 1
    counter = 0
    for element in output:
        try:
            pkgs.append(element.split(" ")[0].strip())
        except IndexError as e:
            print("IndexError: "+str(e))
    print("🟢 Scoop search finished")
    return sorted(pkgs)

def getChocolateyPackages() -> None:
    pkgs = []
    versions = {}
    CHOCO_BLACKLISTED_PACKAGES = ["Did", "Features?", "Validation", "-", "being", "It"]
    print("🔵 Starting choco search")
    cacheFile = os.path.join(os.path.expanduser("~"), ".wingetui/cacheddata/chocolateypackages")
    cachePath = os.path.dirname(cacheFile)
    if not os.path.exists(cachePath):
        os.makedirs(cachePath)
    if os.path.exists(cacheFile):
        with open(cacheFile, "r") as f:
            content = f.read()
            if content != "":
                print("🟢 Found valid cache for chocolatey!")
                for line in content.split("\n"):
                    export = line.split(" ")
                    if len(export) > 1 and not export[0] in CHOCO_BLACKLISTED_PACKAGES:
                        pkgs.append(export[0])
                        versions[export[0]] = export[1]
    return pkgs, versions


try:
    os.remove("screenshot_database.xlsx")
except FileNotFoundError:
    pass
except PermissionError:
    input("PermissionError while deleting the old exe file.")
    import sys
    sys.exit(1)

workbook = xlsxwriter.Workbook('screenshot_database.xlsx', {'strings_to_urls': False})

worksheet = workbook.add_worksheet()

boldformat = workbook.add_format({"bold": True})
boldformat.set_locked(True)
iconformat = workbook.add_format()
iconformat.set_left(2)
iconformat.set_left_color("#888888")
iconformat.set_right(1)
iconformat.set_right_color("#888888")
iconformat.set_top(2)
iconformat.set_bottom(2)
iconformat.set_text_wrap()
iconformat.set_bg_color("#F9E6BD")
iconformat.set_locked(False)
screenshotformat = workbook.add_format()
screenshotformat.set_left(1)
screenshotformat.set_left_color("#888888")
screenshotformat.set_right_color("#888888")
screenshotformat.set_top(2)
screenshotformat.set_bottom(2)
screenshotformat.set_text_wrap()
screenshotformat.set_locked(False)
screenshotformat.set_bg_color("#BDF9F9")
idformat = workbook.add_format()
idformat.set_left(1)
idformat.set_left_color("#888888")
idformat.set_right(1)
idformat.set_right_color("#888888")
idformat.set_top(2)
idformat.set_bottom(2)
idformat.set_text_wrap()
idformat.set_bg_color("#D6BDF9")
idformat.set_locked(True)
worksheet.write('A1', 'Package id', boldformat)
worksheet.write('B1', 'Icon URL (PNG Only)', boldformat)
worksheet.write('C1', 'Screenshot 1 URL (PNG ONLY)', boldformat)
worksheet.write('D1', 'Screenshot 2 URL (PNG ONLY)', boldformat)
worksheet.write('E1', 'Screenshot 3 URL (PNG ONLY)', boldformat)
worksheet.write('F1', 'Screenshot 4 URL (PNG ONLY)', boldformat)
worksheet.write('G1', 'Screenshot 5 URL (PNG ONLY)', boldformat)
worksheet.write('H1', 'Screenshot 6 URL (PNG ONLY)', boldformat)
worksheet.write('I1', 'Screenshot 7 URL (PNG ONLY)', boldformat)
worksheet.write('J1', 'Screenshot 8 URL (PNG ONLY)', boldformat)
worksheet.write('K1', 'Screenshot 9 URL (PNG ONLY)', boldformat)
worksheet.write('L1', 'Even more screenshots, one URL per cell', boldformat)
worksheet.set_column_pixels(0, 1, 300)
worksheet.set_column_pixels(1, 2, 300)
worksheet.set_column_pixels(2, 3, 250)
worksheet.set_column_pixels(3, 23, 260)

def getRow(n):
    alphabet = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z")
    if n < 26:
        return alphabet[n]
    elif n < 26**26:
        return alphabet[(n//26)-1]+alphabet[n%26]

done = []

print("Generating Winget packages...")

wingetCount = 0
wingetTotal = 0

counter = 3
for id in getwingetPackages():
    iconId = ".".join(id.split(".")[1:])
    iconId = iconId.replace(" ", "-").replace("_", "-").replace(".", "-").lower()
    worksheet.write("A"+str(counter), iconId, idformat)
    wingetCount += 1
    wingetTotal += 1
    try:
        item = contents["icons_and_screenshots"][iconId]
        worksheet.write("B"+str(counter), str(item["icon"]), iconformat)
        if str(item["icon"]).strip() != "":
            done.append(iconId)
        for i in range(2, len(item["images"])+2):
            worksheet.write(getRow(i)+str(counter), item["images"][i-2], screenshotformat)
    except KeyError:
        pass
    counter += 1

print("Generating Scoop packages...")

scoopCount = 0
scoopTotal = 0

for id in getScoopPackages():
    iconId = id.replace(" ", "-").replace("_", "-").replace(".", "-").lower()
    scoopTotal += 1
    if not iconId in done:
        scoopCount += 1
        worksheet.write("A"+str(counter), iconId, idformat)
        try:
            item = contents["icons_and_screenshots"][iconId]
            worksheet.write("B"+str(counter), str(item["icon"]), iconformat)
            if str(item["icon"]).strip() != "":
                done.append(iconId)
            for i in range(2, len(item["images"])+2):
                worksheet.write(getRow(i)+str(counter), item["images"][i-2], screenshotformat)
        except KeyError:
            pass
        counter += 1

print("Generating Chocolatey packages...")

chocoCount = 0
chocoTotal = 0

a = getChocolateyPackages()
chocopkgs = a[0]
chocoversions = a[1]
for id in chocopkgs:
    iconId = id.replace(".install", "").replace(".portable", "").replace(" ", "-").replace("_", "-").replace(".", "-").lower()
    chocoTotal += 1
    if not iconId in done:
        chocoCount += 1
        worksheet.write("A"+str(counter), iconId, idformat)
        try:
            item = contents["icons_and_screenshots"][iconId]
            worksheet.write("B"+str(counter), str(item["icon"] if item["icon"] not in ("", None) else f"https://community.chocolatey.org/content/packageimages/{id}.{chocoversions[id]}.png"), iconformat)
            done.append(iconId)
            for i in range(2, len(item["images"])+2):
                worksheet.write(getRow(i)+str(counter), item["images"][i-2], screenshotformat)
        except KeyError:
            worksheet.write("B"+str(counter), str(f"https://community.chocolatey.org/content/packageimages/{id}.{chocoversions[id]}.png"), iconformat)
        counter += 1
    else:
        print("Skipped", id, iconId)

workbook.close()

print()
print("Winget total packages:", wingetTotal)
print("Winget added packages:", wingetCount)
print("Scoop total packages:", scoopTotal)
print("Scoop added packages:", scoopCount)
print("Chocolatey total packages:", chocoTotal)
print("Chocolatey added packages:", chocoCount)

os.startfile("https://drive.google.com/drive/u/2/folders/1TOO3rupM1e793z-jlwNcQMGCqDL8fFOL")
print()
subprocess.Popen(r'explorer /select,"'+os.path.abspath("screenshot_database.xlsx").replace("/", "\\")+'"')
