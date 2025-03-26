#imports
import os, datetime, json, asyncio
from dotenv import find_dotenv, load_dotenv
from agents import Agent, Runner, OpenAIResponsesModel, FileSearchTool, AsyncOpenAI

#load .env variables
env_location = find_dotenv()
load_dotenv(env_location)

#load vector ids
vector_ids_raw = os.getenv('VECTOR_IDS')
if not vector_ids_raw:
    raise ValueError("VECTOR_IDS environment variable is not set")

# Parse the JSON array from the environment variable
vector_ids = json.loads(vector_ids_raw)

#api
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

model = OpenAIResponsesModel(
    model = "gpt-4o-mini",
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
)

conversation_history = []


#define agent instructions
with open("agents/orchestrator/orchestrator_instructions.txt", 'r+') as f:
    orchestrator_instructions = f.read()
with open("agents/altman/altman_instructions.txt", 'r+') as f:
    altman_instructions = f.read()
with open("agents/bezos/bezos_instructions.txt", 'r+') as f:
    bezos_instructions = f.read()
with open("agents/bissett/bissett_instructions.txt", 'r+') as f:
    bissett_instructions = f.read()
with open("agents/buffett/buffett_instructions.txt", 'r+') as f:
    buffett_instructions = f.read()
with open("agents/hormozi/hormozi_instructions.txt", 'r+') as f:
    hormozi_instructions = f.read()
with open("agents/huang/huang_instructions.txt", 'r+') as f:
    huang_instructions = f.read()
with open("agents/melancon/melancon_instructions.txt", 'r+') as f:
    melancon_instructions = f.read()
with open("agents/musk/musk_instructions.txt", 'r+') as f:
    musk_instructions = f.read()
with open("agents/padar/padar_instructions.txt", 'r+') as f:
    padar_instructions = f.read()
with open("agents/woods/woods_instructions.txt", 'r+') as f:
    woods_instructions = f.read()


#create agents with instructions
altman = Agent(
    name='Altman', 
    model=model,
    instructions= altman_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[0]]
        )
    ]
)

bezos = Agent(
    name='Bezos', 
    model=model,
    instructions=bezos_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[1]]
        )
    ]
)

bissett = Agent(
    name='Bissett', 
    model=model,
    instructions=bissett_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[2]]
        )
    ]
)

buffett = Agent(
    name='Buffett', 
    model=model,
    instructions=buffett_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[3]]
        )
    ]
)

hormozi = Agent(
    name='Hormozi', 
    model=model,
    instructions=hormozi_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[4]]
        )
    ]
)

huang = Agent(
    name='Huang', 
    model=model,
    instructions=huang_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[5]]
        )
    ]
)

melancon = Agent(
    name='Melancon', 
    model=model,
    instructions=melancon_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[6]]
        )
    ]
)

musk = Agent(
    name='Musk', 
    model=model,
    instructions=musk_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[7]]
        )
    ]
)

padar = Agent(
    name='Padar',   
    model=model,
    instructions=padar_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[8]]
        )
    ]
)

woods = Agent(
    name='Woods', 
    model=model,
    instructions=woods_instructions,
    tools=[
        FileSearchTool(
            max_num_results=2,
            vector_store_ids=[vector_ids[9]]
        )
    ]
)


orchestrator = Agent(
    name='Orchestrator',
    model=model,
    instructions=orchestrator_instructions,
    tools=[]  # Remove the function from tools since we're not using it as a tool
)

async def eval_response_async(context: str) -> str:
    # print('Evaluating orchestrator response for board member queries')
    # """Check if orchestrator ended on a question for a boardmember, 
    # if so, run corresponding tool and get a response, then continue"""
    
    # Look for the last line containing a question mark
    lines = context.split('\n')
    last_question_line = None
    for line in reversed(lines):  # Search from the end of the message
        if '?' in line:
            last_question_line = line
            # print(f"Found question: {last_question_line}")
            break

    if not last_question_line:
        # print("No questions found in response")
        return ""
    
    # Map of member names to their agent objects
    agent_map = {
        'altman': altman,
        'bezos': bezos,
        'bissett': bissett,
        'buffett': buffett,
        'hormozi': hormozi,
        'huang': huang,
        'melancon': melancon,
        'musk': musk,
        'padar': padar,
        'woods': woods
    }
    
    # First names map
    first_name_map = {
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
    
    # Check for board member names
    for member_name in agent_map.keys():
        if member_name in last_question_line.lower():
            # print(f"Detected question for board member: {member_name}")
            s = f'Contribute to the following conversation by responding to the last question: {context}'
            agent_obj = agent_map[member_name]
            result = await Runner.run(agent_obj, input=s)
            return result.final_output
    
    # Check for first names
    for first_name, member_name in first_name_map.items():
        if first_name in last_question_line.lower():
            # print(f"Detected question for board member: {member_name} (by first name)")
            s = f'Contribute to the following conversation by responding to the last question: {context}'
            agent_obj = agent_map[member_name]
            result = await Runner.run(agent_obj, input=s)
            return result.final_output
    
    # print("No board member detected in question")
    return ""

test = False

#main loop
async def main():
    if test:
        print(await eval_response_async('altman, what is your opinion on the current state of the company?'))
        input("Press Enter to continue...")
    
    run = True
    while run:
        prompt = input('> ')
        if prompt.lower() == 'exit':
            run = False
            break
            
        # Add user message to conversation history
        conversation_history.append({"role": "user","content": prompt})
        
        # Run the orchestrator with conversation history
        # print("Running orchestrator...")
        result = await Runner.run(orchestrator, input=conversation_history)
        
        # Add orchestrator response to conversation history
        if result.final_output:
            conversation_history.append({"role": "assistant","content": result.final_output})
            print(f'Orchestrator: {result.final_output}')
            
            # Evaluate if a board member response is needed
            board_response = await eval_response_async(result.final_output)
            if board_response:
                print(f'Board Member Response: {board_response}')
                # Add the board member's response to the conversation history
                conversation_history.append({"role": "assistant", "content": board_response})

if __name__ == '__main__':
    asyncio.run(main())