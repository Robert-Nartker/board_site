# Board Meeting Simulator

An AI-powered board meeting simulator that uses the OpenAI Agents SDK to create interactive discussions between AI board members with different expertise.

## Features

- **Expert Board Members**: Access to AI agents representing business leaders like Sam Altman, Jeff Bezos, Elon Musk, and more
- **Interactive Discussions**: Board members respond to questions and interact with each other
- **Topic Analysis**: AI orchestrator analyzes discussion topics and brings in relevant experts
- **User Participation**: Users can join the discussion and guide the meeting

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
3. Board members will contribute their expertise to the discussion
4. You can ask follow-up questions or redirect the conversation

## Technical Implementation

This application uses:
- OpenAI Agents SDK for AI orchestration
- Function tools to get board member responses
- Streamlit for the web interface
- Async processing for efficient LLM calls

## Requirements

- Python 3.9+
- OpenAI API key with access to GPT-4o-mini or compatible models 