"""
Formal Verification Integration
Uses Yosys equiv_check for logic equivalence verification
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional, List
import re


class FormalVerifier:
    """Performs formal equivalence checking using Yosys"""
    
    def __init__(self, enable_verification: bool = False):
        self.enable_verification = enable_verification
        self.yosys_available = self._check_yosys()
    
    def _check_yosys(self) -> bool:
        """Check if Yosys is available"""
        try:
            result = subprocess.run(
                ["yosys", "-V"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def equiv_check(
        self,
        ref_hdl: Path,
        gen_hdl: Path,
        output_dir: Path,
        timeout: int = 60
    ) -> Dict[str, any]:
        """
        Run Yosys equivalence check
        
        Args:
            ref_hdl: Path to reference HDL
            gen_hdl: Path to generated HDL
            output_dir: Directory for output files
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with equivalence status and report
        """
        if not self.enable_verification or not self.yosys_available:
            return {
                "status": "skipped",
                "reason": "Formal verification disabled or Yosys not available",
                "equivalent": None
            }
        
        try:
            # Create Yosys script for equivalence check
            script = f"""
# Read both designs
read_verilog {ref_hdl}
hierarchy -top -check
proc; opt; fsm; opt; memory; opt
rename -top ref_design

read_verilog {gen_hdl}
hierarchy -top -check
proc; opt; fsm; opt; memory; opt
rename -top gen_design

# Equivalence check
equiv_make ref_design gen_design equiv
equiv_simple -seq 10
equiv_status -assert
"""
            script_file = output_dir / "equiv_check.ys"
            script_file.write_text(script)
            
            # Run Yosys
            result = subprocess.run(
                ["yosys", "-s", str(script_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(output_dir)
            )
            
            # Parse output
            report_path = output_dir / "equiv_report.txt"
            report_path.write_text(result.stdout + "\n" + result.stderr)
            
            return self.parse_equiv_report(result.stdout, result.stderr)
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "equivalent": None,
                "errors": ["Equivalence check timed out"]
            }
        except Exception as e:
            return {
                "status": "error",
                "equivalent": None,
                "errors": [str(e)]
            }
    
    def parse_equiv_report(
        self,
        stdout: str,
        stderr: str
    ) -> Dict[str, any]:
        """
        Extract equivalence status from Yosys output
        
        Args:
            stdout: Standard output from Yosys
            stderr: Standard error from Yosys
            
        Returns:
            Dictionary with parsed results
        """
        output = stdout + "\n" + stderr
        
        result = {
            "status": "unknown",
            "equivalent": None,
            "counterexamples": [],
            "errors": []
        }
        
        # Check for equivalence status
        if "Equivalence successfully proven" in output or "Proved" in output:
            result["status"] = "proven"
            result["equivalent"] = True
        elif "Found counterexample" in output or "Counterexample" in output:
            result["status"] = "counterexample"
            result["equivalent"] = False
            # Extract counterexample details
            counterexample_match = re.search(
                r'Counterexample[:\s]+(.*?)(?:\n|$)',
                output,
                re.IGNORECASE | re.DOTALL
            )
            if counterexample_match:
                result["counterexamples"].append(counterexample_match.group(1))
        elif "Error" in output or "error" in stderr:
            result["status"] = "error"
            # Extract error messages
            error_lines = [line for line in stderr.split('\n') if 'error' in line.lower()]
            result["errors"] = error_lines[:5]
        else:
            result["status"] = "inconclusive"
        
        return result
    
    def suggest_fixes(self, counterexample: Dict) -> List[str]:
        """
        Convert Yosys counterexample to actionable repair hints
        
        Args:
            counterexample: Counterexample data from parse_equiv_report
            
        Returns:
            List of repair suggestions
        """
        hints = []
        
        if counterexample.get("status") == "counterexample":
            hints.append("Logic equivalence check failed - design behavior differs from reference")
            
            if counterexample.get("counterexamples"):
                hints.append("Review counterexample to identify incorrect signal behavior")
        
        elif counterexample.get("status") == "error":
            errors = counterexample.get("errors", [])
            for error in errors[:3]:
                if "syntax" in error.lower():
                    hints.append("Syntax error detected during formal verification")
                elif "port" in error.lower():
                    hints.append("Port mismatch between reference and generated design")
        
        return hints

