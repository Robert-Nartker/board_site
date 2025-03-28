import os
import json
import asyncio
import streamlit as st
import yaml
from yaml.loader import SafeLoader
from dotenv import find_dotenv, load_dotenv
from agents import Agent, Runner, OpenAIResponsesModel, FileSearchTool, AsyncOpenAI

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Board Meeting Simulation",
    page_icon="🌐",
    layout="wide"
)

# Load environment variables
env_location = find_dotenv()
load_dotenv(env_location)

# Simple password authentication with rate limiting
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0

if not st.session_state.authenticated:
    # Check if user has exceeded maximum attempts
    if st.session_state.failed_attempts >= 10:
        st.error("Too many failed attempts. Please try again later.")
        st.stop()
    
    # Get the allowed password from environment variable, default to 'cof' if not set
    allowed_password = os.getenv('APP_PASSWORD', 'cof')
    password = st.text_input("Enter password:", type="password")
    if password:
        if password.lower() == allowed_password.lower():
            st.session_state.authenticated = True
            st.session_state.failed_attempts = 0  # Reset counter on successful login
            st.rerun()
        else:
            st.session_state.failed_attempts += 1
            remaining_attempts = 10 - st.session_state.failed_attempts
            st.error(f"Incorrect password. {remaining_attempts} attempts remaining.")
    st.stop()

# Define avatar URLs for visual distinction
AVATAR_URLS = {
    "orchestrator": "💻",
    "altman": "https://artthat.net/wp-content/uploads/2023/02/Sam-Altman-770x764.jpg",
    "bezos": "https://wallpapers.com/images/hd/jeff-bezos-smiling-bdb8zimqljhfcpu3.jpg",
    "bissett": "https://media.captivate.fm/profile_picture/acbd3592-dee0-493c-82d2-795fbd480c73/9e3c1088-889f-435f-b818-2bb6775b7206/AEIx07bdZj_YEQ-IEAk1BGZ6.png",
    "buffett": "http://personajeshistoricos.com/wp-content/uploads/2018/05/warren-buffett-01.jpg",
    "hormozi": "https://static.wikia.nocookie.net/youtube/images/a/ab/AlexHormozi.jpg/revision/latest?cb=20230626140726",
    "huang": "https://inteligenciafinanceira.com.br/wp-content/uploads/2024/02/jensen-huang-nvidia.jpg?w=904",
    "melancon": "https://www.cpa.com/sites/cpa/files/media/images/headshots/barry-melancon-2022.jpg",
    "musk": "https://m.media-amazon.com/images/M/MV5BOTk4M2ZlZDQtMjIxYS00ZDEyLWE3YjItZjc0ZDlmZTZiYzAxXkEyXkFqcGdeQXVyMDY3OTcyOQ@@._V1_FMjpg_UX1000_.jpg",
    "padar": "https://media.licdn.com/dms/image/v2/C4E34AQETb2dTws3ndw/ugc-proxy-shrink_1280_800/ugc-proxy-shrink_1280_800/0/1594145983209?e=2147483647&v=beta&t=ehMkL6_gkcNd4I8Cym772r7LPa8snmHJzkqjDhkuxAQ",
    "woods": "https://m.media-amazon.com/images/S/amzn-author-media-prod/13vfutkue49g0qtdeegdjm7jll._SY600_.jpg",
    "user": "👨‍💼"
}

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False
if "next_speaker" not in st.session_state:
    st.session_state.next_speaker = None
if "prompt_needed" not in st.session_state:
    st.session_state.prompt_needed = False
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "first_round_speakers" not in st.session_state:
    st.session_state.first_round_speakers = []
if "meeting_phase" not in st.session_state:
    st.session_state.meeting_phase = "setup"
if "last_speaker" not in st.session_state:
    st.session_state.last_speaker = None
if "speaker_counts" not in st.session_state:
    st.session_state.speaker_counts = {
        "orchestrator": 0,
        "altman": 0,
        "bezos": 0,
        "bissett": 0,
        "buffett": 0,
        "hormozi": 0,
        "huang": 0,
        "melancon": 0,
        "musk": 0,
        "padar": 0,
        "woods": 0,
        "user": 0
    }

