# Telegram Package Tracking

Telegram package tracking service with backend code and bot instructions.

# How to Use

1. Talk to ``BotFather`` in Telegram to setup the bot.

2. Add the bot to a channel with administrative privileges so that the bot can send messages to the channel.

3. Get the code.

4. Run ``./setup.sh``.

5. Export ``TELEGRAM_BOT_TOKEN`` and ``USPS_TOKEN`` environmental variables.

6. Run the ``packageTrackingBackend.py`` script.

7. In Telegram, copy and paste the following text to ``BotFather`` after ``/setcommand`` and choosing the right bot.

```
start - greetings
help -show command usage
usps - enter a tracking number
clear - clear all tracking
```
