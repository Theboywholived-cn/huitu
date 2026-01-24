# Git 快速同步脚本
# 用法: .\git_sync.ps1 "提交信息"
# 示例: .\git_sync.ps1 "修复了3D图表显示问题"

param(
    [Parameter(Mandatory=$false)]
    [string]$message = "代码更新"
)

Write-Host "🔍 检查修改状态..." -ForegroundColor Cyan
git status

Write-Host "`n📦 添加所有修改..." -ForegroundColor Yellow
git add .

Write-Host "`n💾 提交修改..." -ForegroundColor Green
git commit -m $message

Write-Host "`n🚀 推送到GitHub..." -ForegroundColor Magenta
git push origin main

Write-Host "`n✅ 同步完成！" -ForegroundColor Green
git log --oneline -1
