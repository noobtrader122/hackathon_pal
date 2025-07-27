""""
----------------------------------------------------------------------
----------------------------------------------------------------------
"""

import hashlib

def hash_password(password):
    # Ideally use werkzeug.security or passlib for better security!
    import werkzeug.security
    return werkzeug.security.generate_password_hash(password)

def verify_password(user_input, hashed):
    import werkzeug.security
    return werkzeug.security.check_password_hash(hashed, user_input)

