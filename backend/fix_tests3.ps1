$files = Get-ChildItem -Path "C:\Projects\Fuzzer\backend\tests" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    if ($content -match "app.dependency_overrides\[get_db\] = override_get_db") {
        # Remove it from global scope
        $content = $content -replace "app.dependency_overrides\[get_db\] = override_get_db\r?\n?", ""
        
        # Inject it into setup_db fixture, or before client = TestClient(app) if no setup_db
        if ($content -match "def setup_db\(\):") {
            $content = $content -replace "def setup_db\(\):", "def setup_db():`n    app.dependency_overrides[get_db] = override_get_db"
            $content = $content -replace "yield\r?\n\s+Base.metadata.drop_all\(bind=engine\)", "yield`n    app.dependency_overrides.clear()`n    Base.metadata.drop_all(bind=engine)"
        } elseif ($content -match "def test_health_check") {
            # In test_main.py, there is no setup_db fixture, we must create one.
            $fixture = "`n@pytest.fixture(autouse=True)`ndef setup_db():`n    Base.metadata.drop_all(bind=engine)`n    Base.metadata.create_all(bind=engine)`n    app.dependency_overrides[get_db] = override_get_db`n    yield`n    app.dependency_overrides.clear()`n    Base.metadata.drop_all(bind=engine)`n`n"
            $content = $content -replace "def test_health_check", "$fixture`ndef test_health_check"
            # Remove the global create_all and drop_all in test_main
            $content = $content -replace "Base.metadata.drop_all\(bind=engine\)\r?\nBase.metadata.create_all\(bind=engine\)", ""
        }
    }
    
    Set-Content -Path $file.FullName -Value $content -NoNewline
    Write-Host "Fixed DI override in $($file.Name)"
}
