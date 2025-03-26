# AI Board Meeting

A Streamlit-based chat interface for simulating a board meeting with AI personalities.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   VECTOR_IDS=["vs_id1","vs_id2","vs_id3","vs_id4","vs_id5","vs_id6","vs_id7","vs_id8","vs_id9","vs_id10"]
   ```

## Running the Application

Run the Streamlit app:
```
streamlit run app.py
```

## Features

- Chat interface with AI-powered board members
- Orchestrator manages the conversation flow
- Board members respond to questions directed at them
- Knowledge retrieval from each member's specialized vector database
- Select different OpenAI models in the sidebar
- Reset conversation history with one click

## File Structure

- `app.py` - Streamlit application
- `main.py` - Core functionality (CLI version)
- `/agents` - Contains instructions for each agent personality
- `.env` - Environment variables (API keys, vector store IDs) 