#!/usr/bin/env python3
"""
XYZ Hypothesis Generator for Pretotyping

Helps users create well-formed hypotheses in the format:
"At least X% of Y (target users) will Z (take action)"
"""

import sys
import json
from typing import Dict, Any, Tuple


def validate_percentage(x: str) -> Tuple[bool, str]:
    """Validate that X is a reasonable percentage."""
    try:
        value = float(x)
        if value <= 0 or value > 100:
            return False, "Percentage must be between 0 and 100"
        if value > 50:
            return True, "⚠️  Warning: >50% is very optimistic. Consider being more conservative."
        return True, ""
    except ValueError:
        return False, "Must be a valid number"


def validate_audience(y: str) -> Tuple[bool, str]:
    """Validate that Y is specific enough."""
    if len(y.strip()) < 5:
        return False, "Target audience should be more specific"
    
    # Check for vague terms
    vague_terms = ["people", "users", "everyone", "anyone", "somebody"]
    if any(term in y.lower() for term in vague_terms):
        return True, "💡 Tip: Consider being more specific about your target audience"
    
    return True, ""


def validate_action(z: str) -> Tuple[bool, str]:
    """Validate that Z is measurable."""
    if len(z.strip()) < 5:
        return False, "Action should be more specific"
    
    # Check for measurable verbs
    measurable_verbs = ["sign up", "purchase", "download", "subscribe", "register", 
                       "click", "share", "pay", "buy", "install", "use"]
    
    if not any(verb in z.lower() for verb in measurable_verbs):
        return True, "💡 Tip: Use measurable actions like 'sign up', 'purchase', 'download'"
    
    return True, ""


def calculate_sample_size(x: float, confidence: float = 0.95) -> int:
    """
    Calculate minimum sample size needed for statistical significance.
    Using simplified formula for proportion estimation.
    """
    # Z-score for 95% confidence
    z = 1.96 if confidence == 0.95 else 2.576
    
    # Convert percentage to proportion
    p = x / 100
    
    # Margin of error (5%)
    e = 0.05
    
    # Sample size formula: n = (Z^2 * p * (1-p)) / e^2
    n = (z ** 2 * p * (1 - p)) / (e ** 2)
    
    return int(n) + 1


def generate_hypothesis(x: str, y: str, z: str) -> Dict[str, Any]:
    """Generate formatted hypothesis and success criteria."""
    
    # Validate inputs
    x_valid, x_msg = validate_percentage(x)
    y_valid, y_msg = validate_audience(y)
    z_valid, z_msg = validate_action(z)
    
    warnings = []
    errors = []
    
    if not x_valid:
        errors.append(f"X (percentage): {x_msg}")
    elif x_msg:
        warnings.append(x_msg)
    
    if not y_valid:
        errors.append(f"Y (audience): {y_msg}")
    elif y_msg:
        warnings.append(y_msg)
    
    if not z_valid:
        errors.append(f"Z (action): {z_msg}")
    elif z_msg:
        warnings.append(z_msg)
    
    if errors:
        return {
            "success": False,
            "errors": errors,
            "warnings": warnings
        }
    
    # Generate hypothesis
    x_float = float(x)
    hypothesis = f"At least {x}% of {y.strip()} will {z.strip()}"
    
    # Calculate sample size
    sample_size = calculate_sample_size(x_float)
    
    # Generate success criteria
    success_criteria = {
        "hypothesis": hypothesis,
        "minimum_conversion_rate": f"{x}%",
        "target_audience": y.strip(),
        "target_action": z.strip(),
        "minimum_sample_size": sample_size,
        "recommended_timeframe": "1-2 weeks",
        "success_threshold": f"At least {int(sample_size * x_float / 100)} conversions out of {sample_size} exposures"
    }
    
    return {
        "success": True,
        "hypothesis": hypothesis,
        "criteria": success_criteria,
        "warnings": warnings
    }


def interactive_mode():
    """Run in interactive mode."""
    print("=" * 60)
    print("XYZ Hypothesis Generator")
    print("=" * 60)
    print("\nCreate a testable hypothesis in the format:")
    print("'At least X% of Y (target users) will Z (take action)'\n")
    
    # Get X
    while True:
        x = input("X - What percentage? (e.g., 10): ").strip()
        valid, msg = validate_percentage(x)
        if valid:
            if msg:
                print(f"  {msg}")
            break
        else:
            print(f"  ❌ {msg}")
    
    # Get Y
    while True:
        y = input("\nY - Who is your target audience? (e.g., 'fitness enthusiasts aged 25-35'): ").strip()
        valid, msg = validate_audience(y)
        if valid:
            if msg:
                print(f"  {msg}")
            break
        else:
            print(f"  ❌ {msg}")
    
    # Get Z
    while True:
        z = input("\nZ - What action will they take? (e.g., 'sign up for a free trial'): ").strip()
        valid, msg = validate_action(z)
        if valid:
            if msg:
                print(f"  {msg}")
            break
        else:
            print(f"  ❌ {msg}")
    
    # Generate result
    result = generate_hypothesis(x, y, z)
    
    print("\n" + "=" * 60)
    print("GENERATED HYPOTHESIS")
    print("=" * 60)
    print(f"\n📋 {result['hypothesis']}\n")
    
    print("SUCCESS CRITERIA:")
    print("-" * 60)
    criteria = result['criteria']
    print(f"• Minimum conversion rate: {criteria['minimum_conversion_rate']}")
    print(f"• Minimum sample size: {criteria['minimum_sample_size']} exposures")
    print(f"• Success threshold: {criteria['success_threshold']}")
    print(f"• Recommended timeframe: {criteria['recommended_timeframe']}")
    print()
    
    if result.get('warnings'):
        print("TIPS:")
        print("-" * 60)
        for warning in result['warnings']:
            print(f"  {warning}")
        print()


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    elif len(sys.argv) == 4:
        # Command-line mode
        x, y, z = sys.argv[1], sys.argv[2], sys.argv[3]
        result = generate_hypothesis(x, y, z)
        print(json.dumps(result, indent=2))
    else:
        print("Usage:")
        print("  Interactive mode: python xyz_hypothesis.py")
        print("  Command-line mode: python xyz_hypothesis.py <X> <Y> <Z>")
        print("\nExample:")
        print("  python xyz_hypothesis.py 10 'fitness enthusiasts' 'sign up for a trial'")
        sys.exit(1)


if __name__ == "__main__":
    main()
