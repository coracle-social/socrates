# Data Vending Machine
Data Vending Machine (DVM)
This project demonstrates a Retrieval-Augmented Generation (RAG) system that integrates Nostr event data with an LLM for querying and summarization. It leverages Chroma for vector storage and supports configurable LLM summarizers (e.g., OpenAI's GPT-4 or a custom/local model).

Project Structure
graphql
Copy
socrates/
├── README.md
├── requirements.txt
├── config.yaml
├── .gitignore
├── data/                  # Place your event data here (e.g., SQLite DB or CSV)
├── scripts/               
│   ├── embed_to_chroma.py # Script to embed events into Chroma
│   └── query_and_summarize.py  # Script to retrieve and summarize events
└── dvm/                   
    ├── __init__.py
    ├── embed.py         # Core embedding logic
    ├── query.py         # Query logic for retrieving events
    ├── summarizer.py    # Abstract summarizer interface
    └── llm_wrappers/    
        ├── __init__.py
        ├── openai_summarizer.py  # GPT-4 (or similar) summarizer
        └── custom_llm_summarizer.py # Custom/local LLM summarizer
Setup
Clone the Repository:

bash
Copy
git clone https://your-repo-url.git
cd socrates
Create a Virtual Environment & Install Dependencies:

bash
Copy
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
Configuration:

Update config.yaml with your desired settings:
events_file: Path to your event data (default is data/default_events.db).
summarizer.type: Choose between openai or custom.
summarizer.openai_api_key: Insert your API key if using OpenAI.
Example config.yaml:
yaml
Copy
events_file: "data/default_events.db"

summarizer:
  type: "openai"   # options: "openai" or "custom"
  openai_api_key: "YOUR_OPENAI_API_KEY"
Usage
Embedding Events
Run the embedding script to process events and store embeddings in Chroma:

bash
Copy
python scripts/embed_to_chroma.py
Querying & Summarization
Query the system and get a summary from the chosen LLM:

bash
Copy
python scripts/query_and_summarize.py --query "Your query here"
Optional flags:

--events-file: Specify an alternative events file.
--summarizer: Override the summarizer type.
--debug: Enable verbose logging.
Future Improvements
Enhance error handling and logging.
Provide a mini-dataset for mentor testing.
Expand the summarizer interface for more LLM options.
