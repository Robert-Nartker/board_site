import streamlit as st
import asyncio
import os
import json
from dotenv import find_dotenv, load_dotenv
from agents import Agent, Runner, OpenAIResponsesModel, FileSearchTool, AsyncOpenAI

# Initialize session state to store conversation
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
    st.session_state.initialized = False
    st.session_state.agents = {}
    
# Page configuration
st.set_page_config(page_title="AI Board Meeting", page_icon="🤖", layout="wide")
st.title("AI Board Meeting")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    model_option = st.selectbox(
        "Select Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        index=0
    )
    
    # Add a button to reset the conversation
    if st.button("Reset Conversation"):
        st.session_state.conversation_history = []
        st.rerun()

# Function to initialize agents (only run once)
async def initialize_agents():
    if st.session_state.initialized:
        return
    
    with st.spinner("Initializing agents..."):
        # Load .env variables
        env_location = find_dotenv()
        load_dotenv(env_location)
        
        # Load vector ids
        vector_ids_raw = os.getenv('VECTOR_IDS')
        if not vector_ids_raw:
            st.error("VECTOR_IDS environment variable is not set")
            return
        
        # Parse the JSON array from the environment variable
        vector_ids = json.loads(vector_ids_raw)
        
        # API
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY environment variable is not set")
            return
        
        model = OpenAIResponsesModel(
            model=model_option,
            openai_client=AsyncOpenAI(api_key=OPENAI_API_KEY)
        )
        
        # Load agent instructions
        agent_names = ["orchestrator", "altman", "bezos", "bissett", "buffett", 
                      "hormozi", "huang", "melancon", "musk", "padar", "woods"]
        
        instructions = {}
        for name in agent_names:
            with open(f"agents/{name}/{name}_instructions.txt", 'r+') as f:
                instructions[name] = f.read()
        
        # Create agent objects
        agent_map = {
            'altman': Agent(
                name='Altman', 
                model=model,
                instructions=instructions["altman"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[0]])]
            ),
            'bezos': Agent(
                name='Bezos', 
                model=model,
                instructions=instructions["bezos"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[1]])]
            ),
            'bissett': Agent(
                name='Bissett', 
                model=model,
                instructions=instructions["bissett"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[2]])]
            ),
            'buffett': Agent(
                name='Buffett', 
                model=model,
                instructions=instructions["buffett"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[3]])]
            ),
            'hormozi': Agent(
                name='Hormozi', 
                model=model,
                instructions=instructions["hormozi"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[4]])]
            ),
            'huang': Agent(
                name='Huang', 
                model=model,
                instructions=instructions["huang"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[5]])]
            ),
            'melancon': Agent(
                name='Melancon', 
                model=model,
                instructions=instructions["melancon"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[6]])]
            ),
            'musk': Agent(
                name='Musk', 
                model=model,
                instructions=instructions["musk"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[7]])]
            ),
            'padar': Agent(
                name='Padar', 
                model=model,
                instructions=instructions["padar"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[8]])]
            ),
            'woods': Agent(
                name='Woods', 
                model=model,
                instructions=instructions["woods"],
                tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[9]])]
            ),
            'orchestrator': Agent(
                name='Orchestrator',
                model=model,
                instructions=instructions["orchestrator"],
                tools=[]
            )
        }
        
        # Store in session state
        st.session_state.agents = agent_map
        st.session_state.first_name_map = {
            'sam': 'altman',
            'jeff': 'bezos',
            'martin': 'bissett',
            'warren': 'buffett',
            'alex': 'hormozi',
            'jensen': 'huang',
            'barry': 'melancon',
            'elon': 'musk',
            'jody': 'padar',
            'geoff': 'woods'
        }
        st.session_state.initialized = True

# Function to check if orchestrator's response needs a board member reply
async def eval_response_async(context: str) -> str:
    # Look for the last line containing a question mark
    lines = context.split('\n')
    last_question_line = None
    for line in reversed(lines):  # Search from the end of the message
        if '?' in line:
            last_question_line = line
            break

    if not last_question_line:
        return ""
    
    agent_map = st.session_state.agents
    first_name_map = st.session_state.first_name_map
    
    # Check for board member names
    for member_name in agent_map.keys():
        if member_name != 'orchestrator' and member_name in last_question_line.lower():
            s = f'Contribute to the following conversation by responding to the last question: {context}'
            agent_obj = agent_map[member_name]
            result = await Runner.run(agent_obj, input=s)
            return f"{member_name.capitalize()}: {result.final_output}"
    
    # Check for first names
    for first_name, member_name in first_name_map.items():
        if first_name in last_question_line.lower():
            s = f'Contribute to the following conversation by responding to the last question: {context}'
            agent_obj = agent_map[member_name]
            result = await Runner.run(agent_obj, input=s)
            return f"{member_name.capitalize()}: {result.final_output}"
    
    return ""

# Display conversation history
for message in st.session_state.conversation_history:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# Get user input
user_input = st.chat_input("Enter your message...")

# Process user input
if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.conversation_history.append({"role": "user", "content": user_input})
    
    # Run asynchronously
    async def process_message():
        # Initialize agents if not already done
        if not st.session_state.initialized:
            await initialize_agents()
        
        # Run the orchestrator with the conversation history
        with st.spinner("Orchestrator is thinking..."):
            result = await Runner.run(
                st.session_state.agents["orchestrator"], 
                input=st.session_state.conversation_history
            )
            
            if result.final_output:
                orchestrator_msg = f"Orchestrator: {result.final_output}"
                st.chat_message("assistant").write(orchestrator_msg)
                st.session_state.conversation_history.append({"role": "assistant", "content": orchestrator_msg})
                
                # Check if any board member should respond
                with st.spinner("Board member is responding..."):
                    board_response = await eval_response_async(result.final_output)
                    if board_response:
                        st.chat_message("assistant").write(board_response)
                        st.session_state.conversation_history.append({"role": "assistant", "content": board_response})
    
    # Run the async function
    asyncio.run(process_message())

# Initialize agents when the app starts
if not st.session_state.initialized:
    asyncio.run(initialize_agents()) 