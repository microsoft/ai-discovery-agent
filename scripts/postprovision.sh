#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

. "$SCRIPT_DIR/map-env-vars.sh"

if [ -n "$OAUTH_SETTINGS" ]; then
    echo "Restoring OAUTH_ settings to environment..."
    # Read the JSON array and set each OAUTH_ variable

    echo $OAUTH_SETTINGS > "/tmp/${WEB_APP_NAME}_oauth.json"
    az webapp config appsettings set -n $WEB_APP_NAME -g $RESOURCE_GROUP_NAME --settings "@/tmp/${WEB_APP_NAME}_oauth.json"
    rm "/tmp/${WEB_APP_NAME}_oauth.json"
else
    echo "No OAUTH_SETTINGS found to apply."
fi

if [ -n "$OAUTH_SETTINGS_STAGING" ]; then
    echo "Restoring OAUTH_ settings to staging environment..."
    # Read the JSON array and set each OAUTH_ variable

    echo $OAUTH_SETTINGS_STAGING > "/tmp/${WEB_APP_NAME}_oauth_staging.json"
    az webapp config appsettings set -n $WEB_APP_NAME -g $RESOURCE_GROUP_NAME --slot staging --settings "@/tmp/${WEB_APP_NAME}_oauth_staging.json"
    rm "/tmp/${WEB_APP_NAME}_oauth_staging.json"
else
    echo "No OAUTH_SETTINGS found to apply."
fi

. "$SCRIPT_DIR/enable-network.sh"


