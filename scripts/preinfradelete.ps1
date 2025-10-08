# Pre-infrastructure deletion script
# remove assignments
$appId = azd env get-value AZURE_GH_FED_CLIENT_ID
$subscriptionId = azd env get-value AZURE_SUBSCRIPTION_ID

az role assignment delete --assignee "appId=$appId" --role "Contributor" --scope "/subscriptions/$subscriptionId"
az role assignment delete --assignee "appId=$appId" --role "User Access Administrator" --scope "/subscriptions/$subscriptionId"
