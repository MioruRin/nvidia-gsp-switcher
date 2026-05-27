Set objShell = CreateObject("Shell.Application")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
objShell.ShellExecute "python", """" & scriptDir & "\gsp_switcher.py"" --admin", "", "runas", 1
