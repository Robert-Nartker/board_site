# Board Meeting Simulator

An AI-powered board meeting simulator that uses the OpenAI Agents SDK to create interactive discussions between AI board members with different expertise.

## Features

- **Expert Board Members**: Access to AI agents representing business leaders like Sam Altman, Jeff Bezos, Elon Musk, and more
- **Interactive Discussions**: Board members respond to questions and interact with each other
- **Topic Analysis**: AI orchestrator analyzes discussion topics and brings in relevant experts
- **User Participation**: Users can join the discussion and guide the meeting
- **Clearly Labeled Responses**: Each board member's response is clearly labeled with their name

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Make sure you have the required agent instruction files in the following structure:
   ```
   agents/
     orchestrator/
       orchestrator_instructions.txt
     altman/
       altman_instructions.txt
     bezos/
       bezos_instructions.txt
     ...
   ```

## Running the Application

Start the Streamlit app:

```
streamlit run app.py
```

Then open your browser to the URL provided by Streamlit (typically http://localhost:8501).

## Usage

1. Type a business topic in the chat input
2. The AI orchestrator will analyze the topic and select relevant board members
3. Board members will contribute their expertise to the discussion, with each response clearly labeled with their name
4. You can ask follow-up questions or redirect the conversation

## Technical Implementation

This application uses:
- OpenAI Agents SDK for AI orchestration
- Individual function tools for each board member
- Automatic name labeling of responses
- Streamlit for the web interface
- Async processing for efficient LLM calls

### Implementation Details

Each board member is implemented as a separate function tool:
- `get_altman_response`: Gets responses from Sam Altman
- `get_bezos_response`: Gets responses from Jeff Bezos
- `get_musk_response`: Gets responses from Elon Musk
- etc.

When the orchestrator calls one of these tools:
1. The tool sends the question to the appropriate board member agent
2. The agent generates a response based on its instructions and expertise
3. The response is automatically prefixed with the board member's name (e.g., "Elon Musk: [response]")
4. This ensures you can track which board member is actually responding

## Requirements

- Python 3.9+
- OpenAI API key with access to GPT-4o-mini or compatible models 