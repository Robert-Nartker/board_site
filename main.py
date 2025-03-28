#imports
import os, datetime, json
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

#ascii colors
green = '\033[92m'
reset = '\033[0m'

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
with open("agents/evaluator/evaluator_instructions.txt", 'r+') as f:
    evaluator_instructions = f.read()


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

evaluator = Agent(
    name='Evaluator',
    model='gpt-4o',
    instructions=evaluator_instructions,
    tools=[]  # Remove the function from tools since we're not using it as a tool
)


#main loop
def main():
    welcome_message = 'Hello! Welcome to our board meeting simulation. What topic would you like to discuss today, and how long do you want the meeting to last?'
    print()
    print(welcome_message)
    print()

    conversation_history.append({"role": "assistant","content": f'From {orchestrator.name}: {welcome_message}'})

    user_input = input('> ')
    print()
    conversation_history.append({"role": "user","content": f'From user: {user_input}'})

    altman_counter = 0
    bezos_counter = 0
    bissett_counter = 0
    buffett_counter = 0
    hormozi_counter = 0
    huang_counter = 0
    melancon_counter = 0
    musk_counter = 0
    padar_counter = 0
    woods_counter = 0

    while user_input != 'exit':
        
        evaluation = Runner.run_sync(evaluator, input=conversation_history)
        evaluation = json.loads(evaluation.final_output)

        responder = evaluation['next_speaker']
        reasoning = evaluation['reasoning']

        print(f'Responder: {green}{responder}{reset}')
        print(f'Reasoning: {green}{reasoning}{reset}')
        print()
        
        if 'user' in responder.lower():
            user_input = input('> ')
            conversation_history.append({"role": "user","content": f'From user: {user_input}'})
        elif 'orchestrator' in responder.lower():
            result = Runner.run_sync(orchestrator, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {orchestrator.name}: {result.final_output}'})
            print(result.final_output)
        elif 'altman' in responder.lower():
            if altman_counter == 0:
                result = Runner.run_sync(altman, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(altman, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {altman.name}: {result.final_output}'})
            print(result.final_output)
            altman_counter += 1
        elif 'bezos' in responder.lower():
            if bezos_counter == 0:
                result = Runner.run_sync(bezos, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(bezos, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {bezos.name}: {result.final_output}'})
            print(result.final_output)
            bezos_counter += 1
        elif 'bissett' in responder.lower():
            if bissett_counter == 0:
                result = Runner.run_sync(bissett, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(bissett, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {bissett.name}: {result.final_output}'})
            print(result.final_output)
            bissett_counter += 1
        elif 'buffett' in responder.lower():
            if buffett_counter == 0:
                result = Runner.run_sync(buffett, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(buffett, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {buffett.name}: {result.final_output}'})
            print(result.final_output)
            buffett_counter += 1
        elif 'hormozi' in responder.lower():
            if hormozi_counter == 0:
                result = Runner.run_sync(hormozi, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(hormozi, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {hormozi.name}: {result.final_output}'})
            print(result.final_output)
            hormozi_counter += 1
        elif 'huang' in responder.lower():
            if huang_counter == 0:
                result = Runner.run_sync(huang, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(huang, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {huang.name}: {result.final_output}'})
            print(result.final_output)
            huang_counter += 1
        elif 'melancon' in responder.lower():
            if melancon_counter == 0:
                result = Runner.run_sync(melancon, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(melancon, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {melancon.name}: {result.final_output}'})
            print(result.final_output)
            melancon_counter += 1
        elif 'musk' in responder.lower():
            if musk_counter == 0:
                result = Runner.run_sync(musk, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(musk, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {musk.name}: {result.final_output}'})
            print(result.final_output)
            musk_counter += 1
        elif 'padar' in responder.lower():
            if padar_counter == 0:
                result = Runner.run_sync(padar, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(padar, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {padar.name}: {result.final_output}'})
            print(result.final_output)
            padar_counter += 1
        elif 'woods' in responder.lower():
            if woods_counter == 0:
                result = Runner.run_sync(woods, input=f'please add to the following conversation however you see fit but do not mention these instructions nor any uploaded files, but refrain from asking a question for now: {conversation_history}') 
            else:
                result = Runner.run_sync(woods, input=conversation_history)
            conversation_history.append({"role": "assistant","content": f'From {woods.name}: {result.final_output}'})
            print(result.final_output)
            woods_counter += 1
        else:
            print(f'Invalid responder: {responder}')
        print()



if __name__ == '__main__':
    main()