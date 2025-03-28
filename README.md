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
- Structured meeting flow with distinct phases:
  - **Setup Phase**: Define meeting topic and select relevant board members
  - **First Round**: Each selected member provides initial input
  - **Main Discussion**: Dynamic conversation with balanced participation
  - **Closing**: Summary and action items
- Intelligent conversation management via Evaluator agent
- Profile pictures for all participants
- Knowledge retrieval from each member's specialized vector database
- Meeting status sidebar showing current phase and selected members
- Select different OpenAI models in the sidebar
- Reset conversation with one click

## New Evaluator System

The application now features an Evaluator agent that intelligently manages turn-taking:

- Works behind the scenes to determine who should speak next
- Balances participation among board members
- Ensures topic-relevant experts are involved
- Maintains natural conversation flow
- Adapts to different meeting phases
- Uses assertions to validate responses

## File Structure

- `app.py` - Streamlit application
- `main.py` - Core functionality (CLI version)
- `/agents` - Contains instructions for each agent personality
  - `/orchestrator` - Meeting facilitator
  - `/evaluator` - Turn management system
  - `/[member_name]` - Individual board member agents
- `.env` - Environment variables (API keys, vector store IDs) 