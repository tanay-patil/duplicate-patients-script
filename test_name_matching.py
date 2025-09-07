#!/usr/bin/env python3
"""
Test script for name matching logic
"""

from config import Config
from duplicate_patient_manager import DuplicatePatientManager

def test_name_matching_cases():
    """Test various name matching scenarios"""
    config = Config()
    manager = DuplicatePatientManager(config)
    
    print("🧪 Testing Name Matching Logic")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        # Should MATCH - Direct match
        ("John", "Doe", "John", "Doe", True),
        ("Mary", "Smith", "Mary", "Smith", True),
        
        # Should MATCH - Similar names (fuzzy match)
        ("John", "Doe", "Jon", "Doe", True),
        ("Mary", "Johnson", "Mary", "Johnson", True),  # Exact match for clarity
        
        # Should MATCH - Name interchange
        ("John", "Doe", "Doe", "John", True),
        ("Mary", "Smith", "Smith", "Mary", True),
        
        # Should NOT MATCH - Only first name matches
        ("John", "Doe", "John", "Smith", False),
        ("Mary", "Johnson", "Mary", "Williams", False),
        
        # Should NOT MATCH - Only last name matches
        ("John", "Smith", "Michael", "Smith", False),
        ("David", "Johnson", "Robert", "Johnson", False),
        
        # Should NOT MATCH - Completely different names
        ("John", "Doe", "Mary", "Smith", False),
        ("Alice", "Johnson", "Bob", "Williams", False),
        
        # Should NOT MATCH - Missing names
        ("John", "", "John", "Doe", False),
        ("", "Doe", "John", "Doe", False),
        
        # Edge cases
        ("Jean-Claude", "Van Damme", "Jean", "Claude", False),  # Should not match partial names
        ("Mary Ann", "Smith", "Mary", "Ann Smith", False),      # Complex name structures
    ]
    
    passed = 0
    failed = 0
    
    for i, (fname1, lname1, fname2, lname2, expected_match) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        result = manager.calculate_name_similarity(fname1, lname1, fname2, lname2)
        actual_match = result['is_name_match']
        
        status = "✅ PASS" if actual_match == expected_match else "❌ FAIL"
        if actual_match == expected_match:
            passed += 1
        else:
            failed += 1
            
        print(f"  Input: '{fname1} {lname1}' vs '{fname2} {lname2}'")
        print(f"  Expected: {'MATCH' if expected_match else 'NO MATCH'}")
        print(f"  Actual: {'MATCH' if actual_match else 'NO MATCH'} ({result['match_type']}, {result['overall_similarity']}%)")
        print(f"  Status: {status}")
        
        if actual_match != expected_match:
            print(f"  Details: {result['details']}")
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print(f"Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("🎉 All tests passed! Name matching logic is working correctly.")
    else:
        print("⚠️ Some tests failed. Please review the name matching logic.")

if __name__ == "__main__":
    test_name_matching_cases()
