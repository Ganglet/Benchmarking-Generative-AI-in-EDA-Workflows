"""
Phase 5 Micro-Repair Engine
Automated fixes that run BEFORE GPT invocation to reduce model workload
These repairs are deterministic and fix common syntax errors
"""

import re
from typing import Optional


class Phase5Repair:
    """
    Micro-repair engine for FSM and Mixed designs
    
    PRE-REPAIR (before GPT): Mechanical text fixes
    - Fix model's generation stupidities (stray end, obvious syntax violations)
    - Simple regex-based fixes that don't require AST parsing
    
    POST-REPAIR (after GPT): AST-level structural fixes  
    - Fix structural violations (multi-statement case items, begin/end placement)
    - Requires AST parsing and understanding of code structure
    - Handled by post_process_verilog() in run_phase2.py
    
    This module handles PRE-REPAIR only.
    """
    
    def __init__(self):
        pass
    
    def repair_before_generation(self, code: str, category: str) -> str:
        """
        Apply PRE-REPAIR (mechanical text fixes) BEFORE passing code to GPT.
        These fixes are deterministic, regex-based, and don't require AI or AST parsing.
        
        PRE-REPAIR RULES:
        - Fix stray 'end' in case items (text pattern matching)
        - Remove obvious syntax violations (model's generation stupidities)
        - Simple text replacements that don't require structural understanding
        
        POST-REPAIR (handled elsewhere):
        - Multi-statement case item begin/end wrapping (requires AST)
        - Structural begin/end placement (requires AST)
        - Next_state relocation (requires AST)
        
        Args:
            code: Generated Verilog code
            category: Task category ('fsm', 'mixed', 'sequential', 'combinational')
            
        Returns:
            Repaired code
        """
        repaired = code
        
        if category == 'fsm':
            repaired = self._repair_fsm_pre(repaired)
        elif category == 'mixed':
            repaired = self._repair_mixed_pre(repaired)
        
        return repaired
    
    def _repair_fsm_pre(self, code: str) -> str:
        """
        PRE-REPAIR: FSM-specific mechanical text fixes
        Only fixes that don't require AST parsing or structural understanding
        """
        lines = code.split('\n')
        repaired_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # PRE-REPAIR FIX 1: Remove stray 'end' inside case items (simple text pattern)
            # Pattern: case_label: statement; end (stray end)
            if re.search(r'\d+\'b\d+:\s*.*;\s*end\s*$', line):
                # Remove the stray 'end'
                line = re.sub(r';\s*end\s*$', ';', line)
            
            # PRE-REPAIR FIX 2: Fix obvious syntax violations (model's generation stupidities)
            # This is kept minimal - structural fixes go to post-repair
            
            repaired_lines.append(line)
            i += 1
        
        return '\n'.join(repaired_lines)
    
    def _repair_mixed_pre(self, code: str) -> str:
        """
        PRE-REPAIR: Mixed design-specific mechanical text fixes
        Only fixes that don't require AST parsing or structural understanding
        """
        lines = code.split('\n')
        repaired_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # PRE-REPAIR FIX 1: Regex to fix "2'b00: result = a + b; end" pattern
            # Pattern: case_item with stray 'end' inside (mechanical text fix)
            if re.search(r'\d+\'b\d+:\s*.*;\s*end\s*$', line):
                # Remove the stray 'end' - simple text replacement
                line = re.sub(r';\s*end\s*$', ';', line)
            
            # PRE-REPAIR FIX 2: Remove stray 'end' that appears standalone in case blocks
            # This is a model generation stupidity - simple text fix
            if re.search(r'^\s*end\s*$', line) and i > 0:
                prev_line = lines[i-1].strip() if i > 0 else ""
                # If previous line is a case item label, this is a stray end
                if re.search(r'\d+\'b\d+:\s*$', prev_line) or re.search(r'\w+:\s*$', prev_line):
                    i += 1
                    continue
            
            # Multi-statement case item wrapping → POST-REPAIR (requires AST)
            # Default assignment injection → POST-REPAIR (requires structural understanding)
            # Case structure fixes → POST-REPAIR (requires AST)
            
            # Find case statement for reference but don't fix here (post-repair handles it)
            if re.search(r'\bcase\s*\(', line, re.IGNORECASE):
                case_start = i
                # Find endcase
                case_end = i
                depth = 0
                for j in range(i, len(lines)):
                    if 'begin' in lines[j]:
                        depth += 1
                    if 'end' in lines[j]:
                        depth -= 1
                    if 'endcase' in lines[j].lower() and depth == 0:
                        case_end = j
                        break
                
                # Multi-statement case item wrapping handled by POST-REPAIR (requires AST)
                # Skip to endcase
                repaired_lines.append(line)  # case line
                i += 1
                while i < case_end:
                    repaired_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    repaired_lines.append(lines[i])  # endcase
                i += 1
                continue
            
            repaired_lines.append(line)
            i += 1
        
        return '\n'.join(repaired_lines)
    
    def detect_fsm_issues(self, code: str) -> list:
        """Detect common FSM issues for feedback generation - TOP 3 TRIGGERS ONLY"""
        issues = []
        
        # TOP 3 TRIGGER 1: Check if case is outside always block
        if re.search(r'\bcase\s*\(', code, re.IGNORECASE):
            case_positions = [m.start() for m in re.finditer(r'\bcase\s*\(', code, re.IGNORECASE)]
            for pos in case_positions:
                before_case = code[:pos]
                if not re.search(r'always', before_case, re.IGNORECASE):
                    issues.append("case_outside_always")
                    break
        
        # TOP 3 TRIGGER 2: Check if next_state assigned in always_ff
        if re.search(r'next_state\s*[<=]=', code, re.IGNORECASE):
            # Find all next_state assignments
            next_state_positions = [m.start() for m in re.finditer(r'next_state\s*[<=]=', code, re.IGNORECASE)]
            for pos in next_state_positions:
                # Look backwards for always_ff
                before_assign = code[:pos]
                if re.search(r'always_ff', before_assign, re.IGNORECASE) and not re.search(r'always_comb', before_assign, re.IGNORECASE):
                    issues.append("next_state_in_always_ff")
                    break
        
        # TOP 3 TRIGGER 3: Check for missing begin/end in multi-statement case items
        case_blocks = list(re.finditer(r'\bcase\s*\(', code, re.IGNORECASE))
        for match in case_blocks:
            after_case = code[match.end():]
            endcase_pos = after_case.find('endcase')
            if endcase_pos > 0:
                case_body = after_case[:endcase_pos]
                # Check if case items have multiple statements without begin/end
                lines = case_body.split('\n')
                for i, line in enumerate(lines):
                    if re.search(r'^\s*\d+\'b\d+:\s*|^\s*\w+:\s*', line):  # Case item label
                        # Count statements in this item (until next label or endcase)
                        statements = 0
                        for j in range(i+1, len(lines)):
                            if re.search(r'^\s*\d+\'b\d+:\s*|^\s*\w+:\s*|^\s*default:\s*|^\s*endcase', lines[j]):
                                break
                            if lines[j].strip() and not lines[j].strip().startswith('//'):
                                statements += 1
                        if statements > 1 and 'begin' not in case_body[max(0, i-5):i+20]:
                            issues.append("missing_begin_end_case")
                            break
        
        return issues[:3]  # Return top 3 only
    
    def detect_mixed_issues(self, code: str) -> list:
        """Detect common Mixed design issues for feedback generation - TOP 3 TRIGGERS ONLY"""
        issues = []
        
        # TOP 3 TRIGGER 1: Check for stray 'end' in case items
        if re.search(r'\d+\'b\d+:\s*.*;\s*end\s*$', code, re.MULTILINE):
            issues.append("stray_end_in_case_item")
        
        # TOP 3 TRIGGER 2: Check for multi-statement case items without begin/end
        lines = code.split('\n')
        in_case = False
        
        for i, line in enumerate(lines):
            if re.search(r'\bcase\s*\(', line, re.IGNORECASE):
                in_case = True
            elif 'endcase' in line.lower():
                in_case = False
            elif in_case and re.search(r'^\s*\d+\'b\d+:\s*', line):  # Case item label
                # Count statements in this item
                statements = 0
                for j in range(i+1, len(lines)):
                    if re.search(r'^\s*\d+\'b\d+:\s*|^\s*\w+:\s*|^\s*default:\s*|^\s*endcase', lines[j]):
                        break
                    if lines[j].strip() and not lines[j].strip().startswith('//'):
                        statements += 1
                # Check if multi-statement and missing begin/end
                if statements > 1:
                    # Look for begin in this item
                    item_text = '\n'.join(lines[i:i+statements+2])
                    if 'begin' not in item_text.lower():
                        issues.append("missing_begin_end_case")
                        break
        
        # TOP 3 TRIGGER 3: Check for missing default assignment
        if re.search(r'\bcase\s*\(', code, re.IGNORECASE):
            # Check if result/output is initialized before case
            case_match = re.search(r'\bcase\s*\(', code, re.IGNORECASE)
            if case_match:
                before_case = code[:case_match.start()]
                # Check for default assignment
                if not re.search(r'(result|output)\s*=\s*', before_case, re.IGNORECASE):
                    # Check if default case exists
                    after_case = code[case_match.end():]
                    endcase_pos = after_case.find('endcase')
                    if endcase_pos > 0:
                        case_body = after_case[:endcase_pos]
                        if 'default' not in case_body:
                            issues.append("missing_default_assignment")
        
        return issues[:3]  # Return top 3 only

