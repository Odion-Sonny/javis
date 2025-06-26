#!/usr/bin/env python3
"""
Command Parser Example
Demonstrates the capabilities of the command parser module.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.nlp import (
    CommandParser, CommandIntent, ParameterType, 
    create_command_parser
)
from jarvis.nlp.command_parser import EXAMPLE_COMMANDS


def demonstrate_basic_parsing():
    """Demonstrate basic command parsing."""
    print("=" * 60)
    print("Basic Command Parsing Examples")
    print("=" * 60)
    
    parser = create_command_parser()
    
    test_commands = [
        "open file config.json",
        "create a new document called report.txt",
        "launch Calculator",
        "show system information",
        "what time is it",
        "hello Jarvis",
        "copy data.csv to backup folder",
        "run command ls -la",
        "what is artificial intelligence"
    ]
    
    for command_text in test_commands:
        print(f"\n📝 Input: '{command_text}'")
        result = parser.parse_command(command_text)
        
        print(f"   🎯 Intent: {result.intent.value}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        if result.action:
            print(f"   ⚡ Action: {result.action}")
        
        if result.parameters:
            print("   📋 Parameters:")
            for param in result.parameters:
                print(f"      • {param.name}: {param.value} ({param.param_type.value})")
        
        if result.clarification_needed:
            print(f"   ❓ Clarification: {result.clarification_needed}")
        
        if result.suggestions:
            print("   💡 Suggestions:")
            for suggestion in result.suggestions:
                print(f"      • {suggestion}")


def demonstrate_context_awareness():
    """Demonstrate context-aware parsing."""
    print("\n" + "=" * 60)
    print("Context-Aware Parsing Examples")
    print("=" * 60)
    
    parser = create_command_parser()
    
    # Sequence of related commands
    command_sequence = [
        "open file data.csv",
        "copy it to backup folder",
        "delete the original",
        "open another file",
        "list files in that directory"
    ]
    
    print("Command sequence demonstrating context:")
    
    for i, command_text in enumerate(command_sequence, 1):
        print(f"\n{i}. Input: '{command_text}'")
        result = parser.parse_command(command_text)
        
        print(f"   Intent: {result.intent.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Context used: {result.context_used}")
        
        if result.parameters:
            for param in result.parameters:
                print(f"   Parameter: {param.name} = {param.value}")
        
        if result.clarification_needed:
            print(f"   Clarification: {result.clarification_needed}")


def demonstrate_ambiguous_commands():
    """Demonstrate handling of ambiguous commands."""
    print("\n" + "=" * 60)
    print("Ambiguous Command Handling")
    print("=" * 60)
    
    parser = create_command_parser()
    
    ambiguous_commands = [
        "open",  # Missing target
        "run",   # Missing what to run
        "file",  # Just mentions file
        "delete something",  # Vague target
        "show me"  # Missing what to show
    ]
    
    for command_text in ambiguous_commands:
        print(f"\n📝 Input: '{command_text}'")
        result = parser.parse_command(command_text)
        
        print(f"   🎯 Intent: {result.intent.value}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        
        if result.clarification_needed:
            print(f"   ❓ Clarification needed: {result.clarification_needed}")
        
        if result.suggestions:
            print("   💡 Suggestions:")
            for suggestion in result.suggestions:
                print(f"      • {suggestion}")


def demonstrate_parameter_extraction():
    """Demonstrate parameter extraction capabilities."""
    print("\n" + "=" * 60)
    print("Parameter Extraction Examples")
    print("=" * 60)
    
    parser = create_command_parser()
    
    complex_commands = [
        "copy file.txt from /home/user to /backup/folder",
        "move all *.py files to the scripts directory",
        "open Visual Studio Code with project.json",
        "run command 'find . -name \"*.log\" -type f'",
        "create new folder called 'Project Reports' in Documents",
        "search for files containing 'TODO' in the current directory"
    ]
    
    for command_text in complex_commands:
        print(f"\n📝 Input: '{command_text}'")
        result = parser.parse_command(command_text)
        
        print(f"   🎯 Intent: {result.intent.value}")
        print(f"   ⚡ Action: {result.action}")
        print(f"   📊 Confidence: {result.confidence:.2f}")
        
        if result.parameters:
            print("   📋 Extracted Parameters:")
            for param in result.parameters:
                print(f"      • {param.name}: '{param.value}' ({param.param_type.value})")
                print(f"        Confidence: {param.confidence:.2f}")
                if param.source_text:
                    print(f"        Source: '{param.source_text}'")


def demonstrate_command_history():
    """Demonstrate command history and context management."""
    print("\n" + "=" * 60)
    print("Command History and Context Management")
    print("=" * 60)
    
    parser = create_command_parser()
    
    # Execute several commands to build history
    commands = [
        "open file report.txt",
        "show system info",
        "launch Firefox",
        "create folder backup",
        "what time is it"
    ]
    
    print("Building command history...")
    for cmd in commands:
        result = parser.parse_command(cmd)
        print(f"  ✓ {cmd} -> {result.intent.value}")
    
    # Show history
    print(f"\n📚 Command History ({len(parser.get_command_history())} commands):")
    for i, cmd in enumerate(parser.get_command_history(), 1):
        print(f"  {i}. {cmd.raw_text} -> {cmd.intent.value}")
    
    # Show context state
    print(f"\n🧠 Current Context:")
    context = parser.context
    print(f"  Last file: {context.last_file}")
    print(f"  Last directory: {context.last_directory}")
    print(f"  Last application: {context.last_application}")
    
    # Test context-based parsing
    print(f"\n🔄 Context-based parsing:")
    contextual_command = "open it again"
    result = parser.parse_command(contextual_command)
    print(f"  Input: '{contextual_command}'")
    print(f"  Result: {result.intent.value} (context used: {result.context_used})")


def demonstrate_user_preferences():
    """Demonstrate user preference learning."""
    print("\n" + "=" * 60)
    print("User Preference Learning")
    print("=" * 60)
    
    parser = create_command_parser()
    
    # Set some user preferences
    parser.set_user_preference('default_editor', 'Visual Studio Code')
    parser.set_user_preference('preferred_browser', 'Firefox')
    parser.set_user_preference('default_directory', '/home/user/projects')
    
    print("Set user preferences:")
    print(f"  Default editor: {parser.get_user_preference('default_editor')}")
    print(f"  Preferred browser: {parser.get_user_preference('preferred_browser')}")
    print(f"  Default directory: {parser.get_user_preference('default_directory')}")
    
    # These preferences could be used to enhance command parsing
    # For example, "open editor" could resolve to "open Visual Studio Code"
    print(f"\n💡 Preferences can be used to resolve ambiguous commands:")
    print(f"  'open editor' -> 'open {parser.get_user_preference('default_editor')}'")
    print(f"  'open browser' -> 'open {parser.get_user_preference('preferred_browser')}'")


def demonstrate_all_command_types():
    """Demonstrate parsing of all supported command types."""
    print("\n" + "=" * 60)
    print("All Supported Command Types")
    print("=" * 60)
    
    parser = create_command_parser()
    
    for category, commands in EXAMPLE_COMMANDS.items():
        print(f"\n📂 {category}:")
        for command_text in commands:
            result = parser.parse_command(command_text, use_context=False)  # Fresh context for each
            
            status = "✅" if result.confidence > 0.6 else "⚠️" if result.confidence > 0.3 else "❌"
            print(f"  {status} {command_text}")
            print(f"      → {result.intent.value} ({result.confidence:.2f})")
            
            if result.action:
                print(f"      → Action: {result.action}")
            
            if result.clarification_needed:
                print(f"      → Needs clarification: {result.clarification_needed}")


def interactive_demo():
    """Interactive demo allowing user input."""
    print("\n" + "=" * 60)
    print("Interactive Command Parser Demo")
    print("=" * 60)
    print("Enter commands to see how they're parsed.")
    print("Type 'quit' to exit, 'history' to see command history, 'clear' to clear context.")
    print("-" * 60)
    
    parser = create_command_parser()
    
    while True:
        try:
            user_input = input("\n🎤 Enter command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'history':
                history = parser.get_command_history()
                print(f"\n📚 Command History ({len(history)} commands):")
                for i, cmd in enumerate(history, 1):
                    print(f"  {i}. {cmd.raw_text} -> {cmd.intent.value}")
                continue
            elif user_input.lower() == 'clear':
                parser.clear_context()
                print("🧹 Context cleared!")
                continue
            elif not user_input:
                continue
            
            # Parse the command
            result = parser.parse_command(user_input)
            
            # Display results
            print(f"\n📊 Parsing Results:")
            print(f"  🎯 Intent: {result.intent.value}")
            print(f"  📈 Confidence: {result.confidence:.2f}")
            print(f"  🔄 Context used: {result.context_used}")
            
            if result.action:
                print(f"  ⚡ Action: {result.action}")
            
            if result.parameters:
                print(f"  📋 Parameters:")
                for param in result.parameters:
                    print(f"    • {param.name}: {param.value} ({param.param_type.value})")
            
            if result.clarification_needed:
                print(f"  ❓ Clarification: {result.clarification_needed}")
            
            if result.suggestions:
                print(f"  💡 Suggestions:")
                for suggestion in result.suggestions:
                    print(f"    • {suggestion}")
            
            # Show JSON representation
            print(f"\n📄 JSON representation:")
            print(json.dumps(result.to_dict(), indent=2))
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Run all command parser demonstrations."""
    print("🧠 Command Parser Module Demonstration")
    print("This shows the natural language command parsing capabilities.")
    
    try:
        demonstrate_basic_parsing()
        demonstrate_context_awareness()
        demonstrate_ambiguous_commands()
        demonstrate_parameter_extraction()
        demonstrate_command_history()
        demonstrate_user_preferences()
        demonstrate_all_command_types()
        
        # Ask if user wants interactive demo
        print("\n" + "=" * 60)
        response = input("Would you like to try the interactive demo? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Command parser demonstration completed!")


if __name__ == "__main__":
    main()