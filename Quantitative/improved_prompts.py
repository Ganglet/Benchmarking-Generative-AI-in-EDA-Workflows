"""
Improved Prompt Engineering for HDL Generation

Different prompt strategies to test:
- Few-shot with examples
- Chain-of-thought reasoning
- Strict formatting rules
- Syntax-aware prompts
"""

def get_few_shot_prompt(specification: str) -> str:
    """
    Few-shot learning: Provide examples before the task
    """
    return f"""You are a Verilog HDL expert. Generate synthesizable Verilog-2001 code.

Here are examples of CORRECT Verilog modules:

Example 1 - Simple Logic:
module or_gate(input wire a, input wire b, output wire y);
    assign y = a | b;
endmodule

Example 2 - Multi-bit:
module adder_4bit(input wire [3:0] a, input wire [3:0] b, output wire [3:0] sum, output wire carry);
    wire [4:0] temp;
    assign temp = a + b;
    assign sum = temp[3:0];
    assign carry = temp[4];
endmodule

Example 3 - Sequential:
module dff(input wire clk, input wire rst, input wire d, output reg q);
    always @(posedge clk) begin
        if (rst)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule

Now generate Verilog for this specification:
{specification}

Requirements:
- Start with 'module' keyword
- End with 'endmodule'
- Use 'wire' with 'assign' for combinational logic
- Use 'reg' with 'always @' for sequential logic
- No code outside module definition
- Use only standard Verilog syntax

Verilog code:
"""


def get_constrained_prompt(specification: str) -> str:
    """
    Highly constrained prompt with strict rules
    """
    return f"""Generate ONLY synthesizable Verilog code. Follow these rules EXACTLY:

SPECIFICATION: {specification}

MANDATORY RULES:
1. Start with: module <name>(
2. Declare all ports with 'input wire' or 'output wire'
3. For combinational logic, use ONLY 'assign' statements
4. For sequential logic, use 'output reg' and 'always @(posedge clk)'
5. End with: endmodule
6. NO explanations, NO comments, NO text outside the module
7. Use ONLY these operators: &, |, ^, ~, +, -, ==, !=, <, >, <=, >=, ? :
8. NO 'integer', NO 'sub-operation', NO invented keywords

CORRECT FORMAT:
module <name>(<ports>);
    <logic>
endmodule

Generate ONLY the Verilog module now:
"""


def get_chain_of_thought_prompt(specification: str) -> str:
    """
    Ask model to reason step-by-step
    """
    return f"""You are a Verilog expert. Design the following circuit step-by-step.

SPECIFICATION: {specification}

Think through this systematically:

Step 1: What are the inputs and outputs?
Step 2: Is this combinational or sequential logic?
Step 3: What Verilog constructs should you use?
  - Combinational → use 'wire' + 'assign'
  - Sequential → use 'reg' + 'always @(posedge clk)'
Step 4: Write the module.

Now provide ONLY the final Verilog code (no explanations):
"""


def get_syntax_corrected_prompt(specification: str) -> str:
    """
    Emphasize common mistakes to avoid
    """
    return f"""Generate Verilog code for: {specification}

CRITICAL - AVOID THESE COMMON MISTAKES:
❌ Do NOT use 'sub-operation' (not a real keyword)
❌ Do NOT put code outside module...endmodule
❌ Do NOT use 'integer' in synthesizable code
❌ Do NOT use 'reg' with 'assign'
❌ Do NOT use 'if-else' outside 'always' blocks

✓ DO use 'assign' for combinational outputs
✓ DO declare ports as 'input wire' or 'output wire'
✓ DO keep all code inside the module
✓ DO use standard Verilog-2001 syntax only

Generate clean, valid Verilog code:
"""


def get_minimal_prompt(specification: str) -> str:
    """
    Minimal, direct prompt
    """
    return f"""Write valid Verilog-2001 code for: {specification}

Use proper syntax. Output ONLY the module code.
"""


def get_structured_prompt(specification: str, inputs: list, outputs: list) -> str:
    """
    Provide structure explicitly
    """
    input_decls = ", ".join([f"input wire {inp}" for inp in inputs])
    output_decls = ", ".join([f"output wire {out}" for out in outputs])
    
    return f"""Complete this Verilog module:

module design(
    {input_decls},
    {output_decls}
);
    // Your logic here to implement: {specification}
    // Use only 'assign' statements for combinational logic
endmodule

Provide the completed module:
"""


# Prompt comparison test
PROMPT_STRATEGIES = {
    "original": lambda spec: f"Generate Verilog code for: {spec}",
    "few_shot": get_few_shot_prompt,
    "constrained": get_constrained_prompt,
    "chain_of_thought": get_chain_of_thought_prompt,
    "syntax_corrected": get_syntax_corrected_prompt,
    "minimal": get_minimal_prompt,
    "structured": get_structured_prompt
}


def get_prompt(specification: str, strategy: str = "few_shot", **kwargs) -> str:
    """
    Get prompt using specified strategy
    
    Args:
        specification: Circuit description
        strategy: One of the PROMPT_STRATEGIES keys
        **kwargs: Additional args (e.g., inputs, outputs for structured)
    
    Returns:
        Formatted prompt string
    """
    if strategy not in PROMPT_STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy}. Choose from {list(PROMPT_STRATEGIES.keys())}")
    
    prompt_func = PROMPT_STRATEGIES[strategy]
    
    # Handle structured prompt which needs inputs/outputs
    if strategy == "structured" and "inputs" in kwargs and "outputs" in kwargs:
        return prompt_func(specification, kwargs["inputs"], kwargs["outputs"])
    elif strategy == "structured":
        # Fall back to few_shot if inputs/outputs not provided
        return get_few_shot_prompt(specification)
    else:
        return prompt_func(specification)


# Testing code
if __name__ == "__main__":
    test_spec = "Design a 2-bit binary adder with inputs a[1:0], b[1:0] and outputs sum[1:0], carry_out"
    
    print("=" * 70)
    print("PROMPT STRATEGY COMPARISON")
    print("=" * 70)
    
    for strategy_name in PROMPT_STRATEGIES:
        print(f"\n{'='*70}")
        print(f"Strategy: {strategy_name.upper()}")
        print(f"{'='*70}")
        
        if strategy_name == "structured":
            prompt = get_prompt(test_spec, strategy_name, 
                              inputs=["a[1:0]", "b[1:0]"], 
                              outputs=["sum[1:0]", "carry_out"])
        else:
            prompt = get_prompt(test_spec, strategy_name)
        
        print(prompt)
        print()

