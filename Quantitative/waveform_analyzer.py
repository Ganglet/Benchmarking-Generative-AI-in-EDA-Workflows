"""
VCD Waveform Analysis Module
Handles VCD file generation, parsing, and comparison for semantic repair
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

try:
    # Try different VCD parsing approaches
    try:
        import vcd
        PYVCD_AVAILABLE = True
        VCD_MODULE = vcd
    except ImportError:
        try:
            from pyvcd import vcd as vcd_module
            PYVCD_AVAILABLE = True
            VCD_MODULE = vcd_module
        except ImportError:
            PYVCD_AVAILABLE = False
            VCD_MODULE = None
except Exception:
    PYVCD_AVAILABLE = False
    VCD_MODULE = None

if not PYVCD_AVAILABLE:
    print("⚠ VCD parsing not available. Install with: pip install pyvcd")


class WaveformAnalyzer:
    """Analyzes VCD waveforms to identify logic mismatches"""
    
    def __init__(self, enable_vcd: bool = True):
        self.enable_vcd = enable_vcd and PYVCD_AVAILABLE
        if not PYVCD_AVAILABLE and enable_vcd:
            print("⚠ Waveform analysis disabled: pyvcd not installed")
    
    def generate_vcd(
        self, 
        testbench_path: Path, 
        hdl_path: Path, 
        output_dir: Path,
        timeout: int = 30
    ) -> Optional[Path]:
        """
        Run iverilog simulation with VCD dump enabled
        
        Args:
            testbench_path: Path to testbench file
            hdl_path: Path to HDL file
            output_dir: Directory for output files
            timeout: Timeout in seconds
            
        Returns:
            Path to generated VCD file, or None if failed
        """
        if not self.enable_vcd:
            return None
        
        vcd_path = output_dir / "waveform.vcd"
        
        try:
            # Compile with testbench
            compile_result = subprocess.run(
                ["iverilog", "-o", str(output_dir / "sim.vvp"),
                 str(hdl_path), str(testbench_path)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if compile_result.returncode != 0:
                return None
            
            # Run simulation (VCD dump should be in testbench via $dumpvars)
            sim_result = subprocess.run(
                ["vvp", str(output_dir / "sim.vvp")],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(output_dir)
            )
            
            # Check if VCD file was created
            if vcd_path.exists():
                return vcd_path
            else:
                # Try to find VCD file with different name
                vcd_files = list(output_dir.glob("*.vcd"))
                if vcd_files:
                    return vcd_files[0]
                return None
                
        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"Error generating VCD: {e}")
            return None
    
    def load_vcd(self, vcd_path: Path) -> Optional[Dict]:
        """
        Parse VCD file using pyvcd
        
        Args:
            vcd_path: Path to VCD file
            
        Returns:
            Dictionary with signal data, or None if failed
        """
        if not self.enable_vcd or not vcd_path.exists():
            return None
        
        try:
            # Parse VCD file - simple text-based parser
            vcd_data = {}
            with open(vcd_path, 'r') as f:
                content = f.read()
            
            # VCD parser - handles $var declarations and value changes
            lines = content.split('\n')
            signal_codes = {}  # Map code -> signal_name
            signal_data = {}   # Map signal_name -> list of (time, value)
            current_time = 0
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Parse $var declaration: $var wire 1 ! signal_name $end
                if line.startswith('$var'):
                    parts = line.split()
                    if len(parts) >= 5:
                        signal_code = parts[3]  # Code like '!', '$', etc.
                        signal_name = parts[4]   # Signal name
                        signal_codes[signal_code] = signal_name
                        signal_data[signal_name] = []
                
                # Parse time stamp: #time
                elif line.startswith('#'):
                    time_match = re.match(r'#(\d+)', line)
                    if time_match:
                        current_time = int(time_match.group(1))
                        # Next lines contain value changes until next # or $end
                        i += 1
                        while i < len(lines):
                            value_line = lines[i].strip()
                            if not value_line or value_line.startswith('$') or value_line.startswith('#'):
                                i -= 1  # Back up one line
                                break
                            
                            # Parse value change: value_code or bvalue code
                            # Single bit: 0!, 1$, etc. or Multi-bit: b1010 code
                            if value_line.startswith('b'):
                                match = re.match(r'b([01xXzZ]+)\s+(\S+)', value_line)
                                if match:
                                    value = match.group(1)
                                    code = match.group(2)
                                    if code in signal_codes:
                                        signal_name = signal_codes[code]
                                        signal_data[signal_name].append((current_time, value))
                            else:
                                # Single bit value: 0code or 1code
                                match = re.match(r'([01xXzZ])(\S+)', value_line)
                                if match:
                                    value = match.group(1)
                                    code = match.group(2)
                                    if code in signal_codes:
                                        signal_name = signal_codes[code]
                                        signal_data[signal_name].append((current_time, value))
                            
                            i += 1
                
                i += 1
            
            # Convert to dict format with sorted data
            for signal_name, data in signal_data.items():
                if data:
                    vcd_data[signal_name] = sorted(data, key=lambda x: x[0])
            
            return vcd_data if vcd_data else None
            
        except Exception as e:
            print(f"Error loading VCD: {e}")
            return None
    
    def compare_waveforms(
        self, 
        ref_vcd: Dict, 
        gen_vcd: Dict
    ) -> Dict[str, List[Tuple[int, str, str]]]:
        """
        Compare two waveforms to identify mismatches
        
        Args:
            ref_vcd: Reference waveform data
            gen_vcd: Generated waveform data
            
        Returns:
            Dictionary mapping signal names to list of (time, ref_value, gen_value) mismatches
        """
        mismatches = {}
        
        # Compare common signals
        common_signals = set(ref_vcd.keys()) & set(gen_vcd.keys())
        
        for signal in common_signals:
            ref_data = dict(ref_vcd[signal])
            gen_data = dict(gen_vcd[signal])
            
            # Find all time points
            all_times = set(ref_data.keys()) | set(gen_data.keys())
            
            signal_mismatches = []
            for time in sorted(all_times):
                ref_val = ref_data.get(time, "X")
                gen_val = gen_data.get(time, "X")
                
                if ref_val != gen_val:
                    signal_mismatches.append((time, ref_val, gen_val))
            
            if signal_mismatches:
                mismatches[signal] = signal_mismatches
        
        return mismatches
    
    def identify_logic_mismatches(
        self, 
        diff_result: Dict[str, List[Tuple[int, str, str]]]
    ) -> List[str]:
        """
        Analyze waveform differences to suggest fixes
        
        Args:
            diff_result: Output from compare_waveforms()
            
        Returns:
            List of repair hints (e.g., "enable signal inverted", "missing state transition")
        """
        hints = []
        
        for signal, mismatches in diff_result.items():
            if not mismatches:
                continue
            
            # Analyze mismatch patterns
            ref_values = [m[1] for m in mismatches]
            gen_values = [m[2] for m in mismatches]
            
            # Check for inverted signal
            if len(set(ref_values)) == 2 and len(set(gen_values)) == 2:
                if set(ref_values) == set(gen_values):
                    # Values are swapped - likely inverted
                    hints.append(f"Signal '{signal}' may be inverted (enable/disable logic)")
            
            # Check for missing transitions
            ref_transitions = len([i for i in range(1, len(ref_values)) if ref_values[i] != ref_values[i-1]])
            gen_transitions = len([i for i in range(1, len(gen_values)) if gen_values[i] != gen_values[i-1]])
            
            if ref_transitions > gen_transitions:
                hints.append(f"Signal '{signal}' missing {ref_transitions - gen_transitions} transition(s)")
            
            # Check for constant vs changing
            if len(set(ref_values)) > 1 and len(set(gen_values)) == 1:
                hints.append(f"Signal '{signal}' is constant but should change")
            
            # Check for wrong initial value
            if mismatches and mismatches[0][1] != mismatches[0][2]:
                hints.append(f"Signal '{signal}' has wrong initial value")
        
        return hints
    
    def inject_vcd_dump(self, testbench_path: Path, output_path: Path) -> bool:
        """
        Inject $dumpvars into testbench if not present
        
        Args:
            testbench_path: Original testbench
            output_path: Path to write modified testbench
            
        Returns:
            True if successful
        """
        try:
            content = testbench_path.read_text()
            
            # Check if $dumpvars already exists
            if "$dumpvars" in content or "$dumpfile" in content:
                # Already has VCD dump
                output_path.write_text(content)
                return True
            
            # Find initial block or add one
            if "initial begin" in content:
                # Add dumpvars after initial begin
                content = content.replace(
                    "initial begin",
                    "initial begin\n    $dumpfile(\"waveform.vcd\");\n    $dumpvars(0, dut);"
                )
            else:
                # Add initial block at the beginning
                content = "initial begin\n    $dumpfile(\"waveform.vcd\");\n    $dumpvars(0, dut);\nend\n\n" + content
            
            output_path.write_text(content)
            return True
            
        except Exception as e:
            print(f"Error injecting VCD dump: {e}")
            return False

