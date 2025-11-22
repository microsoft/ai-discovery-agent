#!/usr/bin/env -S uv run
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import yaml
import os
import sys
import json
import azure.ai.agents as agents

def get_azure_credential():
    """
    Returns an Azure credential object based on the LOCAL_DEVELOPMENT environment variable.

    If LOCAL_DEVELOPMENT is set to "true" (case-insensitive), returns a DefaultAzureCredential instance,
    which is suitable for local development and supports multiple authentication methods.
    Otherwise, returns a ManagedIdentityCredential instance, which is intended for use in production environments
    where managed identity is available.

    Returns:
        DefaultAzureCredential or ManagedIdentityCredential: The appropriate Azure credential object.
    """
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

    if os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true":
        # Use DefaultAzureCredential for local development; it attempts multiple authentication methods including environment variables, managed identity, Azure CLI, etc.
        credential = DefaultAzureCredential()  # CodeQL [SM05139] Okay use of DefaultAzureCredential as it is only used in development
    else:
        credential = ManagedIdentityCredential()
    return credential

def deploy_agent(agent_yaml_path: str, endpoint: str):
    with open(agent_yaml_path, 'r') as file:
        agent_config = yaml.safe_load(file)
    
    client=agents.AgentsClient(credential=get_azure_credential(),endpoint=endpoint)

    #remove version and id
    if 'id' in agent_config:
        del agent_config['id']
    if 'version' in agent_config:
        del agent_config['version']
    client.create_agent(agent_config)

    # agent = client.create_agent(
    # model=agent_config['model']['id'],
    #     name=agent_config.get('name', 'Agent'),
    #     instructions=agent_config.get('instructions', ''),
    #     tools=agent_config.get('tools', []),
    #     # tool_resources=agent_config.get('tool_resources'),
    #     temperature=agent_config.get('temperature'),
    #     top_p=agent_config.get('top_p'),
    #     response_format=agent_config.get('response_format')
    # )
    # print(f"Agent created successfully with ID: {agent.id}")
    # Simulate deployment logic
    # print(f"Deploying agent with the following configuration:\n{yaml.dump(agent_config)}")
    
    # Here you would add the actual deployment logic, e.g., API calls to deploy the agent

def list_agents(endpoint: str):
    client=agents.AgentsClient(credential=get_azure_credential(),endpoint=endpoint)
    agents_list = client.list_agents()
    for agent in agents_list:
        print(f"Agent ID: {agent.id}, Name: {agent.name}")

def get_agent_details(agent_id: str, endpoint: str, format: str = "yaml"):
    client=agents.AgentsClient(credential=get_azure_credential(),endpoint=endpoint)
    agent = client.get_agent(agent_id)
    if format == "json":
        print(json.dumps(agent.as_dict(), indent=2))
    else:        
        agent_dict = agent.as_dict()
        print(yaml.dump(agent_dict, default_flow_style=False, sort_keys=False))

if __name__ == "__main__":
    endpoint = os.getenv("AZURE_AI_AGENTS_ENDPOINT")
    if not endpoint:
        print("AZURE_AI_AGENTS_ENDPOINT environment variable is not set.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: deploy.py <action>º [<agent_yaml_path>|<agent_id>]")
        sys.exit(1)

    action = sys.argv[1]    
    if action == "deploy":
        if len(sys.argv) != 3:
            print("Usage: deploy.py deploy <agent_yaml_path>")
            sys.exit(1)
        deploy_agent(sys.argv[2], endpoint)
    elif action == "list":
        list_agents(endpoint)
    elif action == "details":
        if len(sys.argv) < 3:
            print("Usage: deploy.py details <agent_id>")
            sys.exit(1)
        get_agent_details(sys.argv[2], endpoint, sys.argv[3] if len(sys.argv) > 3 else "yaml")
    else:
        print("Unknown action. Available actions: deploy, list, details")
        sys.exit(1)