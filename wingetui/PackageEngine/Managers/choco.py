if __name__ == "__main__":
    # WingetUI cannot be run directly from this file, it must be run by importing the wingetui module
    import os
    import subprocess
    import sys
    sys.exit(subprocess.run(["cmd", "/C", "python", "-m", "wingetui"], shell=True, cwd=os.path.dirname(__file__).split("wingetui")[0]).returncode)


import os
import subprocess

from wingetui.Core.Tools import *
from wingetui.Core.Tools import _
from wingetui.PackageEngine.Classes import *


class ChocoPackageManager(PackageManagerWithSources):

    if getSettings("UseSystemChocolatey"):
        print("🟡 System chocolatey used")
        EXECUTABLE = "choco.exe"
    else:
        possiblePath = os.path.join(os.path.expanduser("~"), "AppData/Local/Programs/WingetUI/choco-cli/choco.exe")
        if os.path.isfile(possiblePath):
            print("🔵 Found default chocolatey installation on expected location")
            EXECUTABLE = possiblePath.replace("/", "\\")
        else:
            print("🟡 Chocolatey was not found on the default location, perhaps a portable WingetUI installation?")
            EXECUTABLE = os.path.join(os.path.join(realpath, "choco-cli"), "choco.exe").replace("/", "\\")
        os.environ["chocolateyinstall"] = os.path.dirname(EXECUTABLE)

    NAME = "Chocolatey"

    def __init__(self):
        super().__init__()
        self.IconPath = getMedia("choco")
        self.Capabilities.CanRunAsAdmin = True
        self.Capabilities.CanSkipIntegrityChecks = True
        self.Capabilities.CanRunInteractively = True
        self.Capabilities.SupportsCustomVersions = True
        self.Capabilities.SupportsCustomArchitectures = True
        self.Capabilities.SupportsPreRelease = True
        self.Capabilities.SupportsCustomSources = True

        self.Properties.Name = self.NAME
        self.Properties.Description = _("The classical package manager for windows. You'll find everything there. <br>Contains: <b>General Software</b>")
        self.Properties.Icon = getMedia("choco")
        self.Properties.ColorIcon = getMedia("choco_color")
        self.IconPath = self.Properties.Icon

        self.Properties.InstallVerb = "install"
        self.Properties.UpdateVerb = "upgrade"
        self.Properties.UninstallVerb = "uninstall"
        self.Properties.ExecutableName = "choco"

        self.KnownSources = [
            ManagerSource(self, "chocolatey", "https://community.chocolatey.org/api/v2/")
        ]

        self.BLACKLISTED_PACKAGE_NAMES = ["Did", "Features?", "Validation", "-", "being", "It", "Error", "L'accs", "Maximum", "This", "Output Is Package name ", "'chocolatey'", "Operable"]
        self.BLACKLISTED_PACKAGE_IDS = ["Did", "Features?", "Validation", "-", "being", "It", "Error", "L'accs", "Maximum", "This", "Output is package name ", "operable", "Invalid"]
        self.BLACKLISTED_PACKAGE_VERSIONS = ["Did", "Features?", "Validation", "-", "being", "It", "Error", "L'accs", "Maximum", "This", "packages", "current version", "installed version", "is", "program", "validations", "argument", "no"]

    def isEnabled(self) -> bool:
        return not getSettings(f"Disable{self.NAME}")

    def getPackagesForQuery(self, query: str) -> list[Package]:
        print(f"🔵 Searching packages on chocolatey for query {query}")
        packages: list[Package] = []
        try:
            p = subprocess.Popen([self.EXECUTABLE, "search", query], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, env=os.environ.copy())
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                if line:
                    if len(line.split(" ")) >= 2:
                        name = formatPackageIdAsName(line.split(" ")[0])
                        id = line.split(" ")[0]
                        version = line.split(" ")[1]
                        if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                            packages.append(Package(name, id, version, self.NAME, Choco))
            return packages
        except Exception as e:
            report(e)
            return packages

    def getAvailableUpdates(self) -> list[UpgradablePackage]:
        f"""
        Will retieve the upgradable packages by {self.NAME} in the format of a list[UpgradablePackage] object.
        """
        print(f"🔵 Starting {self.NAME} search for updates")
        try:
            packages: list[UpgradablePackage] = []
            p = subprocess.Popen([self.EXECUTABLE, "outdated"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            rawoutput = "\n\n---------" + self.NAME
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if line:

                    if len(line.split("|")) >= 3:
                        # Replace these lines with the parse mechanism
                        name = formatPackageIdAsName(line.split("|")[0])
                        id = line.split("|")[0]
                        version = line.split("|")[1]
                        newVersion = line.split("|")[2]
                        source = self.NAME
                    else:
                        continue

                    if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                        packages.append(UpgradablePackage(name, id, version, newVersion, source, Choco))
            print(f"🟢 {self.NAME} search for updates finished with {len(packages)} result(s)")
            Globals.PackageManagerOutput += rawoutput
            return packages
        except Exception as e:
            report(e)
            return []

    def getInstalledPackages(self, second_attempt=False) -> list[Package]:
        f"""
        Will retieve the intalled packages by {self.NAME} in the format of a list[Package] object.
        """
        print(f"🔵 Starting {self.NAME} search for installed packages")
        try:
            packages: list[Package] = []
            p = subprocess.Popen([self.EXECUTABLE, "list"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            rawoutput = "\n\n---------" + self.NAME
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if line:
                    if len(line.split(" ")) >= 2:
                        name = formatPackageIdAsName(line.split(" ")[0])
                        id = line.split(" ")[0]
                        version = line.split(" ")[1]
                        source = self.NAME
                        if id == "Chocolatey" and "v" in version:
                            continue
                        if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                            packages.append(Package(name, id, version, source, Choco))
            print(f"🟢 {self.NAME} search for installed packages finished with {len(packages)} result(s)")
            Globals.PackageManagerOutput += rawoutput
            if len(packages) <= 2 and not second_attempt:
                print("🟠 Chocolatey got too few installed packages, retrying")
                return self.getInstalledPackages(second_attempt=True)
            else:
                return packages
        except Exception as e:
            report(e)
            return []

    def getPackageDetails(self, package: Package) -> PackageDetails:
        """
        Will return a PackageDetails object containing the information of the given Package object
        """
        print(f"🔵 Starting get info for {package.Name} on {self.NAME}")
        details = PackageDetails(package)
        try:
            p = subprocess.Popen([self.EXECUTABLE, "info", package.Id], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            output: list[str] = []
            details.ManifestUrl = f"https://community.chocolatey.org/packages/{package.Id}"
            details.Architectures = ["x86"]
            isReadingDescription = False
            isReadingReleaseNotes = False
            while p.poll() is None:
                line = p.stdout.readline()
                if line:
                    output.append(str(line, encoding='utf-8', errors="ignore"))
            for line in output:
                if isReadingDescription:
                    if line.startswith("  "):
                        details.Description += "<br>" + line[2:]
                    else:
                        isReadingDescription = False
                if isReadingReleaseNotes:
                    if line.startswith("  "):
                        details.ReleaseNotes += "<br>" + line[2:]
                    else:
                        isReadingReleaseNotes = False
                        if details.ReleaseNotes != "":
                            if details.ReleaseNotes != "":
                                details.ReleaseNotesUrl = _("Not available")

                if "Title:" in line:
                    details.Name = line.split("|")[0].replace("Title:", "").strip()
                    details.UpdateDate = line.split("|")[1].replace("Published:", "").strip()
                elif "Author:" in line:
                    details.Author = line.replace("Author:", "").strip()
                elif "Software Site:" in line:
                    details.HomepageURL = line.replace("Software Site:", "").strip()
                elif "Software License:" in line:
                    details.LicenseURL = line.replace("Software License:", "").strip()
                elif "Package Checksum:" in line:
                    details.InstallerHash = "<br>" + (line.replace("Package Checksum:", "").strip().replace("'", "").replace("(SHA512)", ""))
                elif "Description:" in line:
                    details.Description = line.replace("Description:", "").strip()
                    isReadingDescription = True
                elif "Release Notes" in line:
                    details.ReleaseNotesUrl = line.replace("Release Notes:", "").strip()
                    details.ReleaseNotes = ""
                    isReadingReleaseNotes = True
                elif "Tags" in line:
                    details.Tags = [tag for tag in line.replace("Tags:", "").strip().split(" ") if tag != ""]
            details.Versions = []

            details.Description = ConvertMarkdownToHtml(details.Description)
            details.ReleaseNotes = ConvertMarkdownToHtml(details.ReleaseNotes)

            p = subprocess.Popen([self.EXECUTABLE, "find", "-e", package.Id, "-a"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            print(f"🟢 Starting get info for id {package.Id}")
            output = []
            while p.poll() is None:
                line = p.stdout.readline().strip()
                if b" " in line:
                    output.append(str(line, encoding='utf-8', errors="ignore"))
            for line in output:
                details.Versions.append(line.split(" ")[1])
            print(f"🟢 Get info finished for {package.Name} on {self.NAME}")
            return details
        except Exception as e:
            report(e)
            return details

    def getIcon(self, source: str) -> QIcon:
        if not self.LoadedIcons:
            self.LoadedIcons = True
            self.icon = QIcon(getMedia("choco"))
        return self.icon

    def getParameters(self, options: InstallationOptions, isAnUninstall: bool = False) -> list[str]:
        Parameters: list[str] = []
        if not isAnUninstall:
            if options.Architecture and options.Architecture == "x86":
                Parameters.append("--forcex86")
            if options.PreRelease:
                Parameters.append("--prerelease")
        if options.CustomParameters:
            Parameters += options.CustomParameters
        if options.InteractiveInstallation:
            Parameters.append("--notsilent")
        if options.SkipHashCheck and not isAnUninstall:
            Parameters += ["--ignore-checksums", "--force"]
        if options.Version and not isAnUninstall:
            Parameters += ["--version=" + options.Version, "--allow-downgrade"]
        return Parameters

    def startInstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [self.EXECUTABLE, "install", package.Id, "-y"] + self.getParameters(options)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ.copy())
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing {package.Name}").start()
        return p

    def startUpdate(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [self.EXECUTABLE, "upgrade", package.Id, "-y"] + self.getParameters(options)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} update with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ.copy())
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: updating {package.Name}").start()
        return p

    def installationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        counter = 0
        p.stdin = b"\r\n"
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        outputCode = p.returncode
        if outputCode in (1641, 3010):
            outputCode = RETURNCODE_OPERATION_SUCCEEDED
        elif outputCode == 3010:
            outputCode = RETURNCODE_NEEDS_RESTART
        elif ("Run as administrator" in output or "The requested operation requires elevation" in output or 'ERROR: Exception calling "CreateDirectory" with "1" argument(s): "Access to the path' in output) and outputCode != 0:
            outputCode = RETURNCODE_NEEDS_ELEVATION
        widget.finishInstallation.emit(outputCode, output)

    def startUninstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [self.EXECUTABLE, "uninstall", package.Id, "-y"] + self.getParameters(options)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command
        print(f"🔵 Starting {package} uninstall with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ.copy())
        Thread(target=self.uninstallationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: uninstalling {package.Name}").start()
        return p

    def uninstallationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        outputCode = RETURNCODE_OPERATION_SUCCEEDED
        counter = 0
        output = ""
        p.stdin = b"\r\n"
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = line.strip()
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        outputCode = p.returncode
        if outputCode in (1605, 1614, 1641):
            outputCode = RETURNCODE_OPERATION_SUCCEEDED
        elif outputCode == 3010:
            outputCode = RETURNCODE_NEEDS_RESTART
        elif "Run as administrator" in output or "The requested operation requires elevation" in output:
            outputCode = RETURNCODE_NEEDS_ELEVATION
        widget.finishInstallation.emit(outputCode, output)

    def getSources(self) -> None:
        print(f"🔵 Starting {self.NAME} source search...")
        p = subprocess.Popen(f"{self.EXECUTABLE} source list", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
        output = []
        sources: list[ManagerSource] = []
        counter = 0
        while p.poll() is None:
            line = p.stdout.readline()
            line = line.strip()
            if line:
                if counter > 0 and b"---" not in line:
                    output.append(str(line, encoding='utf-8', errors="ignore"))
                else:
                    counter += 1
        counter = 0
        for element in output:
            try:
                while "  " in element.strip():
                    element = element.strip().replace("  ", " ")
                element: list[str] = element.split("|")
                sources.append(ManagerSource(self, element[0].strip().split(" - ")[0], element[0].strip().split(" - ")[1]))
            except IndexError:
                continue

        print(f"🟢 {self.NAME} source search finished with {len(sources)} sources")
        return sources

    def installSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [self.EXECUTABLE, "source", "add", "--name", source.Name, "--source", source.Url, "-y"]
        print(f"🔵 Starting source {source.Name} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def uninstallSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = [self.EXECUTABLE, "source", "remove", "--name", source.Name, "-y"]
        print(f"🔵 Starting source {source.Name} removal with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def sourceProgressThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        counter = 0
        p.stdin = b"\r\n"
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                widget.addInfoLine.emit((line, is_newline))
                counter += 1
                widget.counterSignal.emit(counter)
                if is_newline:
                    output += line + "\n"
        p.wait()
        widget.finishInstallation.emit(p.returncode, output)

    def detectManager(self, signal: Signal = None) -> None:
        o = subprocess.run(f"{self.EXECUTABLE} -v", shell=True, stdout=subprocess.PIPE)
        Globals.componentStatus[f"{self.NAME}Found"] = shutil.which(self.EXECUTABLE) is not None
        Globals.componentStatus[f"{self.NAME}Version"] = o.stdout.decode('utf-8').replace("\n", " ").replace("\r", " ")

        if getSettings("ShownWelcomeWizard") and not getSettings("UseSystemChocolatey") and not getSettings("ChocolateyAddedToPath") and not os.path.isfile(r"C:\ProgramData\Chocolatey\bin\choco.exe"):
            # If the user is running bundled chocolatey and chocolatey is not in path, add chocolatey to path
            subprocess.run("powershell -NoProfile -Command [Environment]::SetEnvironmentVariable(\\\"PATH\\\", \\\"" + self.EXECUTABLE.replace('\\choco.exe', '\\bin') + ";\\\"+[Environment]::GetEnvironmentVariable(\\\"PATH\\\", \\\"User\\\"), \\\"User\\\")", shell=True, check=False)
            subprocess.run(f"powershell -NoProfile -Command [Environment]::SetEnvironmentVariable(\\\"chocolateyinstall\\\", \\\"{os.path.dirname(self.EXECUTABLE)}\\\", \\\"User\\\")", shell=True, check=False)
            print("🔵 Adding chocolatey to path...")
            setSettings("ChocolateyAddedToPath", True)

        if signal:
            signal.emit()

    def updateSources(self, signal: Signal = None) -> None:
        pass  # Handled by the package manager, no need to manually reload
        if signal:
            signal.emit()


Choco = ChocoPackageManager()
