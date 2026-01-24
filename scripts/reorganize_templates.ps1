$ProgressPreference = 'SilentlyContinue'
$templatesRoot = "D:\文件夹\绘图\图像代码数据汇总"
$backupRoot = "D:\文件夹\绘图\图像代码数据汇总_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Write-Host "Beginning backup..." -ForegroundColor Cyan
Copy-Item -Path $templatesRoot -Destination $backupRoot -Recurse
Write-Host "Backup completed: $backupRoot" -ForegroundColor Green

function Get-ChartType {
    param([string]$filename, [string]$dirname, [string]$code)
    
    $search = ($filename + $dirname + $code).ToLower()
    
    # Match patterns (English keywords mainly)
    if ($search -match "taylor") { return "taylor" }
    if ($search -match "violin") { return "violin" }
    if ($search -match "boxplot") { return "boxplot" }
    if ($search -match "heatmap|imshow|contour") { return "heatmap" }
    if ($search -match "bar\(") { return "bar" }
    if ($search -match "scatter.*matrix|pairplot") { return "scatter_matrix" }
    if ($search -match "scatter" -and $search -match "cmap|colorbar") { return "scatter_cmap" }
    if ($search -match "scatter" -and $search -match "subplot") { return "scatter_multi" }
    if ($search -match "scatter") { return "scatter" }
    if ($search -match "plot\(" -and $search -match "subplot") { return "line_multi" }
    if ($search -match "plot\(") { return "line" }
    if ($search -match "hist") { return "hist" }
    
    return "other"
}

function Get-NormalizedName {
    param([string]$pyfile)
    
    try {
        $content = Get-Content -Path $pyfile -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $content) { return $null }
        
        if ($content -match 'TITLE\s*=\s*["\'](.+?)["\']') {
            return $matches[1].Trim()
        }
        
        if ($content -match 'plt\.(suptitle|title)\(\s*["\'](.+?)["\']') {
            $title = $matches[2].Trim()
            if ($title -and $title -notmatch "title|figure") {
                return $title
            }
        }
        
        $basename = [System.IO.Path]::GetFileNameWithoutExtension($pyfile)
        return $basename
    } catch {
        return $null
    }
}


$migrations = @{}
Write-Host "Scanning original structure..." -ForegroundColor Cyan
$count = 0

foreach ($category in Get-ChildItem $templatesRoot -Directory) {
    foreach ($root in Get-ChildItem $category.FullName -Directory -Recurse) {
        $pyfiles = @(Get-ChildItem $root.FullName -Filter "*.py" -File | Where-Object { $_.Name -notmatch "^__" })
        if ($pyfiles.Count -eq 0) { continue }
        
        $mainPy = $pyfiles[0]
        foreach ($pf in $pyfiles) {
            if ($pf.BaseName -eq $root.BaseName) {
                $mainPy = $pf
                break
            }
        }
        if ($pyfiles.Count -gt 1 -and $mainPy -eq $pyfiles[0]) {
            $mainPy = $pyfiles | Sort-Object -Property Length -Descending | Select-Object -First 1
        }
        
        $code = Get-Content -Path $mainPy.FullName -Raw -ErrorAction SilentlyContinue
        $chartTypeId = Get-ChartType -filename $mainPy.BaseName -dirname $root.BaseName -code $code
        
        $normName = Get-NormalizedName -pyfile $mainPy.FullName
        if (-not $normName) {
            $normName = $root.BaseName
        }
        
        $normName = $normName -replace "[^a-zA-Z0-9_-]", ""
        if ($normName.Length -gt 50) {
            $normName = $normName.Substring(0, 50)
        }
        
        $newChartTypeDir = Join-Path $templatesRoot $chartTypeId
        $newTemplateDir = Join-Path $newChartTypeDir $normName
        
        $migrations[$root.FullName] = @{
            OldPath = $root.FullName
            NewPath = $newTemplateDir
            ChartType = $chartTypeId
            TemplateName = $normName
            MainPyFile = $mainPy.FullName
        }
        
        $count++
    }
}

Write-Host "Found $count template directories" -ForegroundColor Green

Write-Host "Clearing original directory..." -ForegroundColor Cyan
foreach ($item in Get-ChildItem $templatesRoot) {
    if ($item.Name -notlike "*backup*" -and $item.Name -notlike "*.ps1") {
        Remove-Item $item.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Executing migrations..." -ForegroundColor Cyan
$successCount = 0
$errors = @()

foreach ($key in $migrations.Keys) {
    $info = $migrations[$key]
    $newPath = $info.NewPath
    
    try {
        if (-not (Test-Path $newPath)) {
            New-Item -ItemType Directory -Path $newPath -Force | Out-Null
        }
        
        foreach ($item in Get-ChildItem $info.OldPath) {
            if ($item.Name -eq ".idea") { continue }
            
            if ($item.PSIsContainer) {
                Copy-Item -Path $item.FullName -Destination "$newPath\$($item.Name)" -Recurse -Force -ErrorAction SilentlyContinue
            } else {
                Copy-Item -Path $item.FullName -Destination "$newPath\$($item.Name)" -Force -ErrorAction SilentlyContinue
            }
        }
        
        $mainPyName = [System.IO.Path]::GetFileName($info.MainPyFile)
        if ($mainPyName -ne "main.py") {
            if (Test-Path "$newPath\$mainPyName") {
                Rename-Item -Path "$newPath\$mainPyName" -NewName "main.py" -Force
            }
        }
        
        Write-Host "[OK] $($info.ChartType) / $($info.TemplateName)" -ForegroundColor Green
        $successCount++
    } catch {
        $errors += "[ERR] $($info.OldPath): $_"
    }
}

Write-Host "`nMigration Results: $successCount / $count succeeded" -ForegroundColor Green
if ($errors.Count -gt 0) {
    Write-Host "Errors encountered:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
}

Write-Host "Backup saved: $backupRoot" -ForegroundColor Cyan
