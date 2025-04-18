#!/usr/bin/env python3
"""
Direct model test script using Hugging Face API.

This script tests models directly using the Hugging Face API.
"""

import os
import sys
import json
import time
import argparse
import logging
from typing import Dict, Any, List
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get Hugging Face token from environment
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    logger.error("HF_TOKEN not found in environment. Checking .env file...")
    try:
        with open('/app/.env', 'r') as f:
            for line in f:
                if line.startswith('HF_TOKEN='):
                    HF_TOKEN = line.strip().split('=', 1)[1].strip('"\'')
                    logger.info(f"Found HF_TOKEN in .env file")
                    break
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")

if not HF_TOKEN:
    logger.error("HF_TOKEN not found. Cannot proceed.")
    sys.exit(1)

# Target models to evaluate
TARGET_MODELS = [
    "microsoft/phi-4-mini-instruct",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct"
]

# Test cases
TEST_CASES = {
    "speed": {
        "prompt": "What is the capital of France?",
        "expected_tokens": 20
    },
    "structured_output": {
        "prompt": "Generate a JSON object representing a user profile with fields for name, age, and email.",
        "system_prompt": "You are a structured data assistant. Respond with valid JSON only."
    },
    "tool_use": {
        "prompt": "I need to know the weather in Paris for my trip next week.",
        "system_prompt": """You are a tool selection agent. Available tools:
- get_weather(location: str, date: str): Get weather forecast for a location
- search_web(query: str): Search the web for information
- calculate_route(start: str, end: str): Calculate route between locations""",
        "expected_tool": "get_weather"
    }
}

