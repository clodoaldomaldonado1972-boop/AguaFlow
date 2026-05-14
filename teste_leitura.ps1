$headers = @{
    "Authorization" = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJwYWN4aGd2c2Nxbmxhd3hnd2ZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzMzNDk3NiwiZXhwIjoyMDg4OTEwOTc2fQ.AXgdtiUEtCWk94_nw3k-4xC8sl0CzjjkGPmdpTNEkJQ"
    "apikey"        = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJwYWN4aGd2c2Nxbmxhd3hnd2ZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MzMzNDk3NiwiZXhwIjoyMDg4OTEwOTc2fQ.AXgdtiUEtCWk94_nw3k-4xC8sl0CzjjkGPmdpTNEkJQ"
    "Content-Type"  = "application/json"
    "Prefer"        = "return=representation"
}

$body = @{
    unidade_id       = "101"
    tipo_registro    = "Água"
    leitura_agua     = 0
    valor_leitura    = 0
    leiturista       = "Zelador"
    data_hora_coleta = "2026-05-14T21:30:00+00:00" # Horário novo para evitar 409
    foto_url         = "https://rpacxhgvscqnlawxgwfk.supabase.co/storage/v1/object/public/fotos_hidrometros/162/20260514_132942_AGUA.jpg"
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "https://rpacxhgvscqnlawxgwfk.supabase.co/rest/v1/leituras" -Method POST -Headers $headers -Body $body
    Write-Host "✅ SUCESSO: Registro inserido!"
    $r | ConvertTo-Json
} catch {
    $resp = $_.Exception.Response
    if ($resp) {
        $stream = $resp.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $errorBody = $reader.ReadToEnd()
        Write-Host "❌ ERRO STATUS: $($resp.StatusCode)" -ForegroundColor Red
        Write-Host "❌ DETALHE DO ERRO: $errorBody" -ForegroundColor Yellow
    } else {
        Write-Host "❌ ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
}