# App header with logout button
col1, col2 = st.columns([6,1])
with col1:
    st.title("Board Meeting Simulation")
with col2:
    if st.button("Logout"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("Engage in a simulated board meeting with AI board members.")

# Sidebar for settings and information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This application simulates a board meeting with AI-powered board members.
    Each member has their own personality, expertise, and speaking style.
    
    The conversation is managed by an orchestrator and an evaluator that
    determines who should speak next.
    """)
    
    if st.button("Reset Conversation"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.header("Board Members")
    st.markdown("""
    - **Sam Altman**: AI, OpenAI leadership
    - **Jeff Bezos**: E-commerce, customer obsession
    - **Martin Bissett**: Accounting practice growth
    - **Warren Buffett**: Value investing, long-term strategy
    - **Alex Hormozi**: Business scaling, sales, marketing
    - **Jensen Huang**: GPUs, AI hardware, computing
    - **Barry Melancon**: Accounting profession, regulation
    - **Elon Musk**: Innovation, space, electric vehicles
    - **Jody Padar**: Modern accounting, tech adoption
    - **Geoff Woods**: AI leadership, organizational innovation
    """)

# Function to initialize agents
async def initialize_agents():
    if st.session_state.initialized:
        return
    
    # Load .env variables
    env_location = find_dotenv()
    load_dotenv(env_location)
    
    # Load vector ids
    vector_ids_raw = os.getenv('VECTOR_IDS')
    if not vector_ids_raw:
        st.error("VECTOR_IDS environment variable is not set")
        return
    
    # Parse the JSON array from the environment variable
    try:
        vector_ids = json.loads(vector_ids_raw)
    except json.JSONDecodeError:
        st.error("Failed to parse VECTOR_IDS as JSON")
        return
    
    # OpenAI API setup
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY environment variable is not set")
        return
    
    model = OpenAIResponsesModel(
        model="gpt-4o-mini",
        openai_client=AsyncOpenAI(api_key=OPENAI_API_KEY)
    )
    
    # Load agent instructions
    instructions = {}
    for agent_name in ["orchestrator", "altman", "bezos", "bissett", "buffett", 
                        "hormozi", "huang", "melancon", "musk", "padar", "woods", "evaluator"]:
        try:
            with open(f"agents/{agent_name}/{agent_name}_instructions.txt", 'r') as f:
                instructions[agent_name] = f.read()
        except FileNotFoundError:
            st.error(f"Could not find instructions file for {agent_name}")
            return
    
    # Create agents with instructions
    st.session_state.agents = {
        "altman": Agent(
            name='Altman', 
            model=model,
            instructions=instructions["altman"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[0]])]
        ),
        "bezos": Agent(
            name='Bezos', 
            model=model,
            instructions=instructions["bezos"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[1]])]
        ),
        "bissett": Agent(
            name='Bissett', 
            model=model,
            instructions=instructions["bissett"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[2]])]
        ),
        "buffett": Agent(
            name='Buffett', 
            model=model,
            instructions=instructions["buffett"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[3]])]
        ),
        "hormozi": Agent(
            name='Hormozi', 
            model=model,
            instructions=instructions["hormozi"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[4]])]
        ),
        "huang": Agent(
            name='Huang', 
            model=model,
            instructions=instructions["huang"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[5]])]
        ),
        "melancon": Agent(
            name='Melancon', 
            model=model,
            instructions=instructions["melancon"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[6]])]
        ),
        "musk": Agent(
            name='Musk', 
            model=model,
            instructions=instructions["musk"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[7]])]
        ),
        "padar": Agent(
            name='Padar', 
            model=model,
            instructions=instructions["padar"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[8]])]
        ),
        "woods": Agent(
            name='Woods', 
            model=model,
            instructions=instructions["woods"],
            tools=[FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[9]])]
        ),
        "orchestrator": Agent(
            name='Orchestrator',
            model=model,
            instructions=instructions["orchestrator"],
            tools=[]
        ),
        "evaluator": Agent(
            name='Evaluator',
            model='gpt-4o',
            instructions=instructions["evaluator"],
            tools=[]
        )
    }
    
    st.session_state.initialized = True

# Function to get next speaker from evaluator
async def get_next_speaker():
    if not st.session_state.initialized:
        await initialize_agents()
    
    try:
        result = await Runner.run(
            st.session_state.agents["evaluator"],
            input=st.session_state.conversation_history
        )
        
        if result and result.final_output:
            try:
                # Try to parse the JSON response
                evaluation = json.loads(result.final_output)
                next_speaker = evaluation.get("next_speaker", "orchestrator").lower()
                reasoning = evaluation.get("reasoning", "Default reasoning")
                
                # For debugging
                st.session_state.last_reasoning = reasoning
                
                return next_speaker, False  # False for prompt_needed (simplified)
            except json.JSONDecodeError:
                st.error("Failed to parse evaluator response as JSON")
                return "orchestrator", False
    except Exception as e:
        st.error(f"Error getting next speaker: {e}")
        return "orchestrator", False

# Function to get response from orchestrator
async def get_orchestrator_response(prompt=None):
    if not st.session_state.initialized:
        await initialize_agents()
    
    orchestrator = st.session_state.agents["orchestrator"]
    
    try:
        if prompt:
            result = await Runner.run(orchestrator, input=f"{prompt}: {st.session_state.conversation_history}")
        else:
            result = await Runner.run(orchestrator, input=st.session_state.conversation_history)
        
        return result.final_output if result else "I apologize, but I'm having trouble responding right now."
    except Exception as e:
        st.error(f"Error getting orchestrator response: {e}")
        return "I apologize, but I'm having trouble responding right now."

# Function to get response from a board member
async def get_board_member_response(member_name, recent_context=None):
    if not st.session_state.initialized:
        await initialize_agents()
    
    member_name = member_name.lower()
    if member_name not in st.session_state.agents:
        st.error(f"Unknown board member: {member_name}")
        return f"[Error: Unknown board member '{member_name}']"
    
    agent = st.session_state.agents[member_name]
    
    # Check if this is the first time the board member is speaking
    is_first_time = st.session_state.speaker_counts.get(member_name, 0) == 0
    
    try:
        if is_first_time:
            result = await Runner.run(
                agent, 
                input=f"Please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {st.session_state.conversation_history}"
            )
        else:
            if recent_context:
                result = await Runner.run(
                    agent, 
                    input=f"Respond to the recent messages in the context of the ongoing conversation: {recent_context}"
                )
            else:
                result = await Runner.run(agent, input=st.session_state.conversation_history)
        
        return result.final_output if result else "I apologize, but I'm having trouble responding right now."
    except Exception as e:
        st.error(f"Error getting response from {member_name}: {e}")
        return f"I apologize, but I'm having trouble responding right now."

# Function to check if the meeting phase changes based on orchestrator's response
def update_meeting_phase(response):
    if "first round" in response.lower() and st.session_state.meeting_phase == "setup":
        st.session_state.meeting_phase = "first_round"
        
        # Extract selected board members from the response (simplified version)
        board_members = ["altman", "bezos", "bissett", "buffett", "hormozi", 
                         "huang", "melancon", "musk", "padar", "woods"]
        st.session_state.first_round_speakers = [m for m in board_members if m in response.lower()]
    
    elif "main discussion" in response.lower() and st.session_state.meeting_phase == "first_round":
        st.session_state.meeting_phase = "main_discussion"
    
    elif "closing" in response.lower() and st.session_state.meeting_phase == "main_discussion":
        st.session_state.meeting_phase = "closing"

# Display the conversation history
for message in st.session_state.conversation_history:
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        st.chat_message("user", avatar=AVATAR_URLS["user"]).write(content)
    elif role == "assistant":
        # Extract the speaker name from the content format "From {name}: {message}"
        if "From " in content and ": " in content:
            name = content.split("From ")[1].split(": ")[0].lower()
            message_content = content.split(": ", 1)[1]
            
            # Use avatar if available, otherwise fallback to orchestrator
            avatar = AVATAR_URLS.get(name, AVATAR_URLS["orchestrator"])
            st.chat_message(name, avatar=avatar).write(message_content)
        else:
            # Fallback if format is unexpected
            st.chat_message("assistant", avatar=AVATAR_URLS["orchestrator"]).write(content)

# Chat input
user_input = st.chat_input("Enter your message..." if not st.session_state.waiting_for_response else "Waiting for response...", disabled=st.session_state.waiting_for_response)

# Process user input or continue conversation flow
async def process_conversation():
    # Initialize agents if not already done
    if not st.session_state.initialized:
        await initialize_agents()
    
    # If we received user input
    if user_input:
        st.session_state.waiting_for_response = True
        st.chat_message("user", avatar=AVATAR_URLS["user"]).write(user_input)
        st.session_state.conversation_history.append({"role": "user", "content": user_input})
        st.session_state.last_speaker = "user"
        st.session_state.speaker_counts["user"] += 1
        
        # Get next speaker after user input (usually orchestrator)
        next_speaker, prompt_needed = await get_next_speaker()
        st.session_state.next_speaker = next_speaker
        st.session_state.prompt_needed = prompt_needed
    
    # If we're waiting for a response and know who should speak next
    elif st.session_state.waiting_for_response and st.session_state.next_speaker:
        next_speaker = st.session_state.next_speaker
        prompt_needed = st.session_state.prompt_needed
        
        # Process response based on next speaker
        with st.spinner(f"{next_speaker.capitalize()} is responding..."):
            if next_speaker == "orchestrator":
                response = await get_orchestrator_response()
                st.chat_message("orchestrator", avatar=AVATAR_URLS["orchestrator"]).write(response)
                st.session_state.conversation_history.append({"role": "assistant", "content": f"From {next_speaker.capitalize()}: {response}"})
                st.session_state.last_speaker = "orchestrator"
                
                # Check for phase transitions or member selections
                update_meeting_phase(response)
                
            elif next_speaker != "user" and next_speaker in st.session_state.agents:
                # Get response from board member
                response = await get_board_member_response(next_speaker, 
                                                        [msg["content"] for msg in st.session_state.conversation_history[-3:]])
                st.chat_message(next_speaker, avatar=AVATAR_URLS.get(next_speaker, AVATAR_URLS["orchestrator"])).write(response)
                st.session_state.conversation_history.append({"role": "assistant", "content": f"From {next_speaker.capitalize()}: {response}"})
                st.session_state.last_speaker = next_speaker
                
                # If in first round, remove the speaker who just spoke
                if st.session_state.meeting_phase == "first_round":
                    if next_speaker in st.session_state.first_round_speakers:
                        st.session_state.first_round_speakers.remove(next_speaker)
            
            # If next speaker is user, we stop and wait for input
            elif next_speaker == "user":
                st.session_state.waiting_for_response = False
                st.rerun()  # Rerun to update the input field
        
    # If this is the first interaction, start with orchestrator
    elif not st.session_state.conversation_history:
        st.session_state.waiting_for_response = True
        
        # Start with a welcome message from orchestrator
        with st.spinner("Orchestrator is starting the meeting..."):
            response = await get_orchestrator_response("Welcome the user and introduce yourself as the meeting facilitator.")
            st.chat_message("orchestrator", avatar=AVATAR_URLS["orchestrator"]).write(response)
            st.session_state.conversation_history.append({"role": "assistant", "content": f"From Orchestrator: {response}"})
            st.session_state.last_speaker = "orchestrator"
            
            # Get next speaker (should be user)
            next_speaker, prompt_needed = await get_next_speaker()
            st.session_state.next_speaker = next_speaker
            st.session_state.prompt_needed = prompt_needed
            
            # If next speaker is user, enable input
            if next_speaker == "user":
                st.session_state.waiting_for_response = False

# Run the conversation process
if st.session_state.initialized or not st.session_state.conversation_history:
    asyncio.run(process_conversation())

# Display current state in the sidebar for debugging
with st.sidebar:
    st.divider()
    # Only show debug information in development
    if os.getenv('ENVIRONMENT', 'development').lower() == 'development':
        st.subheader("Debug Information")
        st.write(f"Meeting Phase: {st.session_state.meeting_phase}")
        st.write(f"Next Speaker: {st.session_state.next_speaker}")
        st.write(f"Last Speaker: {st.session_state.last_speaker}")
        st.write(f"First Round Speakers: {st.session_state.first_round_speakers}")
        if "last_reasoning" in st.session_state:
            st.write(f"Last Reasoning: {st.session_state.last_reasoning}") 