# 需要以管理员权限运行
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "请以管理员身份运行此脚本！"
    Exit
}

Write-Host "开始清理C盘..." -ForegroundColor Green

# 创建进度显示函数
function Show-Progress {
    param (
        [string]$Activity,
        [int]$PercentComplete
    )
    Write-Progress -Activity $Activity -PercentComplete $PercentComplete -Status "$PercentComplete% 完成"
}

# 清理临时文件夹
Show-Progress -Activity "C盘清理" -PercentComplete 10
Write-Host "正在清理临时文件..." -ForegroundColor Cyan

$tempFolders = @(
    "C:\Windows\Temp\*",
    "C:\Users\*\AppData\Local\Temp\*"
)

foreach ($folder in $tempFolders) {
    Write-Host "  清理: $folder" -ForegroundColor Gray
    $files = Get-ChildItem -Path $folder -File -Recurse -ErrorAction SilentlyContinue
    $totalFiles = $files.Count
    $currentFile = 0
    
    foreach ($file in $files) {
        $currentFile++
        if ($currentFile % 10 -eq 0) {
            $percent = [math]::Min([math]::Round(($currentFile / $totalFiles) * 100), 100)
            Show-Progress -Activity "清理临时文件" -PercentComplete $percent
        }
        Write-Host "    删除: $($file.FullName)" -ForegroundColor DarkGray
        Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
    }
}

# 清理Windows更新缓存
Show-Progress -Activity "C盘清理" -PercentComplete 30
Write-Host "正在清理Windows更新缓存..." -ForegroundColor Cyan
Stop-Service -Name wuauserv -Force
Write-Host "  已停止Windows更新服务" -ForegroundColor Gray
Write-Host "  清理: C:\Windows\SoftwareDistribution\*" -ForegroundColor Gray
Remove-Item -Path "C:\Windows\SoftwareDistribution\*" -Recurse -Force -ErrorAction SilentlyContinue
Start-Service -Name wuauserv
Write-Host "  已重启Windows更新服务" -ForegroundColor Gray

# 清理回收站
Show-Progress -Activity "C盘清理" -PercentComplete 50
Write-Host "正在清空回收站..." -ForegroundColor Cyan
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# 自动运行磁盘清理工具（显示窗口和进度）
Show-Progress -Activity "C盘清理" -PercentComplete 60
Write-Host "正在准备系统磁盘清理工具..." -ForegroundColor Cyan

# 设置要清理的项目（数字对应不同的清理选项）
$volumeCaches = @(
    "Active Setup Temp Folders",
    "BranchCache",
    "Content Indexer Cleaner",
    "D3D Shader Cache",
    "Delivery Optimization Files",
    "Device Driver Packages",
    "Diagnostic Data Viewer database files",
    "Downloaded Program Files",
    "Internet Cache Files",
    "Memory Dump Files",
    "Old ChkDsk Files", 
    "Previous Installations",
    "Recycle Bin",
    "RetailDemo Offline Content",
    "Setup Log Files",
    "System error memory dump files", 
    "System error minidump files",
    "Temporary Files",
    "Temporary Setup Files",
    "Thumbnail Cache",
    "Update Cleanup",
    "Upgrade Discarded Files",
    "User file versions",
    "Windows Defender Antivirus",
    "Windows Error Reporting Files",
    "Windows ESD installation files",
    "Windows Upgrade Log Files"
)

# 创建注册表项以自动运行清理
$regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VolumeCaches"
$counter = 0
$total = $volumeCaches.Count

foreach ($cache in $volumeCaches) {
    $counter++
    $percent = [math]::Round(($counter / $total) * 100)
    Show-Progress -Activity "配置磁盘清理工具" -PercentComplete $percent
    
    $cachePath = Join-Path $regPath $cache
    Write-Host "  配置: $cache" -ForegroundColor Gray
    if (Test-Path $cachePath) {
        Set-ItemProperty -Path $cachePath -Name "StateFlags0001" -Value 2 -Type DWORD -ErrorAction SilentlyContinue
    }
}

# 运行清理（显示窗口）
Show-Progress -Activity "C盘清理" -PercentComplete 80
Write-Host "正在运行系统磁盘清理工具...（将弹出窗口显示清理进度）" -ForegroundColor Cyan
Write-Host "请勿关闭弹出的磁盘清理窗口，等待其自动完成..." -ForegroundColor Yellow

# 带窗口运行清理工具，这样用户可以看到清理进度
Start-Process -Wait -FilePath "cleanmgr.exe" -ArgumentList "/sagerun:1"

# 显示C盘剩余空间
Show-Progress -Activity "C盘清理" -PercentComplete 100
$drive = Get-PSDrive C
$freeSpace = [math]::Round($drive.Free / 1GB, 2)
$usedSpace = [math]::Round(($drive.Used / 1GB), 2)
$totalSpace = [math]::Round(($drive.Free + $drive.Used) / 1GB, 2)

Write-Progress -Activity "C盘清理" -Completed
Write-Host "`n清理完成！" -ForegroundColor Green
Write-Host "C盘总空间: $totalSpace GB" -ForegroundColor Yellow
Write-Host "已使用空间: $usedSpace GB" -ForegroundColor Yellow
Write-Host "剩余空间: $freeSpace GB" -ForegroundColor Yellow

# 添加暂停防止窗口关闭
Write-Host "`n按任意键退出..." -ForegroundColor Magenta
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")