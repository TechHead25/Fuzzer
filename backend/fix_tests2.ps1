$files = Get-ChildItem -Path "C:\Projects\Fuzzer\backend\tests" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    $content = $content -replace 'from sqlalchemy.pool import StaticPool\n?', ""
    $content = $content -replace 'SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"', "SQLALCHEMY_DATABASE_URL = `"sqlite:///./$($file.Name.Replace('.py', '.db'))`""
    $content = $content -replace ', poolclass=StaticPool', ""
    
    if ($content -match "Base.metadata.create_all\(bind=engine\)") {
        if ($content -notmatch "Base.metadata.drop_all\(bind=engine\)") {
            $content = $content -replace "Base.metadata.create_all\(bind=engine\)", "Base.metadata.drop_all(bind=engine)`nBase.metadata.create_all(bind=engine)"
        }
    }
    
    Set-Content -Path $file.FullName -Value $content -NoNewline
    Write-Host "Reverted and added drop_all to $($file.Name)"
}