def test_model(model_name: str) -> Dict[str, Any]:
    """
    Test a model on key metrics using the Hugging Face API.

    Args:
        model_name: Name of the model to test

    Returns:
        results: Test results
    """
    try:
        # Create Hugging Face inference client
        client = InferenceClient(model=model_name, token=HF_TOKEN)

        results = {
            "model": model_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {}
        }

        # Test speed
        logger.info(f"Testing {model_name} on speed...")
        speed_test = TEST_CASES["speed"]

        start_time = time.time()
        response = client.text_generation(
            prompt=speed_test["prompt"],
            max_new_tokens=100,
            temperature=0.2,
            return_full_text=False
        )
        end_time = time.time()

        duration = end_time - start_time
        tokens_per_second = speed_test["expected_tokens"] / duration if duration > 0 else 0

        results["tests"]["speed"] = {
            "duration": duration,
            "tokens_per_second": tokens_per_second,
            "response": response
        }

        logger.info(f"  Speed test completed in {duration:.2f}s ({tokens_per_second:.2f} tokens/s)")

        # Test structured output
        logger.info(f"Testing {model_name} on structured output...")
        structured_test = TEST_CASES["structured_output"]

        # Format prompt based on model
        if "qwen" in model_name.lower():
            full_prompt = f"<|im_start|>system\n{structured_test['system_prompt']}<|im_end|>\n<|im_start|>user\n{structured_test['prompt']}<|im_end|>\n<|im_start|>assistant\n"
        else:
            full_prompt = f"System: {structured_test['system_prompt']}\n\nUser: {structured_test['prompt']}\n\nAssistant: "

        start_time = time.time()
        try:
            response = client.text_generation(
                prompt=full_prompt,
                max_new_tokens=200,
                temperature=0.2,
                return_full_text=False
            )

            # Check if response is valid JSON
            is_valid_json = True
            try:
                # Try to extract JSON from the response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    json_response = json.loads(json_str)
                else:
                    is_valid_json = False
                    json_response = None
            except Exception:
                is_valid_json = False
                json_response = None
        except Exception as e:
            is_valid_json = False
            json_response = None
            response = str(e)
            logger.error(f"  Error in structured output test: {e}")

        end_time = time.time()
        duration = end_time - start_time

        results["tests"]["structured_output"] = {
            "duration": duration,
            "is_valid_json": is_valid_json,
            "response": response
        }

        logger.info(f"  Structured output test completed in {duration:.2f}s (Valid JSON: {is_valid_json})")

        # Test tool use
        logger.info(f"Testing {model_name} on tool use...")
        tool_test = TEST_CASES["tool_use"]

        # Format prompt based on model
        if "qwen" in model_name.lower():
            full_prompt = f"<|im_start|>system\n{tool_test['system_prompt']}<|im_end|>\n<|im_start|>user\n{tool_test['prompt']}<|im_end|>\n<|im_start|>assistant\n"
        else:
            full_prompt = f"System: {tool_test['system_prompt']}\n\nUser: {tool_test['prompt']}\n\nAssistant: "

        start_time = time.time()
        try:
            response = client.text_generation(
                prompt=full_prompt,
                max_new_tokens=200,
                temperature=0.2,
                return_full_text=False
            )
            tool_mentioned = tool_test["expected_tool"].lower() in response.lower()
        except Exception as e:
            response = str(e)
            tool_mentioned = False
            logger.error(f"  Error in tool use test: {e}")

        end_time = time.time()
        duration = end_time - start_time

        results["tests"]["tool_use"] = {
            "duration": duration,
            "tool_mentioned": tool_mentioned,
            "response": response
        }

        logger.info(f"  Tool use test completed in {duration:.2f}s (Tool mentioned: {tool_mentioned})")

        return results

    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}")
        return {
            "model": model_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

def run_tests(models: List[str] = None) -> Dict[str, Any]:
    """
    Run tests on specified models.

    Args:
        models: List of models to test (if None, use all TARGET_MODELS)

    Returns:
        results: Test results
    """
    # Use default models if not specified
    if models is None:
        models = TARGET_MODELS

    # Prepare results dictionary
    results = {
        "models": models,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "results": []
    }

    # Run tests
    for model in models:
        logger.info(f"Testing model: {model}")

        # Test model
        model_results = test_model(model)

        # Add to results
        results["results"].append(model_results)

    return results

def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze test results and provide insights.

    Args:
        results: Test results

    Returns:
        analysis: Analysis of results
    """
    models = results["models"]
    all_results = results["results"]

    # Prepare analysis dictionary
    analysis = {
        "models": models,
        "timestamp": results["timestamp"],
        "model_performance": {},
        "overall_ranking": {}
    }

    # Analyze performance by model
    for model_result in all_results:
        model = model_result["model"]

        # Skip if error
        if "error" in model_result:
            analysis["model_performance"][model] = {
                "error": model_result["error"]
            }
            continue

        tests = model_result.get("tests", {})

        # Get speed metrics
        speed_test = tests.get("speed", {})
        speed_duration = speed_test.get("duration", 0)
        tokens_per_second = speed_test.get("tokens_per_second", 0)

        # Get structured output metrics
        structured_test = tests.get("structured_output", {})
        structured_duration = structured_test.get("duration", 0)
        is_valid_json = structured_test.get("is_valid_json", False)

        # Get tool use metrics
        tool_test = tests.get("tool_use", {})
        tool_duration = tool_test.get("duration", 0)
        tool_mentioned = tool_test.get("tool_mentioned", False)

        # Store model performance
        analysis["model_performance"][model] = {
            "speed": {
                "duration": speed_duration,
                "tokens_per_second": tokens_per_second
            },
            "structured_output": {
                "duration": structured_duration,
                "is_valid_json": is_valid_json
            },
            "tool_use": {
                "duration": tool_duration,
                "tool_mentioned": tool_mentioned
            }
        }

        # Calculate overall score
        speed_score = min(10, tokens_per_second / 10)  # Normalize to 0-10 range
        structured_score = 10 if is_valid_json else 0
        tool_score = 10 if tool_mentioned else 0

        # Combined score (adjust weights as needed)
        score = (
            speed_score * 0.3 +  # 30% weight for speed
            structured_score * 0.4 +  # 40% weight for structured output
            tool_score * 0.3  # 30% weight for tool use
        )

        analysis["model_performance"][model]["overall_score"] = score

    # Sort models by score
    sorted_models = sorted(
        [m for m in models if m in analysis["model_performance"] and "error" not in analysis["model_performance"][m]],
        key=lambda m: analysis["model_performance"][m]["overall_score"],
        reverse=True
    )

    # Store overall ranking
    for i, model in enumerate(sorted_models):
        analysis["overall_ranking"][model] = {
            "rank": i + 1,
            "score": analysis["model_performance"][model]["overall_score"]
        }

    return analysis

def print_analysis(analysis: Dict[str, Any]):
    """
    Print analysis results in a readable format.

    Args:
        analysis: Analysis of results
    """
    print("\n===== DIRECT MODEL TEST RESULTS =====")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Models evaluated: {', '.join(analysis['models'])}")

    print("\n----- OVERALL RANKING -----")
    for model, ranking in sorted(analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        print(f"{ranking['rank']}. {model} (Score: {ranking['score']:.2f})")

    print("\n----- MODEL PERFORMANCE -----")
    for model, perf in analysis["model_performance"].items():
        print(f"\n{model}:")

        if "error" in perf:
            print(f"  Error: {perf['error']}")
            continue

        # Speed metrics
        speed = perf["speed"]
        print(f"  Speed: {speed['tokens_per_second']:.2f} tokens/s ({speed['duration']:.2f}s)")

        # Structured output metrics
        structured = perf["structured_output"]
        print(f"  Structured Output: {'Valid' if structured['is_valid_json'] else 'Invalid'} JSON ({structured['duration']:.2f}s)")

        # Tool use metrics
        tool = perf["tool_use"]
        print(f"  Tool Use: {'Tool mentioned' if tool['tool_mentioned'] else 'Tool not mentioned'} ({tool['duration']:.2f}s)")

        # Overall score
        print(f"  Overall Score: {perf['overall_score']:.2f}")

    # Print recommendations
    print("\n----- RECOMMENDATIONS -----")

    # Get the top model overall
    top_model = next(iter(sorted(analysis["overall_ranking"].items(), key=lambda x: x[1]["rank"])), (None, None))[0]

    if top_model:
        print(f"Best overall model: {top_model}")

        # Get best model for each metric
        best_speed = max(
            [m for m in analysis["models"] if m in analysis["model_performance"] and "error" not in analysis["model_performance"][m]],
            key=lambda m: analysis["model_performance"][m]["speed"]["tokens_per_second"]
        )

        best_structured = [
            m for m in analysis["models"]
            if m in analysis["model_performance"] and "error" not in analysis["model_performance"][m]
            and analysis["model_performance"][m]["structured_output"]["is_valid_json"]
        ]

        best_tool = [
            m for m in analysis["models"]
            if m in analysis["model_performance"] and "error" not in analysis["model_performance"][m]
            and analysis["model_performance"][m]["tool_use"]["tool_mentioned"]
        ]

        print(f"Best model for speed: {best_speed}")
        print(f"Models with valid structured output: {', '.join(best_structured) if best_structured else 'None'}")
        print(f"Models with correct tool use: {', '.join(best_tool) if best_tool else 'None'}")

        # Print specific use case recommendations
        print("\nRecommended models by use case:")
        print(f"  Speed-critical applications: {best_speed}")
        print(f"  API integration/structured data: {best_structured[0] if best_structured else 'None'}")
        print(f"  Tool/function calling: {best_tool[0] if best_tool else 'None'}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Direct test of models using Hugging Face API")
    parser.add_argument("--models", nargs="+", choices=TARGET_MODELS + ["all"], default=["all"],
                      help="Models to test")
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()

    # Process model selection
    if "all" in args.models:
        models = TARGET_MODELS
    else:
        models = args.models

    # Run tests
    results = run_tests(models)

    # Analyze results
    analysis = analyze_results(results)

    # Print analysis
    print_analysis(analysis)

    # Save results if output file specified
    if args.output:
        output_data = {
            "results": results,
            "analysis": analysis
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    main()
