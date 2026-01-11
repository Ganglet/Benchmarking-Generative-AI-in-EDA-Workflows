"""
AI Model Interface for HDL Generation
Supports Ollama (local) and HuggingFace Transformers
"""

import json
import os
import time
import requests
from typing import Optional, Dict, Tuple, List
from pathlib import Path

class OllamaInterface:
    """Interface for Ollama local models (Llama3, TinyLlama, etc.)"""
    
    def __init__(self, model_name: str, base_url: Optional[str] = None):
        """
        Initialize Ollama interface
        
        Args:
            model_name: Name of model (e.g., 'llama3', 'tinyllama')
            base_url: Ollama API endpoint (defaults to OLLAMA_BASE_URL env var or http://localhost:11434)
                     For Docker: use http://host.docker.internal:11434 (Windows/Mac) or host IP (Linux)
        """
        self.model_name = model_name
        if base_url is None:
            # Support environment variable for Docker compatibility
            # Use host.docker.internal on Windows/Mac Docker Desktop
            # On Linux, use the host's IP address or set OLLAMA_BASE_URL
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        else:
            self.base_url = base_url
        self._verify_connection()
    
    def _verify_connection(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available = [m['name'] for m in models]
                print(f"✓ Ollama connected. Available models: {available}")
            else:
                print("⚠ Ollama API returned error. Is Ollama running?")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Cannot connect to Ollama at {self.base_url}")
            print(f"  Make sure Ollama is running: 'ollama serve'")
            if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                print(f"  For Docker: Set OLLAMA_BASE_URL=http://host.docker.internal:11434 (Windows/Mac)")
                print(f"  Or use host IP address on Linux")
            print(f"  Error: {e}")
    
    def generate_hdl(
        self, 
        specification: str, 
        prompt_template: str = "A",
        temperature: float = 0.0,
        max_tokens: int = 512
    ) -> Tuple[str, float]:
        """
        Generate Verilog HDL from specification
        
        Args:
            specification: Natural language description of circuit
            prompt_template: Template ID ('A', 'B', or 'C')
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (generated_code, generation_time_seconds)
        """
        prompt = self._construct_prompt(specification, prompt_template)
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                },
                timeout=120  # 2 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_code = result.get('response', '')
                generation_time = time.time() - start_time
                
                # Extract just the Verilog code
                code = self._extract_verilog_code(generated_code)
                return code, generation_time
            else:
                print(f"Error: API returned {response.status_code}")
                return self._fallback_code(), time.time() - start_time
                
        except requests.exceptions.Timeout:
            print(f"Timeout generating code for: {specification[:50]}...")
            return self._fallback_code(), 120.0
        except Exception as e:
            print(f"Error during generation: {e}")
            return self._fallback_code(), time.time() - start_time
    
    def generate_with_confidence(
        self,
        specification: str,
        prompt_template: str = "A",
        temperature: float = 0.0,
        max_tokens: int = 512,
        num_samples: int = 3
    ) -> Tuple[str, float, Optional[List[float]], float]:
        """
        Generate HDL with confidence metrics
        
        Args:
            specification: Natural language description
            prompt_template: Template ID
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            num_samples: Number of samples for entropy calculation
            
        Returns:
            Tuple of (code, gen_time, log_probs, entropy)
            log_probs may be None if not available
        """
        # Generate primary sample
        code, gen_time = self.generate_hdl(specification, prompt_template, temperature, max_tokens)
        
        # Generate additional samples for entropy (if temperature > 0)
        samples = [code]
        if temperature > 0 and num_samples > 1:
            for _ in range(num_samples - 1):
                sample_code, _ = self.generate_hdl(
                    specification, prompt_template, temperature, max_tokens
                )
                samples.append(sample_code)
        
        # Compute entropy from samples
        from confidence_tracker import ConfidenceTracker
        tracker = ConfidenceTracker()
        entropy = tracker.compute_entropy(samples)
        
        # Log probabilities not available from Ollama API directly
        # Would need model API support for this
        log_probs = None
        
        return code, gen_time, log_probs, entropy
    
    def _construct_prompt(self, specification: str, template: str = "A") -> str:
        """Build prompt based on template type"""
        
        if template == "A":
            # Minimal natural-language specification
            prompt = f"""{specification}

Write only the Verilog module code. Do not include explanations."""
            
        elif template == "B":
            # Specification + explicit requirements
            prompt = f"""Write synthesizable Verilog code for the following specification:

{specification}

Requirements:
- Use proper Verilog-2001 syntax
- Include complete module declaration with all ports
- Make the design synthesizable (no delays, no initial blocks in synthesis)
- Add brief comments for clarity
- Use descriptive signal names

Provide only the Verilog code:"""
            
        elif template == "C":
            # Detailed with examples
            prompt = f"""Design and implement in Verilog:

{specification}

Guidelines:
- Follow standard RTL design practices
- Use blocking assignments (=) for combinational logic
- Use non-blocking assignments (<=) for sequential logic
- Include reset logic for sequential elements
- Test your logic mentally before writing

Verilog module:"""
        else:
            prompt = specification
        
        return prompt
    
    def _extract_verilog_code(self, response: str) -> str:
        """Extract Verilog code from model response"""
        
        # Look for code blocks
        if "```verilog" in response:
            start = response.find("```verilog") + len("```verilog")
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                code = response[start:end].strip()
                # Remove language tag if present
                if code.startswith("verilog\n"):
                    code = code[8:]
                return code
        
        # Look for module declaration
        if "module " in response:
            start = response.find("module ")
            # Find endmodule
            end = response.find("endmodule", start)
            if end != -1:
                return response[start:end+9].strip()
        
        # Return full response if no clear code block found
        return response.strip()
    
    def _fallback_code(self) -> str:
        """Return fallback code on error"""
        return """// Error: Failed to generate code
module error_module(
    input wire clk,
    output reg error
);
    always @(posedge clk) begin
        error <= 1'b1;
    end
endmodule"""


