"""
Test TOTP Secret Format
Helps you validate your TOTP secret before running the bot
"""

def validate_totp_secret(secret):
    """Validate if a string is a valid base32 TOTP secret"""
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=')
    secret_upper = secret.upper()
    invalid_chars = set(secret_upper) - valid_chars
    
    print(f"\nTOTP Secret Analysis:")
    print(f"  Length: {len(secret)}")
    print(f"  Uppercase: {secret_upper}")
    print(f"  Valid base32: {'YES' if not invalid_chars else 'NO'}")
    
    if invalid_chars:
        print(f"  Invalid characters: {invalid_chars}")
        print("\n  TOTP secrets should only contain:")
        print("    - Letters A-Z")
        print("    - Numbers 2-7")
        print("    - Optional padding: =")
        return False
    
    # Try to generate a TOTP token
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()
        print(f"\n  ✓ Valid! Current 6-digit code: {token}")
        return True
    except Exception as e:
        print(f"\n  ✗ Error generating TOTP: {e}")
        return False

def main():
    print("="*70)
    print("TOTP Secret Validator")
    print("="*70)
    print()
    print("The TOTP secret is the long base32 string you got when setting up")
    print("two-factor authentication (NOT the 6-digit code from your app).")
    print()
    print("Example valid TOTP secret: JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP")
    print()
    
    from getpass import getpass
    secret = getpass("Enter your TOTP secret to validate: ").strip()
    
    if validate_totp_secret(secret):
        print("\n✓ Your TOTP secret is valid! You can use it with the bot.")
    else:
        print("\n✗ Invalid TOTP secret. Please check and try again.")
        print("\nTip: If you don't have the TOTP secret, you may need to:")
        print("  1. Disable 2FA on Angel One")
        print("  2. Re-enable it and save the base32 secret this time")
        print("  3. Or scan the QR code with an app that shows the secret")

if __name__ == "__main__":
    main()
