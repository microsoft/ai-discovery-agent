#!/bin/sh
# Pre-infrastructure deletion script
# remove assignments
az role assignment delete --assignee "appId=$(azd env get-value AZURE_GH_FED_CLIENT_ID)" --role "Contributor" --scope "/subscriptions/$(azd env get-value AZURE_SUBSCRIPTION_ID)"
az role assignment delete --assignee "appId=$(azd env get-value AZURE_GH_FED_CLIENT_ID)" --role "User Access Administrator" --scope "/subscriptions/$(azd env get-value AZURE_SUBSCRIPTION_ID)"
echo "Role assignments removed."
