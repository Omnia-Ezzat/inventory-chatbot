import asyncio
from graph import graph


async def chat():

    print("Inventory Chatbot Ready!")
    print("Type 'exit' to quit.\n")

    state = {
        "messages": [],
        "generated_sql": "",
        "query_results": [],
        "error_message": "",
        "retry_count": 0
    }

    while True:

        user_input = input("> ")
        # --- Chitchat handling ---
        if user_input.lower() in ["hi", "hello", "hey"]:
            print("Bot: Hello! How can I help you with the inventory?")
            continue

        if user_input.lower() in ["how are you", "how are you doing"]:
            print("Bot: I'm doing great! Ask me about your inventory.")
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        state["messages"].append({
            "role": "user",
            "content": user_input
        })

        state = await graph.ainvoke(state)

        response = state["messages"][-1]["content"]

        if isinstance(response, dict):
            print("\nBot:", response.get("natural_language_answer"))
        else:
            print("\nBot:", response)

        print()


if __name__ == "__main__":
    asyncio.run(chat())