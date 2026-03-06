from neo4j_agent import Neo4jAgent

def main():
    print("Knowledge Graph Chatbot Ready")
    print("Type 'exit' to quit.\n")
    
    agent = Neo4jAgent()
    
    try:
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                break
                
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            response = agent.process_request(user_input)
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\nGoodbye!")
    finally:
        agent.close()

if __name__ == "__main__":
    main()
