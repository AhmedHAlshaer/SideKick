"""
Memory Viewer - Inspect and manage your Sidekick's memories
Run this script to see what your Sidekick remembers!
"""

from app.memory_manager import MemoryManager
import json

def main():
    print("🧠 Sidekick Memory Viewer\n" + "="*50 + "\n")
    
    # Initialize memory manager
    mm = MemoryManager(persist_directory="./chroma_db")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. View all memories")
        print("2. Search for specific memories")
        print("3. Add a manual memory")
        print("4. Clear all memories (⚠️  dangerous!)")
        print("5. Get memory statistics")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            view_all_memories(mm)
        elif choice == "2":
            search_memories(mm)
        elif choice == "3":
            add_memory(mm)
        elif choice == "4":
            clear_memories(mm)
        elif choice == "5":
            show_stats(mm)
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


def view_all_memories(mm):
    """View all stored memories"""
    print("\n" + "="*50)
    print("📚 ALL MEMORIES")
    print("="*50)
    
    # Get all memories by searching with a very broad query
    memories = mm.recall_memories("", k=100)  # Get up to 100 memories
    
    if not memories:
        print("No memories stored yet!")
        return
    
    for i, memory in enumerate(memories, 1):
        print(f"\n{i}. {memory['content']}")
        print(f"   Type: {memory['metadata'].get('memory_type', 'unknown')}")
        print(f"   Time: {memory['metadata'].get('timestamp', 'unknown')}")
        if 'source' in memory['metadata']:
            print(f"   Source: {memory['metadata']['source']}")
    
    print(f"\n📊 Total: {len(memories)} memories")


def search_memories(mm):
    """Search for specific memories"""
    print("\n" + "="*50)
    print("🔍 SEARCH MEMORIES")
    print("="*50)
    
    query = input("\nWhat do you want to search for? ")
    k = input("How many results? (default 5): ").strip()
    k = int(k) if k else 5
    
    memories = mm.recall_memories(query, k=k)
    
    if not memories:
        print("\n❌ No relevant memories found.")
        return
    
    print(f"\n✅ Found {len(memories)} relevant memories:\n")
    for i, memory in enumerate(memories, 1):
        print(f"{i}. {memory['content']}")
        print(f"   Relevance Score: {memory['relevance_score']:.3f} (lower = more relevant)")
        print(f"   Type: {memory['metadata'].get('memory_type', 'unknown')}")
        print()


def add_memory(mm):
    """Manually add a memory"""
    print("\n" + "="*50)
    print("➕ ADD MEMORY")
    print("="*50)
    
    content = input("\nWhat should I remember? ")
    if not content.strip():
        print("❌ Memory cannot be empty.")
        return
    
    print("\nMemory types:")
    print("1. fact (general information)")
    print("2. preference (user preferences)")
    print("3. instruction (how to do things)")
    print("4. other")
    
    type_choice = input("Choose type (1-4, default 1): ").strip()
    type_map = {"1": "fact", "2": "preference", "3": "instruction", "4": "other"}
    memory_type = type_map.get(type_choice, "fact")
    
    mm.store_memory(content, memory_type=memory_type)
    print(f"\n✅ Memory stored successfully as '{memory_type}'!")


def clear_memories(mm):
    """Clear all memories"""
    print("\n⚠️  WARNING: This will delete ALL memories permanently!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm == "DELETE":
        mm.clear_all_memories()
        print("✅ All memories cleared.")
    else:
        print("❌ Cancelled.")


def show_stats(mm):
    """Show memory statistics"""
    print("\n" + "="*50)
    print("📊 MEMORY STATISTICS")
    print("="*50)
    
    # Get all memories
    all_memories = mm.recall_memories("", k=1000)
    
    if not all_memories:
        print("\nNo memories stored yet!")
        return
    
    # Count by type
    type_counts = {}
    for memory in all_memories:
        mem_type = memory['metadata'].get('memory_type', 'unknown')
        type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
    
    print(f"\n📈 Total Memories: {len(all_memories)}")
    print(f"\n📁 Breakdown by Type:")
    for mem_type, count in sorted(type_counts.items()):
        print(f"   - {mem_type}: {count}")
    
    # Get most recent
    memories_with_time = [
        m for m in all_memories 
        if 'timestamp' in m['metadata']
    ]
    if memories_with_time:
        most_recent = max(
            memories_with_time, 
            key=lambda m: m['metadata']['timestamp']
        )
        print(f"\n🕐 Most Recent Memory:")
        print(f"   {most_recent['content'][:80]}...")
        print(f"   Time: {most_recent['metadata']['timestamp']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

