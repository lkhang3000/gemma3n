"""
Gemma Chatbot - Windows Desktop Application
Ứng dụng chat sử dụng Gemma AI model
"""

import os
import sys
import traceback
from pathlib import Path

# Thêm thư mục root vào Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from ui.chat_window import ChatWindow
    import customtkinter as ctk
    from tkinter import messagebox
    import torch
    from transformers import AutoTokenizer
    
except ImportError as e:
    print(f"❌ Lỗi import: {e}")
    print("📋 Cần cài đặt các package sau:")
    print("pip install customtkinter transformers torch torchvision torchaudio")
    input("Nhấn Enter để thoát...")
    sys.exit(1)

def check_requirements():
    """Kiểm tra system requirements"""
    print("🔍 Đang kiểm tra system requirements...")
    
    # Kiểm tra Python version
    if sys.version_info < (3, 8):
        print("❌ Cần Python 3.8 trở lên")
        return False
        
    # Kiểm tra GPU (optional)
    if torch.cuda.is_available():
        print(f"✅ GPU khả dụng: {torch.cuda.get_device_name(0)}")
        print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("⚠️ Không phát hiện GPU, sẽ sử dụng CPU (chậm hơn)")
        
    # Kiểm tra disk space (cần ~5GB cho model)
    import shutil
    free_space = shutil.disk_usage(".").free / (1024**3)
    if free_space < 5:
        print(f"⚠️ Disk space thấp: {free_space:.1f} GB (khuyến nghị >= 5GB)")
        
    print("✅ System requirements OK")
    return True

def setup_environment():
    """Thiết lập môi trường"""
    # Tạo thư mục cache nếu chưa có
    cache_dir = Path.home() / ".cache" / "gemma_chatbot"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Thiết lập Hugging Face cache
    os.environ['HF_HOME'] = str(cache_dir / "huggingface")
    os.environ['TRANSFORMERS_CACHE'] = str(cache_dir / "transformers")
    
    # Thiết lập số threads cho CPU
    if not torch.cuda.is_available():
        torch.set_num_threads(4)  # Tối ưu cho CPU
        
    print("🔧 Môi trường đã được thiết lập")

def main():
    """Main function"""
    print("🚀 Khởi động Gemma Chatbot...")
    print("=" * 50)
    
    try:
        # Kiểm tra requirements
        if not check_requirements():
            input("❌ System requirements không đủ. Nhấn Enter để thoát...")
            return
            
        # Thiết lập môi trường
        setup_environment()
        
        # Khởi tạo và chạy ứng dụng
        print("🎨 Đang khởi tạo giao diện...")
        app = ChatWindow()
        
        print("✅ Ứng dụng đã sẵn sàng!")
        print("💡 Mẹo: Model sẽ tải trong background, vui lòng đợi...")
        print("=" * 50)
        
        # Chạy ứng dụng
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 Đang thoát ứng dụng...")
        
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        print("\n📋 Chi tiết lỗi:")
        traceback.print_exc()
        
        # Hiển thị error dialog nếu có thể
        try:
            root = ctk.CTk()
            root.withdraw()  # Ẩn window chính
            messagebox.showerror(
                "Lỗi ứng dụng",
                f"Đã xảy ra lỗi không mong muốn:\n\n{str(e)}\n\nVui lòng kiểm tra console để biết chi tiết."
            )
        except:
            pass
            
        input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    main()