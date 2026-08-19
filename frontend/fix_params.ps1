$files = Get-ChildItem -Path "src\app\projects" -Recurse -Filter "page.tsx" | Select-Object -ExpandProperty FullName

foreach ($file in $files) {
    $content = Get-Content $file -Raw
    
    $modified = $false
    
    # Check if already imported
    if ($content -notmatch "import \{ use \} from 'react';") {
        $content = "import { use } from 'react';`n" + $content
        $modified = $true
    }
    
    # Single ID param pages
    if ($content -match "params \}: \{ params: \{ id: string \} \}") {
        $content = $content -replace "params \}: \{ params: \{ id: string \} \}", "params }: { params: Promise<{ id: string }> }"
        $content = $content -replace "const projectId = Number\(params.id\);", "const resolvedParams = use(params);`n  const projectId = Number(resolvedParams.id);"
        $modified = $true
    }
    
    # Dual ID param pages (campaign_id, crash_id)
    if ($content -match "params \}: \{ params: \{ id: string, ([a-zA-Z_]+): string \} \}") {
        $content = $content -replace "params \}: \{ params: \{ id: string, ([a-zA-Z_]+): string \} \}", "params }: { params: Promise<{ id: string, `$1: string }> }"
        $content = $content -replace "const projectId = Number\(params.id\);`n\s+const ([a-zA-Z]+Id) = Number\(params.([a-z_]+)\);", "const resolvedParams = use(params);`n  const projectId = Number(resolvedParams.id);`n  const `$1 = Number(resolvedParams.`$2);"
        $modified = $true
    }

    if ($modified) {
        Set-Content -Path $file -Value $content -NoNewline
        Write-Host "Updated $file"
    }
}
