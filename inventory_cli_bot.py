import asyncio
import time
import json
import os
from graph import graph

# Simple colors for terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def chat():
    # Enable ANSI colors on Windows
    if os.name == 'nt':
        os.system('color')

    print(f"\n{Colors.HEADER}{Colors.BOLD}==========================================")
    print("      Inventory Chatbot (CLI Mode)        ")
    print(f"=========================================={Colors.ENDC}")
    print("Type 'exit' or 'quit' to stop.\n")

    state = {
        "messages": [],
        "generated_sql": "",
        "query_results": [],
        "error_message": "",
        "retry_count": 0
    }

    while True:
        try:
            user_input = input(f"{Colors.BOLD}You > {Colors.ENDC}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.OKBLUE}Bot: Goodbye!{Colors.ENDC}")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print(f"{Colors.OKBLUE}Bot: Goodbye!{Colors.ENDC}")
            break

        # --- Quick chitchat handling ---
        if user_input.lower() in ["hi", "hello", "hey"]:
            print(f"{Colors.OKGREEN}Bot: Hello! How can I help you with your inventory today?{Colors.ENDC}\n")
            continue

        state["messages"].append({
            "role": "user",
            "content": user_input
        })

        print(f"{Colors.OKCYAN}Thinking...{Colors.ENDC}", end="\r", flush=True)
        
        start_time = time.time()
        try:
            state = await graph.ainvoke(state)
            latency = (time.time() - start_time) * 1000
            
            # Clear "Thinking..."
            print(" " * 20, end="\r")

            # Extract final message content
            messages = state.get("messages", [])
            if not messages:
                print(f"{Colors.FAIL}Error: No response from agent.{Colors.ENDC}\n")
                continue

            last_message = messages[-1]
            content = last_message.get("content", "")
            sql_used = state.get("generated_sql", "N/A")

            # Handle response extraction
            if isinstance(content, dict):
                answer = content.get("natural_language_answer", str(content))
            else:
                try:
                    parsed = json.loads(content)
                    answer = parsed.get("natural_language_answer", content)
                except:
                    answer = content

            print(f"{Colors.OKGREEN}Bot: {answer}{Colors.ENDC}")
            
            # Show technical details
            print(f"{Colors.HEADER}--- Technical Details ---")
            print(f"SQL: {Colors.OKBLUE}{sql_used}{Colors.HEADER}")
            print(f"Latency: {Colors.OKBLUE}{latency:.2f}ms{Colors.ENDC}")
            print(f"{Colors.HEADER}------------------------{Colors.ENDC}\n")

        except Exception as e:
            # Clear "Thinking..."
            print(" " * 20, end="\r")
            print(f"{Colors.FAIL}Error: {str(e)}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        pass