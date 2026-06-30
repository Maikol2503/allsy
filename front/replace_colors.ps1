$files = Get-ChildItem -Path "C:\Users\maikol\Desktop\allsys\front\src\app" -Recurse -Include *.css, *.html

$replacements = @{
    '(?i)#007782' = 'var(--ap-color-primary)'
    '(?i)#005c65' = 'var(--ap-color-primary-hover)'
    '(?i)#1e3a8a' = 'var(--ap-color-primary)'
    '(?i)#3b82f6' = 'var(--ap-color-primary)'
    '(?i)#2563eb' = 'var(--ap-color-primary)'
    '(?i)#93c5fd' = 'var(--ap-color-primary-hover)'
    
    '(?i)#2c3e50' = 'var(--text-main)'
    '(?i)#34495e' = 'var(--text-main)'
    '(?i)#1e293b' = 'var(--text-main)'
    
    '(?i)#7f8c8d' = 'var(--text-muted)'
    '(?i)#95a5a6' = 'var(--text-muted)'
    '(?i)#475569' = 'var(--text-muted)'
    '(?i)#6B7280' = 'var(--text-muted)'
    
    '(?i)#e0e6ed' = 'var(--border-color)'
    '(?i)#eaedf1' = 'var(--border-color)'
    '(?i)#cbd5e1' = 'var(--border-color)'
    '(?i)#E5E7EB' = 'var(--border-color)'
    
    '(?i)#f4f6f8' = 'var(--bg-body)'
    '(?i)#f8f9fa' = 'var(--bg-body)'
    '(?i)#F3F4F6' = 'var(--bg-body)'
    
    '(?i)#27ae60' = 'var(--ap-color-success)'
    '(?i)#eafaf1' = 'var(--ap-color-success-bg)'
    
    '(?i)#e74c3c' = 'var(--ap-color-danger)'
    '(?i)#c0392b' = 'var(--ap-color-danger)'
    '(?i)#fceceb' = 'var(--ap-color-danger-bg)'
    
    '(?i)#f1c40f' = 'var(--text-muted)'
}

foreach ($file in $files) {
    if ($file.Length -gt 0) {
        $content = Get-Content $file.FullName -Raw
        if ($content -ne $null) {
            $originalContent = $content
            
            foreach ($key in $replacements.Keys) {
                $content = [System.Text.RegularExpressions.Regex]::Replace($content, $key, $replacements[$key])
            }
            
            if ($content -cne $originalContent) {
                Set-Content -Path $file.FullName -Value $content -NoNewline
                Write-Host "Updated $($file.FullName)"
            }
        }
    }
}
