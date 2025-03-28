# imports needed globally or for auth
import os
import streamlit as st
import json # Needed for vector ID parsing early

# --- Page Configuration (MUST be the first st command) ---
st.set_page_config(
    page_title="Board Meeting Simulation",
    initial_sidebar_state="collapsed"
)

# --- Password Authentication State Initialization ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
if "password_guesses" not in st.session_state:
    st.session_state.password_guesses = 0
MAX_PASSWORD_GUESSES = 10
# CORRECT_PASSWORD will be loaded from env inside the login block if needed

# --- Password Entry Logic ---
# Only show login form if password is not correct
if not st.session_state.password_correct:

    # Check if locked out first on rerun
    if st.session_state.password_guesses >= MAX_PASSWORD_GUESSES:
        st.error("🚨 Too many incorrect password attempts. Access denied.")
        st.stop() # Halt script execution for this session

    # --- Load and Validate APP_PASSWORD ---
    # Load the password from environment variable *here* when needed for login
    CORRECT_PASSWORD = st.secrets['APP_PASSWORD']
    if not CORRECT_PASSWORD:
        st.error("🚨 Critical Error: The `APP_PASSWORD` environment variable is not set in the `.env` file or system environment. Authentication cannot proceed.")
        st.stop()
    # ------------------------------------

    # Display login form
    st.title("Login Required")
    st.warning("🔒 This application requires a password to protect API usage.")
    st.caption("Note: Password check uses the `APP_PASSWORD` environment variable.") # Updated caption

    with st.form("password_form"):
        password_attempt = st.text_input("Enter Password:", type="password", key="password_widget")
        submitted = st.form_submit_button("Login")

        if submitted:
            # Compare with the password loaded from environment
            if password_attempt == CORRECT_PASSWORD:
                st.session_state.password_correct = True
                st.session_state.password_guesses = 0 # Reset guess count on success
                st.success("Login successful! Loading application...") # Optional feedback
                # Rerun needed to get past the `if not st.session_state.password_correct` block
                st.rerun()
            else:
                st.session_state.password_guesses += 1
                remaining_guesses = MAX_PASSWORD_GUESSES - st.session_state.password_guesses
                if remaining_guesses > 0:
                    st.error(f"Incorrect password. {remaining_guesses} attempts remaining.")
                else:
                    st.error("Incorrect password. No attempts remaining. Access denied.")
                    # Lockout message will appear more permanently on the next rerun due to the check at the top

    # Stop execution here if password is not correct, preventing main app code below from running
    st.stop()


