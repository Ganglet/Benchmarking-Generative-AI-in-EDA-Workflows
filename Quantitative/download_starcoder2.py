#!/usr/bin/env python3
"""
Download StarCoder2-7B model.
This will resume any partial download.
"""

from model_interface import HuggingFaceInterface

print("Downloading StarCoder2-7B model...")
print("This may take a while (model is ~14GB).")
print("The download will resume if interrupted.\n")

try:
    model = HuggingFaceInterface("bigcode/starcoder2-7b")
    if model.model is not None and model.tokenizer is not None:
        print("\n✓ Model downloaded and loaded successfully!")
        print("✓ StarCoder2-7B is ready to use.")
    else:
        print("\n⚠ Model download completed but loading failed.")
except KeyboardInterrupt:
    print("\n\nDownload interrupted. You can resume by running this script again.")
except Exception as e:
    print(f"\n✗ Error: {e}")
    print("Try running again - it should resume the download.")
