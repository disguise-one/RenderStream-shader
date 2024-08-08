$zipFile = "shadertoy.zip"
$buildFolder = "build"
$filesToZip = Get-ChildItem shaders/*.glsl, images/*, *.py, *.pyrs, requirements.txt, README.md

if (Test-Path $buildFolder) {
    Remove-Item -Recurse -Force $buildFolder
}
if (Test-Path $zipFile) {
    Remove-Item $zipFile
}

New-Item -ItemType Directory -Force -Path $buildFolder > $null
foreach ($file in $filesToZip) {
    $destinationPath = Join-Path $buildFolder (Resolve-Path -Relative $file)
    $destinationDir = Split-Path $destinationPath
    if (!(Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Force -Path $destinationDir > $null
    }
    Copy-Item -Path $file.FullName -Destination $destinationPath
}

Add-Type -AssemblyName "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory($buildFolder, $zipFile)

Remove-Item -Recurse -Force $buildFolder
