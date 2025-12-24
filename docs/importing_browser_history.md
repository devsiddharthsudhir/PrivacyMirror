# Importing browser history (offline)

Ethical Mirror can read **Chrome/Edge** history from the browser’s SQLite database.  
Because browsers lock this file, follow one of these:

## Safer method (recommended)
1. Close Chrome / Edge fully.
2. Copy the History file to a temporary location (e.g., Desktop).
3. Import the *copy* into Ethical Mirror.

## Typical locations

### Windows (Chrome)
`C:\Users\<you>\AppData\Local\Google\Chrome\User Data\Default\History`

### macOS (Chrome)
`~/Library/Application Support/Google/Chrome/Default/History`

### Linux (Chrome)
`~/.config/google-chrome/Default/History`

Edge locations are similar but under Microsoft.

## What we read
We read only:
- URL
- page title (if available)
- visit timestamps

We do not modify the database.

## Privacy note
You must only import **your own** browser history with **your own** consent.
