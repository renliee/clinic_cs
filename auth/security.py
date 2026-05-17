"""
Password hashing using bcrypt.
- autogenerate and embed salt in every hash.
- rounds controls how many time the hashing is done, higher = more secure but slower.
- we use salt as extra random char in the pw, so same password generate diff hash.
"""

import bcrypt

def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    Returns the hash as a UTF-8 string (store as String in db column)
    """
    password_bytes = plain_password.encode("utf-8") #bcrypt only work in bytes
    #generate salt and set rounds to 12 (hashing will be done 2^12 times and only compare the final hashing)
    salt = bcrypt.gensalt(rounds=12) 
    hashed_bytes = bcrypt.hashpw(password_bytes, salt) #hash using the pw and salt

    return hashed_bytes.decode("utf-8") #return the hashed bytes as a string

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """verify a plain text password againts bcrypted password store in db (return True if matched, otherwise False)."""
    #convert both string to bytes
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    #checkpw extract the salt from stored hash, hash the plain password, then compare 
    return bcrypt.checkpw(password_bytes, hashed_bytes)