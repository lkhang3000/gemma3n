import subprocess

class OllamaGemmaModel:
    def __init__(self):
        self.model_name = "gemma:2b"

    def load_model(self):
        """Load model từ Ollama"""
        try:
            # Gọi lệnh kiểm tra model
            result = subprocess.run(
                ["ollama", "run", self.model_name],
                input="Xin chào\n",  # câu đơn giản để khởi động
                text=True,
                capture_output=True,
                timeout=10
            )
            return True if result.returncode == 0 else False
        except Exception as e:
            print(f"Lỗi khi load model Ollama: {e}")
            return False

    def get_response(self, prompt):
        """Gửi prompt và nhận response từ Ollama"""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model_name],
                input=prompt,
                text=True,
                capture_output=True,
                timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            return f"❌ Lỗi khi gọi model: {e}"

    def cleanup(self):
        """Hàm dọn dẹp nếu cần"""
        pass
