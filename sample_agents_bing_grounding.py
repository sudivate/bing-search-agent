# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the Bing grounding tool from
    the Azure Agents service using a synchronous client.

USAGE:
    python sample_agents_bing_grounding.py

    Before running the sample:

    pip install azure-ai-projects azure-ai-agents azure-identity

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - The Azure AI Project endpoint, as found in the Overview
                          page of your Azure AI Foundry portal.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Azure AI Foundry project.
    3) AZURE_BING_CONNECTION_ID - The ID of the Bing connection, in the format of:
       /subscriptions/{subscription-id}/resourceGroups/{resource-group-name}/providers/Microsoft.MachineLearningServices/workspaces/{workspace-name}/connections/{connection-name}
"""

import json
import os
from datetime import datetime

from azure.ai.agents.models import BingGroundingTool, MessageRole
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def load_prompt_from_file(file_path):
    """Load agent instructions from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(
            f"Warning: Prompt file '{file_path}' not found. Using default instructions.")
        return "You are a helpful agent"


def save_conversation_to_markdown(conversation_history, run_details_list):
    """Save entire conversation to a markdown file with timestamp."""
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.md"
    filepath = os.path.join("search-results", filename)

    # Calculate overall search statistics
    total_search_calls = 0
    total_runs = len(run_details_list)
    runs_with_search = 0

    for run_details in run_details_list:
        run_tool_calls = run_details.get('tool_calls', [])
        run_search_calls = 0

        for call in run_tool_calls:
            call_type = call.get('type', '')
            # Count any Bing-related tool calls or calls with bing_grounding details
            if ('bing' in call_type.lower() or
                call_type == 'bing_grounding' or
                    call.get('bing_grounding')):
                run_search_calls += 1

        total_search_calls += run_search_calls
        if run_search_calls > 0:
            runs_with_search += 1

    # Create markdown content
    markdown_content = f"""# Conversation Log - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Conversation Summary
- **Total Messages**: {len(conversation_history)}
- **Total Agent Runs**: {total_runs}
- **Runs with Bing Search**: {runs_with_search}/{total_runs}
- **Total Search Calls**: {total_search_calls}
- **Overall Compliance**: {'✅ COMPLIANT' if runs_with_search == total_runs else f'❌ PARTIAL ({runs_with_search}/{total_runs} runs used search)'}

---

"""

    # Add each conversation exchange
    for i, exchange in enumerate(conversation_history, 1):
        user_input = exchange['user_input']
        agent_response = exchange['agent_response']
        citations = exchange['citations']
        run_details = exchange['run_details']

        # Check if search was used for this exchange
        search_used = False
        search_calls = 0

        for call in run_details.get('tool_calls', []):
            call_type = call.get('type', '')
            # Check for any Bing-related tool calls
            if ('bing' in call_type.lower() or
                call_type == 'bing_grounding' or
                    call.get('bing_grounding')):
                search_calls += 1
                search_used = True

        markdown_content += f"""## Exchange {i}

### Search Status
- **Bing Search Used**: {'✅ YES' if search_used else '❌ NO'}
- **Search Calls**: {search_calls}
- **Compliance**: {'COMPLIANT' if search_used else 'NON-COMPLIANT'}

### User Input
{user_input}

### Agent Response
```json
{agent_response}
```

### Citations
"""

        if citations:
            for j, annotation in enumerate(citations, 1):
                markdown_content += f"{j}. [{annotation.url_citation.title}]({annotation.url_citation.url})\n"
        else:
            markdown_content += "No citations found.\n"

        markdown_content += f"""
### Technical Details
- **Run Status**: {run_details.get('status', 'Unknown')}
- **Run ID**: {run_details.get('run_id', 'Unknown')}
- **Thread ID**: {run_details.get('thread_id', 'Unknown')}

### Tool Calls
"""

        if run_details.get('tool_calls'):
            for call in run_details['tool_calls']:
                markdown_content += f"- **Call ID**: {call.get('id', 'Unknown')}\n"
                markdown_content += f"  - **Type**: {call.get('type', 'Unknown')}\n"
                bing_details = call.get('bing_grounding', {})
                if bing_details:
                    markdown_content += f"  - **Request URL**: {bing_details.get('requesturl', 'Unknown')}\n"
        else:
            markdown_content += "No tool calls recorded.\n"

        markdown_content += "\n---\n\n"

    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Conversation saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return None


project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

# [START create_agent_with_bing_grounding_tool]
conn_id = os.environ["AZURE_BING_CONNECTION_ID"]

# Initialize agent bing tool and add the connection id
bing = BingGroundingTool(connection_id=conn_id)

# Load instructions from agent instructions file
instructions = load_prompt_from_file("agent_instructions.txt")

print("🔍 Bing Search Agent - Interactive Mode")
print("Type 'exit' to end the conversation and save results")
print("=" * 50)

