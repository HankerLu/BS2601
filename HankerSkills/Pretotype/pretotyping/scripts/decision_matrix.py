#!/usr/bin/env python3
"""
Decision Matrix Generator for Pretotyping

Creates a visual decision matrix to help make Go/Pivot/Stop decisions.
"""

import sys
import json
from typing import Dict, Any, List


def generate_decision_matrix(
    actual_rate: float,
    expected_rate: float,
    sample_size: int,
    confidence_lower: float,
    confidence_upper: float
) -> str:
    """Generate ASCII decision matrix visualization."""
    
    performance_ratio = actual_rate / expected_rate if expected_rate > 0 else 0
    
    matrix = []
    matrix.append("=" * 70)
    matrix.append("DECISION MATRIX")
    matrix.append("=" * 70)
    matrix.append("")
    
    # Visual performance indicator
    matrix.append("PERFORMANCE vs TARGET:")
    matrix.append("-" * 70)
    
    bar_length = 50
    target_pos = int(bar_length * 0.5)  # Target at 50%
    actual_pos = min(int(bar_length * performance_ratio), bar_length)
    
    bar = ['-'] * bar_length
    bar[target_pos] = '|'
    if actual_pos < bar_length:
        bar[actual_pos] = '●'
    
    matrix.append("0%  " + ''.join(bar) + "  200%")
    matrix.append("     " + " " * target_pos + "↑")
    matrix.append("     " + " " * target_pos + "Target")
    matrix.append("")
    
    # Decision zones
    matrix.append("DECISION ZONES:")
    matrix.append("-" * 70)
    matrix.append("")
    
    zones = [
        ("🟢 GO ZONE", "≥ 100% of target", "Proceed to next stage"),
        ("🟡 PIVOT ZONE", "50-99% of target", "Adjust and retest"),
        ("🔴 STOP ZONE", "< 50% of target", "Major pivot or stop"),
    ]
    
    for zone, criteria, action in zones:
        matrix.append(f"{zone:20} {criteria:20} → {action}")
    
    matrix.append("")
    
    # Current position
    if performance_ratio >= 1.0:
        zone = "🟢 GO ZONE"
    elif performance_ratio >= 0.5:
        zone = "🟡 PIVOT ZONE"
    else:
        zone = "🔴 STOP ZONE"
    
    matrix.append(f"YOUR POSITION: {zone}")
    matrix.append(f"Performance: {performance_ratio*100:.1f}% of target")
    matrix.append("")
    
    # Confidence assessment
    matrix.append("CONFIDENCE ASSESSMENT:")
    matrix.append("-" * 70)
    
    if sample_size < 100:
        confidence_level = "🔴 LOW - Need more data"
    elif sample_size < 500:
        confidence_level = "🟡 MEDIUM - Reasonable sample"
    else:
        confidence_level = "🟢 HIGH - Strong sample size"
    
    matrix.append(f"Sample size: {sample_size} → {confidence_level}")
    matrix.append(f"95% CI: {confidence_lower:.1f}% - {confidence_upper:.1f}%")
    
    ci_width = confidence_upper - confidence_lower
    if ci_width > 10:
        matrix.append("⚠️  Wide confidence interval - consider more data")
    
    matrix.append("")
    matrix.append("=" * 70)
    
    return "\n".join(matrix)


def generate_comparison_table(scenarios: List[Dict[str, Any]]) -> str:
    """Generate comparison table for multiple scenarios."""
    
    table = []
    table.append("=" * 90)
    table.append("SCENARIO COMPARISON")
    table.append("=" * 90)
    table.append("")
    
    # Header
    header = f"{'Scenario':<20} {'Actual':<12} {'Expected':<12} {'Performance':<15} {'Decision':<15}"
    table.append(header)
    table.append("-" * 90)
    
    # Rows
    for scenario in scenarios:
        name = scenario.get('name', 'Unnamed')[:19]
        actual = f"{scenario['actual_rate']:.1f}%"
        expected = f"{scenario['expected_rate']:.1f}%"
        
        perf_ratio = scenario['actual_rate'] / scenario['expected_rate'] if scenario['expected_rate'] > 0 else 0
        performance = f"{perf_ratio*100:.0f}%"
        
        if perf_ratio >= 1.0:
            decision = "🟢 GO"
        elif perf_ratio >= 0.5:
            decision = "🟡 PIVOT"
        else:
            decision = "🔴 STOP"
        
        row = f"{name:<20} {actual:<12} {expected:<12} {performance:<15} {decision:<15}"
        table.append(row)
    
    table.append("")
    table.append("=" * 90)
    
    return "\n".join(table)


def interactive_mode():
    """Run in interactive mode."""
    print("=" * 70)
    print("Decision Matrix Generator")
    print("=" * 70)
    print("\nGenerate a visual decision matrix for your pretotype results.\n")
    
    # Get inputs
    try:
        actual_rate = float(input("Actual conversion rate (e.g., 8.5 for 8.5%): "))
        expected_rate = float(input("Expected conversion rate (e.g., 10 for 10%): "))
        sample_size = int(input("Sample size (number of exposures): "))
        confidence_lower = float(input("Confidence interval lower bound (e.g., 5.2): "))
        confidence_upper = float(input("Confidence interval upper bound (e.g., 11.8): "))
    except ValueError:
        print("Error: Invalid input")
        sys.exit(1)
    
    # Generate matrix
    matrix = generate_decision_matrix(
        actual_rate, expected_rate, sample_size,
        confidence_lower, confidence_upper
    )
    
    print("\n" + matrix)


def main():
    """Main entry point."""
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_mode()
    elif len(sys.argv) == 2:
        # JSON input mode
        try:
            data = json.loads(sys.argv[1])
            
            if 'scenarios' in data:
                # Multiple scenarios comparison
                result = generate_comparison_table(data['scenarios'])
            else:
                # Single scenario matrix
                result = generate_decision_matrix(
                    data['actual_rate'],
                    data['expected_rate'],
                    data['sample_size'],
                    data['confidence_lower'],
                    data['confidence_upper']
                )
            
            print(result)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error: Invalid JSON input - {e}")
            sys.exit(1)
    else:
        print("Usage:")
        print("  Interactive mode: python decision_matrix.py")
        print("  JSON mode: python decision_matrix.py '{...}'")
        print("\nExample:")
        print('  python decision_matrix.py \'{"actual_rate": 8.5, "expected_rate": 10, "sample_size": 200, "confidence_lower": 5.2, "confidence_upper": 11.8}\'')
        sys.exit(1)


if __name__ == "__main__":
    main()
