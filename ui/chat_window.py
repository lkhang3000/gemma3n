import customtkinter as ctk
from tkinter import messagebox
import threading
import queue
import time
import sys
import os
from back_end.form import Form

try:
    from back_end.chatbot_backend import GUIChatbot
    BACKEND_AVAILABLE = True
    print("✅ Backend imported successfully")
except ImportError as e:
    print(f"❌ Backend import error: {e}")
    BACKEND_AVAILABLE = False

class ChatWindow:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Medical Chatbot - GUI Demo")
        self.root.geometry("1000x800")
        self.root.minsize(700, 600)

        self.is_model_loaded = False
        self.response_queue = queue.Queue()
        self.is_generating = False
        
        # Initialize medical form system
        try:
            self.medicalForm = Form()
            print("✅ Medical form system initialized")
        except Exception as e:
            print(f"❌ Medical form initialization error: {e}")
            self.medicalForm = None
    
        # Initialize chatbot backend
        if BACKEND_AVAILABLE:
            try:
                self.chatbot = GUIChatbot(
                    mode="auto",
                    status_callback=self.update_status,
                    progress_callback=self.update_progress
                )
                print("✅ Chatbot initialized")
            except Exception as e:
                print(f"❌ Chatbot initialization error: {e}")
                self.chatbot = None
        else:
            self.chatbot = None

        self.create_widgets()
        
        # Add welcome message
        self.add_message("Welcome to Medical Chatbot! 🏥", "system")
        if BACKEND_AVAILABLE and self.chatbot:
            self.add_message("System initializing... Please wait", "system")
        else:
            self.add_message("⚠️ Backend not available - Running in demo mode", "system")

    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self.root, height=80)
        header_frame.pack(fill="x", padx=20, pady=20)
        header_frame.pack_propagate(False)

        # Toggle menu 
        def toggle_button():
            def close_menu():
                toggle_menu_frm.destroy()
                self.toggle_btn.configure(text='☰')
                self.toggle_btn.configure(command=toggle_button)
                
            self.window_height = self.root.winfo_height()
            toggle_menu_frm = ctk.CTkFrame(self.root, fg_color='#158aaf', width=200, height=self.window_height)
            toggle_menu_frm.place(x=18, y=85)
    
            self.toggle_btn.configure(text='✕')
            self.toggle_btn.configure(command=close_menu)

            # Chat History button
            chatHistory_btn = ctk.CTkButton(
                toggle_menu_frm, 
                text='Chat History', 
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color='white',
                text_color='#158aaf',
                width=160,
                height=40,
                command=self.show_chat_history
            )
            chatHistory_btn.place(x=20, y=50)

            # System Info button
            info_btn = ctk.CTkButton(
                toggle_menu_frm,
                text='System Info',
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color='white',
                text_color='#158aaf',
                width=160,
                height=40,
                command=self.show_system_info
            )
            info_btn.place(x=20, y=105)

            # Reset Chat button
            reset_btn = ctk.CTkButton(
                toggle_menu_frm,
                text='Reset Chat',
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color='white',
                text_color='#158aaf',
                width=160,
                height=40,
                command=self.reset_conversation
            )
            reset_btn.place(x=20, y=160)

            # Login button
            login_btn = ctk.CTkButton(
                toggle_menu_frm,
                text='Create Medical Form',
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color='white',
                text_color='#158aaf',
                width=160,
                height=40,
                command=self.show_login_popup
            )
            login_btn.place(x=20, y=215)

        
        self.toggle_btn = ctk.CTkButton(
            header_frame,
            text='☰',
            fg_color='#158aaf',
            text_color='white',
            font=ctk.CTkFont(weight="bold", size=16),
            width=40,
            height=40,
            command=toggle_button  
        )
        self.toggle_btn.pack(side="left", padx=10)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Medical Chatbot Demo",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(expand=True, pady=20)

        # Chat frame
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            width=800,
            height=400,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        # Input frame
        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="How are you doing?...",
            font=ctk.CTkFont(size=12),
            height=40
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15)

        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            width=80,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.send_button.pack(side="right", padx=(0, 10), pady=15)

        self.clear_button = ctk.CTkButton(
            input_frame,
            text="Clear",
            command=self.clear_chat,
            width=60,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.clear_button.pack(side="right", padx=(0, 20), pady=15)

        # Status frame
        status_frame = ctk.CTkFrame(self.root, height=80)
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="System has not been initializing, please wait...",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=300)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)

        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_message())

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
            
        if self.is_generating:
            self.add_message("⚠️ We're working on the previous message, please wait...", "system")
            return
            
        self.add_message(message, "user")
        self.message_entry.delete(0, "end")
        
        # Disable send button to prevent spam
        self.send_button.configure(state="disabled")
        self.is_generating = True
        
        # Use backend if available
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                # Check if chatbot has the required method
                if hasattr(self.chatbot, 'generate_response_async'):
                    # Show "thinking" message
                    thinking_msg = "🤔 Analyzing..."
                    self.add_message(thinking_msg, "system")
                    
                    # Generate response asynchronously
                    def response_callback(response):
                        try:
                            # Remove "thinking" message by getting current content and removing last system message
                            current_content = self.chat_display.get("1.0", "end")
                            lines = current_content.strip().split('\n')
                            
                            # Find and remove the thinking message lines
                            filtered_lines = []
                            skip_next = False
                            for i, line in enumerate(lines):
                                if "🤔 Analyzing" in line:
                                    skip_next = True
                                    continue
                                if skip_next and line.strip() == "":
                                    skip_next = False
                                    continue
                                if not skip_next:
                                    filtered_lines.append(line)
                            
                            # Clear and re-add content without thinking message
                            self.chat_display.delete("1.0", "end")
                            if filtered_lines:
                                self.chat_display.insert("1.0", '\n'.join(filtered_lines) + '\n')
                            
                            # Add AI response
                            self.add_message(response, "ai")
                            
                        except Exception as e:
                            print(f"Error in response callback: {e}")
                            self.add_message(f"❌ Error showing response: {str(e)}", "system")
                        
                        finally:
                            # Re-enable send button
                            self.send_button.configure(state="normal")
                            self.is_generating = False
                    
                    self.chatbot.generate_response_async(message, response_callback)
                else:
                    # Method not available, use fallback
                    raise AttributeError("generate_response_async method not available")
                    
            except Exception as e:
                print(f"Backend error: {e}")
                self.add_message(f"❌ Backend error: {str(e)}", "system")
                self.send_button.configure(state="normal")
                self.is_generating = False
        else:
            # Fallback to simple response if backend not available
            def simple_response():
                try:
                    time.sleep(1)
                    if any(keyword in message.lower() for keyword in ["chest pain", "difficulty breathing", "heart attack"]):
                        response = "🚨 WARNING: The symptoms you described above can be serious!\n\n1. Please contact medical help immediately (115)\n2. Please do not hesitate with the help of a medical team.\n\n"
                    elif "hi" in message.lower() or "hello" in message.lower():
                        response = "Greetings, i am Medical Chatbot. I can provide you with necessary medical knowledge, but please directly consult a medical expert in urgent situation."
                    else:
                        response = f"⚠️ Backend not available.\n\nYou said: '{message}'\n"
                    
                    self.add_message(response, "ai")
                    
                except Exception as e:
                    self.add_message(f"❌ Response generating error: {str(e)}", "system")
                
                finally:
                    self.send_button.configure(state="normal")
                    self.is_generating = False
            
            threading.Thread(target=simple_response, daemon=True).start()

    def update_status(self, status_text):
        """Update status label from backend"""
        try:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text=status_text)
                self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating status: {e}")

    def update_progress(self, progress_value):
        """Update progress bar from backend"""
        try:
            if hasattr(self, 'progress_bar'):
                self.progress_bar.set(progress_value)
                self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating progress: {e}")

    def clear_chat(self):
        self.chat_display.delete("1.0", "end")
        self.add_message("Chat deleted. 🧹", "system")

    def reset_conversation(self):
        """Reset the conversation in backend and clear chat"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                # Check if reset method exists
                if hasattr(self.chatbot, 'reset_conversation'):
                    success = self.chatbot.reset_conversation()
                    if success:
                        self.clear_chat()
                        self.add_message("✅ Chat conversation has been reset. Now you can start over! 🔄", "system")
                    else:
                        self.add_message("❌ Failed to reset conversation", "system")
                else:
                    # Fallback if method doesn't exist
                    self.clear_chat()
                    self.add_message("✅ Chat has been cleared! 🔄", "system")
            except Exception as e:
                self.add_message(f"❌ Error resetting conversation: {str(e)}", "system")
        else:
            self.clear_chat()
            self.add_message("✅ Demo reset successful! 🔄", "system")

    def show_chat_history(self):
        """Show conversation history in a popup"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                # Check if method exists
                if hasattr(self.chatbot, 'get_status'):
                    status = self.chatbot.get_status()
                else:
                    status = {
                        'initialized': hasattr(self.chatbot, 'is_initialized') and self.chatbot.is_initialized,
                        'mode': getattr(self.chatbot, 'mode', 'unknown'),
                        'conversation_turns': len(getattr(self.chatbot, 'conversation_history', [])) - 1
                    }
                
                history = getattr(self.chatbot, 'conversation_history', [])

                history_window = ctk.CTkToplevel(self.root)
                history_window.title("Chat History")
                history_window.geometry("700x600")
                
                history_text = ctk.CTkTextbox(history_window, wrap="word")
                history_text.pack(fill="both", expand=True, padx=20, pady=20)
                
                history_info = f"Status: {'Initialized' if status['initialized'] else 'Uninitialized'}\n"
                history_info += f"Mode: {status['mode']}\n"
                if 'model' in status:
                    history_info += f"Model: {status['model']}\n"
                history_info += f"Number of messages: {status['conversation_turns']}\n\n"

                if len(history) > 1:  # Has conversation beyond system prompt
                    history_info += "=== CONVERSATION HISTORY ===\n\n"
                    for i, msg in enumerate(history[1:], 1):  # Skip system prompt
                        role = "👤 You" if msg['role'] == 'user' else "🤖 AI Assistant"
                        history_info += f"[{i}] {role}:\n"
                        content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
                        history_info += f"{content}\n\n"
                        history_info += "-" * 50 + "\n\n"
                else:
                    history_info += "=== CONVERSATION HISTORY ===\n\n"
                    history_info += "No conversation history yet. Start chatting to see history here!\n"
                
                history_text.insert("1.0", history_info)
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot show chat history: {str(e)}")
        else:
            messagebox.showinfo("Information", "Chat history not available in demo mode")

    def show_system_info(self):
        """Show system information in a popup"""
        if self.chatbot and BACKEND_AVAILABLE:
            try:
                # Check if method exists
                if hasattr(self.chatbot, 'get_system_requirements'):
                    requirements = self.chatbot.get_system_requirements()
                else:
                    requirements = {"error": "System requirements method not available"}
            
                info_window = ctk.CTkToplevel(self.root)
                info_window.title("System Information")
                info_window.geometry("700x500")
                
                info_text = ctk.CTkTextbox(info_window, wrap="word")
                info_text.pack(fill="both", expand=True, padx=20, pady=20)
                
                if "error" in requirements:
                    info_content = f"❌ Error: {requirements['error']}\n\n"
                    info_content += "Basic System Info:\n"
                    info_content += f"• Python: {sys.version}\n"
                    info_content += f"• Backend Available: {'✅' if BACKEND_AVAILABLE else '❌'}\n"
                    info_content += f"• Chatbot Initialized: {'✅' if self.chatbot else '❌'}\n"
                else:
                    current = requirements['current_specs']
                    recommended = requirements['recommended_specs']
                    meets = requirements['meets_requirements']
                    
                    info_content = "=== SYSTEM INFORMATION ===\n\n"
                    info_content += "Current Specifications:\n"
                    info_content += f"• CPU Cores: {current['cpu_cores']} ({'✅' if meets['cpu'] else '❌'} recommended: {recommended['cpu_cores']})\n"
                    info_content += f"• RAM: {current['ram_gb']:.1f}GB ({'✅' if meets['ram'] else '❌'} recommended: {recommended['ram_gb']}GB)\n"
                    info_content += f"• AVX Support: {'✅' if current['has_avx'] else '❌'}\n"
                    info_content += f"• OS: {current['os_type']}\n\n"
                    
                    info_content += f"Meets Requirements: {'✅ Yes' if meets['overall'] else '❌ No'}\n\n"
                    
                    if requirements['performance_tips']:
                        info_content += "Performance Improvement Tips:\n"
                        for tip in requirements['performance_tips']:
                            info_content += f"• {tip}\n"
            
                info_text.insert("1.0", info_content)
                
            except Exception as e:
                messagebox.showerror("Error", f"Cannot show system information: {str(e)}")
        else:
            system_info = f"Backend: ❌ Not Available\nPython: {sys.version}\nOS: {os.name}"
            messagebox.showinfo("System Information", system_info)

    def add_message(self, message, sender):
        """Add message to chat display with proper formatting"""
        timestamp = time.strftime("%H:%M:%S")
        
        if sender == "user":
            prefix = f"[{timestamp}] 👤 You: "
            color = "#4A9EFF"
        elif sender == "system":
            prefix = f"[{timestamp}] 🔔 System: "
            color = "#FFA500"
        else:  # ai
            prefix = f"[{timestamp}] 🤖 Medical AI: "
            color = "#32CD32"

        # Insert message with formatting
        current_pos = self.chat_display.index("end")
        self.chat_display.insert("end", prefix + message + "\n\n")
        
        # Scroll to bottom
        self.chat_display.see("end")
        self.root.update_idletasks()

    def show_login_popup(self):
        # Create popup window
        popup = ctk.CTkToplevel(self.root)
        popup.title("Create Medical Form")
        popup.geometry("400x350")
        popup.grab_set()  # Make it modal
        
        # Center the popup
        popup.transient(self.root)
        
        # Title
        title_label = ctk.CTkLabel(
            popup,
            text="Chatbot Medical Form",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Name field
        name_label = ctk.CTkLabel(popup, text="Name:", font=ctk.CTkFont(size=12))
        name_label.pack(pady=(10, 5))
        
        name_entry = ctk.CTkEntry(popup, placeholder_text="Enter your name", width=250)
        name_entry.pack(pady=(0, 10))
        
        # Age field
        age_label = ctk.CTkLabel(popup, text="Age:", font=ctk.CTkFont(size=12))
        age_label.pack(pady=(10, 5))
        
        age_entry = ctk.CTkEntry(popup, placeholder_text="Enter your age", width=250)
        age_entry.pack(pady=(0, 20))
        
        # Status label for showing save result
        status_label = ctk.CTkLabel(popup, text="", font=ctk.CTkFont(size=12))
        status_label.pack(pady=(0, 10))
        
        # Sign up function using your backend
        def handle_form():
            name = name_entry.get().strip()
            age = age_entry.get().strip()
            
            if not name or not age:
                status_label.configure(text="❌ Please fill in all fields", text_color="red")
                return
            
            try:
                if self.medicalForm:
                    new_user = self.medicalForm.signUp(name, age)
                    status_label.configure(text="✅ Saved successfully!", text_color="green")
                    
                    # Clear the form after successful save
                    name_entry.delete(0, "end")
                    age_entry.delete(0, "end")
                else:
                    status_label.configure(text="❌ Medical form system not available", text_color="red")
            except Exception as e:
                status_label.configure(text=f"❌ Error: {str(e)}", text_color="red")
        
        # Submit button
        submit_btn = ctk.CTkButton(
            popup,
            text="Submit",
            command=handle_form,
            width=120,
            height=40
        )
        submit_btn.pack(pady=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            popup,
            text="Close",
            command=popup.destroy,
            width=100,
            height=40
        )
        close_btn.pack(pady=10)

    def run(self):
        """Start the GUI application"""
        try:
            print("🚀 Starting Medical Chatbot GUI...")
            self.root.mainloop()
        except Exception as e:
            print(f"❌ GUI Error: {e}")
            messagebox.showerror("Lỗi nghiêm trọng", f"Ứng dụng gặp lỗi: {str(e)}")

if __name__ == "__main__":
    try:
        app = ChatWindow()
        app.run()
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        messagebox.showerror("Lỗi khởi động", f"Không thể khởi động ứng dụng: {str(e)}")