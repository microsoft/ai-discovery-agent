
import os


def get_azure_credential():
    """Get Azure credential based on environment."""
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    if os.getenv("LOCAL_DEVELOPMENT","false").lower() == "true":
        # Use DefaultAzureCredential for local development with managed identity
        credential = DefaultAzureCredential()  # CodeQL [SM05139] Okay use of DefaultAzureCredential as it is only used in development 
    else:
        credential = ManagedIdentityCredential()
    return credential
