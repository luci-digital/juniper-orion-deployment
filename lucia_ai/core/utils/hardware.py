"""
Hardware detection and optimization utilities for Lucia AI
Provides universal hardware detection and configuration
"""

import platform
import logging
import psutil
from typing import Dict, Any, Optional
import subprocess
import os

logger = logging.getLogger(__name__)

class HardwareDetector:
    """Detect and configure hardware for optimal inference performance"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get comprehensive system information"""
        system = platform.system()
        machine = platform.machine()
        processor = platform.processor()
        
        # Get CPU info
        cpu_info = {
            "count": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "usage": psutil.cpu_percent(interval=1)
        }
        
        # Get memory info
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_percent": memory.percent
        }
        
        return {
            "system": system,
            "machine": machine,
            "processor": processor,
            "cpu": cpu_info,
            "memory": memory_info
        }
    
    @staticmethod
    def detect_gpu() -> Dict[str, Any]:
        """Detect available GPU hardware"""
        gpu_info = {
            "available": False,
            "type": None,
            "device": "cpu",
            "name": None,
            "memory_gb": None
        }
        
        system = platform.system().lower()
        
        try:
            import torch
            
            # Check for Apple Silicon GPU (Metal)
            if system == "darwin":
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    gpu_info.update({
                        "available": True,
                        "type": "metal",
                        "device": "mps",
                        "name": "Apple Silicon GPU"
                    })
                    
                    # Try to get chip info
                    try:
                        result = subprocess.run(
                            ["sysctl", "-n", "machdep.cpu.brand_string"],
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            gpu_info["name"] = result.stdout.strip()
                    except:
                        pass
            
            # Check for NVIDIA GPU
            elif torch.cuda.is_available():
                gpu_info.update({
                    "available": True,
                    "type": "cuda",
                    "device": "cuda",
                    "name": torch.cuda.get_device_name(0),
                    "memory_gb": round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
                })
            
            # Check for AMD GPU (ROCm)
            elif hasattr(torch, 'hip') and torch.hip.is_available():
                gpu_info.update({
                    "available": True,
                    "type": "rocm",
                    "device": "rocm",
                    "name": "AMD GPU (ROCm)"
                })
                
        except ImportError:
            logger.warning("PyTorch not installed - GPU detection limited")
        except Exception as e:
            logger.error(f"Error detecting GPU: {e}")
        
        return gpu_info
    
    @staticmethod
    def get_optimal_device() -> str:
        """Get the optimal device for inference"""
        gpu_info = HardwareDetector.detect_gpu()
        
        if gpu_info["available"]:
            logger.info(f"Using {gpu_info['type'].upper()} GPU: {gpu_info['name']}")
            return gpu_info["device"]
        else:
            logger.info("No GPU detected, using CPU")
            return "cpu"
    
    @staticmethod
    def get_optimal_batch_size(device: str, model_size_gb: float = 1.0) -> int:
        """Calculate optimal batch size based on available hardware"""
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        if device == "mps":
            # Apple Silicon unified memory - be conservative
            return min(4, int(available_gb / (model_size_gb * 2)))
        elif device == "cuda":
            try:
                import torch
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                return min(8, int(gpu_memory_gb / (model_size_gb * 1.5)))
            except:
                return 4
        else:
            # CPU - very conservative
            return min(2, int(available_gb / (model_size_gb * 3)))
    
    @staticmethod
    def optimize_for_hardware(device: str) -> Dict[str, Any]:
        """Get optimization settings for the detected hardware"""
        settings = {
            "device": device,
            "dtype": "float32",
            "use_flash_attention": False,
            "use_bettertransformer": False,
            "compile_model": False,
            "num_threads": psutil.cpu_count(logical=False)
        }
        
        if device == "mps":
            settings.update({
                "dtype": "float16",
                "use_bettertransformer": True,
                "compile_model": False  # MPS doesn't support torch.compile yet
            })
        elif device == "cuda":
            settings.update({
                "dtype": "float16",
                "use_flash_attention": True,
                "use_bettertransformer": True,
                "compile_model": True
            })
        elif device == "rocm":
            settings.update({
                "dtype": "float16",
                "use_bettertransformer": True,
                "compile_model": False
            })
        
        return settings
    
    @staticmethod
    def check_ollama_availability() -> bool:
        """Check if Ollama is installed and running"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_hardware_report() -> str:
        """Generate a comprehensive hardware report"""
        system_info = HardwareDetector.get_system_info()
        gpu_info = HardwareDetector.detect_gpu()
        optimal_device = HardwareDetector.get_optimal_device()
        
        report = []
        report.append("=" * 60)
        report.append("LUCIA AI - HARDWARE DETECTION REPORT")
        report.append("=" * 60)
        report.append(f"\nSystem: {system_info['system']} ({system_info['machine']})")
        report.append(f"Processor: {system_info['processor']}")
        report.append(f"CPU Cores: {system_info['cpu']['count']} ({system_info['cpu']['threads']} threads)")
        report.append(f"Memory: {system_info['memory']['total_gb']} GB total, {system_info['memory']['available_gb']} GB available")
        
        report.append("\nGPU Information:")
        if gpu_info['available']:
            report.append(f"  Type: {gpu_info['type'].upper()}")
            report.append(f"  Name: {gpu_info['name']}")
            if gpu_info['memory_gb']:
                report.append(f"  Memory: {gpu_info['memory_gb']} GB")
        else:
            report.append("  No GPU detected")
        
        report.append(f"\nOptimal Device: {optimal_device.upper()}")
        
        if HardwareDetector.check_ollama_availability():
            report.append("\nOllama: ✓ Available")
        else:
            report.append("\nOllama: ✗ Not available")
        
        report.append("=" * 60)
        
        return "\n".join(report)

if __name__ == "__main__":
    # Print hardware report when run directly
    print(HardwareDetector.get_hardware_report())