#!/usr/bin/env python3
"""
Simple verification script to check if the GGUF model loads correctly.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Model Verification Script")
print("=" * 70)

# Check if model file exists
model_path = "models/phi3.5.gguf"
if not os.path.exists(model_path):
    print(f"\n✗ Error: Model file not found at {model_path}")
    print("  Please ensure the GGUF file is in the models/ directory")
    sys.exit(1)

print(f"\n✓ Model file found: {model_path}")
print(f"  Size: {os.path.getsize(model_path) / (1024**3):.2f} GB")

# Import DSPy signatures (this will configure the model)
print("\nLoading DSPy with llama-cpp-python...")
try:
    from agent import dspy_signatures
    print("✓ DSPy configuration loaded successfully")
except Exception as e:
    print(f"✗ Error loading DSPy: {e}")
    sys.exit(1)

# Import dspy for simple test
import dspy

# Define a simple signature for testing
class HelloSignature(dspy.Signature):
    """Simple test signature"""
    question = dspy.InputField(desc="A question")
    answer = dspy.OutputField(desc="An answer")

# Test the model
print("\nTesting model with simple prediction...")
try:
    # First test: raw model call
    print("\n--- Test 1: Raw Model Call ---")
    raw_response = dspy.settings.lm("Say hello in one word.")
    print(f"Raw response: {raw_response}")
    
    # Second test: DSPy Predict
    print("\n--- Test 2: DSPy Predict ---")
    predictor = dspy.Predict(HelloSignature)
    result = predictor(question="Say hello in one word")
    
    print("\n" + "=" * 70)
    print("✓✓✓ Model Test Successful! ✓✓✓")
    print("=" * 70)
    print(f"\nQuestion: Say hello in one word")
    print(f"Answer: {result.answer}")
    print(f"Full result object: {result}")
    print("\nThe GGUF model is loaded and working correctly!")
    
except Exception as e:
    print("\n" + "=" * 70)
    print("✗✗✗ Model Test Failed ✗✗✗")
    print("=" * 70)
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    print("\nPossible issues:")
    print("  1. GGUF file may be corrupted")
    print("  2. llama-cpp-python may not be installed correctly")
    print("  3. Model format may be incompatible")
    print("\nTry reinstalling llama-cpp-python:")
    print("  pip install --upgrade --force-reinstall llama-cpp-python")
    sys.exit(1)

print("\n" + "=" * 70)
print("Verification Complete")
print("=" * 70)
