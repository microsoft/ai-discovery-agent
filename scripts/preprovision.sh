echo "Finding current CLIENT_IP_ADDRESS (for development network permissions)..."
azd env set CLIENT_IP_ADDRESS $(curl ifconfig.me 2>/dev/null | tr -d '\r')
