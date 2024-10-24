from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from stellar_sdk import Server, Asset
from datetime import datetime
from datetime import timezone
import re
import asyncio
import aiohttp
import certifi
import ssl
import psycopg2
import os

# Get the DATABASE_URL from Heroku environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Connect to PostgreSQL using psycopg2
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Create the necessary table for storing wallets if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_wallets (
        user_id BIGINT,
        wallet_address TEXT,
        first_xai_transaction_date TEXT,
        PRIMARY KEY (user_id, wallet_address)
    )
''')
conn.commit()

# Initialize Stellar server
server = Server("https://horizon.stellar.org")

# Example assets
xai_asset = Asset("XAI", "GDW4UCJVOUIRLXVY4FWSXQJBCIA3QZPFMVRL3KMAIMTCXASWGBJFRXAI")
x_asset = Asset("X", "GAS4LCHPWEHCWRPR2LAIRCYWGSPSUID7HGYGTAIAR4B5E3SAW7YUQLAX")
tbc_asset = Asset("TBC", "GA5I7GQNVWGC6ETTA4XUNG6FHNEJ4HEOD363VRMT7SCOAUXQMJBGOTBC")
nlink_asset = Asset("NLINK", "GBX743B3DQKLE5XUN5Z56GOIVMMXRKQJTIRQSVIY3AH3JJQA53EMLINK")
starlink_asset = Asset("STARLINK", "GCKUU7BDNL7A4D7JABYE5WSHRXBPQJTKJYAAPEPNYJSV7CHRD5SSLINK")
hyper_asset = Asset("HYPER", "GCIELJ7SU5DNTLRZLXEANRZ2Q7TBP4FDXAV52NQQWSBFCKSMDNZRHYPR")

# Function to add wallet to the database
def add_wallet_to_db(user_id, wallet_address, first_xai_transaction_date):
    cursor.execute('INSERT OR IGNORE INTO user_wallets (user_id, wallet_address, first_xai_transaction_date) VALUES (?, ?, ?)', 
                   (user_id, wallet_address, first_xai_transaction_date))
    conn.commit()

# Function to get wallets from the database
def get_wallets_from_db(user_id):
    cursor.execute('SELECT wallet_address FROM user_wallets WHERE user_id = ?', (user_id,))
    return [row[0] for row in cursor.fetchall()]

# Function to get the custom keyboard
def get_custom_keyboard():
    keyboard = [
        ["💼 WALLET", "🚀 DIVIDENDS"],
        ["📥 Telegram Channel", "📊 LOBSTR"],
        ["📈 Check Tiers", "💸WITHDRAW"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_custom_keyboard()  # Get the custom keyboard
    await update.message.reply_text(
        "🔭*Welcome to the Musk’s lab!*🥼 \n\n🤖My name is *DiviBot* and my purpose here is to help you manage your dividends and track ROI seamlessly. \n\n⚖️With *DiviBot* you can get real-time updates and make smart investment decisions. You can always use my knowledges to check for the dividend tiers. \n\n🌎Join my creator’s Telegram channel for insights, and use the buy link to easily purchase *XAi* to grow your portfolio by upgrading your tiers!",
        parse_mode="Markdown",
        reply_markup=keyboard  # Attach the keyboard markup
   )

# Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💼 WALLET":
        await handle_wallet(update, context)
    elif text == "🚀 DIVIDENDS":
        await handle_dividends(update, context)
    elif text == "📥 Telegram Channel":
        await handle_telegram_channel(update, context)
    elif text == "📊 LOBSTR":
        await handle_lobstr(update, context)
    elif text == "📈 Check Tiers":
        await handle_tiers(update, context)
    else:
        await add_wallet(update, context)

# Wallet button handler (updated with Remove button)
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = get_wallets_from_db(user_id)
    if not wallets:
        await update.message.reply_text(
            "*❌There is no wallet recorded for your account.*\n✅Please send your Stellar PUBLIC KEY to add it.", parse_mode="Markdown")
    else:
        buttons = [
            [
                InlineKeyboardButton(wallet, callback_data=f"wallet_{wallet}"),
                InlineKeyboardButton("❌ Remove", callback_data=f"remove_{wallet}")
            ]
            for wallet in wallets
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "*👝Here are your wallets:*", parse_mode="Markdown", reply_markup=reply_markup)
        await update.message.reply_text(
            "*✅To add another wallet, please send your Stellar PUBLIC KEY.*", parse_mode="Markdown")
            
            # Function to remove wallet from the database
def remove_wallet_from_db(user_id, wallet_address):
    cursor.execute('DELETE FROM user_wallets WHERE user_id = ? AND wallet_address = ?', (user_id, wallet_address))
    conn.commit()

# Handler for removing a wallet
async def handle_remove_wallet_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("remove_"):
        wallet_address = data.split("_", 1)[1]
        user_id = query.from_user.id  # Use query.from_user to get the user ID
        remove_wallet_from_db(user_id, wallet_address)
        
        # Notify the user that the wallet was removed
        await query.edit_message_text(f"❌ Wallet {wallet_address} has been removed.")
        
        # Show the updated wallet list (this time we need to pass `query` instead of `update`)
        await handle_wallet(query, context)

# Add a timeout to the fetch call
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=3)

#FIRST TRANS
async def get_first_xai_transaction_date(wallet_address):
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        cursor = None
        max_iterations = 5000  # Increase the number of iterations to cover more records if needed
        iteration = 0
        batch_size = 90  # Adjust this to make smaller requests for faster processing
        
        async with aiohttp.ClientSession() as session:
            while iteration < max_iterations:
                # Create URL for operations, paginated with cursor, requesting smaller batches
                url = f"https://horizon.stellar.org/accounts/{wallet_address}/operations?order=asc&limit={batch_size}"
                if cursor:
                    url += f"&cursor={cursor}"

                async with session.get(url, ssl=ssl_context, timeout=10) as response:
                    if response.status != 200:
                        return f"Error fetching transaction history: Status Code {response.status}"

                    operations = await response.json()
                    records = operations.get('_embedded', {}).get('records', [])
                    if not records:
                        return "No transactions found."

                    # Search for the first XAI-related buy/sell offer or payment
                    for record in records:
                        if record['type'] in ['manage_buy_offer', 'manage_sell_offer', 'create_passive_sell_offer', 'payment', 'path_payment_strict_receive', 'path_payment_strict_send']:
                            if (
                                ('asset_code' in record and record['asset_code'] == 'XAI' and record.get('asset_issuer') == xai_asset.issuer) or
                                ('selling_asset_code' in record and record['selling_asset_code'] == 'XAI' and record.get('selling_asset_issuer') == xai_asset.issuer) or
                                ('buying_asset_code' in record and record['buying_asset_code'] == 'XAI' and record.get('buying_asset_issuer') == xai_asset.issuer)
                            ):
                                # Format the date to the desired output
                                transaction_date = record['created_at']
                                formatted_date = datetime.strptime(transaction_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d\n%H:%M:%S UTC")
                                return formatted_date

                    # Prepare for next iteration if there are more records
                    cursor = records[-1]['paging_token']
                    iteration += 1

            # If no XAI transaction was found within the limited iterations
            return "No XAI transactions found in recent history."
                
    except aiohttp.ClientError as e:
        return f"Error: Unable to connect to Horizon API. {e}"
    except asyncio.TimeoutError:
        return "Error: Request timed out. Please try again later."
    except Exception as e:
        return f"Error fetching transaction history: {e}"

    return None
    
# Properly escape special characters in MarkdownV2
def escape_markdown_v2(text):
    # Escape all special characters for MarkdownV2
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

#AD WALLET
# Function to add a wallet and fetch the first XAI transaction date
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = update.message.text.strip()

    if wallet_address.startswith("G") and len(wallet_address) == 56:
        # Send an immediate message to notify the user that the fetching process has started
        await update.message.reply_text("⏳ Fetching your wallet info... Please wait.")

        # Fetch the first XAI transaction date in the same flow
        first_xai_date = await get_first_xai_transaction_date(wallet_address)
        
        # After fetching, continue with adding the wallet to the database
        if first_xai_date:
            # Store the wallet and first XAI transaction date in the database
            add_wallet_to_db(user_id, wallet_address, first_xai_date)
            
            # Properly escape special characters in the wallet address for HTML mode
            escaped_wallet_address = wallet_address.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            await update.message.reply_text(
                f"✅ Wallet <code>{escaped_wallet_address}</code> added successfully!\n📅 First XAI transaction on: {first_xai_date}",
                parse_mode="HTML"
            )
        else:
            # If no XAI transactions are found, handle that case
            escaped_wallet_address = wallet_address.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            await update.message.reply_text(
                f"✅ Wallet <code>{escaped_wallet_address}</code> added successfully!\n⚠️ No XAI transactions found.",
                parse_mode="HTML"
            )
    else:
        # If the wallet address is invalid, send an error message
        await update.message.reply_text(
            "❌ Invalid wallet address.\nPlease send a valid Stellar wallet address starting with 'G'.",
            parse_mode="HTML"
        )
            
# Correct the wallet click handler to show the right balance for XAI
# Correct the wallet click handler to show the right balance for XAI
async def handle_wallet_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("wallet_"):
        wallet_address = data.split("_", 1)[1]
        try:
            # Fetch account data from Stellar network
            account = server.accounts().account_id(wallet_address).call()

            # Debug: Check account structure
            print(f"Account data for wallet {wallet_address}: {account}")

            # Check if 'balances' exists in the response and is a list
            balances = account.get("balances", [])
            if not isinstance(balances, list):
                await query.edit_message_text(f"Error: Balances data is not in a list format for {wallet_address}")
                return
            
            # Extract XAi balance, with a fallback of "0" if not found
            xai_balance = next(
                (b["balance"] for b in balances if b.get("asset_code") == "XAI" and b.get("asset_issuer") == xai_asset.issuer),
                "0"
            )
            
            # Calculate the XAI dividend tier and payment
            xai_tier, weekly_dividends = calculate_payment(float(xai_balance))

            # Format the dividend details
            dividend_info = format_dividends(weekly_dividends)

            # Format the response message
            message = (
                f"👝 <b>Wallet:</b> <code>{wallet_address}</code>\n"
                f"📊 <b>XAi Balance:</b> {xai_balance} XAi\n"
                f"🌐 <b>XAi Dividend Tier:</b> {xai_tier}\n"
                f"🪙 <b>Weekly Dividends:</b>\n{dividend_info}"
            )

            # Send the formatted response
            await query.edit_message_text(message, parse_mode="HTML")

        except Exception as e:
            # In case of an error, display a friendly message
            await query.edit_message_text(f"Error fetching wallet data: {e}")

# Helper function to format accumulated dividend information based on eligibility and tier
def format_accumulated_payment_info(accumulated_dividends, tier):
    # Define the dividend percentages for each tier and token eligibility
    token_percentage_map = {
        1: {"xai": 0.035, "tesla": 0.06, "xelon": 0.04, "tbc": None, "nlink": None, "x": None, "starlink": None},
        2: {"xai": 0.052, "tesla": 0.09, "xelon": 0.06, "tbc": 0.045, "nlink": None, "x": None, "starlink": None},
        3: {"xai": 0.08, "tesla": 0.13, "xelon": 0.12, "tbc": 0.07, "nlink": 0.02, "x": None, "starlink": None},
        4: {"xai": 0.105, "tesla": 0.22, "xelon": 0.17, "tbc": 0.09, "nlink": 0.03, "x": 0.0007, "starlink": None},
        5: {"xai": 0.16, "tesla": 0.42, "xelon": 0.35, "tbc": 0.12, "nlink": 0.06, "x": 0.0025, "starlink": 0.025},
        # Add other tiers here if applicable
    }

    # Retrieve the correct percentages for the given tier
    percentages = token_percentage_map.get(tier, {})

    # Format the dividend information based on eligibility and percentages for the given tier
    accumulated_payment_info = ""
    if percentages.get("xai"):
        accumulated_payment_info += f"<b>👑 {percentages['xai']*100:.1f}% xAI</b>: {accumulated_dividends[0]:.2f} XAi ({accumulated_dividends[0] * XAI_PRICE:.2f} XLM)\n"
    if percentages.get("tesla"):
        accumulated_payment_info += f"<b>© {percentages['tesla']*100:.1f}% TESLA</b>: {accumulated_dividends[1]:.5f} TESLA ({accumulated_dividends[1] * TESLA_PRICE:.2f} XLM)\n"
    if percentages.get("xelon"):
        accumulated_payment_info += f"<b>🔥 {percentages['xelon']*100:.1f}% XELON</b>: {accumulated_dividends[2]:.2f} XELON ({accumulated_dividends[2] * XELON_PRICE:.2f} XLM)\n"
    if percentages.get("tbc"):
        accumulated_payment_info += f"<b>⚙️ {percentages['tbc']*100:.1f}% TBC</b>: {accumulated_dividends[3]:.5f} TBC ({accumulated_dividends[3] * TBC_PRICE:.2f} XLM)\n"
    if percentages.get("nlink"):
        accumulated_payment_info += f"<b>🧠 {percentages['nlink']*100:.1f}% NLINK</b>: {accumulated_dividends[4]:.5f} NLINK ({accumulated_dividends[4] * NLINK_PRICE:.2f} XLM)\n"
    if percentages.get("x"):
        accumulated_payment_info += f"<b>✖ {percentages['x']*100:.2f}% X</b>: {accumulated_dividends[5]:.5f} X ({accumulated_dividends[5] * X_PRICE:.2f} XLM)\n"
    if percentages.get("starlink"):
        accumulated_payment_info += f"<b>⭐️ {percentages['starlink']*100:.2f}% STARLINK</b>: {accumulated_dividends[6]:.5f} STARLINK ({accumulated_dividends[6] * STARLINK_PRICE:.2f} XLM)\n"

    return accumulated_payment_info

#WITHDRAW
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = get_wallets_from_db(user_id)

    if not wallets:
        await update.message.reply_text(
            "*❌ Please add a wallet first by clicking on 💼 WALLET.*", parse_mode="Markdown"
        )
        return

    total_dividends = 0  # Initialize total dividends
    total_xlm_equivalent = 0  # Initialize total XLM equivalent
    message_parts = []

    # Asset prices
    XAI_PRICE = 3
    TESLA_PRICE = 1500
    XELON_PRICE = 0.8
    TBC_PRICE = 100
    NLINK_PRICE = 250
    STARLINK_PRICE = 50
    HYPER_PRICE = 75
    X_PRICE = 10

    # Iterate over each wallet
    for wallet_address in wallets:
        try:
            # Fetch the first XAI transaction date from the database
            cursor.execute('SELECT first_xai_transaction_date FROM user_wallets WHERE user_id = ? AND wallet_address = ?', (user_id, wallet_address))
            first_xai_date_row = cursor.fetchone()

            if not first_xai_date_row or not first_xai_date_row[0]:
                message_parts.append(f"👝 Wallet: `{wallet_address}`\n❌ No XAI transactions found in recent history.")
                continue

            first_xai_date = first_xai_date_row[0]

            # Get the first XAI transaction date and convert it to a datetime object
            try:
                first_xai_date_obj = datetime.strptime(first_xai_date, "%Y-%m-%d\n%H:%M:%S UTC")
            except ValueError as e:
                message_parts.append(f"Error fetching wallet data for `{wallet_address}`: `{e}`\n")
                continue

            # Convert naive datetime to timezone-aware in UTC
            first_xai_date_obj = first_xai_date_obj.replace(tzinfo=timezone.utc)

            # Get the current date in UTC (aware)
            current_date = datetime.now(timezone.utc)

            # Calculate the number of weeks between the first XAI transaction and today
            weeks_since_first_transaction = max((current_date - first_xai_date_obj).days // 7, 1)

            # Fetch account details from Stellar network
            account = server.accounts().account_id(wallet_address).call()
            balances = account["balances"]

            # Extract XAi balance by checking for the XAI asset
            xai_balance = next(
                (b["balance"] for b in balances if b.get("asset_code") == "XAI" and b.get("asset_issuer") == xai_asset.issuer),
                "0"  # Default to "0" if the asset is not found
            )
            xai_balance = float(xai_balance)

            if xai_balance == 0:
                message_parts.append(f"👝 Wallet: `{wallet_address}`\n❌ No XAi balance in this wallet.")
                continue

            # Calculate the weekly dividends
            xai_tier, weekly_dividends = calculate_payment(xai_balance)
           # print(f"Weekly Dividends for wallet {wallet_address}: {weekly_dividends}")

            # Ensure weekly_dividends is a list of dictionaries
            if isinstance(weekly_dividends, str):
               # print(f"Error: weekly_dividends is a string: {weekly_dividends}")
                continue

            # Accumulate dividends based on the number of weeks since the first transaction
            accumulated_dividends = [round(value['value'] * weeks_since_first_transaction, 5) for value in weekly_dividends if isinstance(value, dict)]
           # print(f"Accumulated Dividends for wallet {wallet_address}: {accumulated_dividends}")

            # Ensure that accumulated dividends are not zero
            if all(dividend == 0 for dividend in accumulated_dividends):
                print(f"Accumulated dividends are all zero for wallet: {wallet_address}")
                continue

            # Calculate XLM equivalent for each dividend
            accumulated_xlm_equivalents = []
            total_wallet_xlm = 0  # XLM for this specific wallet

            for dividend, accumulated_dividend in zip(weekly_dividends, accumulated_dividends):
                asset = dividend['asset']
                if asset == "XAi":
                    xlm_value = accumulated_dividend * XAI_PRICE
                elif asset == "TESLA":
                    xlm_value = accumulated_dividend * TESLA_PRICE
                elif asset == "XELON":
                    xlm_value = accumulated_dividend * XELON_PRICE
                elif asset == "TBC":
                    xlm_value = accumulated_dividend * TBC_PRICE
                elif asset == "NLINK":
                    xlm_value = accumulated_dividend * NLINK_PRICE
                elif asset == "X":
                    xlm_value = accumulated_dividend * X_PRICE
                elif asset == "STARLINK":
                    xlm_value = accumulated_dividend * STARLINK_PRICE
                elif asset == "HYPER":
                    xlm_value = accumulated_dividend * HYPER_PRICE
                else:
                    xlm_value = 0  # If we can't identify the asset

                accumulated_xlm_equivalents.append(xlm_value)
                total_wallet_xlm += xlm_value

            # Summing all accumulated dividends in XLM
            total_xlm_equivalent += total_wallet_xlm
           # print(f"Total XLM equivalent for wallet {wallet_address}: {total_wallet_xlm}")

            # Summing all accumulated dividends
            total_dividends += sum(accumulated_dividends)

            # Create formatted accumulated payment info for display
            accumulated_payment_info = "\n".join([
                f"{dividend['name']} {dividend['rate']*100:.1f}%: {accumulated_dividend:.5f} {dividend['asset']} (≈ {xlm_value:.2f} XLM)"
                for dividend, accumulated_dividend, xlm_value in zip(weekly_dividends, accumulated_dividends, accumulated_xlm_equivalents)
            ])

            message_parts.append(f"👝 Wallet: {wallet_address}\n📊 Accumulated Dividends for {weeks_since_first_transaction} weeks:\n{accumulated_payment_info}\n")

        except Exception as e:
            message_parts.append(f"Error fetching wallet data for `{wallet_address}`: `{e}`\n")
           # print(f"Error encountered for wallet {wallet_address}: {e}")

    # Prepare and send the final message
    if total_dividends > 0:
        message = (
            f"💸 <b>Withdrawal option soon available</b>\n\n"
            f"{'\n'.join(message_parts)}"
            f"\n💰 <b>Total XLM equivalent from all wallets:</b> {total_xlm_equivalent:.2f} XLM"
        )
        await update.message.reply_text(message, parse_mode="HTML")
    else:
        await update.message.reply_text(
            "*❌ No accumulated dividends found.*", parse_mode="Markdown"
        )
        
# Tiers and benefits handler (first part)
async def handle_tiers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tiers_message_part1 = (
        "Tier 1 - <b>1-150 xAI</b>\n"
        "👑 <b>3.5% xAI:</b> 0.04 - 5.25 xAI (0.11 - 15.75 XLM)\n"
        "© <b>6% TESLA:</b> 0.00012 - 0.02 TESLA (0.18 - 27.00 XLM)\n"
        "🔥 <b>4% XELON:</b> 0.15 - 22.50 XELON (0.12 - 18.00 XLM)\n\n"
        
        "Tier 2 - <b>151-600 xAI</b>\n"
        "👑 <b>5.2% xAI:</b> 7.85 - 31.20 XAi (23.56 - 93.60 XLM)\n"
        "© <b>9% TESLA:</b> 0.03 - 0.11 TESLA (40.77 - 162.00 XLM)\n"
        "🔥 <b>6% XELON:</b> 33.97 - 135.00 XELON (27.18 - 108.00 XLM)\n"
        "⚙ <b>4.5% TBC:</b> 0.20 - 0.81 TBC (20.38 - 81.00 XLM)\n\n"
        
        "Tier 3 - <b>601-1,200 xAI</b>\n"
        "👑 <b>8% xAI:</b> 48.08 - 96.00 XAi (144.24 - 288.00 XLM)\n"
        "© <b>13% TESLA:</b> 0.16 - 0.31 TESLA (234.39 - 468.00 XLM)\n"
        "🔥 <b>12% XELON:</b> 270.45 - 540.00 XELON (216.36 - 432.00 XLM)\n"
        "⚙ <b>7% TBC:</b> 1.26 - 2.52 TBC (126.21 - 252.00 XLM)\n"
        "🧠 <b>2% NLINK:</b> 0.14 - 0.29 NLINK (36.06 - 72.00 XLM)\n\n"
        
        "Tier 4 - <b>1,201-6,000 xAI</b>\n"
        "👑 <b>10.5% xAI:</b> 126.11 - 630.00 XAi (378.31 - 1,890.00 XLM)\n"
        "© <b>22% TESLA:</b> 0.53 - 2.64 TESLA (792.66 - 3,960.00 XLM)\n"
        "🔥 <b>17% XELON:</b> 765.64 - 3,825.00 XELON (612.51 - 3,060.00 XLM)\n"
        "⚙ <b>9% TBC:</b> 3.24 - 16.20 TBC (324.27 - 1,620.00 XLM)\n"
        "🧠 <b>3% NLINK:</b> 0.43 - 2.16 NLINK (108.09 - 540.00 XLM)\n"
        "✖ <b>0.07% X:</b> 0.25 - 1.26 X (2.52 - 12.60 XLM)\n"
   )

    tiers_message_part2 = (
        "Tier 5 - <b>6,001-12,000 xAI</b>\n"
        "👑 <b>16% xAI:</b> 960.16 - 1,920.00 XAi (2,880.48 - 5,760.00 XLM)\n"
        "© <b>42% TESLA:</b> 5.04 - 10.08 TESLA (7,561.26 - 15,120.00 XLM)\n"
        "🔥 <b>35% XELON:</b> 7,876.31 - 15,750.00 XELON (6,301.05 - 12,600.00 XLM)\n"
        "⚙ <b>12% TBC:</b> 21.60 - 43.20 TBC (2,160.36 - 4,320.00 XLM)\n"
        "🧠 <b>6% NLINK:</b> 4.32 - 8.64 NLINK (1,080.18 - 2,160.00 XLM)\n"
        "✖ <b>0.25% X:</b> 4.50 - 9.00 X (45.01 - 90.00 XLM)\n"
        "⭐ <b>2.5% STARLINK:</b> 9.00 - 18.00 STARLINK (450.08 - 900.00 XLM)\n\n"
        
        "Tier 6 - <b>12,001-28,000 xAI</b>\n"
        "👑 <b>28% xAI:</b> 3,360.28 - 7,840.00 XAi (10,080.84 - 23,520.00 XLM)\n"
        "© <b>65% TESLA:</b> 15.60 - 36.40 TESLA (23,401.95 - 54,600.00 XLM)\n"
        "🔥 <b>52% XELON:</b> 23,401.95 - 54,600.00 XELON (18,721.56 - 43,680.00 XLM)\n"
        "⚙ <b>22% TBC:</b> 79.21 - 184.80 TBC (7,920.66 - 18,480.00 XLM)\n"
        "🧠 <b>12% NLINK:</b> 17.28 - 40.32 NLINK (4,320.36 - 10,080.00 XLM)\n"
        "✖ <b>0.7% X:</b> 25.20 - 58.80 X (252.02 - 588.00 XLM)\n"
        "⭐ <b>5% STARLINK:</b> 36.00 - 84.00 STARLINK (1,800.15 - 4,200.00 XLM)\n"
        "🆎 <b>6% HYPER:</b> 28.80 - 67.20 HYPER (2,160.18 - 5,040.00 XLM)\n\n"

        "Tier 7 - <b>28,001-60,000 xAI</b>\n"
        "👑 <b>55% xAI:</b> 15,400.55 - 30,000.00 XAi (46,201.65 - 90,000.00 XLM)\n"
        "© <b>105% TESLA:</b> 58.80 - 114.00 TESLA (88,203.15 - 171,000.00 XLM)\n"
        "🔥 <b>90% XELON:</b> 94,503.37 - 183,750.00 XELON (75,602.70 - 147,000.00 XLM)\n"
        "⚙ <b>32% TBC:</b> 268.81 - 525.00 TBC (26,880.96 - 52,500.00 XLM)\n"
        "🧠 <b>18% NLINK:</b> 60.48 - 117.00 NLINK (15,120.54 - 29,250.00 XLM)\n"
        "✖ <b>1.2% X:</b> 100.80 - 195.00 X (1,008.04 - 1,950.00 XLM)\n"
        "⭐ <b>7% STARLINK:</b> 117.60 - 225.00 STARLINK (5,880.21 - 11,250.00 XLM)\n"
        "🆎 <b>9% HYPER:</b> 100.80 - 216.00 HYPER (7,560.27 - 16,200.00 XLM)\n\n"
        
        "Tier 8 - <b>60,001-120,000 xAI</b>\n"
        "👑 <b>110% xAI:</b> 66,001.10 - 132,000.00 XAi (198,003.30 - 396,000.00 XLM)\n"
        "© <b>215% TESLA:</b> 258.00 - 516.00 TESLA (387,006.45 - 774,000.00 XLM)\n"
        "🔥 <b>150% XELON:</b> 337,505.62 - 675,000.00 XELON (270,004.50 - 540,000.00 XLM)\n"
        "⚙ <b>55% TBC:</b> 990.02 - 1,980.00 TBC (99,001.65 - 198,000.00 XLM)\n"
        "🧠 <b>25% NLINK:</b> 180.00 - 360.00 NLINK (45,000.75 - 90,000.00 XLM)\n"
        "✖ <b>2.5% X:</b> 450.01 - 900.00 X (4,500.07 - 9,000.00 XLM)\n"
        "⭐ <b>10% STARLINK:</b> 360.01 - 720.00 STARLINK (18,000.30 - 36,000.00 XLM)\n"
        "🆎 <b>12% HYPER:</b> 288.00 - 576.00 HYPER (21,600.36 - 43,200.00 XLM)\n\n"
        
        "Tier 9 - <b>120,001-300,000 xAI</b>\n"
        "👑 <b>370% xAI:</b> 444,003.70 - 1,110,000.00 XAi (1,332,011.10 - 3,330,000.00 XLM)\n"
        "© <b>515% TESLA:</b> 1,236.01 - 3,090.00 TESLA (1,854,015.45 - 4,635,000.00 XLM)\n"
        "🔥 <b>220% XELON:</b> 990,008.25 - 2,475,000.00 XELON (792,006.60 - 1,980,000.00 XLM)\n"
        "⚙ <b>115% TBC:</b> 4,140.03 - 10,350.00 TBC (414,003.45 - 1,035,000.00 XLM)\n"
        "🧠 <b>35% NLINK:</b> 504.00 - 1,260.00 NLINK (126,001.05 - 315,000.00 XLM)\n"
        "✖ <b>5.5% X:</b> 1,980.02 - 4,950.00 X (19,800.17 - 49,500.00 XLM)\n"
        "⭐ <b>15% STARLINK:</b> 1,080.01 - 2,700.00 STARLINK (54,000.45 - 135,000.00 XLM)\n"
        "🆎 <b>18% HYPER:</b> 864.01 - 2,160.00 HYPER (64,800.54 - 162,000.00 XLM)\n\n"

        "Tier 10 - <b>300,001+ xAI</b>\n"
        "👑 <b>1050% xAI:</b> 3,150,010.50+ XAi (9,450,031.50+ XLM)\n"
        "© <b>2100% TESLA:</b> 12,600.04+ TESLA (18,900,063.00+ XLM)\n"
        "🔥 <b>275% XELON:</b> 3,093,760.31+ XELON (2,475,008.25+ XLM)\n"
        "⚙ <b>320% TBC:</b> 28,800.10+ TBC (2,880,009.60+ XLM)\n"
        "🧠 <b>50% NLINK:</b> 1,800.01+ NLINK (450,001.50+ XLM)\n"
        "✖ <b>7% X:</b> 6,300.02+ X (63,000.21+ XLM)\n"
        "⭐ <b>25% STARLINK:</b> 4,500.02+ STARLINK (225,000.75+ XLM)\n"
        "🆎 <b>30% HYPER:</b> 3,600.01+ HYPER (270,000.90+ XLM)\n"
   )

# Send the first message
    await update.message.reply_text(tiers_message_part1, parse_mode="HTML")

    # Send the second message after the first
    await update.message.reply_text(tiers_message_part2, parse_mode="HTML")

# Correct the dividend fetching logic
async def handle_dividends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    # Retrieve wallets from the database instead of using user_wallets
    wallets = get_wallets_from_db(user_id)
    
    if not wallets:
        await update.message.reply_text(
            "*❌ Please add a wallet first by clicking on 💼 WALLET.*", parse_mode="Markdown"
        )
        return

    for wallet_address in wallets:
        try:
            # Fetch account details from the Stellar network
            account = server.accounts().account_id(wallet_address).call()

            # Check if 'balances' exists in the response and is a list
            balances = account.get("balances", [])
            if not isinstance(balances, list):
                await update.message.reply_text(f"Error: Balances data is not in a list format for {wallet_address}")
                continue

            # Extract XAi balance using the correct asset code and issuer
            xai_balance = next(
                (b.get("balance") for b in balances if b.get("asset_code") == "XAI" and b.get("asset_issuer") == xai_asset.issuer),
                "0"  # Default to "0" if XAI asset is not found
            )

            # Convert the balance to a float for calculations
            xai_balance = float(xai_balance)
            
            # Calculate XAi dividend tier and payments
            xai_tier, weekly_dividends = calculate_payment(xai_balance)
            
            # Format the dividends properly for display
            dividends_info = "\n".join([
                f"{dividend['name']} {dividend['rate']*100:.1f}%: {dividend['value']:.2f} {dividend['asset']}"
                for dividend in weekly_dividends
            ])

            # Format the message
            message = (
                f"👝 <b>Wallet:</b> {wallet_address}\n"
                f"📊 <b>XAi Balance:</b> {xai_balance:.2f} XAi\n"
                f"🌐 <b>XAi Dividend Tier:</b> {xai_tier}\n"
                f"🪙 <b>Weekly Dividends:</b>\n{dividends_info}"
            )

            await update.message.reply_text(message, parse_mode="HTML")
        
        except Exception as e:
            await update.message.reply_text(f"Error fetching wallet data for `{wallet_address}`: `{e}`", parse_mode="Markdown")

# Telegram Channel handler
async def handle_telegram_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛩*Join our Telegram Channel: @whipspacex *\n\n 👑*Join our Whiplash Family: @Whiplash347*", parse_mode="Markdown")

# LOBSTR handler
async def handle_lobstr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*✅Buy XAI now on LOBSTR:* [https://lobstr.co/trade/XAI](https://lobstr.co/trade/XAI:GDW4UCJVOUIRLXVY4FWSXQJBCIA3QZPFMVRL3KMAIMTCXASWGBJFRXAI)\n\n"
        "*✅Buy TESLA now on LOBSTR:* [https://lobstr.co/trade/TESLA](https://lobstr.co/trade/TESLA:GBDJ47CSXL4XKEVLCJ6C3OJE23GTX2Q2SCOBXJFDWB2DPU3C4A5ELONX)\n\n"
        "*✅Buy X now on LOBSTR:* [https://lobstr.co/trade/X](https://lobstr.co/trade/X:GAS4LCHPWEHCWRPR2LAIRCYWGSPSUID7HGYGTAIAR4B5E3SAW7YUQLAX)\n\n"
        "*✅Buy XELON now on LOBSTR:* [https://lobstr.co/trade/XELON](https://lobstr.co/trade/XELON:GDPK4GJW4VOYBMDNYNMWMRCEQFDESBNGLBTTI5VZ5LRSJBPVZTTELONX)\n\n"
        "*✅Buy TBC now on LOBSTR:* [https://lobstr.co/trade/TBC](https://lobstr.co/trade/TBC:GA5I7GQNVWGC6ETTA4XUNG6FHNEJ4HEOD363VRMT7SCOAUXQMJBGOTBC)\n\n"
        "*✅Buy NLINK now on LOBSTR:* [https://lobstr.co/trade/NLINK](https://lobstr.co/trade/NLINK:GBX743B3DQKLE5XUN5Z56GOIVMMXRKQJTIRQSVIY3AH3JJQA53EMLINK)\n\n"
        "*✅Buy STARLINK now on LOBSTR:* [https://lobstr.co/trade/STARLINK](https://lobstr.co/trade/STARLINK:GCKUU7BDNL7A4D7JABYE5WSHRXBPQJTKJYAAPEPNYJSV7CHRD5SSLINK)\n\n"
        "*✅Buy HYPER now on LOBSTR:* [https://lobstr.co/trade/HYPER](https://lobstr.co/trade/HYPER:GCIELJ7SU5DNTLRZLXEANRZ2Q7TBP4FDXAV52NQQWSBFCKSMDNZRHYPR)",
        parse_mode="Markdown"
    )

# Token prices (assuming these are still accurate, adjust as needed)
XAI_PRICE = 3  # 1 XAI = 3 XLM
TESLA_PRICE = 1500  # 1 TESLA = 1500 XLM
XELON_PRICE = 0.8  # 1 XELON = 0.8 XLM
TBC_PRICE = 100  # 1 TBC = 100 XLM
NLINK_PRICE = 250  # 1 NLINK = 250 XLM
STARLINK_PRICE = 50  # 1 STARLINK = 50 XLM
HYPER_PRICE = 75  # 1 HYPER = 75 XLM
X_PRICE = 10  # 1 X = 10 XLM

def calculate_payment(xai_balance: float) -> tuple:
    """Calculates dividends and assigns tier based on xAI balance."""
    
    # Tier 1: 1-150 xAI
    if 1 <= xai_balance <= 150:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.035, "value": round(xai_balance * 0.035, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.06, "value": round(xai_balance * 0.06 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.04, "value": round(xai_balance * 0.04 / XELON_PRICE, 2), "asset": "XELON"}
        ]
        return 'Tier 1', dividend_data
    
    # Tier 2: 151-600 xAI
    elif 151 <= xai_balance <= 600:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.052, "value": round(xai_balance * 0.052, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.09, "value": round(xai_balance * 0.09 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.06, "value": round(xai_balance * 0.06 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.045, "value": round(xai_balance * 0.045 / TBC_PRICE, 5), "asset": "TBC"}
        ]
        return 'Tier 2', dividend_data

    # Tier 3: 601-1,200 xAI
    elif 601 <= xai_balance <= 1200:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.08, "value": round(xai_balance * 0.08, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.13, "value": round(xai_balance * 0.13 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.12, "value": round(xai_balance * 0.12 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.07, "value": round(xai_balance * 0.07 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.02, "value": round(xai_balance * 0.02 / NLINK_PRICE, 5), "asset": "NLINK"}
        ]
        return 'Tier 3', dividend_data

    # Tier 4: 1,201-6,000 xAI
    elif 1201 <= xai_balance <= 6000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.105, "value": round(xai_balance * 0.105, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.22, "value": round(xai_balance * 0.22 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.17, "value": round(xai_balance * 0.17 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.09, "value": round(xai_balance * 0.09 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.03, "value": round(xai_balance * 0.03 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.0007, "value": round(xai_balance * 0.0007 / X_PRICE, 5), "asset": "X"}
        ]
        return 'Tier 4', dividend_data

    # Tier 5: 6,001-12,000 xAI
    elif 6001 <= xai_balance <= 12000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.16, "value": round(xai_balance * 0.16, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.42, "value": round(xai_balance * 0.42 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.35, "value": round(xai_balance * 0.35 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.12, "value": round(xai_balance * 0.12 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.06, "value": round(xai_balance * 0.06 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.0025, "value": round(xai_balance * 0.0025 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.025, "value": round(xai_balance * 0.025 / STARLINK_PRICE, 5), "asset": "STARLINK"}
        ]
        return 'Tier 5', dividend_data

    # Tier 6: 12,001-28,000 xAI
    elif 12001 <= xai_balance <= 28000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.28, "value": round(xai_balance * 0.28, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 0.65, "value": round(xai_balance * 0.65 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.52, "value": round(xai_balance * 0.52 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.22, "value": round(xai_balance * 0.22 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.12, "value": round(xai_balance * 0.12 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.007, "value": round(xai_balance * 0.007 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.05, "value": round(xai_balance * 0.05 / STARLINK_PRICE, 5), "asset": "STARLINK"},
            {"name": "🆎 HYPER", "rate": 0.06, "value": round(xai_balance * 0.06 / HYPER_PRICE, 5), "asset": "HYPER"}
        ]
        return 'Tier 6', dividend_data

    # Tier 7: 28,001-60,000 xAI
    elif 28001 <= xai_balance <= 60000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 0.55, "value": round(xai_balance * 0.55, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 1.05, "value": round(xai_balance * 1.05 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 0.9, "value": round(xai_balance * 0.9 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.32, "value": round(xai_balance * 0.32 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.18, "value": round(xai_balance * 0.18 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.012, "value": round(xai_balance * 0.012 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.07, "value": round(xai_balance * 0.07 / STARLINK_PRICE, 5), "asset": "STARLINK"},
            {"name": "🆎 HYPER", "rate": 0.09, "value": round(xai_balance * 0.09 / HYPER_PRICE, 5), "asset": "HYPER"}
        ]
        return 'Tier 7', dividend_data

    # Tier 8: 60,001-120,000 xAI
    elif 60001 <= xai_balance <= 120000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 1.1, "value": round(xai_balance * 1.1, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 2.15, "value": round(xai_balance * 2.15 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 1.5, "value": round(xai_balance * 1.5 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 0.55, "value": round(xai_balance * 0.55 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.25, "value": round(xai_balance * 0.25 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.025, "value": round(xai_balance * 0.025 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.1, "value": round(xai_balance * 0.1 / STARLINK_PRICE, 5), "asset": "STARLINK"},
            {"name": "🆎 HYPER", "rate": 0.12, "value": round(xai_balance * 0.12 / HYPER_PRICE, 5), "asset": "HYPER"}
        ]
        return 'Tier 8', dividend_data

    # Tier 9: 120,001-300,000 xAI
    elif 120001 <= xai_balance <= 300000:
        dividend_data = [
            {"name": "👑 xAI", "rate": 3.7, "value": round(xai_balance * 3.7, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 5.15, "value": round(xai_balance * 5.15 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 2.2, "value": round(xai_balance * 2.2 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 1.15, "value": round(xai_balance * 1.15 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.35, "value": round(xai_balance * 0.35 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.055, "value": round(xai_balance * 0.055 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.15, "value": round(xai_balance * 0.15 / STARLINK_PRICE, 5), "asset": "STARLINK"},
            {"name": "🆎 HYPER", "rate": 0.18, "value": round(xai_balance * 0.18 / HYPER_PRICE, 5), "asset": "HYPER"}
        ]
        return 'Tier 9', dividend_data

    # Tier 10: 300,001+ xAI
    else:
        dividend_data = [
            {"name": "👑 xAI", "rate": 10.5, "value": round(xai_balance * 10.5, 2), "asset": "XAi"},
            {"name": "© TESLA", "rate": 21, "value": round(xai_balance * 21 / TESLA_PRICE, 5), "asset": "TESLA"},
            {"name": "🔥 XELON", "rate": 2.75, "value": round(xai_balance * 2.75 / XELON_PRICE, 2), "asset": "XELON"},
            {"name": "⚙ TBC", "rate": 3.2, "value": round(xai_balance * 3.2 / TBC_PRICE, 5), "asset": "TBC"},
            {"name": "🧠 NLINK", "rate": 0.5, "value": round(xai_balance * 0.5 / NLINK_PRICE, 5), "asset": "NLINK"},
            {"name": "✖ X", "rate": 0.07, "value": round(xai_balance * 0.07 / X_PRICE, 5), "asset": "X"},
            {"name": "⭐ STARLINK", "rate": 0.25, "value": round(xai_balance * 0.25 / STARLINK_PRICE, 5), "asset": "STARLINK"},
            {"name": "🆎 HYPER", "rate": 0.3, "value": round(xai_balance * 0.3 / HYPER_PRICE, 5), "asset": "HYPER"}
        ]
        return 'Tier 10', dividend_data

def format_dividends(dividend_data):
    formatted_dividends = "\n".join([
        f"{dividend['name']} {dividend['rate']*100:.1f}%: {dividend['value']:.2f} {dividend['asset']}"
        for dividend in dividend_data
    ])
    return formatted_dividends

def main():
    application = ApplicationBuilder().token("7053305969:AAGEO15sSkMXQGZoKi-3NodCMr_OuYr-opw").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("WITHDRAW"), handle_withdraw))

    # Message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Callback query handlers for wallet clicks and remove button
    application.add_handler(CallbackQueryHandler(handle_wallet_click, pattern=r'^wallet_'))
    application.add_handler(CallbackQueryHandler(handle_remove_wallet_click, pattern=r'^remove_'))

    application.run_polling()

if __name__ == "__main__":
    main()
