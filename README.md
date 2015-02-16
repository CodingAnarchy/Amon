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
* CSRF verification on API calls while logged in
  
Able to use GnuPG to do encryption related tasks
  
* encrypt and decrypt a message
* sign a message and verify signatures
* import and export public and private keys
* list keys in keyring
* generate new key for user
    
Able to work with Gmail

* send email using Gmail SMTP server (must have Gmail account)
* fetch email from Gmail using IMAP (currently set to get emails with PGP messages)
* fetch headers for listing of email
* fetch mailbox listing with nested mailboxes

GUI interface

* menu bar options
* preferences menu saves preferences to disk in encrypted format
* mailbox and mail listing (sometimes freezes on updating due to apparent bug (Possibly [Glib bug](https://bugs.launchpad.net/ubuntu/+source/gnome-control-center/+bug/1264368))
  * Receives "Warning: Source ID XXX was not found when attempting to remove it" message on trying to append list item
  * List does not accept any further appends after this point.
  
# In Development

* Continued keybase API support (signup in progress)
* Continued GPG support
* Support for working with encrypted and plaintext files
* Email parsing and decrypting support
* GUI interface (using GTK+3)
  
# Obligatory Reminder

No code in this repository is guaranteed to work and is in great flux as development occurs.

# Donation BTC Address

If you'd like to donate Bitcoin to assist in development of this software, donations can be sent to 1DXxbZJr7ubUd8QBxvcPVvpPERiQXTDCv6.
Donations are also accepted via email (such as with Coinbase) to mtanous22@gmail.com.
    
