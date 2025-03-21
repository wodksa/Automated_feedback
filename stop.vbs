Set objShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "taskkill", "/F /IM python.exe", strPath, "", 0