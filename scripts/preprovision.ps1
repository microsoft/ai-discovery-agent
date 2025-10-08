Write-Host "Finding current CLIENT_IP_ADDRESS (for development network permissions)..."
$clientIp = (Invoke-WebRequest -Uri 'https://ifconfig.me' -UseBasicParsing).Content.Trim()
azd env set CLIENT_IP_ADDRESS $clientIp
