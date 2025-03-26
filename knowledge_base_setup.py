import os, json
from io import BytesIO
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def create_vector_ids():
    board = ['altman', 'bezos', 'bissett', 'buffett', 'hormozi', 'huang', 'melancon', 'musk', 'padar', 'woods']
    ids = []
    for agent in board:
        agent_ids = []
        for file in os.listdir(os.path.join("agents/", f'{agent}/files')):
            with open(os.path.join("agents/", f'{agent}/files', file), 'rb') as f:
                result = client.files.create(
                    file=f,
                    purpose='assistants'
                )
                agent_ids.append(result.id)
        ids.append(agent_ids)

    vector_ids = []
    counter = -1
    for agent_ids in ids:
        counter += 1
        vector_store = client.vector_stores.create(
            name=f'{board[counter]} Store',
        )
        for file_id in agent_ids:
            client.vector_stores.files.create(
                vector_store_id=vector_store.id,
                file_id=file_id
            )
        vector_ids.append(vector_store.id)

    with open('vector_ids.json', 'w') as f:
        json.dump(vector_ids, f)

if __name__ == '__main__':
    create_vector_ids()
