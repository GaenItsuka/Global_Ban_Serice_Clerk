# Global_Ban_Serice_Clerk
A telegram bot to process global ban request.

## Installation

### Install dependencies

To install dependencies, please run the following command:
```
pip install -r requirements.txt
```

### Install package

To install this package, you may choose one of the following options:

```
# Install in editable mode
pip install -e .

# Install to site-packages
python setup.py install --user
```

## Quick Start

Please export your bot token as environment variable before running the bot:

```
export BOT_TOKEN=<your bot token>
```

After the bot token is ready, you may start the bot with your user ID:
```
python -m Global_Ban_Serice_Clerk --ownerID <your telegram user ID>
```