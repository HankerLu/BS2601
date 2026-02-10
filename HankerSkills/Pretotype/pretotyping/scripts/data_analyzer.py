#!/usr/bin/env python3
"""
Data Analyzer for Pretotyping Validation

Analyzes validation data and provides insights on whether to Go/Pivot/Stop.
"""

import sys
import json
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class ValidationData:
    """Container for validation metrics."""
    exposures: int  # Total number of people exposed
    conversions: int  # Number of people who took action
    expected_rate: float  # Expected conversion rate (as percentage)
    timeframe_days: int  # How long the test ran


def calculate_conversion_rate(conversions: int, exposures: int) -> float:
    """Calculate conversion rate as percentage."""
    if exposures == 0:
        return 0.0
    return (conversions / exposures) * 100


def calculate_confidence_interval(conversions: int, exposures: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for conversion rate using Wilson score interval.
    Returns (lower_bound, upper_bound) as percentages.
    """
    if exposures == 0:
        return (0.0, 0.0)
    
    # Z-score for confidence level
    z = 1.96 if confidence == 0.95 else 2.576
    
    p = conversions / exposures
    n = exposures
    
    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denominator
    margin = z * ((p * (1-p) / n + z**2 / (4*n**2)) ** 0.5) / denominator
    
    lower = max(0, center - margin) * 100
    upper = min(1, center + margin) * 100
    
    return (lower, upper)


def is_statistically_significant(conversions: int, exposures: int, expected_rate: float) -> bool:
    """
    Check if the result is statistically significant.
    Returns True if we can be confident the true rate differs from expected.
    """
    lower, upper = calculate_confidence_interval(conversions, exposures)
    
    # If expected rate is outside the confidence interval, it's significant
    return expected_rate < lower or expected_rate > upper


def make_decision(data: ValidationData) -> Dict[str, Any]:
    """
    Analyze data and make Go/Pivot/Stop recommendation.
    
    Decision rules:
    - GO: Actual rate >= expected rate (within confidence)
    - PIVOT: Actual rate is 50-99% of expected (shows some promise)
    - STOP: Actual rate < 50% of expected (far from target)
    """
    actual_rate = calculate_conversion_rate(data.conversions, data.exposures)
    lower, upper = calculate_confidence_interval(data.conversions, data.exposures)
    
    # Calculate performance vs expected
    if data.expected_rate > 0:
        performance_ratio = actual_rate / data.expected_rate
    else:
        performance_ratio = 0
    
    # Determine if sample size is sufficient
    min_sample_size = max(100, int(1000 / data.expected_rate)) if data.expected_rate > 0 else 100
    sufficient_sample = data.exposures >= min_sample_size
    
    # Make decision
    if actual_rate >= data.expected_rate and sufficient_sample:
        decision = "GO"
        confidence = "HIGH"
        reasoning = f"Actual conversion rate ({actual_rate:.2f}%) meets or exceeds target ({data.expected_rate}%)"
    elif lower >= data.expected_rate and sufficient_sample:
        decision = "GO"
        confidence = "MEDIUM"
        reasoning = f"Even the lower confidence bound ({lower:.2f}%) meets target ({data.expected_rate}%)"
    elif performance_ratio >= 0.5 and sufficient_sample:
        decision = "PIVOT"
        confidence = "MEDIUM"
        reasoning = f"Actual rate ({actual_rate:.2f}%) is {performance_ratio*100:.0f}% of target. Shows promise but needs adjustment"
    elif not sufficient_sample:
        decision = "CONTINUE TESTING"
        confidence = "LOW"
        reasoning = f"Sample size ({data.exposures}) is too small. Need at least {min_sample_size} exposures"
    else:
        decision = "STOP"
        confidence = "HIGH"
        reasoning = f"Actual rate ({actual_rate:.2f}%) is only {performance_ratio*100:.0f}% of target ({data.expected_rate}%). Significant gap"
    
    # Generate next steps
    next_steps = generate_next_steps(decision, data, actual_rate, performance_ratio)
    
    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning,
        "metrics": {
            "actual_conversion_rate": f"{actual_rate:.2f}%",
            "expected_conversion_rate": f"{data.expected_rate}%",
            "confidence_interval": f"{lower:.2f}% - {upper:.2f}%",
            "performance_vs_target": f"{performance_ratio*100:.0f}%",
            "sample_size": data.exposures,
            "conversions": data.conversions,
            "test_duration": f"{data.timeframe_days} days"
        },
        "next_steps": next_steps
    }


def generate_next_steps(decision: str, data: ValidationData, actual_rate: float, performance_ratio: float) -> List[str]:
    """Generate actionable next steps based on decision."""
    steps = []
    
    if decision == "GO":
        steps.append("✅ Proceed to prototype development")
        steps.append("📊 Consider expanding test to validate at larger scale")
        steps.append("💡 Document what worked well for future reference")
    
    elif decision == "PIVOT":
        steps.append("🔄 Analyze why conversion is lower than expected")
        steps.append("💬 Interview users who showed interest but didn't convert")
        steps.append("🎯 Consider adjusting: value proposition, pricing, target audience, or messaging")
        steps.append("🧪 Run another pretotype test with adjustments")
    
    elif decision == "STOP":
        steps.append("🛑 Consider stopping or major pivot")
        steps.append("🔍 Analyze: Was the audience wrong? Value prop unclear? Timing off?")
        steps.append("💡 Extract learnings before moving on")
        steps.append("🤔 If you still believe in the idea, test a fundamentally different approach")
    
    elif decision == "CONTINUE TESTING":
        min_sample = max(100, int(1000 / data.expected_rate)) if data.expected_rate > 0 else 100
        steps.append(f"📈 Continue testing until you reach {min_sample} exposures")
        steps.append("⏱️  Give it at least 1-2 weeks for meaningful data")
        steps.append("🎯 Consider expanding reach if traffic is too low")
    
    return steps


def analyze_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze data from dictionary input."""
    validation_data = ValidationData(
        exposures=data['exposures'],
        conversions=data['conversions'],
        expected_rate=data['expected_rate'],
        timeframe_days=data.get('timeframe_days', 7)
    )
    return make_decision(validation_data)


def interactive_mode():
    """Run in interactive mode."""
    print("=" * 60)
    print("Pretotyping Data Analyzer")
    print("=" * 60)
    print("\nEnter your validation test results:\n")
    
    # Get inputs
    while True:
        try:
            exposures = int(input("How many people were exposed to your pretotype? "))
            if exposures < 0:
                print("  ❌ Must be a positive number")
                continue
            break
        except ValueError:
            print("  ❌ Must be a valid number")
    
    while True:
        try:
            conversions = int(input("How many people took the target action? "))
            if conversions < 0 or conversions > exposures:
                print(f"  ❌ Must be between 0 and {exposures}")
                continue
            break
        except ValueError:
            print("  ❌ Must be a valid number")
    
    while True:
        try:
            expected_rate = float(input("What was your expected conversion rate? (e.g., 10 for 10%) "))
            if expected_rate <= 0 or expected_rate > 100:
                print("  ❌ Must be between 0 and 100")
                continue
            break
        except ValueError:
            print("  ❌ Must be a valid number")
    
    while True:
        try:
            timeframe = int(input("How many days did you run the test? "))
            if timeframe <= 0:
                print("  ❌ Must be a positive number")
                continue
            break
        except ValueError:
            print("  ❌ Must be a valid number")
    
    # Analyze
    data = ValidationData(exposures, conversions, expected_rate, timeframe)
    result = make_decision(data)
    
    # Display results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n🎯 DECISION: {result['decision']}")
    print(f"📊 CONFIDENCE: {result['confidence']}")
    print(f"\n💡 {result['reasoning']}\n")
    
    print("METRICS:")
    print("-" * 60)
    metrics = result['metrics']
    print(f"• Actual conversion rate: {metrics['actual_conversion_rate']}")
    print(f"• Expected conversion rate: {metrics['expected_conversion_rate']}")
    print(f"• 95% Confidence interval: {metrics['confidence_interval']}")
    print(f"• Performance vs target: {metrics['performance_vs_target']}")
    print(f"• Sample size: {metrics['sample_size']}")
    print(f"• Conversions: {metrics['conversions']}")
    print(f"• Test duration: {metrics['test_duration']}")
    
    print("\nNEXT STEPS:")
    print("-" * 60)
    for step in result['next_steps']:
        print(f"  {step}")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    elif len(sys.argv) == 2:
        # JSON input mode
        try:
            data = json.loads(sys.argv[1])
            result = analyze_from_dict(data)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError:
            print("Error: Invalid JSON input")
            sys.exit(1)
    else:
        print("Usage:")
        print("  Interactive mode: python data_analyzer.py")
        print("  JSON mode: python data_analyzer.py '{\"exposures\": 200, \"conversions\": 15, \"expected_rate\": 10, \"timeframe_days\": 7}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
