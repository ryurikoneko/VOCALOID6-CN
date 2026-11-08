param(
    [string]$InstallDir = (Join-Path $env:LOCALAPPDATA 'VOCALOID6-CN-6.13.3-R1'),
    [switch]$NoDesktopShortcut
)
$ErrorActionPreference = 'Stop'
try {
    $root = (Resolve-Path -LiteralPath $InstallDir).ProviderPath.TrimEnd('\')
    $receiptPath = Join-Path $root 'V6CN-install.json'
    $receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([IO.Path]::GetFullPath($receipt.Destination).TrimEnd('\') -ine $root) { throw 'Install receipt does not match this directory.' }
    if ([IO.Path]::GetFullPath($receipt.Source).TrimEnd('\') -ieq $root) { throw 'Refusing to modify the original installation.' }
    foreach ($path in @($root, (Join-Path $root 'zh-CN'))) {
        if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked installation directories are not supported.' }
    }
    foreach ($name in @('VOCALOID6.exe','VOCALOID6.dll')) {
        $path = Join-Path $root $name
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing installed file: $name" }
        if ((Get-Item -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked file: $name" }
    }
    foreach ($name in @('VOCALOID6.dll','VOCALOID6Plugin.dll')) {
        $expected = $receipt.Copied.PSObject.Properties[$name].Value
        if (-not $expected -or (Get-FileHash -LiteralPath (Join-Path $root $name) -Algorithm SHA256).Hash -ine $expected) { throw "Original copied file changed: $name" }
    }
    $template = Join-Path $PSScriptRoot 'tools\Start-Chinese.template.cmd'
    if (-not (Test-Path -LiteralPath $template)) { throw 'Extract the complete repair ZIP before running it.' }
    $patchNames = @('V6CN.StartupHook.dll','zh-CN/VOCALOID6.resources.dll','zh-CN/VOCALOID6Plugin.resources.dll')
    $payloadManifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'repair-payload.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($name in $patchNames) {
        $sourcePath = Join-Path $PSScriptRoot ('payload/' + $name)
        $expected = $payloadManifest.PSObject.Properties[$name].Value
        if (-not $expected -or -not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Repair package is incomplete: $name" }
        if ((Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash -ine $expected) { throw "Repair package checksum mismatch: $name" }
        $targetPath = Join-Path $root $name
        if ((Test-Path -LiteralPath $targetPath) -and ((Get-Item -LiteralPath $targetPath).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Linked patch file: $name" }
    }
    $backup = Join-Path $root ('V6CN-launcher-backups\' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $backup | Out-Null
    $launcher = Join-Path $root 'Start-Chinese.cmd'
    if (Test-Path -LiteralPath $launcher) {
        if ((Get-Item -LiteralPath $launcher).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked launcher is not supported.' }
        Copy-Item -LiteralPath $launcher -Destination (Join-Path $backup 'Start-Chinese.cmd')
    }
    Copy-Item -LiteralPath $receiptPath -Destination (Join-Path $backup 'V6CN-install.json')
    foreach ($name in $patchNames) {
        $sourcePath = Join-Path $PSScriptRoot ('payload/' + $name)
        $targetPath = Join-Path $root $name
        $expected = $payloadManifest.PSObject.Properties[$name].Value
        $needsCopy = -not (Test-Path -LiteralPath $targetPath -PathType Leaf)
        if (-not $needsCopy) { $needsCopy = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash -ine $expected }
        if ($needsCopy) {
            if (Test-Path -LiteralPath $targetPath -PathType Leaf) {
                $backupPath = Join-Path $backup $name
                New-Item -ItemType Directory -Path (Split-Path -Parent $backupPath) -Force | Out-Null
                Copy-Item -LiteralPath $targetPath -Destination $backupPath
            }
            New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
            Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
        }
        if ((Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash -ine $expected) { throw "Restored patch checksum mismatch: $name" }
        $receiptKey = $name.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $receipt.Managed | Add-Member -MemberType NoteProperty -Name $receiptKey -Value $expected -Force
    }
    Copy-Item -LiteralPath $template -Destination $launcher -Force
    $hash = (Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash.ToLowerInvariant()
    $receipt.Managed | Add-Member -MemberType NoteProperty -Name 'Start-Chinese.cmd' -Value $hash -Force
    $json = $receipt | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($receiptPath, $json, (New-Object Text.UTF8Encoding($false)))
    $shortcutPath = '(not requested)'
    if (-not $NoDesktopShortcut) {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $shortcutPath = Join-Path $desktop 'VOCALOID6 Chinese.lnk'
        if (Test-Path -LiteralPath $shortcutPath) { Copy-Item -LiteralPath $shortcutPath -Destination (Join-Path $backup 'desktop-shortcut.lnk') }
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $env:ComSpec
        $shortcut.Arguments = '/d /c ""' + $launcher + '""'
        $shortcut.WorkingDirectory = $root
        $shortcut.IconLocation = (Join-Path $root 'VOCALOID6.exe') + ',0'
        $shortcut.Description = 'VOCALOID6 Chinese desktop launcher'
        $shortcut.Save()
    }
    $diagnostic = Join-Path $root 'V6CN-startup-diagnostic.txt'
    $lines = @('VOCALOID6 startup diagnostic', ('Time: ' + (Get-Date -Format o)), ('Editor: ' + $root), ('Launcher backup: ' + $backup))
    $processes = @(Get-Process -Name VOCALOID6 -ErrorAction SilentlyContinue)
    $lines += '--- Running processes ---'
    $lines += ($processes | Select-Object Id,ProcessName,Responding,MainWindowTitle | Format-Table -AutoSize | Out-String)
    foreach ($name in @('V6CN-launch.log','V6CN-runtime.log')) {
        $lines += ('--- ' + $name + ' ---')
        $path = Join-Path $root $name
        if (Test-Path -LiteralPath $path) { $lines += Get-Content -LiteralPath $path -Tail 60 -ErrorAction SilentlyContinue }
    }
    $lines += '--- Recent application events ---'
    try {
        $events = Get-WinEvent -FilterHashtable @{LogName='Application';Id=1000,1001,1026;StartTime=(Get-Date).AddHours(-3)} -MaxEvents 200 -ErrorAction Stop |
            Where-Object { $_.Message -match 'VOCALOID6|V6CN' } | Select-Object -First 5
        $lines += ($events | Format-List TimeCreated,Id,ProviderName,Message | Out-String)
    } catch { $lines += 'No matching application events were available.' }
    [IO.File]::WriteAllLines($diagnostic, [string[]]$lines, (New-Object Text.UTF8Encoding($true)))
    Write-Host 'Chinese resources and launcher repaired.' -ForegroundColor Green
    if (-not $NoDesktopShortcut) { Write-Host 'Desktop shortcut created:'; Write-Host $shortcutPath }
    Write-Host 'Diagnostic file:'
    Write-Host $diagnostic
    if ($processes.Count -gt 0) {
        Write-Host 'VOCALOID6 is still running. Close it normally before starting another instance.' -ForegroundColor Yellow
        Write-Host 'If it is unresponsive, save other work and restart Windows before retrying.'
    }
    if (-not $NoDesktopShortcut) { Write-Host 'Keep Start-Chinese.cmd in the Editor folder. Use the desktop shortcut.' }
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
