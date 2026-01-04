# PowerShell API example using Invoke-RestMethod
# Replace the env vars or edit the placeholders below.
$apiUrl = $env:API_URL -or "https://api.example.com/resource"
$token = $env:API_TOKEN -or "YOUR_TOKEN"
$body = @{ name = "Adam"; age = 30 } | ConvertTo-Json
$headers = @{ "Content-Type" = "application/json" }
if ($token -ne "YOUR_TOKEN") { $headers["Authorization"] = "Bearer $token" }
try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $body -TimeoutSec 30
    $response | ConvertTo-Json -Depth 5
} catch {
    Write-Error "Request failed: $_"
}
