
import psutil
import platform
import threading
import logging

from back_end.chatbot_backend import SYSTEM_PROMPT, CRITICAL_SYMPTOMS, RESPONSE_TEMPLATES, REASSURE_SENTENCES

logger = logging.getLogger(__name__)


def _initialize_async(self) -> None:
        """Initialize system in background thread"""
        def init_worker():
            try:
                self.status_callback("Initializing system...")
                self.progress_callback(0.1)
                
                # Hardware capabilities
                self.status_callback("Checking hardware capabilities...")
                self.system_info = {
                    "cpu_cores": psutil.cpu_count(logical=False) or 1,
                    "ram_gb": psutil.virtual_memory().total / (1024 ** 3),
                    "has_avx": self._check_cpu_instructions(),
                    "os_type": platform.system()
                }
                self.progress_callback(0.4)

                # Using local mode with gemma:2b model
                self.status_callback(f"Using local model: {self.current_model}")
                self.progress_callback(0.6)

                # Privacy notices
                self.mode_details = {
                    "local": "All processing occurs on your local device"
                }

                # Initialize conversation
                self.status_callback("Setting up conversation...")
                self.conversation_history = [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT.format(
                            critical_list=", ".join(sorted(CRITICAL_SYMPTOMS)),
                            reassure_sentences=", ".join(sorted(REASSURE_SENTENCES))
                        )
                    }
                ]
                self.progress_callback(0.8)

                # Test local model
                self.status_callback("Testing local model...")
                self._test_local_model()
                self.progress_callback(1.0)
                
                self.is_initialized = True
                self.status_callback(f"Ready in {self.mode} mode with {self.current_model}")
                logger.info(f"GUI System initialized in {self.mode} mode with model {self.current_model}")
                
            except Exception as e:
                self.status_callback(f"Initialization failed: {str(e)}")
                logger.error(f"Initialization error: {str(e)}")

        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()

def _check_cpu_instructions(self) -> bool:
    """Verify CPU supports required instructions (AVX)"""
    try:
        import cpuinfo
        cpu_flags = cpuinfo.get_cpu_info().get('flags', [])
        return 'avx' in cpu_flags
    except Exception as e:
        logger.warning(f"CPU check failed: {str(e)}")
        return True 
    
def _determine_optimal_mode(self) -> str:
    """Automatically select best operation mode"""
    min_local_requirements = (
        self.system_info["cpu_cores"] >= 4
        and self.system_info["ram_gb"] >= 8
        and self.system_info["has_avx"]
    )
    return "local" if min_local_requirements else "server"

def _warn_if_unsupported_hardware(self) -> None:
    """Notify user about potential performance issues via GUI"""
    if self.mode == "local":
        warnings = []
        if self.system_info["cpu_cores"] < 4:
            warnings.append(f"Limited CPU cores ({self.system_info['cpu_cores']}/4 recommended)")
        if self.system_info["ram_gb"] < 8:
            warnings.append(f"Limited RAM ({self.system_info['ram_gb']:.1f}GB/8GB recommended)")
        if not self.system_info["has_avx"]:
            warnings.append("Missing AVX CPU instructions (required for optimal performance)")

        if warnings:
            warning_msg = "Performance warnings detected:\n" + "\n".join(f"- {w}" for w in warnings)
            self.status_callback(warning_msg)
            logger.warning(f"Hardware limitations detected: {warnings}")