# --- Main Application Code (Runs only if password_correct is True) ---
# ---------------------------------------------------------------------
else:
    # Imports needed only for the main application logic
    import datetime
    import asyncio
    import threading
    from agents import Agent, Runner, OpenAIResponsesModel, FileSearchTool, AsyncOpenAI
    import streamlit.components.v1 as components
    import traceback
    import nest_asyncio # Needs to be applied again inside this block if not global

    # --- Apply nest_asyncio patch ---
    # Needs to be applied within this scope if run conditionally
    nest_asyncio.apply()
    # ---------------------------------

    # --- Setup --- (Load env vars needed by main app)
    # Env vars like OPENAI_API_KEY were loaded globally but re-get if needed or preferred
    OPENAI_API_KEY = st.secrets['OPENAI_API_KEY']
    VECTOR_IDS_RAW = st.secrets['VECTOR_IDS'] # Re-get or assume available

    if not OPENAI_API_KEY:
        st.error("OpenAI API Key not found after login. Please check environment configuration.")
        st.stop()
    if not VECTOR_IDS_RAW:
        st.error("Vector IDs not found after login. Please check environment configuration.")
        st.stop()
    try:
        vector_ids = json.loads(VECTOR_IDS_RAW)
        if not isinstance(vector_ids, list) or len(vector_ids) < 10:
            raise ValueError("VECTOR_IDS must be a JSON array with at least 10 IDs.")
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Invalid VECTOR_IDS format after login: {e}")
        st.stop()

    # --- Avatar Definitions ---
    AVATAR_URLS = {
        "Orchestrator": "💻",
        "Altman": "https://artthat.net/wp-content/uploads/2023/02/Sam-Altman-770x764.jpg",
        "Bezos": "https://wallpapers.com/images/hd/jeff-bezos-smiling-bdb8zimqljhfcpu3.jpg",
        "Bissett": "https://media.captivate.fm/profile_picture/acbd3592-dee0-493c-82d2-795fbd480c73/9e3c1088-889f-435f-b818-2bb6775b7206/AEIx07bdZj_YEQ-IEAk1BGZ6.png",
        "Buffett": "http://personajeshistoricos.com/wp-content/uploads/2018/05/warren-buffett-01.jpg",
        "Hormozi": "https://static.wikia.nocookie.net/youtube/images/a/ab/AlexHormozi.jpg/revision/latest?cb=20230626140726",
        "Huang": "https://inteligenciafinanceira.com.br/wp-content/uploads/2024/02/jensen-huang-nvidia.jpg?w=904",
        "Melancon": "https://www.cpa.com/sites/cpa/files/media/images/headshots/barry-melancon-2022.jpg",
        "Musk": "https://m.media-amazon.com/images/M/MV5BOTk4M2ZlZDQtMjIxYS00ZDEyLWE3YjItZjc0ZDlmZTZiYzAxXkEyXkFqcGdeQXVyMDY3OTcyOQ@@._V1_FMjpg_UX1000_.jpg",
        "Padar": "https://media.licdn.com/dms/image/v2/C4E34AQETb2dTws3ndw/ugc-proxy-shrink_1280_800/ugc-proxy-shrink_1280_800/0/1594145983209?e=2147483647&v=beta&t=ehMkL6_gkcNd4I8Cym772r7LPa8snmHJzkqjDhkuxAQ",
        "Woods": "https://m.media-amazon.com/images/S/amzn-author-media-prod/13vfutkue49g0qtdeegdjm7jll._SY600_.jpg",
        "user": "👨‍💼"
    }

    # --- Model and Tools Setup ---
    @st.cache_resource
    def get_openai_model(api_key):
        print("Initializing OpenAI Model...")
        return OpenAIResponsesModel(model="gpt-4o-mini", openai_client=AsyncOpenAI(api_key=api_key))
    model = get_openai_model(OPENAI_API_KEY)

    # --- Agent Instructions Loading ---
    @st.cache_data
    def load_instructions():
        print("Loading Agent Instructions...")
        instructions = {}
        try:
            instructions['orchestrator'] = open("agents/orchestrator/orchestrator_instructions.txt", 'r').read()
            instructions['altman'] = open("agents/altman/altman_instructions.txt", 'r').read()
            instructions['bezos'] = open("agents/bezos/bezos_instructions.txt", 'r').read()
            instructions['bissett'] = open("agents/bissett/bissett_instructions.txt", 'r').read()
            instructions['buffett'] = open("agents/buffett/buffett_instructions.txt", 'r').read()
            instructions['hormozi'] = open("agents/hormozi/hormozi_instructions.txt", 'r').read()
            instructions['huang'] = open("agents/huang/huang_instructions.txt", 'r').read()
            instructions['melancon'] = open("agents/melancon/melancon_instructions.txt", 'r').read()
            instructions['musk'] = open("agents/musk/musk_instructions.txt", 'r').read()
            instructions['padar'] = open("agents/padar/padar_instructions.txt", 'r').read()
            instructions['woods'] = open("agents/woods/woods_instructions.txt", 'r').read()
            instructions['evaluator'] = open("agents/evaluator/evaluator_instructions.txt", 'r').read()
            return instructions
        except FileNotFoundError as e:
            st.error(f"Failed to load instruction file: {e}. Make sure all instruction files are present relative to the script.")
            raise e
    try:
        all_instructions = load_instructions()
    except FileNotFoundError:
        st.stop()

    # --- Agent Creation ---
    @st.cache_resource
    def create_agent(name, instructions, tools, _model, agent_model_name="gpt-4o-mini"):
        print(f"Creating Agent: {name}...")
        return Agent(
            name=name,
            model=_model if name != 'Evaluator' else agent_model_name,
            instructions=instructions,
            tools=tools
        )

    agent_tools = {
        'Altman': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[0]])],
        'Bezos': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[1]])],
        'Bissett': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[2]])],
        'Buffett': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[3]])],
        'Hormozi': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[4]])],
        'Huang': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[5]])],
        'Melancon': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[6]])],
        'Musk': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[7]])],
        'Padar': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[8]])],
        'Woods': [FileSearchTool(max_num_results=2, vector_store_ids=[vector_ids[9]])],
        'Orchestrator': [],
        'Evaluator': [],
    }

    # Create agents using the cached function
    altman = create_agent('Altman', all_instructions['altman'], agent_tools['Altman'], model)
    bezos = create_agent('Bezos', all_instructions['bezos'], agent_tools['Bezos'], model)
    bissett = create_agent('Bissett', all_instructions['bissett'], agent_tools['Bissett'], model)
    buffett = create_agent('Buffett', all_instructions['buffett'], agent_tools['Buffett'], model)
    hormozi = create_agent('Hormozi', all_instructions['hormozi'], agent_tools['Hormozi'], model)
    huang = create_agent('Huang', all_instructions['huang'], agent_tools['Huang'], model)
    melancon = create_agent('Melancon', all_instructions['melancon'], agent_tools['Melancon'], model)
    musk = create_agent('Musk', all_instructions['musk'], agent_tools['Musk'], model)
    padar = create_agent('Padar', all_instructions['padar'], agent_tools['Padar'], model)
    woods = create_agent('Woods', all_instructions['woods'], agent_tools['Woods'], model)
    orchestrator = create_agent('Orchestrator', all_instructions['orchestrator'], agent_tools['Orchestrator'], model)
    evaluator = create_agent('Evaluator', all_instructions['evaluator'], agent_tools['Evaluator'], model, agent_model_name="gpt-4o")

    # Agent mapping for logic (using lowercase keys)
    agents_logic_map = {
        "altman": altman,
        "bezos": bezos,
        "bissett": bissett,
        "buffett": buffett,
        "hormozi": hormozi,
        "huang": huang,
        "melancon": melancon,
        "musk": musk,
        "padar": padar,
        "woods": woods,
        "orchestrator": orchestrator,
    }

    # --- CSS Injection for Highlighting ---
    highlight_css = """
    <style>
        @keyframes pulse {
            0% { box-shadow: 0 0 8px rgba(0, 123, 255, 0.4); }
            50% { box-shadow: 0 0 14px rgba(0, 123, 255, 0.8); }
            100% { box-shadow: 0 0 8px rgba(0, 123, 255, 0.4); }
        }

        body.app-waiting-user [data-testid="stChatInput"] div[data-baseweb="input"] > div:first-child {
            border: 2px solid #007bff;
            border-radius: 0.5rem; /* Match Streamlit's default border-radius */
            animation: pulse 1.5s infinite ease-in-out;
            transition: border 0.3s ease, box-shadow 0.3s ease;
        }
        body.app-waiting-user [data-testid="stChatInput"] textarea::placeholder {
            color: #0056b3;
            font-weight: bold;
        }
    </style>
    """
    st.markdown(highlight_css, unsafe_allow_html=True)
    # --------------------------------------


    # --- Streamlit App Logic ---
    st.title("Board Meeting Simulation")

    # Initialize session state variables for the app itself (if not already done globally)
    # These should persist across reruns within the authenticated session
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "agent_counters" not in st.session_state:
        # Initialize counters using lowercase keys consistent with agents_logic_map
        st.session_state.agent_counters = {name.lower(): 0 for name in AVATAR_URLS if name != 'user'}
    if "app_state" not in st.session_state:
        # States: INITIAL, RUNNING, WAITING_USER
        st.session_state.app_state = "INITIAL"

    # --- JS Injection for Body Class Toggle ---
    # Determine if highlighting should be active *before* rendering the component
    highlight_active = st.session_state.app_state == "WAITING_USER"

    # Pass the Python state to the JS inside the HTML component
    js_code = f"""
    <script>
        // Function to update body class
        function updateBodyClass(highlight) {{
            const body = window.parent.document.body; // Target body of the main Streamlit app window
            const className = "app-waiting-user";

            if (highlight) {{
                if (!body.classList.contains(className)) {{ // Add only if not present
                     body.classList.add(className);
                }}
            }} else {{
                if (body.classList.contains(className)) {{ // Remove only if present
                     body.classList.remove(className);
                }}
            }}
        }}
        // Call the function with the current state
        updateBodyClass({str(highlight_active).lower()});
    </script>
    """
    # Render the component to execute the JS (make it invisible)
    components.html(js_code, height=0, width=0)
    # ------------------------------------------


    # --- Display Chat History ---
    # This runs on *every* rerun to show the current state of the chat
    for message in st.session_state.conversation_history:
        role = message.get("role")
        content = message.get("content", "")

        avatar_icon = None
        display_name = "Assistant" # Default display name
        display_content = content

        if role == "user":
            display_name = "user" # Keep internal name 'user' for display consistency if needed
            avatar_icon = AVATAR_URLS.get("user", "👤") # Default user icon
            if content.startswith("From user:"):
                 display_content = content.replace("From user:", "", 1).strip()

        elif role == "assistant":
            parts = content.split(":", 1)
            if len(parts) == 2 and parts[0].startswith("From "):
                agent_name_from_msg = parts[0].replace("From ", "").strip()
                # Use the extracted agent name for display and avatar lookup
                display_name = agent_name_from_msg
                avatar_icon = AVATAR_URLS.get(agent_name_from_msg, "🤖") # Use name from message, default robot
                display_content = parts[1].strip()
            else:
                # Fallback if format doesn't match
                avatar_icon = AVATAR_URLS.get("Orchestrator", "💻") # Default to orchestrator/computer if unknown assistant
                display_name = "Assistant"

        # Use the determined name and avatar for the chat message
        with st.chat_message(display_name, avatar=avatar_icon):
            st.write(display_content)


    # --- Initial Welcome Message ---
    if st.session_state.app_state == "INITIAL":
        welcome_message = 'Hello! Welcome to our board meeting simulation. What topic would you like to discuss today, and how long do you want the meeting to last?'
        # Add to history only if it's not already there
        if not st.session_state.conversation_history:
            # Ensure the message format includes the name matching the AVATAR_URLS key
            st.session_state.conversation_history.append({"role": "assistant", "content": f'From {orchestrator.name}: {welcome_message}'})
            st.rerun() # Rerun to display the welcome message from history & change state
        else:
            # If history exists but state is INITIAL, move to waiting (e.g., after a restart/clear)
            st.session_state.app_state = "WAITING_USER"
            st.rerun() # Rerun to ensure correct state processing below


    # --- Main Interaction Logic ---

    # --- Chat Input Box ---
    # This is where the CSS highlight will apply when body has class 'app-waiting-user'
    user_prompt = st.chat_input(
        "Send a message...", # Placeholder text
        disabled=(st.session_state.app_state == "RUNNING"),
        key="chat_input_main"
    )

    # --- Process User Input and Run Agent Turns ---
    if user_prompt and st.session_state.app_state != "INITIAL":
        # Set state to RUNNING to disable input temporarily
        st.session_state.app_state = "RUNNING"

        # 1. Add user message to history and display it immediately
        user_message_content = f'From user: {user_prompt}' # Keep internal format consistent
        st.session_state.conversation_history.append({"role": "user", "content": user_message_content})
        # Display user message immediately using the avatar logic
        with st.chat_message("user", avatar=AVATAR_URLS.get("user", "👤")):
            st.write(user_prompt)

        # 2. Loop through agent turns until 'user' is next or error
        MAX_TURNS_PER_INPUT = 15 # Safety break
        turns = 0
        next_speaker = None

        while turns < MAX_TURNS_PER_INPUT:
            turns += 1
            current_turn_speaker = "Unknown" # For error reporting

            # Spinner provides visual feedback during processing
            with st.spinner(f"Thinking..."):
                try:
                    # A. Run Evaluator
                    eval_input = st.session_state.conversation_history
                    # Ensure Runner.run_sync exists and works with nest_asyncio
                    evaluation_result = Runner.run_sync(evaluator, input=eval_input)
                    evaluation_data = json.loads(evaluation_result.final_output)

                    next_speaker_raw = evaluation_data.get('next_speaker', '')
                    next_speaker_logic_key = next_speaker_raw.lower() # Key for logic map
                    reasoning = evaluation_data.get('reasoning', 'No reasoning provided.')
                    current_turn_speaker = f"Evaluator (deciding: {next_speaker_raw})"

                    # B. Check if user's turn
                    if 'user' in next_speaker_logic_key:
                        st.session_state.app_state = "WAITING_USER"
                        # The highlight will be applied automatically on the next rerun via CSS/JS
                        break # Exit the agent turn loop

                    # C. Select and run the designated agent using the logic map
                    selected_agent = agents_logic_map.get(next_speaker_logic_key)

                    if selected_agent:
                        agent_name = selected_agent.name # Get the canonical name (e.g., 'Altman') for display/avatar
                        current_turn_speaker = agent_name
                        agent_input = st.session_state.conversation_history
                        # Use logic key (lowercase) for counters
                        counter = st.session_state.agent_counters.get(next_speaker_logic_key, 0)

                        # Apply special first-turn instruction
                        if counter == 0 and next_speaker_logic_key != 'orchestrator':
                             agent_input = f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {st.session_state.conversation_history}'

                        # Run the agent
                        agent_result = Runner.run_sync(selected_agent, input=agent_input)
                        agent_output = agent_result.final_output

                        # Use the correct agent_name (capitalized) for the message content and avatar lookup
                        message_content = f'From {agent_name}: {agent_output}'
                        st.session_state.conversation_history.append({"role": "assistant", "content": message_content})

                        # Display agent message using avatar logic
                        agent_avatar = AVATAR_URLS.get(agent_name, "🤖")
                        with st.chat_message(agent_name, avatar=agent_avatar):
                            st.write(agent_output)

                        # Increment counter using logic key
                        st.session_state.agent_counters[next_speaker_logic_key] = counter + 1

                    elif next_speaker_logic_key == 'evaluator':
                        st.warning(f"Evaluator designated itself ('{next_speaker_raw}') to speak. Skipping this turn.")
                        continue # Go to the next iteration of the while loop

                    else:
                        st.error(f"Invalid responder designated by evaluator: '{next_speaker_raw}'")
                        st.session_state.app_state = "WAITING_USER"
                        break # Exit loop on error


                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse JSON output from {current_turn_speaker}: {e}")
                    try:
                        # Try to display the raw output that caused the error
                        st.error(f"Raw output was: ```\n{evaluation_result.final_output}\n```")
                    except NameError: # If evaluation_result wasn't assigned yet
                         st.error("Error occurred before evaluator output was received.")
                    st.session_state.app_state = "WAITING_USER"
                    break
                except Exception as e:
                    st.error(f"An error occurred during processing by {current_turn_speaker}: {e}")
                    st.exception(traceback.format_exc()) # Show full traceback in Streamlit
                    st.session_state.app_state = "WAITING_USER"
                    break # Exit loop on error

        # After the loop (natural end or break)
        if turns >= MAX_TURNS_PER_INPUT:
            st.warning("Maximum number of agent turns reached for this input cycle. Please provide further input.")
            # Ensure state allows input
            st.session_state.app_state = "WAITING_USER"

        # If loop finished or broke because user is next, ensure state is WAITING_USER
        # If loop finished without error/user turn after agent spoke, switch state
        if st.session_state.app_state == "RUNNING":
             st.session_state.app_state = "WAITING_USER"

        # Trigger a final rerun after processing is complete to update input state, JS body class etc.
        st.rerun()

    # If no user prompt was submitted on this run, and we are not in INITIAL state
    elif st.session_state.app_state != "INITIAL":
        # Ensure state is correctly set to WAITING_USER if it somehow wasn't already
        # This ensures the highlight appears if the app was left idle in a non-waiting state
        if st.session_state.app_state != "WAITING_USER":
             st.session_state.app_state = "WAITING_USER"
             st.rerun() # Rerun if state was corrected to ensure JS updates body class
        # The chat history is displayed at the top.
        # The st.chat_input widget is waiting at the bottom (and should be enabled/highlighted now).


    # --- Sidebar Content ---
    with st.sidebar:
        st.header("App Options")
        if st.button("Clear Chat History and Restart"):
            # Clear relevant session state keys for app logic reset
            keys_to_clear = ["conversation_history", "agent_counters", "app_state"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            # Keep password status intact unless logout is explicitly chosen
            # Also clear cached resources/data if you want a full reset of agents/instructions
            # st.cache_resource.clear() # Clears all resource caches
            # st.cache_data.clear()    # Clears all data caches
            st.success("Chat history cleared. Reloading app content...")
            st.rerun() # Rerun to re-initialize the app state (will show welcome message)
        st.markdown("---")
        # Add logout button
        if st.button("Logout"):
             st.session_state.password_correct = False
             st.session_state.password_guesses = 0 # Reset guesses
             # Clear other session state upon logout for a clean slate
             keys_to_clear = ["conversation_history", "agent_counters", "app_state"]
             for key in keys_to_clear:
                 if key in st.session_state:
                     del st.session_state[key]
             st.success("Logged out successfully.")
             st.rerun() # Rerun to go back to login screen
        st.markdown("---")
        st.caption("Board Meeting Simulation App")
