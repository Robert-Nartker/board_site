#imports
import os, asyncio, datetime
from dotenv import find_dotenv, load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIResponsesModel

#load .env variables
env_location = find_dotenv()
load_dotenv(env_location)

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
    instructions= altman_instructions
)

bezos = Agent(
    name='Bezos', 
    model=model,
    instructions=bezos_instructions
)

bissett = Agent(
    name='Bissett', 
    model=model,
    instructions=bissett_instructions
)

buffett = Agent(
    name='Buffett', 
    model=model,
    instructions=buffett_instructions
)

hormozi = Agent(
    name='Hormozi', 
    model=model,
    instructions=hormozi_instructions
)

huang = Agent(
    name='Huang', 
    model=model,
    instructions=huang_instructions
)

melancon = Agent(
    name='Melancon', 
    model=model,
    instructions=melancon_instructions
)

musk = Agent(
    name='Musk', 
    model=model,
    instructions=musk_instructions
)

padar = Agent(
    name='Padar',   
    model=model,
    instructions=padar_instructions
)

woods = Agent(
    name='Woods', 
    model=model,
    instructions=woods_instructions
)

orchestrator = Agent(
    name='Orchestrator',
    model=model,
    instructions=orchestrator_instructions,
    handoffs=[altman, bezos, bissett, buffett, hormozi, huang, melancon, musk, padar, woods]
)

#main loop
if __name__ == '__main__':
    run = True
    while run:
        print(conversation_history)
        prompt = input('> ')
        if prompt.lower() == 'exit':
            run = False
            break
            
        # Add user message to conversation history
        conversation_history.append({"role": "user","content": prompt,})
        
        # Run the agent with updated instructions
        result = Runner.run_sync(orchestrator, input=conversation_history)
        
        # Add agent response to conversation history
        if result.final_output:
            conversation_history.append({"role": "assistant","content": result.final_output,})
            print(result.final_output)