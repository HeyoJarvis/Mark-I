# 📧 Gmail API Setup Guide

## Quick Setup Checklist

- [ ] Create Google Cloud Project
- [ ] Enable Gmail API
- [ ] Create OAuth 2.0 Credentials
- [ ] Download credentials JSON file
- [ ] Place file in project directory
- [ ] Set environment variable
- [ ] Test connection

## Step-by-Step Instructions

### 1. Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create Project**:
   - Click "Select a project" → "New Project"
   - Project name: `jarvis-communication-system`
   - Click "Create"

### 2. Enable Gmail API

1. **Navigate to APIs & Services**:
   - Left sidebar → "APIs & Services" → "Library"
2. **Search and Enable**:
   - Search: "Gmail API"
   - Click "Gmail API" → "Enable"

### 3. Configure OAuth Consent Screen

1. **Go to OAuth consent screen**:
   - "APIs & Services" → "OAuth consent screen"
2. **Configure**:
   - User Type: "External" (for personal use)
   - App name: `Jarvis Communication System`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
3. **Scopes**: Skip (click "Save and Continue")
4. **Test users**: Add your Gmail address
5. **Summary**: Click "Back to Dashboard"

### 4. Create OAuth Client ID

1. **Go to Credentials**:
   - "APIs & Services" → "Credentials"
2. **Create Credentials**:
   - Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. **Configure**:
   - Application type: "Desktop application"
   - Name: `Jarvis Gmail Client`
   - Click "Create"
4. **Download**:
   - Click "Download JSON" button
   - Save as `gmail_credentials.json`

### 5. Place Credentials File

**Move the downloaded file to your project directory:**

```bash
# Your file should be placed here:
/home/sdalal/test/ProjectMarmalade/JarvisAlive/gmail_credentials.json
```

### 6. Set Environment Variable

**Option A: For current session**
```bash
export GMAIL_CREDENTIALS_PATH=/home/sdalal/test/ProjectMarmalade/JarvisAlive/gmail_credentials.json
```

**Option B: Permanent (add to ~/.bashrc)**
```bash
echo 'export GMAIL_CREDENTIALS_PATH=/home/sdalal/test/ProjectMarmalade/JarvisAlive/gmail_credentials.json' >> ~/.bashrc
source ~/.bashrc
```

### 7. Test Your Setup

**Run the Gmail setup test:**
```bash
cd /home/sdalal/test/ProjectMarmalade/JarvisAlive
python setup_gmail.py
```

**First-time authentication:**
- A browser window will open
- Sign in with your Google account
- Grant permissions to the app
- You'll see "The authentication flow has completed"
- A `gmail_token.json` file will be created automatically

## File Structure After Setup

```
JarvisAlive/
├── gmail_credentials.json     # Your OAuth credentials (keep private!)
├── gmail_token.json          # Auto-generated auth token (keep private!)
├── setup_gmail.py            # Setup test script
└── test_communication_system.py  # Full system test
```

## Testing Your Setup

### Basic Test
```bash
python setup_gmail.py
```

### Full Communication System Test
```bash
python test_communication_system.py
```

## Troubleshooting

### Common Issues

**❌ "Credentials file not found"**
- Check file path: `/home/sdalal/test/ProjectMarmalade/JarvisAlive/gmail_credentials.json`
- Verify environment variable: `echo $GMAIL_CREDENTIALS_PATH`

**❌ "Gmail API not enabled"**
- Go to Google Cloud Console
- APIs & Services → Library
- Search "Gmail API" → Enable

**❌ "OAuth consent screen not configured"**
- Go to APIs & Services → OAuth consent screen
- Complete the configuration steps above

**❌ "Browser authentication fails"**
- Make sure you're using the correct Google account
- Check that your email is added as a test user
- Try incognito/private browsing mode

**❌ "Invalid credentials"**
- Re-download the credentials file from Google Cloud Console
- Make sure it's named `gmail_credentials.json`
- Check that the JSON file is valid (not corrupted)

### Security Notes

- **Keep credentials private**: Never commit `gmail_credentials.json` to version control
- **Token expiry**: The `gmail_token.json` will auto-refresh, but may need re-authentication occasionally
- **Scopes**: The system requests minimal required permissions (read, send, modify)

## What Happens After Setup

Once Gmail is configured, the communication system will:

1. **Monitor your Gmail** for new messages
2. **Classify messages** using AI (if Claude API key is set)
3. **Trigger automated responses** based on message type
4. **Send email sequences** for lead nurturing
5. **Integrate with semantic chat** for natural language control

## Next Steps

After Gmail setup is complete:

1. **Set up Claude API** for AI message classification
2. **Configure WhatsApp** (optional) for multi-channel monitoring
3. **Test the full system** with `python test_communication_system.py`
4. **Start using semantic chat** to control the system

## Support

If you encounter issues:
- Check the troubleshooting section above
- Review Google Cloud Console configuration
- Verify all files are in the correct locations
- Test with the setup script: `python setup_gmail.py` 