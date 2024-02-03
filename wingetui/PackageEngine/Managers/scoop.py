if __name__ == "__main__":
    # WingetUI cannot be run directly from this file, it must be run by importing the wingetui module
    import os
    import subprocess
    import sys
    sys.exit(subprocess.run(["cmd", "/C", "python", "-m", "wingetui"], shell=True, cwd=os.path.dirname(__file__).split("wingetui")[0]).returncode)

import os
import re
import subprocess

from wingetui.Core.Tools import *
from wingetui.Core.Tools import _
from wingetui.PackageEngine.Classes import *


class ScoopPackageManager(PackageManagerWithSources):

    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    EXECUTABLE = "powershell -NoProfile -ExecutionPolicy ByPass -Command scoop"

    NAME = "Scoop"

    def __init__(self):
        super().__init__()
        self.Capabilities.CanRunAsAdmin = True
        self.Capabilities.CanSkipIntegrityChecks = True
        self.Capabilities.CanRemoveDataOnUninstall = True
        self.Capabilities.SupportsCustomArchitectures = True
        self.Capabilities.SupportsCustomScopes = True
        self.Capabilities.SupportsCustomSources = True
        self.Capabilities.Sources.KnowsPackageCount = True
        self.Capabilities.Sources.KnowsUpdateDate = True

        self.Properties.Name = self.NAME
        self.Properties.Description = _("Great repository of unknown but useful utilities and other interesting packages.<br>Contains: <b>Utilities, Command-line programs, General Software (extras bucket required)</b>")
        self.Properties.Icon = getMedia("scoop")
        self.Properties.ColorIcon = getMedia("scoop_color")
        self.IconPath = self.Properties.Icon

        self.Properties.InstallVerb = "install"
        self.Properties.UpdateVerb = "update"
        self.Properties.UninstallVerb = "uninstall"
        self.Properties.ExecutableName = "scoop"

        self.KnownSources = [
            # This list should reflect the one published on https://github.com/ScoopInstaller/Scoop/blob/master/buckets.json
            ManagerSource(self, "main", "https://github.com/ScoopInstaller/Main"),
            ManagerSource(self, "extras", "https://github.com/ScoopInstaller/Extras"),
            ManagerSource(self, "versions", "https://github.com/ScoopInstaller/Versions"),
            ManagerSource(self, "nirsoft", "https://github.com/kodybrown/scoop-nirsoft"),
            ManagerSource(self, "sysinternals", "https://github.com/niheaven/scoop-sysinternals"),
            ManagerSource(self, "php", "https://github.com/ScoopInstaller/PHP"),
            ManagerSource(self, "nerd-fonts", "https://github.com/matthewjberger/scoop-nerd-fonts"),
            ManagerSource(self, "nonportable", "https://github.com/ScoopInstaller/Nonportable"),
            ManagerSource(self, "java", "https://github.com/ScoopInstaller/Java"),
            ManagerSource(self, "games", "https://github.com/Calinou/scoop-games"),
        ]

    def isEnabled(self) -> bool:
        return not getSettings(f"Disable{self.NAME}")

    def getPackagesForQuery(self, query: str) -> list[Package]:
        f"""
        Will retieve the packages for the given "query: str" from the package manager {self.NAME} in the format of a list[Package] object.
        """
        print(f"🔵 Starting {self.NAME} search for dynamic packages")
        try:
            if shutil.which("scoop-search") is None:
                print("🟡 Installing scoop-search, that was missing...")
                Command = self.EXECUTABLE + " install scoop-search"
                p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
                p.wait()
            packages: list[Package] = []
            p = subprocess.Popen(f"scoop-search {query}", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            rawoutput = "\n\n---------" + self.NAME
            bucket = ""
            while p.poll() is None:
                line: str = str(p.stdout.readline(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if line:
                    if line.startswith("'"):
                        bucket = line.split("'")[1]
                    elif line.startswith("    "):
                        package = list(filter(None, line.strip().split(" ")))
                        if len(package) >= 2:
                            name = formatPackageIdAsName(package[0])
                            id = package[0]
                            version = package[1].replace("(", "").replace(")", "")
                            source = f'{self.NAME}: {bucket}'
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(Package(name, id, version, source, Scoop))
            print(f"🟢 {self.NAME} search for updates finished with {len(packages)} result(s)")
            Globals.PackageManagerOutput += rawoutput
            return packages
        except Exception as e:
            report(e)
            return []

    def getAvailableUpdates(self) -> list[UpgradablePackage]:
        f"""
        Will retieve the upgradable packages by {self.NAME} in the format of a list[UpgradablePackage] object.
        """
        print(f"🔵 Starting {self.NAME} search for updates")
        try:
            packages: list[UpgradablePackage] = []
            p = subprocess.Popen(f"{self.EXECUTABLE} status", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            DashesPassed = False
            rawoutput = "\n\n---------" + self.NAME
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if line:
                    if not DashesPassed:
                        if "----" in line:
                            DashesPassed = True
                    elif "Held package" in line:
                        continue
                    else:
                        package = list(filter(None, line.split(" ")))
                        if len(package) >= 3:
                            name = formatPackageIdAsName(package[0])
                            id = package[0]
                            version = package[1]
                            newVersion = package[2]
                            source = self.NAME
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS and newVersion not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(UpgradablePackage(name, id, version, newVersion, source, Scoop))
            print(f"🟢 {self.NAME} search for updates finished with {len(packages)} result(s)")
            Globals.PackageManagerOutput += rawoutput
            return packages
        except Exception as e:
            report(e)
            return []

    def getInstalledPackages(self) -> list[Package]:
        f"""
        Will retieve the intalled packages by {self.NAME} in the format of a list[Package] object.
        """
        print(f"🔵 Starting {self.NAME} search for installed packages")
        time.sleep(2)
        try:
            packages: list[Package] = []
            p = subprocess.Popen(f"{self.EXECUTABLE} list", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ.copy(), shell=True)
            DashesPassed = False
            rawoutput = "\n\n---------" + self.NAME
            while p.poll() is None:
                line: str = str(p.stdout.readline().strip(), "utf-8", errors="ignore")
                rawoutput += "\n" + line
                if line:
                    if not DashesPassed:
                        if "----" in line:
                            DashesPassed = True
                    else:
                        globalscoop = "Global" in line
                        package = list(filter(None, line.split(" ")))
                        if len(package) >= 2:
                            name = formatPackageIdAsName(package[0])
                            id = package[0]
                            version = package[1]
                            source = f"Scoop{' (Global)' if globalscoop else ''}: {package[2].strip()}"
                            if name not in self.BLACKLISTED_PACKAGE_NAMES and id not in self.BLACKLISTED_PACKAGE_IDS and version not in self.BLACKLISTED_PACKAGE_VERSIONS:
                                packages.append(Package(name, id, version, source, Scoop))
            print(f"🟢 {self.NAME} search for installed packages finished with {len(packages)} result(s)")
            Globals.PackageManagerOutput += rawoutput
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
            unknownStr = _("Not available")
            bucket = "main" if len(package.Source.split(": ")) == 1 else package.Source.split(': ')[-1]
            if bucket in Globals.scoopBuckets:
                bucketRoot = Globals.scoopBuckets[bucket].replace(".git", "")
            else:
                bucketRoot = f"https://github.com/ScoopInstaller/{bucket}"
            details.ManifestUrl = f"{bucketRoot}/blob/master/bucket/{package.Id.split('/')[-1]}.json"
            details.Scopes = [_("Local"), _("Global")]
            details.InstallerType = _("Scoop package")

            rawOutput = b""
            p = subprocess.Popen(' '.join([self.EXECUTABLE, "cat", f"{package.Id}"]), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
            while p.poll() is None:
                pass
            for line in p.stdout.readlines():
                line = line.strip()
                if line:
                    rawOutput += line + b"\n"

            data: dict = json.loads(str(rawOutput, encoding='utf-8', errors="ignore"))

            if "description" in data.keys():
                if type(data["description"]) is list:
                    details.Description = "\n".join(data["description"])
                else:
                    details.Description = data["description"]
            details.Description = ConvertMarkdownToHtml(details.Description)

            if "version" in data.keys():
                details.Versions.append(data["version"])

            if "innosetup" in data.keys():
                details.InstallerType = "Inno Setup"

            if "homepage" in data.keys():
                w: str = data["homepage"]
                details.HomepageURL = w
                if "https://github.com/" in w:
                    details.Author = w.replace("https://github.com/", "").split("/")[0]
                else:
                    for e in ("https://", "http://", "www.", ".com", ".net", ".io", ".org", ".us", ".eu", ".es", ".tk", ".co.uk", ".in", ".it", ".fr", ".de", ".kde", ".microsoft"):
                        w = w.replace(e, "")
                    details.Author = w.split("/")[0].capitalize()

            if "notes" in data.keys():
                if type(data["notes"]) is list:
                    details.ReleaseNotes = "\n".join(data["notes"])
                else:
                    details.ReleaseNotes = data["notes"]
            details.ReleaseNotes = ConvertMarkdownToHtml(details.ReleaseNotes)

            if "license" in data.keys():
                details.License = data["license"] if type(data["license"]) is not dict else data["license"]["identifier"]
                details.LicenseURL = unknownStr if type(data["license"]) is not dict else data["license"]["url"]

            if "url" in data.keys():
                details.InstallerHash = data["hash"][0] if type(data["hash"]) is list else data["hash"]
                url = data["url"][0] if type(data["url"]) is list else data["url"]
                details.InstallerURL = url
                try:
                    details.InstallerSize = int(urlopen(url).length / 1000000)
                except Exception as e:
                    print("🟠 Can't get installer size:", type(e), str(e))
            elif "architecture" in data.keys():
                details.InstallerHash = data["architecture"]["64bit"]["hash"]
                url = data["architecture"]["64bit"]["url"]
                details.InstallerURL = url
                try:
                    details.InstallerSize = int(urlopen(url).length / 1000000)
                except Exception as e:
                    print("🟠 Can't get installer size:", type(e), str(e))
                if type(data["architecture"]) is dict:
                    details.Architectures = list(data["architecture"].keys())

            if "checkver" in data.keys():
                if type(data["checkver"]) is dict:
                    if "url" in data["checkver"].keys():
                        url = data["checkver"]["url"]
                        details.ReleaseNotesUrl = url

            if details.ReleaseNotesUrl == unknownStr and "github.com" in details.InstallerURL:
                try:
                    url = "/".join(details.InstallerURL.replace("/download/", "/tag/").split("/")[:-1])
                    details.ReleaseNotesUrl = url
                except Exception as e:
                    report(e)

            output: list[str] = []
            p = subprocess.Popen(' '.join([self.EXECUTABLE, "info", package.Id]), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
            while p.poll() is None:
                pass
            for line in p.stdout.readlines():
                line = line.strip()
                if line:
                    output.append(self.ansi_escape.sub('', str(line, encoding='utf-8', errors="ignore")))
            for line in output:
                for line in output:
                    if "Updated by" in line:
                        details.Publisher = line.replace("Updated by", "").strip()[1:].strip()
                    elif "Updated at" in line:
                        details.UpdateDate = line.replace("Updated at", "").strip()[1:].strip()

            print(f"🟢 Get info finished for {package.Name} on {self.NAME}")
            return details
        except Exception as e:
            report(e)
            return details

    def getIcon(self, source: str) -> QIcon:
        if not self.LoadedIcons:
            self.LoadedIcons = True
            self.icon = QIcon(getMedia("scoop"))
        return self.icon

    def getParameters(self, options: InstallationOptions, isAnUninstall: bool = False) -> list[str]:
        Parameters: list[str] = []
        if not isAnUninstall:
            if options.Architecture:
                Parameters += ["--arch", options.Architecture]
            if options.SkipHashCheck:
                Parameters.append("--skip")
            if options.RemoveDataOnUninstall:
                Parameters.append("--purge")
        if options.CustomParameters:
            Parameters += options.CustomParameters
        if options.InstallationScope:
            if options.InstallationScope.capitalize() in ("Global", _("Global")):
                Parameters.append("--global")
        return Parameters

    def startInstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        bucket_prefix = ""
        if len(package.Source.split(":")) > 1 and "/" not in package.Source:
            bucket_prefix = package.Source.lower().split(":")[1].replace(" ", "") + "/"
        Command = self.EXECUTABLE.split(" ") + ["install", bucket_prefix + package.Id] + self.getParameters(options)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command + ["--global"]
        print(f"🔵 Starting {package} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing {package.Name}").start()
        return p

    def startUpdate(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        bucket_prefix = ""
        if len(package.Source.split(":")) > 1 and "/" not in package.Source:
            bucket_prefix = package.Source.lower().split(":")[1].replace(" ", "") + "/"
        Command = self.EXECUTABLE.split(" ") + ["update", bucket_prefix + package.Id] + self.getParameters(options)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command + ["--global"]
        print(f"🔵 Starting {package} update with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.installationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: update {package.Name}").start()
        return p

    def installationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        outputCode = 1
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = line.strip()
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                if "Installing" in line:
                    widget.counterSignal.emit(1)
                elif "] 100%" in line or "Downloading" in line:
                    widget.counterSignal.emit(4)
                elif "was installed successfully!" in line:
                    widget.counterSignal.emit(6)
                widget.addInfoLine.emit((line, is_newline))
                if "was installed successfully" in line:
                    outputCode = 0
                elif "is already installed" in line:
                    outputCode = 0
                if is_newline:
                    output += line + "\n"
        if "-g" in output and "successfully" not in output and not options.RunAsAdministrator:
            outputCode = RETURNCODE_NEEDS_SCOOP_ELEVATION
        elif "requires admin rights" in output or "requires administrator rights" in output or "you need admin rights to install global apps" in output:
            outputCode = RETURNCODE_NEEDS_ELEVATION
        if "Latest versions for all apps are installed" in output:
            outputCode = RETURNCODE_NO_APPLICABLE_UPDATE_FOUND
        widget.finishInstallation.emit(outputCode, output)

    def startUninstallation(self, package: Package, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        bucket_prefix = ""
        if len(package.Source.split(":")) > 1 and "/" not in package.Source:
            bucket_prefix = package.Source.lower().split(":")[1].replace(" ", "") + "/"
        Command = self.EXECUTABLE.split(" ") + ["uninstall", bucket_prefix + package.Id] + self.getParameters(options, True)
        if options.RunAsAdministrator:
            Command = [GSUDO_EXECUTABLE] + Command + ["--global"]
        print(f"🔵 Starting {package} uninstall with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.uninstallationThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: uninstall {package.Name}").start()
        return p

    def uninstallationThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        outputCode = 1
        output = ""
        while p.poll() is None:
            line, is_newline = getLineFromStdout(p)
            line = line.strip()
            line = str(line, encoding='utf-8', errors="ignore").strip()
            if line:
                if "Uninstalling" in line:
                    widget.counterSignal.emit(1)
                elif "Removing shim for" in line:
                    widget.counterSignal.emit(4)
                elif "was uninstalled" in line:
                    widget.counterSignal.emit(6)
                widget.addInfoLine.emit((line, is_newline))
                if "was uninstalled" in line:
                    outputCode = 0
                if is_newline:
                    output += line + "\n"
        if "-g" in output and "was uninstalled" not in output and not options.RunAsAdministrator:
            outputCode = RETURNCODE_NEEDS_SCOOP_ELEVATION
        elif "requires admin rights" in output or "requires administrator rights" in output or "you need admin rights to install global apps" in output:
            outputCode = RETURNCODE_NEEDS_ELEVATION
        widget.finishInstallation.emit(outputCode, output)

    def getSources(self) -> None:
        print(f"🔵 Starting {self.NAME} source search...")
        p = subprocess.Popen(f"{self.EXECUTABLE} bucket list", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, cwd=os.getcwd(), env=os.environ, shell=True)
        output = []
        sources: list[ManagerSource] = []
        counter = 0
        while p.poll() is None:
            line = p.stdout.readline()
            line = line.strip()
            if line:
                if counter > 1 and b"---" not in line:
                    output.append(self.ansi_escape.sub('', str(line, encoding='utf-8', errors="ignore")))
                else:
                    counter += 1
        counter = 0
        for element in output:
            try:
                while "  " in element.strip():
                    element = element.strip().replace("  ", " ")
                element: list[str] = element.split(" ")
                sources.append(ManagerSource(self, element[0].strip(), element[1].strip(), element[2].strip() + " " + element[3].strip(), element[4].strip()))
            except IndexError as e:
                try:
                    sources.append(ManagerSource(element[0].strip(), element[1].strip(), "Unknown", "Unknown"))
                except IndexError as f:
                    print(e, f)
                print("IndexError: " + str(e))

        for source in sources:
            Globals.scoopBuckets[source.Name] = source.Url

        print(f"🟢 {self.NAME} source search finished with {len(sources)} sources")
        return sources

    def installSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = self.EXECUTABLE.split(" ") + ["bucket", "add", source.Name, source.Url]
        print(f"🔵 Starting source {source.Name} installation with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def uninstallSource(self, source: ManagerSource, options: InstallationOptions, widget: 'PackageInstallerWidget') -> subprocess.Popen:
        Command = self.EXECUTABLE.split(" ") + ["bucket", "rm", source.Name]
        print(f"🔵 Starting source {source.Name} removal with Command", Command)
        p = subprocess.Popen(Command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, cwd=GSUDO_EXE_LOCATION, env=os.environ)
        Thread(target=self.sourceProgressThread, args=(p, options, widget,), name=f"{self.NAME} installation thread: installing source {source.Name}").start()
        return p

    def sourceProgressThread(self, p: subprocess.Popen, options: InstallationOptions, widget: 'PackageInstallerWidget'):
        output = ""
        counter = 0
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
        try:
            o = subprocess.run(f"{self.EXECUTABLE} -v", shell=True, stdout=subprocess.PIPE)
            Globals.componentStatus[f"{self.NAME}Found"] = shutil.which("scoop") is not None
            Globals.componentStatus[f"{self.NAME}Version"] = o.stdout.decode('utf-8', errors="ignore").replace("\n", " ").replace("\r", " ")
            if signal:
                signal.emit()
        except Exception:
            Globals.componentStatus[f"{self.NAME}Found"] = False
            Globals.componentStatus[f"{self.NAME}Version"] = _("{pm} could not be found").format(pm=self.NAME)
            if signal:
                signal.emit()

    def updateSources(self, signal: Signal = None) -> None:
        print(f"🔵 Reloading {self.NAME} sources...")
        subprocess.run(f"{self.EXECUTABLE} update", shell=True, stdout=subprocess.PIPE)
        if signal:
            signal.emit()


Scoop = ScoopPackageManager()
