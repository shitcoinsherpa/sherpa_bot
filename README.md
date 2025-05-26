# AI Twitter Bot

This bot automatically posts about crypto or artificial intelligence news using AI personalities. It's like having your own crypto influencer that never sleeps.

## What You Need
- A computer (Windows, Mac, or Linux)
- Internet connection
- Two accounts:
  1. OpenAI account (for the AI brain)
  2. Twitter/X developer account (for posting)

## Step 1: Get Your Keys
You need two sets of keys. Here's how to get them:

### OpenAI Key (for the AI brain)
1. Go to https://platform.openai.com/api-keys
2. Sign up if you haven't
3. Add a payment method (they charge a tiny bit per tweet)
4. Click "Create new secret key"
5. Copy it somewhere safe

### Twitter Keys (for posting)
1. Go to https://developer.twitter.com/portal/dashboard
2. Sign up for a developer account
3. Create a new Project and App
4. Find "Keys and Tokens"
5. Generate and save ALL of these:
   - API Key and Secret
   - Access Token and Secret
6. In your app settings, make sure to enable "Read and Write"

## Step 2: Install & Run

### On Windows:
1. Double-click `build.bat` and wait
2. Double-click `run.bat`
3. That's it!

### On Mac:
1. Open Terminal in the bot's folder
2. Make the scripts executable:
   ```bash
   chmod +x build.sh run.sh
   ```
3. Run the setup:
   ```bash
   ./build.sh
   ```
   - If you get permission errors, try:
     ```bash
     sudo ./build.sh
     ```
   - First run will install Homebrew and Python if needed
   - After Homebrew installs, you may need to start a new terminal
4. Start the bot:
   ```bash
   ./run.sh
   ```

### On Linux:
1. Open Terminal in the bot's folder
2. Make the scripts executable:
   ```bash
   chmod +x build.sh run.sh
   ```
3. Run the setup:
   ```bash
   ./build.sh
   ```
   - If you get permission errors, try:
     ```bash
     sudo ./build.sh
     ```
   - Different distributions use different package managers:
     - Ubuntu/Debian: Uses apt-get
     - Fedora: Uses dnf
     - CentOS/RHEL: Uses yum
     - Arch: Uses pacman
4. Start the bot:
   ```bash
   ./run.sh
   ```

## Step 3: Set Up Your Bot
1. When the app opens, paste in your API keys
2. Create an AI character (like "Angry Crypto Trader" or "Blockchain Prophet")
3. Click "Enable Scheduler" to let it run automatically

## Important Notes
- The bot posts every 1.5 hours
- Maximum 500 tweets per month
- The following files are created automatically and contain your private data - never share them:
  - encryption.key
  - encrypted_credentials.bin
  - encrypted_characters.bin

## Help! Something's Wrong!

### Windows Users:
- If you see a blue SmartScreen popup, click "More Info" then "Run Anyway"
- If it says "Python not found", close and reopen the program
- Make sure you're running as Administrator if installation fails

### Mac Users:
- If Homebrew installation fails, check the [official guide](https://brew.sh)
- After installing Homebrew, you may need to restart your terminal
- If Python installation fails:
  ```bash
  brew doctor
  brew update
  brew cleanup
  ```
- Common permission fixes:
  ```bash
  sudo chown -R $(whoami) $(brew --prefix)/*
  ```

### Linux Users:
- Different distributions need different commands:
  - Ubuntu/Debian: `sudo apt-get install python3.10`
  - Fedora: `sudo dnf install python3.10`
  - CentOS/RHEL: `sudo yum install python3.10`
  - Arch: `sudo pacman -Sy python`
- If Python is installed but not found, check your PATH:
  ```bash
  echo $PATH
  which python3.10
  ```
- For permission issues:
  ```bash
  sudo chown -R $USER:$USER .
  ```

### Browser Issues:
- The app should open automatically in your default browser
- If it doesn't, manually go to: http://127.0.0.1:7860
- Make sure no other app is using port 7860

Still not working? Make sure:
1. Your internet connection is working
2. You copied all the API keys correctly
3. You're running from the correct directory
4. All files were extracted from the zip
5. You have the right permissions (try with sudo/admin)
6. Python 3.10 is in your system PATH