# Create agent with the bing tool and process agent run
with project_client:
    agents_client = project_client.agents
    agent = agents_client.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="bing-search-agent",
        instructions=instructions,
        tools=bing.definitions,
        temperature=0.1,
    )
    # [END create_agent_with_bing_grounding_tool]

    print(f"✅ Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = agents_client.threads.create()
    print(f"✅ Created thread, ID: {thread.id}")
    print()

    # Initialize conversation tracking
    conversation_history = []
    run_details_list = []

    try:
        while True:
            # Get user input
            user_input = input("🧑 You: ").strip()

            if user_input.lower() == 'exit':
                print("\n👋 Goodbye! Saving conversation...")
                break

            if not user_input:
                print("Please enter a question or type 'exit' to quit.")
                continue

            print(f"\n🤖 Agent is thinking and searching...")

            # Create message to thread
            message = agents_client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=user_input,
            )

            # Create and process agent run in thread with tools
            run = agents_client.runs.create_and_process(
                thread_id=thread.id, agent_id=agent.id, tool_choice={"type": "bing_grounding"})

            if run.status == "failed":
                print(f"❌ Run failed: {run.last_error}")
                continue

            # Collect run details for this exchange
            run_details = {
                'status': run.status,
                'run_id': run.id,
                'agent_id': agent.id,
                'thread_id': thread.id,
                'tool_calls': []
            }

            # Fetch run steps to get the details of the agent run
            run_steps = agents_client.run_steps.list(
                thread_id=thread.id, run_id=run.id)

            search_calls_made = 0
            for step in run_steps:
                step_details = step.get("step_details", {})
                tool_calls = step_details.get("tool_calls", [])

                if tool_calls:
                    for call in tool_calls:
                        call_type = call.get('type', '')
                        # Debug output
                        print(f"DEBUG: Tool call type: '{call_type}'")

                        # Count any Bing-related tool calls
                        if 'bing' in call_type.lower() or call_type == 'bing_grounding':
                            search_calls_made += 1

                        # Also check if there are bing_grounding details
                        bing_grounding_details = call.get("bing_grounding", {})
                        if bing_grounding_details:
                            # Ensure at least 1 if details exist
                            search_calls_made = max(search_calls_made, 1)

                        # Store tool call details for markdown export
                        run_details['tool_calls'].append({
                            'id': call.get('id'),
                            'type': call_type,
                            'bing_grounding': bing_grounding_details
                        })

                        # Debug output
                        print(
                            f"DEBUG: Stored tool call - ID: {call.get('id')}, Type: {call_type}")

            # Get the Agent's response message with citations
            response_message = agents_client.messages.get_last_message_by_role(
                thread_id=thread.id, role=MessageRole.AGENT)

            agent_response = ""
            citations = []

            if response_message:
                # Collect response text
                for text_message in response_message.text_messages:
                    agent_response += text_message.text.value + "\n"

                # Collect citations
                for annotation in response_message.url_citation_annotations:
                    citations.append(annotation)

            # Display the response
            search_status = "🔍 Search used" if search_calls_made > 0 else "⚠️  No search"
            print(f"\n🤖 Agent ({search_status}):")

            # Try to parse JSON response for better display
            try:
                json_response = json.loads(agent_response.strip())
                if 'candidates' in json_response and json_response['candidates']:
                    candidate = json_response['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        main_text = candidate['content']['parts'][0]['text']
                        print(main_text)

                        # Display grounding metadata info
                        if 'groundingMetadata' in candidate:
                            metadata = candidate['groundingMetadata']
                            if 'webSearchQueries' in metadata and metadata['webSearchQueries']:
                                print(
                                    f"\n🔍 Search queries used: {', '.join(metadata['webSearchQueries'])}")
                            if 'groundingChunks' in metadata and metadata['groundingChunks']:
                                print(
                                    f"📊 Sources found: {len(metadata['groundingChunks'])}")
                    else:
                        print(agent_response.strip())
                else:
                    print(agent_response.strip())
            except (json.JSONDecodeError, KeyError):
                # If not valid JSON or missing expected structure, display as-is
                print(agent_response.strip())

            if citations:
                print(f"\n📚 Sources ({len(citations)} found):")
                for i, annotation in enumerate(citations, 1):
                    print(f"  {i}. {annotation.url_citation.title}")
                    print(f"     {annotation.url_citation.url}")

            # Store this exchange in conversation history
            conversation_history.append({
                'user_input': user_input,
                'agent_response': agent_response.strip(),
                'citations': citations,
                'run_details': run_details
            })
            run_details_list.append(run_details)

            print("\n" + "=" * 50)

    except KeyboardInterrupt:
        print("\n\n⚠️  Conversation interrupted by user. Saving results...")

    # Save the entire conversation
    if conversation_history:
        save_conversation_to_markdown(conversation_history, run_details_list)

        # Display final statistics
        total_exchanges = len(conversation_history)
        exchanges_with_search = 0
        total_search_calls = 0

        for details in run_details_list:
            run_search_calls = 0
            for call in details.get('tool_calls', []):
                call_type = call.get('type', '')
                if ('bing' in call_type.lower() or
                    call_type == 'bing_grounding' or
                        call.get('bing_grounding')):
                    run_search_calls += 1

            total_search_calls += run_search_calls
            if run_search_calls > 0:
                exchanges_with_search += 1

        print(f"\n📊 Session Summary:")
        print(f"   • Total exchanges: {total_exchanges}")
        print(
            f"   • Exchanges with search: {exchanges_with_search}/{total_exchanges}")
        print(f"   • Total search calls: {total_search_calls}")
        print(
            f"   • Compliance: {'✅ FULL' if exchanges_with_search == total_exchanges else '⚠️  PARTIAL'}")
    else:
        print("No conversation to save.")

    # Delete the agent when done
    agents_client.delete_agent(agent.id)
    print("🗑️  Agent deleted")
