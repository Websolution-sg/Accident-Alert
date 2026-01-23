# Waze Accident Monitor for Telegram

This application monitors Waze for accident occurrences in Singapore and automatically posts them to your Telegram channel.

## Features

- 🚨 Real-time accident monitoring from Waze
- 📱 Automatic posting to Telegram channel
- 📍 Location details with Google Maps and Waze links
- ⏰ Configurable check intervals
- 🔄 Prevents duplicate posts

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Create a Telegram Channel

1. Create a new channel in Telegram
2. Add your bot as an administrator to the channel
3. Get your channel ID:
   - For public channels: Use `@yourchannel` format
   - For private channels: You'll need the numeric ID (e.g., `-1001234567890`)

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Application

Option A: Set environment variables (recommended)
```bash
# Windows
set TELEGRAM_BOT_TOKEN=your_bot_token_here
set TELEGRAM_CHANNEL_ID=@yourchannel

# Linux/Mac
export TELEGRAM_BOT_TOKEN=your_bot_token_here
export TELEGRAM_CHANNEL_ID=@yourchannel
```

Option B: Edit the script directly
- Open `waze_accident_monitor.py`
- Find the `main()` function
- Replace `YOUR_BOT_TOKEN_HERE` and `@yourchannel` with your values

### 5. Run the Application

```bash
python waze_accident_monitor.py
```

The application will:
- Check Waze every 5 minutes (configurable)
- Post new accidents to your Telegram channel
- Display status messages in the console

## Configuration

You can modify the check interval in the `main()` function:

```python
# Check every 2 minutes (120 seconds)
monitor.monitor_and_post(check_interval=120)
```

You can also adjust the Singapore bounding box in the `__init__` method if needed.

## Message Format

Each accident alert includes:
- 📍 Location (street and city)
- 🕐 Time reported
- 📊 Accident type (if available)
- 👤 Reporter information
- 📈 Confidence level
- ✅ Reliability score
- 🗺️ Google Maps link
- 🚗 Waze navigation link

## Troubleshooting

### Bot can't post to channel
- Make sure the bot is added as an administrator to your channel
- Verify the channel ID is correct

### No accidents detected
- The Waze API may not always have active accidents
- Try adjusting the bounding box coordinates
- Check your internet connection

### Rate limiting
- The default 5-minute interval should prevent rate limiting
- Don't set the interval too low (< 1 minute)

## Notes

- The application uses Waze's public API which may change
- Accident data depends on Waze user reports
- Keep your bot token secure and never share it publicly
- The application will run continuously until stopped (Ctrl+C)

## License

This project is for educational purposes. Please respect Waze's terms of service.
