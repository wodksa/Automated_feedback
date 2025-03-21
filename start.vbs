Set objShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

Set objShell = CreateObject("Shell.Application")
objShell.ShellExecute "python", "chat_analyzer.py", strPath, "", 1