"""
Test script to verify bcrypt password length handling
Tests the fix for "password cannot be longer than 72 bytes" error
"""

from passlib.context import CryptContext
from app.utils.password_utils import truncate_password_to_bcrypt_limit

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_bcrypt_password_limits():
    """Test that passwords are correctly truncated to 72 bytes for bcrypt"""
    
    print("=" * 60)
    print("Testing Bcrypt Password Length Handling")
    print("=" * 60)
    
    # Test 1: Short password (should work unchanged)
    short_pass = "MyPassword123"
    truncated = truncate_password_to_bcrypt_limit(short_pass)
    print(f"\n✓ Test 1: Short password ({len(short_pass)} chars)")
    print(f"  Original: {short_pass}")
    print(f"  Truncated: {truncated}")
    print(f"  Bytes: {len(truncated.encode('utf-8'))}")
    
    # Test 2: Password at the limit
    exact_limit = "a" * 72
    truncated = truncate_password_to_bcrypt_limit(exact_limit)
    print(f"\n✓ Test 2: Password at 72 byte limit")
    print(f"  Length: {len(truncated.encode('utf-8'))} bytes")
    assert len(truncated.encode('utf-8')) == 72
    
    # Test 3: Long password (should be truncated)
    long_pass = "x" * 100
    truncated = truncate_password_to_bcrypt_limit(long_pass)
    print(f"\n✓ Test 3: Long password ({len(long_pass)} chars)")
    print(f"  Original bytes: {len(long_pass.encode('utf-8'))}")
    print(f"  Truncated bytes: {len(truncated.encode('utf-8'))}")
    assert len(truncated.encode('utf-8')) <= 72
    
    # Test 4: Very long password (300 chars)
    very_long = "SuperLongPassword" * 20  # ~320 chars
    truncated = truncate_password_to_bcrypt_limit(very_long)
    print(f"\n✓ Test 4: Very long password ({len(very_long)} chars)")
    print(f"  Original bytes: {len(very_long.encode('utf-8'))}")
    print(f"  Truncated bytes: {len(truncated.encode('utf-8'))}")
    assert len(truncated.encode('utf-8')) <= 72
    
    # Test 5: Bcrypt hashing and verification with truncated password
    print(f"\n✓ Test 5: Bcrypt hash/verify with long password")
    original_long = "MyUltraSecurePassword" * 10  # ~210 chars
    truncated_for_hash = truncate_password_to_bcrypt_limit(original_long)
    
    try:
        # Hash the truncated password
        hashed = pwd_ctx.hash(truncated_for_hash)
        print(f"  ✓ Successfully hashed truncated password")
        
        # Verify the truncated password
        is_valid = pwd_ctx.verify(truncated_for_hash, hashed)
        assert is_valid, "Password verification failed"
        print(f"  ✓ Successfully verified password")
        
        # Try to verify with wrong password
        is_invalid = pwd_ctx.verify("WrongPassword", hashed)
        assert not is_invalid, "Should reject wrong password"
        print(f"  ✓ Correctly rejected wrong password")
        
    except Exception as e:
        print(f"  ✗ Error during hash/verify: {e}")
        raise
    
    # Test 6: UTF-8 multi-byte characters
    print(f"\n✓ Test 6: UTF-8 multi-byte characters (Hindi)")
    hindi_pass = "नमस्ते" * 20  # Multi-byte UTF-8 characters
    truncated = truncate_password_to_bcrypt_limit(hindi_pass)
    print(f"  Original: {hindi_pass[:20]}... ({len(hindi_pass)} chars)")
    print(f"  Truncated bytes: {len(truncated.encode('utf-8'))}")
    assert len(truncated.encode('utf-8')) <= 72
    print(f"  Truncated: {truncated[:10]}...")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Bcrypt password length handling works correctly")
    print("=" * 60)


if __name__ == "__main__":
    test_bcrypt_password_limits()
