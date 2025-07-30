#!/usr/bin/env python3
"""
Test script to check system requirements and chatbot backend integration
"""

import sys
import os

# Add back_end to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'back_end'))

try:
    from chatbot_backend import GUIChatbot
    print("✅ Backend import successful")
except ImportError as e:
    print(f"❌ Backend import failed: {e}")
    sys.exit(1)

def test_requirements():
    """Test system requirements checking"""
    print("\n" + "="*50)
    print("SYSTEM REQUIREMENTS TEST")
    print("="*50)
    
    def status_callback(msg):
        print(f"Status: {msg}")
    
    def progress_callback(value):
        print(f"Progress: {value*100:.1f}%")
    
    # Initialize chatbot
    chatbot = GUIChatbot(
        mode="auto",
        status_callback=status_callback,
        progress_callback=progress_callback
    )
    
    # Wait for initialization
    import time
    time.sleep(3)
    
    # Get system status
    status = chatbot.get_status()
    print(f"\n📊 System Status:")
    print(f"  - Initialized: {status['initialized']}")
    print(f"  - Mode: {status['mode']}")
    print(f"  - Detail: {status['mode_detail']}")
    print(f"  - Conversation turns: {status['conversation_turns']}")
    
    # Get system requirements
    if hasattr(chatbot, 'get_system_requirements'):
        requirements = chatbot.get_system_requirements()
        print(f"\n🔧 System Requirements:")
        
        current = requirements['current_specs']
        recommended = requirements['recommended_specs']
        meets = requirements['meets_requirements']
        
        print(f"  Current Specs:")
        print(f"    - CPU Cores: {current['cpu_cores']} (Recommended: {recommended['cpu_cores']})")
        print(f"    - RAM: {current['ram_gb']}GB (Recommended: {recommended['ram_gb']}GB)")
        print(f"    - AVX Support: {current['has_avx']} (Recommended: {recommended['has_avx']})")
        print(f"    - OS: {current['os_type']}")
        
        print(f"\n  Requirements Met:")
        print(f"    - CPU: {'✅' if meets['cpu'] else '❌'}")
        print(f"    - RAM: {'✅' if meets['ram'] else '❌'}")
        print(f"    - AVX: {'✅' if meets['avx'] else '❌'}")
        print(f"    - Overall: {'✅' if meets['overall'] else '❌'}")
        
        print(f"\n💡 Performance Tips:")
        for tip in requirements['performance_tips']:
            print(f"    - {tip}")
    
    return chatbot

def test_basic_functionality(chatbot):
    """Test basic chatbot functionality"""
    print("\n" + "="*50)
    print("BASIC FUNCTIONALITY TEST")
    print("="*50)
    
    # Wait for full initialization
    import time
    max_wait = 10
    wait_time = 0
    while not chatbot.is_initialized and wait_time < max_wait:
        print(f"Waiting for initialization... ({wait_time}s)")
        time.sleep(1)
        wait_time += 1
    
    if not chatbot.is_initialized:
        print("❌ Chatbot failed to initialize within 10 seconds")
        return
    
    # Test normal query
    print("\n🧪 Testing normal medical query...")
    test_query = "I have a mild headache"
    response = chatbot.generate_response(test_query)
    print(f"Query: {test_query}")
    print(f"Response: {response[:100]}...")
    
    # Test emergency detection
    print("\n🚨 Testing emergency detection...")
    emergency_query = "I'm having severe chest pain"
    emergency_response = chatbot.generate_response(emergency_query)
    print(f"Query: {emergency_query}")
    print(f"Response: {emergency_response[:100]}...")
    
    print("\n✅ Basic functionality test completed")

if __name__ == "__main__":
    try:
        # Test requirements
        chatbot = test_requirements()
        
        # Test functionality
        test_basic_functionality(chatbot)
        
        print("\n" + "="*50)
        print("ALL TESTS COMPLETED")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
