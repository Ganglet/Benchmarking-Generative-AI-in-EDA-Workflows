"""
AST-Based Syntactic Augmentation
Uses Pyverilog to parse and repair Verilog AST
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re

try:
    from pyverilog.vparser.parser import parse
    from pyverilog.ast_code_generator import codegen
    PYVERILOG_AVAILABLE = True
except ImportError:
    PYVERILOG_AVAILABLE = False
    print("⚠ pyverilog not available. Install with: pip install pyverilog")


class ASTRepair:
    """Repairs Verilog code using AST parsing and manipulation"""
    
    def __init__(self, enable_ast: bool = True):
        self.enable_ast = enable_ast and PYVERILOG_AVAILABLE
        if not PYVERILOG_AVAILABLE and enable_ast:
            print("⚠ AST repair disabled: pyverilog not installed")
    
    def parse_verilog(self, code: str) -> Optional[Any]:
        """
        Build AST from Verilog code
        
        Args:
            code: Verilog source code
            
        Returns:
            AST object, or None if parsing fails
        """
        if not self.enable_ast:
            return None
        
        try:
            # Write code to temporary file (Pyverilog needs file input)
            from tempfile import NamedTemporaryFile
            with NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            try:
                ast, directives = parse([temp_path])
                return ast
            finally:
                Path(temp_path).unlink()
                
        except Exception as e:
            print(f"AST parsing error: {e}")
            return None
    
    def validate_ast(self, ast: Any) -> List[str]:
        """
        Check AST structure for common issues
        
        Args:
            ast: AST object from parse_verilog
            
        Returns:
            List of identified issues
        """
        if ast is None:
            return ["AST parsing failed"]
        
        issues = []
        
        try:
            # Check for module declaration
            if not hasattr(ast, 'description'):
                issues.append("No module found in AST")
                return issues
            
            # Traverse AST to find issues
            # This is a simplified check - full implementation would traverse the tree
            if hasattr(ast, 'description'):
                desc = ast.description
                if hasattr(desc, 'definitions'):
                    for defn in desc.definitions:
                        if hasattr(defn, 'name'):
                            # Check module name
                            pass
                        if hasattr(defn, 'portlist'):
                            # Check ports
                            if defn.portlist is None:
                                issues.append("Module missing port list")
        
        except Exception as e:
            issues.append(f"AST validation error: {e}")
        
        return issues
    
    def repair_ast(self, ast: Any, errors: List[str]) -> Optional[Any]:
        """
        Apply AST-level fixes based on errors
        
        Args:
            ast: AST object
            errors: List of error messages or issues
            
        Returns:
            Repaired AST, or None if repair fails
        """
        if ast is None:
            return None
        
        # Note: Full AST manipulation is complex
        # This is a placeholder for AST repair logic
        # In practice, you would:
        # 1. Identify missing ports and add them
        # 2. Fix incorrect assignments
        # 3. Add missing always blocks
        # 4. Fix signal declarations
        
        # For now, return original AST
        # Full implementation would require deep AST manipulation
        return ast
    
    def regenerate_code(self, ast: Any) -> Optional[str]:
        """
        Convert repaired AST back to Verilog code
        
        Args:
            ast: AST object
            
        Returns:
            Regenerated Verilog code, or None if fails
        """
        if ast is None:
            return None
        
        try:
            from pyverilog.ast_code_generator import codegen
            return codegen(ast)
        except Exception as e:
            print(f"Code generation error: {e}")
            return None
    
    def repair_with_ast(self, code: str, errors: List[str]) -> Optional[str]:
        """
        Complete AST-based repair workflow
        
        Args:
            code: Original Verilog code
            errors: Compilation or validation errors
            
        Returns:
            Repaired code, or None if AST repair fails
        """
        if not self.enable_ast:
            return None
        
        # Parse to AST
        ast = self.parse_verilog(code)
        if ast is None:
            return None
        
        # Validate
        issues = self.validate_ast(ast)
        
        # Repair
        repaired_ast = self.repair_ast(ast, errors + issues)
        if repaired_ast is None:
            return None
        
        # Regenerate
        repaired_code = self.regenerate_code(repaired_ast)
        return repaired_code

