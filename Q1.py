#Q1.py
import os

RAW_FILE = "raw_text.txt"
ENC_FILE = "encrypted_text.txt"
DEC_FILE = "decrypted_text.txt"


def shift_lower_first(c, k): 
    idx = (ord(c) - ord('a') + (k % 13)) % 13
    return chr(ord('a') + idx)

def shift_lower_second(c, k): 
    idx = (ord(c) - ord('n') + (k % 13)) % 13
    return chr(ord('n') + idx)

def shift_upper_first(c, k):  
    idx = (ord(c) - ord('A') + (k % 13)) % 13
    return chr(ord('A') + idx)

def shift_upper_second(c, k):  
    idx = (ord(c) - ord('N') + (k % 13)) % 13
    return chr(ord('N') + idx)

# encryption rules apply different shift formulas depending on
# letter case and whether the letter is in the first or second half of the alphabet.
def encrypt_character(ch, shift1, shift2):
    prod = shift1 * shift2
    ssum = shift1 + shift2

    if 'a' <= ch <= 'z':
        if ch <= 'm':            
            return shift_lower_first(ch, +prod)
        else:                     
            return shift_lower_second(ch, -ssum)
    elif 'A' <= ch <= 'Z':
        if ch <= 'M':             
            return shift_upper_first(ch, -shift1)
        else:                      
            return shift_upper_second(ch, +(shift2 * shift2))
    else:
        return ch  

#decryption reverses the encryption shifts using opposite signs.
def decrypt_character(ch, shift1, shift2):
    prod = shift1 * shift2
    ssum = shift1 + shift2

    if 'a' <= ch <= 'z':
        if ch <= 'm':             
            return shift_lower_first(ch, -prod)
        else:                     
            return shift_lower_second(ch, +ssum)
    elif 'A' <= ch <= 'Z':
        if ch <= 'M':             
            return shift_upper_first(ch, +shift1)
        else:                     
            return shift_upper_second(ch, -(shift2 * shift2))
    else:
        return ch  


def encrypt_file(shift1, shift2):
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    enc = ''.join(encrypt_character(c, shift1, shift2) for c in text)
    with open(ENC_FILE, "w", encoding="utf-8") as f:
        f.write(enc)
    print("Encryption complete. Output written to 'encrypted_text.txt'.")

def decrypt_file(shift1, shift2):
    with open(ENC_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    dec = ''.join(decrypt_character(c, shift1, shift2) for c in text)
    with open(DEC_FILE, "w", encoding="utf-8") as f:
        f.write(dec)
    print("Decryption complete. Output written to 'decrypted_text.txt'.")

def verify_files():
    with open(RAW_FILE, "r", encoding="utf-8") as f1, open(DEC_FILE, "r", encoding="utf-8") as f2:
        same = f1.read() == f2.read()
    if same:
        print("Decryption Successful: Original and decrypted files match.")
    else:
        print("Decryption Failed: Files do not match.")


if __name__ == "__main__":
    shift1 = int(input("Enter shift1: "))
    shift2 = int(input("Enter shift2: "))

    encrypt_file(shift1, shift2)
    decrypt_file(shift1, shift2)
    verify_files()
