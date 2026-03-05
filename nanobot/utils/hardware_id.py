"""Hardware ID generation for unique device identification."""

import hashlib
import platform
import subprocess
import uuid
from typing import Optional


def get_hardware_id() -> str:
    """Generate a unique hardware ID based on system information."""
    try:
        # Collect system identifiers
        identifiers = []
        
        # MAC address (most reliable)
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            identifiers.append(f"mac:{mac}")
        except:
            pass
        
        # System information
        identifiers.append(f"platform:{platform.platform()}")
        identifiers.append(f"machine:{platform.machine()}")
        identifiers.append(f"processor:{platform.processor()}")
        
        # Try to get additional hardware info
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['system_profiler', 'SPHardwareDataType', '-json'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    import json
                    data = json.loads(result.stdout)
                    serial = data.get('SPHardwareDataType', [{}])[0].get('serial_number')
                    if serial:
                        identifiers.append(f"serial:{serial}")
        except:
            pass
        
        # Create hash from all identifiers
        combined = '|'.join(identifiers)
        hardware_id = hashlib.sha256(combined.encode()).hexdigest()[:16]
        
        return hardware_id
        
    except Exception as e:
        # Fallback to a simple UUID if all else fails
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]


def get_device_fingerprint() -> dict:
    """Get detailed device fingerprint for debugging."""
    return {
        "hardware_id": get_hardware_id(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "node": uuid.getnode()
    }


if __name__ == "__main__":
    print(f"Hardware ID: {get_hardware_id()}")
    print(f"Fingerprint: {get_device_fingerprint()}")
