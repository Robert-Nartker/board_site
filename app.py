import streamlit as st
import os, asyncio
from dotenv import find_dotenv, load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIResponsesModel, function_tool

# Load environment variables
env_location = find_dotenv()
load_dotenv(env_location)

# Initialize OpenAI client
model = OpenAIResponsesModel(
    model="gpt-4o-mini",
    openai_client=AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
)

# Initialize session state for conversation history if it doesn't exist
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Load agent instructions
def load_agent_instructions(agent_name):
    with open(f"agents/{agent_name.lower()}/{agent_name.lower()}_instructions.txt", 'r+') as f:
        return f.read()

# Create agents
def initialize_agents():
    agent_names = ['orchestrator', 'altman', 'bezos', 'bissett', 'buffett', 
                   'hormozi', 'huang', 'melancon', 'musk', 'padar', 'woods']
    
    agents = {}
    board_member_tools = []
    
    for name in agent_names:
        instructions = load_agent_instructions(name)
        agent = Agent(
            name=name.capitalize(),
            model=model,
            instructions=instructions
        )
        agents[name] = agent
        
        # Create individual board member tools
        if name != 'orchestrator':
            # Define a tool for each board member
            tool_name = f"get_{name}_response"
            
            @function_tool(name_override=tool_name)
            async def get_member_response(question: str) -> str:
                """Get a response from this board member.

                Args:
                    question: The question to ask the board member
                """
                # Get response from the member agent
                result = await Runner.run(agents[name], input=question)
                # Prefix the response with the board member's name
                return f"{name.capitalize()}: {result.final_output}"
            
            # Add tool to the list
            board_member_tools.append(get_member_response)
    
    # Create orchestrator with individual board member tools
    agents['orchestrator'] = Agent(
        name='Orchestrator',
        model=model,
        instructions=load_agent_instructions('orchestrator'),
        tools=board_member_tools
    )
    
    return agents

async def get_agent_response(agent, conversation_history):
    """Async function to get response from agent"""
    return await Runner.run(agent, input=conversation_history)

# Streamlit UI
st.title("Board Meeting Simulator")
st.subheader("AI-Powered Board Meeting with Expert Agents")

# Initialize agents
if 'agents' not in st.session_state:
    st.session_state.agents = initialize_agents()

# Add a clear button
if st.button("Start New Meeting"):
    st.session_state.conversation_history = []
    st.rerun()

# Display chat messages
for message in st.session_state.conversation_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("What topic would you like to discuss?"):
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Add user message to history
    st.session_state.conversation_history.append({
        "role": "user",
        "content": prompt
    })
    
    # Get response from orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Board members are collaborating..."):
            # Use asyncio.run to handle the event loop
            result = asyncio.run(
                get_agent_response(
                    st.session_state.agents['orchestrator'],
                    st.session_state.conversation_history
                )
            )
            
            if result.final_output:
                st.write(result.final_output)
                # Add assistant response to history
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": result.final_output
                }) 