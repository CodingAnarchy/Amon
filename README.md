# Amon v0.0.1

An interface for Keybase.io and secure email written in Python.

Currently in development - being used to familiarize myself with Keybase for future project work.

# Status
  
Able to login to keybase and perform basic functionality
  
* fetch a user's public key
* fetch the logged in user's private key and decode it
* lookup users information on keybase (some issues on keybase side - see keybase-issues [#1341](https://github.com/keybase/keybase-issues/issues/1341)
* autocomplete API call (could be used for search later)
* kill user sessions
* update user profile (must do all fields at once currently)
  
Able to use GnuPG to do encryption related tasks
  
* encrypt and decrypt a message
* import and export public and private keys
* list keys in keyring
    
Able to send email using Gmail SMTP server (must have Gmail account)

# In Development

* CSRF verification on API calls while logged in
  
# Obligatory Reminder

No code in this repository is guaranteed to work and is in great flux as development occurs.
    
