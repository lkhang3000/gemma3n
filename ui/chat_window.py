import customtkinter as ctk
from tkinter import messagebox, ttk
import threading
import queue
import time
import sys
import os

# Import cả hai loại model
try:
    from ai.ollama_gemma_model import OllamaGemmaModel
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    from ai.gemma_model import GemmaModel
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False

class ChatWindow:
    def __init__(self):
        # Thiết lập giao diện CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Tạo cửa sổ chính
        self.root = ctk.CTk()
        self.root.title("Gemma Chatbot - Enhanced Version")
        self.root.geometry("1000x800")
        self.root.minsize(700, 600)
        
        # Khởi tạo variables
        self.ai_model = None
        self.is_model_loaded = False
        self.current_backend = "ollama"  # default
        
        # Queue để xử lý threading
        self.response_queue = queue.Queue()
        
        # Tạo giao diện
        self.create_widgets()
        
        # Kiểm tra backends có sẵn
        self.check_available_backends()
        
    def check_available_backends(self):
        """Kiểm tra các backend có sẵn"""
        backends = []
        
        if OLLAMA_AVAILABLE:
            backends.append("🦙 Ollama (Khuyến nghị)")
        
        if HUGGINGFACE_AVAILABLE:
            backends.append("🤗 Hugging Face")
        
        if not backends:
            messagebox.showerror(
                "Lỗi", 
                "Không tìm thấy backend nào!\nVui lòng cài đặt Ollama hoặc Hugging Face Transformers"
            )
            return
        
        # Cập nhật dropdown
        self.backend_selector.configure(values=backends)
        self.backend_selector.set(backends[0])
        
        # Tự động load model mặc định
        self.load_model_async()
    
    def create_widgets(self):
        # Header frame
        header_frame = ctk.CTkFrame(self.root, height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Title và Backend selector
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="🤖 Gemma Chatbot Enhanced", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(side="left")
        
        # Backend selector
        backend_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        backend_frame.pack(side="right")
        
        ctk.CTkLabel(backend_frame, text="Backend:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        
        self.backend_selector = ctk.CTkComboBox(
            backend_frame,
            values=["🦙 Ollama", "🤗 Hugging Face"],
            width=150,
            command=self.on_backend_changed
        )
        self.backend_selector.pack(side="left", padx=(0, 10))
        
        # Reload button
        self.reload_button = ctk.CTkButton(
            backend_frame,
            text="🔄 Reload",
            width=60,
            command=self.reload_model
        )
        self.reload_button.pack(side="left")
        
        # Main chat frame
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Chat display area
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
        
        # Message input
        self.message_entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="Nhập tin nhắn của bạn...",
            font=ctk.CTkFont(size=12),
            height=40
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=15)
        
        # Send button
        self.send_button = ctk.CTkButton(
            input_frame, 
            text="Gửi", 
            command=self.send_message,
            width=80,
            height=40,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.send_button.pack(side="right", padx=(0, 10), pady=15)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            input_frame, 
            text="Xóa", 
            command=self.clear_chat,
            width=60,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.clear_button.pack(side="right", padx=(0, 20), pady=15)
        
        # Status frame
        status_frame = ctk.CTkFrame(self.root, height=60)
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        status_frame.pack_propagate(False)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="🔄 Đang khởi tạo...", 
            font=ctk.CTkFont(size=11)
        )
        self.status_label.pack(pady=15)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(status_frame, width=300)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)
        
        # Bind Enter key
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Thêm welcome message
        self.add_message("Chào mừng bạn đến với Gemma Chatbot Enhanced! 🚀", "system")
        
    def on_backend_changed(self, choice):
        """Xử lý khi thay đổi backend"""
        if "Ollama" in choice:
            self.current_backend = "ollama"
        else:
            self.current_backend = "huggingface"
        
        self.add_message(f"Đang chuyển sang {choice}...", "system")
        self.is_model_loaded = False
        self.load_model_async()
    
    def reload_model(self):
        """Reload model"""
        self.add_message("Đang reload model...", "system")
        self.is_model_loaded = False
        if self.ai_model:
            self.ai_model.cleanup()
        self.load_model_async()
    
    def load_model_async(self):
        """Tải model trong background thread"""
        def load_model():
            try:
                self.root.after(0, self.update_status, "🔄 Đang tải model...", 0.2)
                
                # Chọn backend
                if self.current_backend == "ollama":
                    if not OLLAMA_AVAILABLE:
                        raise ImportError("Ollama không có sẵn")
                    self.ai_model = OllamaGemmaModel()
                else:
                    if not HUGGINGFACE_AVAILABLE:
                        raise ImportError("Hugging Face không có sẵn")
                    self.ai_model = GemmaModel()
                
                self.root.after(0, self.update_status, "📥 Đang tải model...", 0.5)
                
                # Load model
                success = self.ai_model.load_model()
                
                if success:
                    self.is_model_loaded = True
                    self.root.after(0, self.on_model_loaded)
                else:
                    self.root.after(0, self.on_model_error, "Model không thể tải")
                    
            except Exception as e:
                self.root.after(0, self.on_model_error, str(e))
                
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()
    
    def update_status(self, message, progress):
        """Cập nhật status và progress"""
        self.status_label.configure(text=message)
        self.progress_bar.set(progress)
        
    def on_model_loaded(self):
        """Callback khi model đã tải xong"""
        self.status_label.configure(text="✅ Sẵn sàng chat!")
        self.progress_bar.set(1.0)
        
        backend_name = "Ollama" if self.current_backend == "ollama" else "Hugging Face"
        self.add_message(f"Model AI ({backend_name}) đã sẵn sàng! Bạn có thể bắt đầu chat.", "system")
        
    def on_model_error(self, error):
        """Callback khi có lỗi tải model"""
        self.status_label.configure(text="❌ Lỗi tải model")
        self.progress_bar.set(0)
        
        error_msg = f"Lỗi tải model: {error}"
        self.add_message(error_msg, "system")
        
        # Hiển thị hướng dẫn tùy theo backend
        if self.current_backend == "ollama":
            self.add_message("💡 Hướng dẫn sử dụng Ollama:", "system")
            self.add_message("1. Tải Ollama từ https://ollama.com/download", "system")
            self.add_message("2. Cài đặt và restart máy", "system")
            self.add_message("3. Chạy lệnh: ollama pull gemma2:2b", "system")
        else:
            self.add_message("💡 Hướng dẫn sử dụng Hugging Face:", "system")
            self.add_message("1. Tạo token tại https://huggingface.co/settings/tokens", "system")
            self.add_message("2. Request access: https://huggingface.co/google/gemma-2b-it", "system")
            self.add_message("3. Set environment variable: HF_TOKEN=your_token", "system")
        
    def send_message(self):
        """Gửi tin nhắn"""
        message = self.message_entry.get().strip()
        if not message:
            return
            
        if not self.is_model_loaded:
            messagebox.showwarning("Chờ đợi", "Model AI chưa sẵn sàng, vui lòng đợi...")
            return
            
        # Hiển thị tin nhắn user
        self.add_message(message, "user")
        self.message_entry.delete(0, "end")
        
        # Vô hiệu hóa nút gửi
        self.send_button.configure(state="disabled", text="Đang xử lý...")
        self.status_label.configure(text="🤔 AI đang suy nghĩ...")
        self.progress_bar.set(0.3)
        
        # Xử lý response trong background thread
        thread = threading.Thread(target=self.process_ai_response, args=(message,), daemon=True)
        thread.start()
        
    def process_ai_response(self, message):
        """Xử lý AI response trong background thread"""
        try:
            response = self.ai_model.get_response(message)
            self.root.after(0, self.handle_ai_response, response)
        except Exception as e:
            self.root.after(0, self.handle_ai_response, f"Xin lỗi, đã có lỗi xảy ra: {str(e)}")
            
    def handle_ai_response(self, response):
        """Xử lý kết quả AI response"""
        self.add_message(response, "bot")
        self.send_button.configure(state="normal", text="Gửi")
        self.status_label.configure(text="✅ Sẵn sàng chat!")
        self.progress_bar.set(1.0)
        
    def clear_chat(self):
        """Xóa lịch sử chat"""
        self.chat_display.delete("0.0", "end")
        self.add_message("Lịch sử chat đã được xóa! 🗑️", "system")
        
    def add_message(self, message, sender):
        """Thêm tin nhắn vào chat display"""
        timestamp = time.strftime("%H:%M:%S")
        
        if sender == "user":
            prefix = f"[{timestamp}] 👤 Bạn: "
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", f"{message}\n\n")
        elif sender == "bot":
            prefix = f"[{timestamp}] 🤖 AI: "
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", f"{message}\n\n")
        elif sender == "system":
            prefix = f"[{timestamp}] 🔔 System: "
            self.chat_display.insert("end", prefix)
            self.chat_display.insert("end", f"{message}\n\n")
            
        # Cuộn xuống cuối
        self.chat_display.see("end")
        
        # Cập nhật display
        self.root.update_idletasks()
        
    def run(self):
        """Chạy ứng dụng"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Đang thoát ứng dụng...")
            if self.ai_model:
                self.ai_model.cleanup()
            self.root.quit()

if __name__ == "__main__":
    app = EnhancedChatWindow()
    app.run()