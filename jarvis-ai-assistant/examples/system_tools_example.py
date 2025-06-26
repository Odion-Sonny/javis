#!/usr/bin/env python3
"""
System Tools Example
Demonstrates the safe system interaction capabilities.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from jarvis.system_tools import SystemTools, create_system_tools


def demonstrate_application_management():
    """Demonstrate application launching and management."""
    print("=" * 60)
    print("Application Management Examples")
    print("=" * 60)
    
    tools = create_system_tools({
        'security_level': 'moderate',
        'allowed_applications': ['calculator', 'notepad', 'textedit', 'terminal']
    })
    
    # Test application launching
    print("\n📱 Testing Application Launch:")
    result = tools.launch_application('calculator')
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    if result.data:
        print(f"  PID: {result.data.get('pid')}")
    
    # Test denied application
    print("\n🚫 Testing Denied Application:")
    result = tools.launch_application('forbidden_app')
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")


def demonstrate_file_operations():
    """Demonstrate safe file operations."""
    print("\n" + "=" * 60)
    print("File Operations Examples")
    print("=" * 60)
    
    tools = create_system_tools({
        'allowed_directories': [os.path.expanduser('~'), '/tmp'],
        'blocked_directories': ['/etc', '/usr', '/bin']
    })
    
    # Test file copy (create a test file first)
    test_file = os.path.expanduser('~/test_jarvis.txt')
    backup_file = os.path.expanduser('~/test_jarvis_backup.txt')
    
    try:
        # Create test file
        with open(test_file, 'w') as f:
            f.write("This is a test file for Jarvis system tools demo.")
        
        print(f"\n📄 Testing File Copy:")
        result = tools.copy_file(test_file, backup_file)
        print(f"  Result: {result.result.value}")
        print(f"  Message: {result.message}")
        if result.data:
            print(f"  Size: {result.data.get('size')} bytes")
        
        print(f"\n📁 Testing File Move:")
        move_file = os.path.expanduser('~/test_jarvis_moved.txt')
        result = tools.move_file(backup_file, move_file)
        print(f"  Result: {result.result.value}")
        print(f"  Message: {result.message}")
        
        print(f"\n🗑️ Testing File Delete (to trash):")
        result = tools.delete_file(test_file, to_trash=True)
        print(f"  Result: {result.result.value}")
        print(f"  Message: {result.message}")
        
        # Clean up
        if os.path.exists(move_file):
            os.remove(move_file)
            
    except Exception as e:
        print(f"  Error in demo: {e}")
    
    # Test blocked directory access
    print(f"\n🚫 Testing Blocked Directory Access:")
    result = tools.copy_file('/etc/passwd', '~/passwd_copy')
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")


def demonstrate_system_information():
    """Demonstrate system information gathering."""
    print("\n" + "=" * 60)
    print("System Information Examples")
    print("=" * 60)
    
    tools = create_system_tools()
    
    print("\n💻 Getting System Information:")
    result = tools.get_system_info()
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    
    if result.data:
        print(f"  Platform: {result.data.get('platform')}")
        print(f"  Architecture: {result.data.get('architecture')}")
        print(f"  CPU Count: {result.data.get('cpu_count')}")
        if 'memory_total' in result.data:
            memory_gb = result.data['memory_total'] / (1024**3)
            print(f"  Total Memory: {memory_gb:.1f} GB")
        if 'cpu_percent' in result.data:
            print(f"  CPU Usage: {result.data['cpu_percent']}%")
    
    print("\n📊 Getting Running Processes (top 5):")
    result = tools.get_running_processes(limit=5)
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    
    if result.data and 'processes' in result.data:
        for i, proc in enumerate(result.data['processes'][:5], 1):
            print(f"  {i}. {proc.get('name', 'Unknown')} (PID: {proc.get('pid')}) - CPU: {proc.get('cpu_percent', 0):.1f}%")


def demonstrate_web_browser_control():
    """Demonstrate web browser control."""
    print("\n" + "=" * 60)
    print("Web Browser Control Examples")
    print("=" * 60)
    
    tools = create_system_tools()
    
    print("\n🌐 Opening URL:")
    result = tools.open_url('https://www.example.com')
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    
    print("\n🔗 Opening URL with auto-protocol:")
    result = tools.open_url('github.com')
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")


def demonstrate_clipboard_operations():
    """Demonstrate clipboard operations."""
    print("\n" + "=" * 60)
    print("Clipboard Operations Examples")
    print("=" * 60)
    
    tools = create_system_tools()
    
    # Test setting clipboard
    test_text = "Hello from Jarvis system tools!"
    print(f"\n📋 Setting Clipboard Content:")
    result = tools.set_clipboard(test_text)
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    
    # Test getting clipboard
    print(f"\n📖 Getting Clipboard Content:")
    result = tools.get_clipboard()
    print(f"  Result: {result.result.value}")
    print(f"  Message: {result.message}")
    if result.data:
        content = result.data.get('content', '')
        print(f"  Content: '{content[:50]}{'...' if len(content) > 50 else ''}'")


def demonstrate_security_features():
    """Demonstrate security features."""
    print("\n" + "=" * 60)
    print("Security Features Examples")
    print("=" * 60)
    
    # Strict security
    strict_tools = create_system_tools({
        'security_level': 'strict',
        'allowed_applications': ['calculator'],
        'allowed_directories': [os.path.expanduser('~/Desktop')],
        'blocked_directories': ['/etc', '/usr', '/bin', '/System']
    })
    
    print("\n🔒 Strict Security Mode:")
    print("  Allowed apps: calculator only")
    print("  Allowed dirs: ~/Desktop only")
    
    # Test launching allowed app
    result = strict_tools.launch_application('calculator')
    print(f"  Calculator launch: {result.result.value}")
    
    # Test launching blocked app
    result = strict_tools.launch_application('terminal')
    print(f"  Terminal launch: {result.result.value} - {result.message}")
    
    # Test file operation in blocked directory
    result = strict_tools.copy_file('/etc/hosts', '~/Desktop/hosts')
    print(f"  Copy from /etc: {result.result.value} - {result.message}")


def show_operation_details(operation):
    """Helper function to show detailed operation results."""
    print(f"\n📊 Operation Details:")
    details = operation.to_dict()
    print(json.dumps(details, indent=2))


def main():
    """Run all system tools demonstrations."""
    print("🛠️ System Tools Module Demonstration")
    print("This shows safe system interaction capabilities.")
    
    try:
        demonstrate_application_management()
        demonstrate_file_operations()
        demonstrate_system_information()
        demonstrate_web_browser_control()
        demonstrate_clipboard_operations()
        demonstrate_security_features()
        
        print("\n" + "=" * 60)
        print("✅ All system tools demonstrations completed!")
        print("\n💡 Key Features Demonstrated:")
        print("  • Safe application launching with whitelisting")
        print("  • Secure file operations with directory restrictions")
        print("  • Comprehensive system information gathering")
        print("  • Web browser control for URL opening")
        print("  • Clipboard operations for text management")
        print("  • Multi-level security controls")
        print("  • Detailed operation logging and error handling")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()