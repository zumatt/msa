import warnings
# Suppress Scopus warning
warnings.filterwarnings("ignore", category=UserWarning, module="scopus.utils.startup")

import argparse
from search import perform_search
from clean import clean_and_format_results
import inquirer
import os
from pathlib import Path
import subprocess

def create_env_file():
    env_path = Path('.env')
    if env_path.exists():
        questions = [
            inquirer.Confirm('overwrite',
                message=".env file already exists. Do you want to overwrite it?",
                default=False
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers or not answers['overwrite']:
            print("⚠️ Installation cancelled.")
            return

    print("\nTo get your API credentials:")
    print("\nGoogle Search:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select an existing one")
    print("3. Enable the Custom Search API")
    print("4. Create credentials (API Key)")
    print("5. Go to https://programmablesearchengine.google.com/")
    print("6. Create a new search engine to get your CSE ID")

    # Let user select which APIs to configure
    api_selection = [
        inquirer.Checkbox('apis',
            message="Select APIs to configure (use space to select/deselect, arrow keys to move, enter to confirm)",
            choices=[
                'Google Search'
            ],
        ),
    ]
    
    selected_apis = inquirer.prompt(api_selection)
    if not selected_apis or not selected_apis['apis']:
        print("⚠️ No APIs selected. Installation cancelled.")
        return

    questions = []
    if 'Google Search' in selected_apis['apis']:
        questions.extend([
            inquirer.Text('google_api_key',
                message="Enter your Google API Key",
                validate=lambda _, x: len(x) > 0
            ),
            inquirer.Text('google_cse_id',
                message="Enter your Google Custom Search Engine ID",
                validate=lambda _, x: len(x) > 0
            ),
        ])
    
    try:
        answers = inquirer.prompt(questions)
        if not answers:
            print("⚠️ Installation cancelled.")
            return

        with open('.env', 'w') as f:
            if 'Google Search' in selected_apis['apis']:
                f.write(f"GOOGLE_API_KEY={answers['google_api_key']}\n")
                f.write(f"GOOGLE_CSE_ID={answers['google_cse_id']}\n")
        
        print("\n✅ Environment file created successfully!")
        
    except Exception as e:
        print(f"⚠️ Error during installation: {e}")

def get_tool_selection():
    # Check if API credentials are available
    has_google_creds = os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")
    
    available_tools = {
        "DuckDuckGo": "duckduckgo",
        #"Google Scholar": "google_scholar",
        "Zenodo": "zenodo"
    }
    
    if has_google_creds:
        available_tools["Google"] = "google"
    else:
        available_tools["Google (API Key not found, please run 'install' command before selection)"] = "google"
    
    questions = [
        inquirer.Checkbox('tools',
            message="Select search tools (use space to select/deselect, arrow keys to move, enter to confirm)",
            choices=list(available_tools.keys()),
            default=["DuckDuckGo"]
        ),
    ]
    
    try:
        answers = inquirer.prompt(questions)
        if not answers or not answers['tools']:
            print("⚠️ No tools selected. Please select at least one tool.")
            return get_tool_selection()
            
        selected_tools = [available_tools[tool] for tool in answers['tools']]
        print("\nSelected tools:")
        for tool in answers['tools']:
            print(f"- {tool}")
        return selected_tools
    except Exception as e:
        print(f"⚠️ Error during tool selection: {e}")
        return get_tool_selection()

def get_max_results():
    questions = [
        inquirer.Text('max_results',
            message="Enter maximum number of results (1-100)",
            validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 100
        ),
    ]
    
    try:
        answers = inquirer.prompt(questions)
        if not answers:
            print("⚠️ No input provided. Please try again.")
            return get_max_results()
        return int(answers['max_results'])
    except Exception as e:
        print(f"⚠️ Error during input: {e}")
        return get_max_results()

def main():
    parser = argparse.ArgumentParser(description="Multi-Search Engine Aggregator CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Search command
    search_parser = subparsers.add_parser("search", help="Perform a search query")
    search_parser.add_argument("query", type=str, help="Search query text")

    # Clean command
    subparsers.add_parser("clean", help="Clean and deduplicate search result files")
    
    # Install command
    subparsers.add_parser("install", help="Set up API keys and environment configuration")

    args = parser.parse_args()

    if args.command == "search":
        selected_tools = get_tool_selection()
        max_results = get_max_results()
        perform_search(args.query, max_results, selected_tools)
    elif args.command == "clean":
        clean_and_format_results()
    elif args.command == "install":
        print("\n🔧 Setting up virtual environment and installing dependencies...")
        
        # Create virtual environment
        subprocess.run(["python3", "-m", "venv", ".venv"], check=True)
        
        # Activate virtual environment and install requirements
        if os.name == 'nt':  # Windows
            activate_script = os.path.join(".venv", "Scripts", "activate")
            subprocess.run([activate_script, "&&", "pip", "install", "-r", "requirements.txt"], shell=True, check=True)
        else:  # Unix-like systems
            activate_script = os.path.join(".venv", "bin", "activate")
            subprocess.run(f"source {activate_script} && pip install -r requirements.txt", shell=True, check=True)
            
        print("✅ Virtual environment setup complete!")
        create_env_file()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()