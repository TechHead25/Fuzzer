$files = Get-ChildItem -Path "C:\Projects\Fuzzer\backend\tests" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    if ($content -match "SQLALCHEMY_DATABASE_URL = `"sqlite:///") {
        $content = $content -replace 'from sqlalchemy import create_engine', "from sqlalchemy import create_engine`nfrom sqlalchemy.pool import StaticPool"
        $content = $content -replace 'SQLALCHEMY_DATABASE_URL = "sqlite:///\./[a-zA-Z_]+\.db"', 'SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"'
        $content = $content -replace 'engine = create_engine\(SQLALCHEMY_DATABASE_URL, connect_args=\{"check_same_thread": False\}\)', 'engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)'
        Set-Content -Path $file.FullName -Value $content -NoNewline
        Write-Host "Updated $($file.Name)"
    }
}
