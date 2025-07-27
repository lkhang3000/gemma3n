import psutil
import platform
import logging
from prompt import SYSTEM_PROMPT, CRITICAL_SYMPTOMS, RESPONSE_TEMPLATES

logger = logging.getLogger(__name__)

def _initialize_system(self) -> None:
    """Initialize system with hardware detection"""
    # Hardware capabilities
    self.system_info = {
        "cpu_cores": psutil.cpu_count(logical=False) or 1,
        "ram_gb": psutil.virtual_memory().total / (1024 ** 3),
        "has_avx": self._check_cpu_instructions(),
        "os_type": platform.system()
    }

    # Mode configuration
    if self.mode == "auto":
        self.mode = self._determine_optimal_mode()

    # Privacy notices
    self.mode_details = {
        "local": "All processing occurs on your local device",
        "server": "Responses are processed on a secure server"
    }

    # Initialize conversation
    self.conversation_history = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                critical_list=", ".join(sorted(CRITICAL_SYMPTOMS))
            )
        }
    ]

    logger.info(f"System initialized in {self.mode} mode")

def _check_cpu_instructions(self) -> bool:
    """Verify CPU supports required instructions (AVX)"""
    try:
        import cpuinfo
        cpu_flags = cpuinfo.get_cpu_info().get('flags', [])
        return 'avx' in cpu_flags
    except Exception as e:
        logger.warning(f"CPU check failed: {str(e)}")
        return True  # Assume supported if check fails

def _determine_optimal_mode(self) -> str:
    """Automatically select best operation mode"""
    min_local_requirements = (
        self.system_info["cpu_cores"] >= 4
        and self.system_info["ram_gb"] >= 8
        and self.system_info["has_avx"]
    )
    return "local" if min_local_requirements else "server"

def _warn_if_unsupported_hardware(self) -> None:
    """Notify user about potential performance issues"""
    if self.mode == "local":
        warnings = []
        if self.system_info["cpu_cores"] < 4:
            warnings.append(f"Limited CPU cores ({self.system_info['cpu_cores']}/4 recommended)")
        if self.system_info["ram_gb"] < 8:
            warnings.append(f"Limited RAM ({self.system_info['ram_gb']:.1f}GB/8GB recommended)")
        if not self.system_info["has_avx"]:
            warnings.append("Missing AVX CPU instructions (required for optimal performance)")

        if warnings:
            warning_msg = "⚠️ Offline Mode Performance Warning:\n" + "\n".join(f"- {w}" for w in warnings)
            print(warning_msg)
            if input("Continue with offline mode? (y/n): ").lower() != 'y':
                self.mode = "server"
                print("Switched to server mode")
                logger.info("User opted to switch to server mode due to hardware limitations")