class HuggingFaceInterface:
    """Interface for HuggingFace Transformers (StarCoder2, etc.)"""
    
    def __init__(self, model_name: str, device: str = "auto"):
        """
        Initialize HuggingFace model
        
        Args:
            model_name: HF model path (e.g., 'bigcode/starcoder2-7b')
            device: Device to use ('cuda', 'cpu', 'auto')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load model and tokenizer"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            print(f"Loading {self.model_name}...")
            
            # Check transformers version
            import transformers
            transformers_version = transformers.__version__
            print(f"  Transformers version: {transformers_version}")
            
            # Try to use StarCoder2ForCausalLM explicitly if available
            model_class = AutoModelForCausalLM
            if "starcoder2" in self.model_name.lower():
                try:
                    from transformers import StarCoder2ForCausalLM
                    model_class = StarCoder2ForCausalLM
                    print(f"  Using StarCoder2ForCausalLM class")
                except ImportError:
                    print(f"  ⚠ StarCoder2ForCausalLM not available in transformers {transformers_version}")
                    print(f"  ⚠ StarCoder2 requires transformers>=4.35.0, but you have {transformers_version}")
                    print(f"  ⚠ Attempting with AutoModelForCausalLM (may fail)")
                    print(f"  ⚠ Please upgrade: pip install --upgrade transformers>=4.35.0")
            
            # Load tokenizer first
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # StarCoder2 and many code models need a pad_token - set it if missing
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                print(f"  Set pad_token to eos_token")
            
            # Determine device - on Mac, use CPU explicitly
            if self.device == "auto":
                if torch.cuda.is_available():
                    device = "cuda"
                    print(f"  Using CUDA")
                else:
                    device = "cpu"
                    print(f"  Using CPU (no GPU detected)")
            else:
                device = self.device
            
            # Load model - use device_map only for CUDA, otherwise use standard device placement
            
            if device == "cuda":
                self.model = model_class.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )
            else:
                # For CPU, load normally and move to CPU explicitly
                self.model = model_class.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    trust_remote_code=True
                )
                self.model = self.model.to(device)
            
            print(f"✓ Model loaded successfully on {device}")
            
        except ImportError as e:
            print("⚠ transformers library not installed or missing StarCoder2 support")
            print(f"  Error: {e}")
            print("  Install: pip install --upgrade transformers>=4.35.0 torch accelerate")
            self.model = None
            self.tokenizer = None
        except Exception as e:
            print(f"⚠ Error loading model: {e}")
            print(f"  Model: {self.model_name}")
            print(f"  Error type: {type(e).__name__}")
            print(f"  Solution: Try upgrading transformers: pip install --upgrade transformers>=4.35.0")
            import traceback
            print(f"  Full traceback:")
            traceback.print_exc()
            self.model = None
            self.tokenizer = None
    
    def generate_hdl(
        self,
        specification: str,
        prompt_template: str = "A",
        temperature: float = 0.0,
        max_tokens: int = 512
    ) -> Tuple[str, float]:
        """Generate Verilog HDL from specification"""
        
        if self.model is None or self.tokenizer is None:
            print("Model not loaded, using fallback")
            return self._fallback_code(), 0.0
        
        prompt = self._construct_prompt(specification, prompt_template)
        
        start_time = time.time()
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Move inputs to model's device
            if hasattr(self.model, 'device'):
                device = self.model.device
            else:
                # If model doesn't have device attribute, get it from first parameter
                device = next(self.model.parameters()).device
            
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature if temperature > 0 else 0.1,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
            )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from output
            if prompt in generated_text:
                generated_text = generated_text[len(prompt):].strip()
            
            generation_time = time.time() - start_time
            
            code = self._extract_verilog_code(generated_text)
            return code, generation_time
            
        except Exception as e:
            print(f"Error during generation: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_code(), time.time() - start_time
    
    def _construct_prompt(self, specification: str, template: str = "A") -> str:
        """Build prompt - same as Ollama interface"""
        return OllamaInterface._construct_prompt(self, specification, template)
    
    def _extract_verilog_code(self, response: str) -> str:
        """Extract Verilog code - same as Ollama interface"""
        return OllamaInterface._extract_verilog_code(self, response)
    
    def _fallback_code(self) -> str:
        """Return fallback code on error"""
        return OllamaInterface._fallback_code(self)


def create_model_interface(model_type: str, model_name: str):
    """
    Factory function to create appropriate model interface
    
    Args:
        model_type: 'ollama' or 'huggingface'
        model_name: Model identifier
        
    Returns:
        Model interface instance
    """
    if model_type.lower() == "ollama":
        return OllamaInterface(model_name)
    elif model_type.lower() == "huggingface":
        return HuggingFaceInterface(model_name)
    else:
        raise ValueError(f"Unknown model type: {model_type}")


# Test code
if __name__ == "__main__":
    print("Testing Ollama Interface...")
    print("-" * 50)
    
    # Test Ollama connection
    try:
        model = OllamaInterface("llama3")
        
        # Test generation
        spec = "Design a 2-bit binary adder in Verilog with inputs a[1:0] and b[1:0], and output sum[1:0] and carry_out."
        
        print(f"\nTest specification: {spec[:60]}...")
        code, gen_time = model.generate_hdl(spec, prompt_template="B")
        
        print(f"\n✓ Generated in {gen_time:.2f}s")
        print("\nGenerated Code:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        
    except Exception as e:
        print(f"✗ Test failed: {e}")

