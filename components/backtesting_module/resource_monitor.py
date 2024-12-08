# components/backtesting_module/resource_monitor.py

import psutil
import logging

class ResourceMonitor:
    """
    Simple resource monitoring to prevent system overload during backtesting.
    """
    
    @staticmethod
    def check_resources():
        """
        Checks if system has enough resources for backtesting.
        """
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80 or memory_percent > 80:
            logging.warning(f"System resources stressed: CPU {cpu_percent}%, Memory {memory_percent}%")
            raise ResourceWarning("System resources are too constrained for backtesting")
            
        return True

    @staticmethod
    def get_resource_usage():
        """
        Returns current resource usage statistics.
        """
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }