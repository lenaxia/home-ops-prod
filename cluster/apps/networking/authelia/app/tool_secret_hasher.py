import hashlib, binascii
import os

def hash_secret(secret):
    # Generate a random 16-byte salt
    salt = os.urandom(16)

    # Number of iterations
    iterations = 310000

    # Generate hash using PBKDF2
    key = hashlib.pbkdf2_hmac('sha512', secret.encode('utf-8'), salt, iterations, dklen=64)

    # Format the hash with algorithm, iterations, salt, and hash
    hashed_secret = f"$pbkdf2-sha512${iterations}${binascii.hexlify(salt).decode('utf-8')}${binascii.hexlify(key).decode('utf-8')}"
    
    return hashed_secret

def main():
    while True:
        # Input the secret from user
        secret = input("Enter the secret to hash (or type 'exit' to quit): ")
        if secret.lower() == 'exit':
            print("Exiting...")
            break
        
        # Generate and print the hash
        hashed_secret = hash_secret(secret)
        print("\nHashed Secret:\n", hashed_secret, "\n\n")
        print()

if __name__ == "__main__":
    main()

