# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Chat event handlers for AI Discovery Workshop Agent.

Contains all Chainlit event handlers and message processing logic.
"""

import asyncio

import chainlit as cl
from chainlit.types import ThreadDict
from langchain_core.runnables import RunnableConfig

from aida.agents import RESPONSE_TAG, agent_manager, agent_registry
from aida.agents.graph_agent import GraphAgent
from aida.persistence import ConversationManager
from aida.utils.config import load_program_info
from aida.utils.logging_setup import get_logger
from aida.utils.mermaid import extract_mermaid

logger = get_logger(__name__)


async def set_chat_profiles(user: cl.User | None = None) -> list[cl.ChatProfile]:
    """
    Set available chat profiles based on user permissions.

    Parameters:
    -----------
    user : Optional[cl.User]
        Current authenticated user

    Returns:
    --------
    List[cl.ChatProfile]
        List of available chat profiles for the user
    """
    profiles: list[cl.ChatProfile] = []

    if user:
        user_roles = user.metadata.get("roles", ["user"])
        available_agents = agent_manager.get_available_agents(user_roles)
        for _, agent_info in available_agents.items():
            profiles.append(
                cl.ChatProfile(
                    name=agent_info["header"],
                    markdown_description=agent_info["subtitle"],
                    default=agent_info.get("default", False),
                )
            )
    return profiles


async def on_chat_start(conversation_manager: ConversationManager) -> None:
    """Initialize the chat session when a user connects."""
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="❌ Authentication required. Please log in.").send()
        return

    await cl.Message(
        content=f"👋 Welcome, {user.metadata.get('first_name', 'User')}! You are logged in as `{user.identifier}`.\n\n"
    ).send()

    user_roles = user.metadata.get("roles", ["user"])
    available_agents = agent_manager.get_available_agents(user_roles)
    if not available_agents:
        await cl.Message(content="❌ No agents available for your user role.").send()
        return
    cl.user_session.set("available_agents", available_agents)

    chat_profile = cl.user_session.get("chat_profile")
    current_agent_key = None
    if chat_profile:
        for agent_key, agent_info in available_agents.items():
            if agent_info.get("header") == chat_profile:
                current_agent_key = agent_key
                await cl.Message(
                    content=f"## {agent_info['header']}.\n\n{agent_info['subtitle']}"
                ).send()
                break

    if not current_agent_key:
        # If no current agent is set, default to the first available agent
        if available_agents:
            current_agent_key = next(iter(available_agents.keys()))
        else:
            await cl.Message(content="❌ No agents available.").send()
            return

    # Set the current agent key in user session
    cl.user_session.set("current_agent_key", current_agent_key)

    # Initialize or load conversation
    await initialize_conversation(
        user.identifier, current_agent_key, conversation_manager
    )


async def on_message(
    conversation_manager: ConversationManager, message: cl.Message
) -> None:
    """Handle incoming messages and route them to the appropriate agent."""
    user = cl.user_session.get("user")
    if not user:
        await cl.Message(content="❌ Authentication required. Please log in.").send()
        return

    content = message.content.strip()

    current_agent_key = cl.user_session.get("current_agent_key")
    if not current_agent_key:
        await cl.Message(
            content="❌ No agent selected. Please select an agent to continue."
        ).send()
        return
    # Process message with current agent
    await process_message(conversation_manager, content, current_agent_key, user)


async def on_chat_resume(
    conversation_manager: ConversationManager,
    thread: ThreadDict,
) -> None:
    """Resume a chat session from thread data."""
    user = cl.user_session.get("user")
    if user:
        user_roles = user.metadata.get("roles", ["user"])
        available_agents = agent_manager.get_available_agents(user_roles)
        cl.user_session.set("available_agents", available_agents)

        # Get the current agent key (this should be set by the chat profile)
        current_agent_key = cl.user_session.get("current_agent_key")
        if not current_agent_key:
            # Try to get from thread metadata or fallback to default
            metadata = thread.get("metadata", {})
            if metadata and "agent_key" in metadata:
                current_agent_key = metadata.get("agent_key")
                if not current_agent_key and available_agents:
                    # Use the first available agent as default
                    current_agent_key = next(iter(available_agents.keys()))

            if current_agent_key:
                cl.user_session.set("current_agent_key", current_agent_key)

        if current_agent_key and conversation_manager:
            try:
                await load_conversation_silently(
                    user.identifier, current_agent_key, conversation_manager
                )
                # Get the loaded conversation history and display it in UI
                conversation_history = cl.user_session.get("conversation_history", [])
                if conversation_history:
                    logger.info(
                        f"Restored {len(conversation_history)} messages to UI on resume"
                    )
                    await rebuild_messages(conversation_history)

            except Exception as e:
                logger.error(f"Error restoring conversation on resume: {e}")
                # Initialize empty conversation as fallback
                cl.user_session.set("conversation_history", [])
                cl.user_session.set("current_conversation_id", None)

        # Fallback: Try to restore from thread metadata (legacy support)
        metadata = thread.get("metadata", {})
        if (
            metadata
            and "conversation_history" in metadata
            and not cl.user_session.get("conversation_history")
        ):
            conversation_history = metadata["conversation_history"]
            cl.user_session.set("conversation_history", conversation_history)

            # Display loaded conversation history in UI
            await rebuild_messages(conversation_history)
    else:
        # No authenticated user - still try metadata fallback for basic functionality
        metadata = thread.get("metadata", {})
        if metadata and "conversation_history" in metadata:
            logger.info(
                "No authenticated user, but found conversation history in thread metadata"
            )


async def initialize_conversation(
    user_id: str, agent_key: str, conversation_manager: ConversationManager
) -> None:
    """
    Initialize or create a new conversation for the user and agent.

    Args:
        user_id: User identifier
        agent_key: Agent identifier
        conversation_manager: ConversationManager instance
    """
    if not conversation_manager:
        # Use in-memory storage if persistence is not available
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", None)
        return

    loading_message = cl.Message("Loading conversation...")
    await loading_message.send()
    # Run the conversation initialization in the background to avoid blocking UI
    asyncio.create_task(
        _initialize_conversation_background(
            user_id, agent_key, conversation_manager, loading_message=loading_message
        )
    )


async def _initialize_conversation_background(
    user_id: str,
    agent_key: str,
    conversation_manager: ConversationManager,
    loading_message: cl.Message,
) -> None:
    """
    Background task to initialize conversation without blocking the main UI thread.
    This runs the I/O operations and then schedules UI updates.
    """
    try:
        # Check if we should load an existing conversation or create a new one
        conversations = await conversation_manager.list_conversations(
            user_id, agent_key
        )

        if conversations:
            # Load the most recent conversation
            recent_conv = conversations[0]
            conversation_id = recent_conv["conversation_id"]
            conversation_data = await conversation_manager.load_conversation(
                user_id, agent_key, conversation_id
            )

            if conversation_data:
                conversation_history = conversation_data.get("messages", [])
                cl.user_session.set("conversation_history", conversation_history)
                cl.user_session.set("current_conversation_id", conversation_id)
                cl.user_session.set(
                    "conversation_title", conversation_data.get("title", "Untitled")
                )

                await cl.Message(
                    content=f"📝 Continuing conversation: **{conversation_data.get('title', 'Untitled')}**\n\n"
                    f"Use `/conversations` to view all conversations or `/new` to start a new one."
                ).send()
                await rebuild_messages(conversation_history)
                return

        # Create new conversation if none exists
        conversation_id = await conversation_manager.create_conversation(
            user_id, agent_key
        )
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", conversation_id)
        cl.user_session.set("conversation_title", "New Conversation")

    except Exception as e:
        logger.error(f"Error initializing conversation: {e}")
        # Fallback to in-memory storage
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", None)
    finally:
        if loading_message:
            await loading_message.remove()


async def load_conversation_silently(
    user_id: str, agent_key: str, conversation_manager: ConversationManager
) -> bool:
    """
    Load the most recent conversation into memory for user and agent without showing status messages.

    Args:
        user_id: User identifier
        agent_key: Agent identifier
        conversation_manager: ConversationManager instance

    Returns:
        True if conversation was loaded, False otherwise
    """
    if not conversation_manager:
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", None)
        return False

    try:
        # Check if we should load an existing conversation
        conversations = await conversation_manager.list_conversations(
            user_id, agent_key
        )

        if conversations:
            # Load the most recent conversation
            recent_conv = conversations[0]
            conversation_id = recent_conv["conversation_id"]
            conversation_data = await conversation_manager.load_conversation(
                user_id, agent_key, conversation_id
            )

            if conversation_data:
                cl.user_session.set(
                    "conversation_history", conversation_data.get("messages", [])
                )
                cl.user_session.set("current_conversation_id", conversation_id)
                cl.user_session.set(
                    "conversation_title", conversation_data.get("title", "Untitled")
                )
                return True

        # Initialize empty conversation if none exists
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", None)
        return False

    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        # Fallback to in-memory storage
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", None)
        return False


async def process_message(
    conversation_manager: ConversationManager,
    content: str,
    agent_key: str,
    user: cl.User,
) -> None:
    """
    Process a message with the specified agent.

    Parameters:
    -----------
    content : str
        The user's message content
    agent_key : str
        The key of the agent to process with
    user : cl.User
        The current user
    """
    if content.startswith("/"):
        # Handle commands like /info, /help, /switch agent_name, /conversations, /new, etc.
        command_parts = content[1:].split(" ", 1)
        command = command_parts[0].lower()
        argument = command_parts[1] if len(command_parts) > 1 else None

        if command == "info":
            # show info about the program from the pyproject.toml file
            program_info = load_program_info()
            await cl.Message(content=program_info).send()
        elif command == "help":
            help_text = (
                "### Available Commands:\n"
                "- `/info`: Show information about the current agent.\n"
                "- `/help`: Show this help message.\n"
                "- `/switch <agent_name>`: Switch to a different agent.\n"
                "- `/conversations`: List all conversations for the current agent.\n"
                "- `/load <conversation_id>`: Load a specific conversation.\n"
                "- `/new`: Start a new conversation.\n"
                "- `/delete <conversation_id>`: Delete a conversation.\n"
                "- `/title <new_title>`: Change the current conversation title.\n"
                "\nAvailable agents are:\n"
            )
            available_agents = cl.user_session.get("available_agents") or {}
            for a_key, a_info in available_agents.items():
                help_text += f"  - `{a_key}`: {a_info['header']}\n"
            await cl.Message(content=help_text).send()
        elif command == "switch":
            if argument:
                available_agents = cl.user_session.get("available_agents", {})
                if available_agents and argument in available_agents:
                    cl.user_session.set("current_agent_key", argument)
                    agent_info = available_agents[argument]
                    await cl.Message(
                        content=f"✅ Switched to agent '{agent_info['header']}'.\n\n{agent_info['subtitle']}"
                    ).send()
                    await initialize_conversation(
                        user.identifier, argument, conversation_manager
                    )
                else:
                    await cl.Message(
                        content=f"❌ Agent '{argument}' not found. Use `/help` to see available agents."
                    ).send()
            else:
                await cl.Message(
                    content="❌ Please specify an agent name to switch to. Usage: `/switch <agent_name>`."
                ).send()
        elif command == "conversations":
            await handle_list_conversations(
                conversation_manager, user.identifier, agent_key
            )
        elif command == "load":
            if argument:
                await handle_load_conversation(
                    conversation_manager, user.identifier, agent_key, argument
                )
            else:
                await cl.Message(
                    content="❌ Please specify a conversation ID to load. Usage: `/load <conversation_id>`."
                ).send()
        elif command == "new":
            await handle_new_conversation(
                conversation_manager, user.identifier, agent_key
            )
        elif command == "delete":
            if argument:
                await handle_delete_conversation(
                    conversation_manager, user.identifier, agent_key, argument
                )
            else:
                await cl.Message(
                    content="❌ Please specify a conversation ID to delete. Usage: `/delete <conversation_id>`."
                ).send()
        elif command == "title":
            if argument:
                await handle_rename_conversation(
                    conversation_manager, user.identifier, agent_key, argument
                )
            else:
                await cl.Message(
                    content="❌ Please specify a new title. Usage: `/title <new_title>`."
                ).send()
        else:
            await cl.Message(
                content=f"❌ Unknown command '/{command}'. Use `/help` for a list of commands."
            ).send()
    else:
        await process_with_agent(conversation_manager, content, agent_key, user)


async def handle_list_conversations(
    conversation_manager: ConversationManager, user_id: str, agent_key: str
) -> None:
    """Handle the /conversations command."""

    if not conversation_manager:
        await cl.Message(content="❌ Conversation persistence is not available.").send()
        return

    try:
        conversations = await conversation_manager.list_conversations(
            user_id, agent_key
        )

        if not conversations:
            await cl.Message(content="📝 No conversations found for this agent.").send()
            return

        content = f"### 📝 Conversations for {agent_key}\n\n"
        current_conv_id = cl.user_session.get("current_conversation_id")

        for conv in conversations:
            status = (
                "🔄 (current)" if conv["conversation_id"] == current_conv_id else ""
            )
            content += f"- **{conv['title']}** {status}\n"
            content += f"  - ID: `{conv['conversation_id']}`\n"
            content += f"  - Messages: {conv['message_count']}\n"
            content += f"  - Updated: {conv['updated_at'][:19] if conv['updated_at'] else 'Unknown'}\n\n"

        content += (
            "\nUse `/load <conversation_id>` to switch to a different conversation."
        )

        await cl.Message(content=content).send()

    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        await cl.Message(content="❌ Error retrieving conversations.").send()


async def handle_load_conversation(
    conversation_manager: ConversationManager,
    user_id: str,
    agent_key: str,
    conversation_id: str,
) -> None:
    """Handle the /load command."""

    if not conversation_manager:
        await cl.Message(content="❌ Conversation persistence is not available.").send()
        return

    try:
        conversation_data = await conversation_manager.load_conversation(
            user_id, agent_key, conversation_id
        )

        if not conversation_data:
            await cl.Message(
                content=f"❌ Conversation `{conversation_id}` not found."
            ).send()
            return

        # Save current conversation if it has content
        current_conv_id = cl.user_session.get("current_conversation_id")
        current_history = cl.user_session.get("conversation_history", [])

        if current_conv_id and current_history:
            await conversation_manager.save_conversation(
                user_id, agent_key, current_conv_id, current_history
            )

        # Load new conversation
        conversation_history = conversation_data.get("messages", [])
        cl.user_session.set("conversation_history", conversation_history)
        cl.user_session.set("current_conversation_id", conversation_id)
        cl.user_session.set(
            "conversation_title", conversation_data.get("title", "Untitled")
        )

        await cl.Message(
            content=f"✅ Loaded conversation: **{conversation_data.get('title', 'Untitled')}**\n\n"
            f"This conversation has {len(conversation_data.get('messages', []))} messages."
        ).send()
        await rebuild_messages(conversation_history)

    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        await cl.Message(content="❌ Error loading conversation.").send()


async def handle_new_conversation(
    conversation_manager: ConversationManager, user_id: str, agent_key: str
) -> None:
    """Handle the /new command."""

    if not conversation_manager:
        # For in-memory storage, just clear the history
        cl.user_session.set("conversation_history", [])
        await cl.Message(content="✅ Started a new conversation.").send()
        return

    try:
        # Save current conversation if it has content
        current_conv_id = cl.user_session.get("current_conversation_id")
        current_history = cl.user_session.get("conversation_history", [])

        if current_conv_id and current_history:
            await conversation_manager.save_conversation(
                user_id, agent_key, current_conv_id, current_history
            )

        # Create new conversation
        conversation_id = await conversation_manager.create_conversation(
            user_id, agent_key
        )
        cl.user_session.set("conversation_history", [])
        cl.user_session.set("current_conversation_id", conversation_id)
        cl.user_session.set("conversation_title", "New Conversation")

        await cl.Message(content="✅ Started a new conversation.").send()

    except Exception as e:
        logger.error(f"Error creating new conversation: {e}")
        await cl.Message(content="❌ Error creating new conversation.").send()


async def handle_delete_conversation(
    conversation_manager: ConversationManager,
    user_id: str,
    agent_key: str,
    conversation_id: str,
) -> None:
    """Handle the /delete command."""

    if not conversation_manager:
        await cl.Message(content="❌ Conversation persistence is not available.").send()
        return

    try:
        # Check if trying to delete current conversation
        current_conv_id = cl.user_session.get("current_conversation_id")
        if conversation_id == current_conv_id:
            await cl.Message(
                content="❌ Cannot delete the current conversation. Switch to another conversation first."
            ).send()
            return

        success = await conversation_manager.delete_conversation(
            user_id, agent_key, conversation_id
        )

        if success:
            await cl.Message(
                content=f"✅ Deleted conversation `{conversation_id}`."
            ).send()
        else:
            await cl.Message(
                content=f"❌ Failed to delete conversation `{conversation_id}`."
            ).send()

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        await cl.Message(content="❌ Error deleting conversation.").send()


async def handle_rename_conversation(
    conversation_manager: ConversationManager,
    user_id: str,
    agent_key: str,
    new_title: str,
) -> None:
    """Handle the /title command."""

    if not conversation_manager:
        await cl.Message(content="❌ Conversation persistence is not available.").send()
        return

    try:
        current_conv_id = cl.user_session.get("current_conversation_id")
        current_history = cl.user_session.get("conversation_history", [])

        if not current_conv_id:
            await cl.Message(content="❌ No active conversation to rename.").send()
            return

        if not current_history:
            current_history = []

        success = await conversation_manager.save_conversation(
            user_id, agent_key, current_conv_id, current_history, new_title
        )

        if success:
            cl.user_session.set("conversation_title", new_title)
            await cl.Message(
                content=f"✅ Conversation renamed to: **{new_title}**"
            ).send()
        else:
            await cl.Message(content="❌ Failed to rename conversation.").send()

    except Exception as e:
        logger.error(f"Error renaming conversation: {e}")
        await cl.Message(content="❌ Error renaming conversation.").send()


async def process_with_agent(
    conversation_manager: ConversationManager,
    content: str,
    agent_key: str,
    user: cl.User,
) -> None:
    """
    Process a message with the specified agent.

    Parameters:
    -----------
    content : str
        The user's message content
    agent_key : str
        The key of the agent to process with
    user : cl.User
        The current user
    """
    try:
        # Get the agent from registry
        agent = agent_registry.get_agent(agent_key)
        if not agent:
            await cl.Message(
                content=f"❌ Agent '{agent_key}' not found in registry."
            ).send()
            return

        # Get conversation history from session
        history: list[dict[str, str]] = (
            cl.user_session.get("conversation_history", []) or []
        )

        # Add user message to history
        history.append({"role": "user", "content": content})

        msg = cl.Message(content="")
        from langchain_core.callbacks import get_usage_metadata_callback

        configurable = {}
        if type(agent) is GraphAgent:
            configurable = {"thread_id": cl.context.session.id}
        # Show typing indicator
        # async with cl.Step(name="🤔 Thinking...") as step:
        with cl.Step(name=agent_key) as step:
            # Process the message with the agent
            step.input = content
            with get_usage_metadata_callback() as cb:
                lcb = cl.LangchainCallbackHandler()
                # Set the schema format for the Langchain callback
                # Needed to avoid issues with Error in callback coroutine: TracerException('No indexed run ID...
                lcb._schema_format = "original+chat"
                async for chunk in agent.astream(
                    history,
                    config=RunnableConfig(
                        callbacks=[
                            lcb,
                        ],
                        configurable=configurable,
                    ),
                ):
                    response = ""
                    if isinstance(chunk, tuple):
                        message, metadata = chunk
                        if (
                            metadata
                            and "tags" in metadata
                            and RESPONSE_TAG in metadata["tags"]
                        ):
                            # Handle agent response chunk
                            response = message.content
                        else:
                            if metadata and "langgraph_node" in metadata:
                                logger.debug(
                                    f"Agent response Node: {metadata["langgraph_node"]}"
                                )
                            else:
                                logger.debug(f"Agent response: {metadata}")

                        if metadata and "langgraph_node" in metadata:
                            step.name = metadata["langgraph_node"]
                            step.output = f"Processing with agent node: {metadata['langgraph_node']}"
                            logger.debug(
                                f"Agent response Node: {metadata['langgraph_node']}"
                            )
                    else:
                        response = chunk.content
                    if cb.usage_metadata:
                        step.output = cb.usage_metadata
                    if response:
                        step.output = "Generating response..."
                        await msg.stream_token(response)
                step.output = cb.usage_metadata
                await step.send()

        response = msg.content.strip() if msg.content else None
        # check if any mermaid tags are present in the response and extract the code
        # there may be multiple mermaid code blocks, so create a list of them
        if response:
            mermaid_codes = extract_mermaid(response)
            # If mermaid codes are found, send them as separate messages
            if mermaid_codes:
                logger.debug("Found %i mermaid code blocks.", len(mermaid_codes))
                msg.elements = list(  # pyright: ignore[reportAttributeAccessIssue]
                    map(
                        lambda code, id: cl.CustomElement(
                            name="MermaidViewer", props={"code": code, "id": id}
                        ),
                        mermaid_codes,
                        range(1, len(mermaid_codes) + 1),
                    )
                )

            await msg.send()
            # Add assistant response to history
            history.append({"role": "assistant", "content": response})
            cl.user_session.set("conversation_history", history)

            # Save conversation to persistence layer
            current_conv_id = cl.user_session.get("current_conversation_id")
            if current_conv_id:
                try:
                    await conversation_manager.save_conversation(
                        user.identifier, agent_key, current_conv_id, history
                    )
                except Exception as e:
                    logger.error(f"Error saving conversation: {e}")

    except Exception as e:
        logger.error(
            f"Error processing with agent {agent_key}: {e}", exc_info=e, stack_info=True
        )
        await cl.Message(content=f"❌ Error processing your message: {str(e)}").send()


async def rebuild_messages(conversation_history: list[dict[str, str]]) -> None:
    """
    Rebuild and display conversation messages in the UI with full mermaid support.

    Parameters:
    -----------
    conversation_history : List[Dict[str, str]]
        List of conversation messages with 'role' and 'content' keys
    """
    if conversation_history:
        logger.info(f"Restoring {len(conversation_history)} messages to UI")
        for message in conversation_history:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "user":
                await cl.Message(content=content, author="User").send()
            elif role == "assistant":
                # Create assistant message with mermaid support
                elements: list[cl.CustomElement] | None = None
                # Check for mermaid diagrams in assistant responses
                if content:
                    mermaid_codes = extract_mermaid(content)
                    # If mermaid codes are found, add them as custom elements
                    if mermaid_codes:
                        logger.debug(
                            "Found %i mermaid code blocks in restored message.",
                            len(mermaid_codes),
                        )
                        elements = list(
                            map(
                                lambda code, id: cl.CustomElement(
                                    name="MermaidViewer",
                                    props={"code": code, "id": id},
                                ),
                                mermaid_codes,
                                range(1, len(mermaid_codes) + 1),
                            )
                        )

                msg = cl.Message(content=content, author="Assistant", elements=elements)

                await msg.send()

        logger.info("Conversation history with mermaid support restored successfully")
