import customtkinter as ctk
from tkinter import messagebox
import threading
import queue
import time

class ChatWindow:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Gemma Chatbot - GUI Demo")
        self.root.geometry("1000x800")
        self.root.minsize(700, 600)

        self.is_model_loaded = False
        self.response_queue = queue.Queue()
        self.create_widgets()

    def create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self.root, height=80)
        header_frame.pack(fill="both", expand=True, padx=20, pady=20)
        header_frame.pack_propagate(False)



        # Chat frame
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            width=800,
            height=400,
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        # Toggle menu 
        def toggle_button():
            def close_menu():
                toggle_menu_frm.destroy()
                self.toggle_btn.configure(text='☰')
                self.toggle_btn.configure(command=toggle_button)
                
            self.window_height = self.root.winfo_height()
            toggle_menu_frm = ctk.CTkFrame(self.root, fg_color='#158aaf', width=200, height=self.window_height)
            toggle_menu_frm.place(x=18, y=85)
    
            self.toggle_btn.configure(text='X')
            self.toggle_btn.configure(command=close_menu)

             # button Chat History
            chatHistory_btn = ctk.CTkButton(
                toggle_menu_frm, 
                text='Chat History', 
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color='white',
                text_color='#158aaf',
                width=160,
                height=40
            )
            chatHistory_btn.place(x=20, y=50)

        
        self.toggle_btn = ctk.CTkButton(
            header_frame,
            text='☰',
            fg_color='#158aaf',
            text_color='white',
            font=ctk.CTkFont(weight="bold", size=10),
            command=toggle_button  
        )
        self.toggle_btn.pack(side="left")

        title_label = ctk.CTkLabel(
            header_frame,
            text="Gemma Chatbot Demo UI",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(expand=True, pady=20)

        # Input
        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="What do you want to know?...",
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
            text="Clear Chat",
            command=self.clear_chat,
            width=60,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.clear_button.pack(side="right", padx=(0, 20), pady=15)

        # Status
        status_frame = ctk.CTkFrame(self.root, height=60)
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="System has not been initialized yet. Please wait...",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=15)

        self.progress_bar = ctk.CTkProgressBar(status_frame, width=300)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)

        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.add_message("Chào mừng bạn đến với bản demo UI của Gemma Chatbot! 🚀", "system")

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return
        self.add_message(message, "user")
        self.message_entry.delete(0, "end")
        self.add_message("⚠️ Chưa có backend AI xử lý tin nhắn.", "system")

    def clear_chat(self):
        self.chat_display.delete("0.0", "end")
        self.add_message("Chat cleared. 🧹", "system")

    def add_message(self, message, sender):
        timestamp = time.strftime("%H:%M:%S")
        prefix = f"[{timestamp}] "
        if sender == "user":
            prefix += "👤 Bạn: "
        elif sender == "system":
            prefix += "🔔 System: "
        else:
            prefix += "🤖 AI: "

        self.chat_display.insert("end", prefix + message + "\n\n")
        self.chat_display.see("end")
        self.root.update_idletasks()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ChatWindow()
    app.run()
