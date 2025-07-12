import requests
import json
import os
import subprocess
import time
from pathlib import Path

class OllamaGemmaModel:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model_name = "gemma2:2b"  # hoặc gemma:2b
        self.is_loaded = False
        self.ollama_running = False
        
        print("🦙 Khởi tạo Ollama Gemma Model")
        
    def check_ollama_installed(self):
        """Kiểm tra Ollama đã cài đặt chưa"""
        try:
            result = subprocess.run(
                ["ollama", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Ollama đã cài đặt: {result.stdout.strip()}")
                return True
            else:
                print("❌ Ollama chưa cài đặt")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Ollama chưa cài đặt hoặc không trong PATH")
            return False
    
    def install_ollama_guide(self):
        """Hướng dẫn cài đặt Ollama"""
        print("\n📋 HƯỚNG DẪN CÀI ĐẶT OLLAMA:")
        print("=" * 40)
        print("🌐 Windows:")
        print("   1. Tải từ: https://ollama.com/download")
        print("   2. Chạy file .exe và làm theo hướng dẫn")
        print("   3. Restart máy tính")
        print("\n🐧 Linux/Mac:")
        print("   curl -fsSL https://ollama.com/install.sh | sh")
        print("\n⚠️ Sau khi cài đặt, chạy lại script này")
        
    def start_ollama_service(self):
        """Khởi động Ollama service"""
        print("🚀 Đang khởi động Ollama service...")
        
        try:
            # Thử kết nối trước
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama service đã chạy")
                self.ollama_running = True
                return True
        except requests.exceptions.RequestException:
            pass
        
        # Nếu chưa chạy, thử khởi động
        try:
            if os.name == 'nt':  # Windows
                subprocess.Popen(["ollama", "serve"], shell=True)
            else:  # Linux/Mac
                subprocess.Popen(["ollama", "serve"])
            
            print("⏳ Đang chờ Ollama service khởi động...")
            time.sleep(3)
            
            # Kiểm tra lại
            for i in range(10):
                try:
                    response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                    if response.status_code == 200:
                        print("✅ Ollama service đã sẵn sàng")
                        self.ollama_running = True
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(2)
                    print(f"⏳ Thử lại... ({i+1}/10)")
            
            print("❌ Không thể khởi động Ollama service")
            return False
            
        except Exception as e:
            print(f"❌ Lỗi khởi động Ollama: {e}")
            return False
    
    def list_available_models(self):
        """Liệt kê các model có sẵn"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"📋 Có {len(models)} model đã cài đặt:")
                for model in models:
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0) / (1024**3)  # GB
                    print(f"   🤖 {name} ({size:.1f} GB)")
                return [model.get("name") for model in models]
            else:
                print("❌ Không thể lấy danh sách model")
                return []
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách model: {e}")
            return []
    
    def pull_model(self, model_name=None):
        """Tải model từ Ollama registry"""
        if not model_name:
            model_name = self.model_name
            
        print(f"📥 Đang tải model {model_name}...")
        print("⏳ Quá trình này có thể mất vài phút...")
        
        try:
            # Stream response để hiển thị progress
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                status = data["status"]
                                if "completed" in data and "total" in data:
                                    completed = data["completed"]
                                    total = data["total"]
                                    percent = (completed / total) * 100
                                    print(f"\r📊 {status}: {percent:.1f}%", end="", flush=True)
                                else:
                                    print(f"\r🔄 {status}", end="", flush=True)
                        except json.JSONDecodeError:
                            continue
                
                print("\n✅ Model đã tải xong!")
                return True
            else:
                print(f"❌ Lỗi tải model: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi tải model: {e}")
            return False
    
    def load_model(self):
        """Tải và chuẩn bị model"""
        if self.is_loaded:
            return True
        
        print("🔍 Đang kiểm tra Ollama...")
        
        # 1. Kiểm tra Ollama đã cài đặt
        if not self.check_ollama_installed():
            self.install_ollama_guide()
            return False
        
        # 2. Khởi động Ollama service
        if not self.start_ollama_service():
            return False
        
        # 3. Kiểm tra model đã có chưa
        available_models = self.list_available_models()
        model_exists = any(self.model_name in model for model in available_models)
        
        if not model_exists:
            print(f"📥 Model {self.model_name} chưa có, đang tải...")
            
            # Thử các tên model khác nhau
            model_variants = [
                "gemma2:2b",
                "gemma:2b", 
                "gemma2:2b-instruct",
                "gemma:2b-instruct"
            ]
            
            success = False
            for variant in model_variants:
                print(f"🔄 Thử tải {variant}...")
                if self.pull_model(variant):
                    self.model_name = variant
                    success = True
                    break
            
            if not success:
                print("❌ Không thể tải model Gemma")
                print("💡 Các model khả dụng khác:")
                print("   - llama3.2:1b (nhẹ)")
                print("   - llama3.2:3b (trung bình)")
                print("   - qwen2.5:1.5b (nhẹ)")
                return False
        
        # 4. Test model
        print(f"🧪 Đang test model {self.model_name}...")
        test_response = self.get_response("Hello", max_length=50)
        if test_response and "lỗi" not in test_response.lower():
            print("✅ Model đã sẵn sàng!")
            self.is_loaded = True
            return True
        else:
            print("❌ Model không hoạt động đúng")
            return False
    
    def get_response(self, user_message, max_length=200, temperature=0.7):
        """Tạo response từ user message"""
        if not self.is_loaded:
            if not self.load_model():
                return "❌ Model chưa sẵn sàng"
        
        try:
            # Tạo prompt
            prompt = self.create_prompt(user_message)
            
            # Gọi Ollama API
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_length,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                bot_response = result.get("response", "").strip()
                
                # Xử lý response
                bot_response = self.clean_response(bot_response)
                
                return bot_response or "Xin lỗi, tôi không thể tạo phản hồi."
            else:
                return f"❌ Lỗi API: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "⏰ Timeout - Model mất quá nhiều thời gian"
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"
    
    def create_prompt(self, user_message):
        """Tạo prompt cho Gemma"""
        # Prompt đơn giản cho Ollama
        return f"""<start_of_turn>user
{user_message}<end_of_turn>
<start_of_turn>model
"""
    
    def clean_response(self, response):
        """Làm sạch response"""
        # Loại bỏ các tag đặc biệt
        response = response.replace("<start_of_turn>", "")
        response = response.replace("<end_of_turn>", "")
        response = response.replace("model", "").strip()
        
        # Loại bỏ xuống dòng thừa
        response = response.replace("\n\n", "\n").strip()
        
        return response
    
    def get_model_info(self):
        """Lấy thông tin model"""
        info = {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "is_loaded": self.is_loaded,
            "ollama_running": self.ollama_running
        }
        
        # Thêm thông tin system
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                info["available_models"] = len(models)
        except:
            pass
        
        return info
    
    def cleanup(self):
        """Dọn dẹp (không cần thiết cho Ollama)"""
        print("🧹 Ollama model cleanup hoàn tất")
        self.is_loaded = False

# Test function
if __name__ == "__main__":
    print("🧪 Testing Ollama Gemma Model...")
    
    model = OllamaGemmaModel()
    
    try:
        if model.load_model():
            # Test conversation
            test_messages = [
                "Xin chào!",
                "Bạn có thể giúp tôi không?",
                "Hôm nay thời tiết thế nào?"
            ]
            
            for msg in test_messages:
                print(f"\n👤 User: {msg}")
                response = model.get_response(msg)
                print(f"🤖 Bot: {response}")
        else:
            print("❌ Không thể tải model")
            
    except KeyboardInterrupt:
        print("\n👋 Test bị hủy")
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        model.cleanup()