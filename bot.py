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

# Initialize Stellar server
server = Server("https://horizon.stellar.org")

# Example assets (if you still need them in future updates)
xai_asset = Asset("XAI", "GDW4UCJVOUIRLXVY4FWSXQJBCIA3QZPFMVRL3KMAIMTCXASWGBJFRXAI")
x_asset = Asset("X", "GAS4LCHPWEHCWRPR2LAIRCYWGSPSUID7HGYGTAIAR4B5E3SAW7YUQLAX")
tbc_asset = Asset("TBC", "GA5I7GQNVWGC6ETTA4XUNG6FHNEJ4HEOD363VRMT7SCOAUXQMJBGOTBC")
nlink_asset = Asset("NLINK", "GBX743B3DQKLE5XUN5Z56GOIVMMXRKQJTIRQSVIY3AH3JJQA53EMLINK")
starlink_asset = Asset("STARLINK", "GCKUU7BDNL7A4D7JABYE5WSHRXBPQJTKJYAAPEPNYJSV7CHRD5SSLINK")
hyper_asset = Asset("HYPER", "GCIELJ7SU5DNTLRZLXEANRZ2Q7TBP4FDXAV52NQQWSBFCKSMDNZRHYPR")

# In-memory stores for user data
user_wallets = {}

# Custom keyboard with buttons
def get_custom_keyboard():
    keyboard = [
        ["💼 WALLET", "🚀 DIVIDENDS"],
        ["📥 Telegram Channel", "📊 LOBSTR"],
        ["📈 Check Tiers"]  # Add the "Check Tiers" button
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
        await handle_tiers(update, context)  # Handle the new "Check Tiers" button
    else:
        # Assume the user is sending a wallet address
        await add_wallet(update, context)

# Wallet button handler (function you need)
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await update.message.reply_text(
            "*❌There is no wallet recorded for your account.*\n✅Please send your Stellar PUBLIC KEY to add it.", parse_mode="Markdown")
    else:
        buttons = [
            [InlineKeyboardButton(wallet, callback_data=f"wallet_{wallet}")]
            for wallet in wallets
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(
            "*👝Here are your wallets:*", parse_mode="Markdown", reply_markup=reply_markup)
        await update.message.reply_text(
            "*✅To add another wallet, please send your Stellar PUBLIC KEY.*", parse_mode="Markdown")

# Add wallet handler
async def add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallet_address = update.message.text.strip()
    if wallet_address.startswith("G") and len(wallet_address) == 56:
        # Validate Stellar address length
        wallets = user_wallets.setdefault(user_id, [])
        if wallet_address not in wallets:
            wallets.append(wallet_address)
            await update.message.reply_text(
                f"*✅Wallet {wallet_address} added successfully!*", parse_mode="Markdown")
        else:
            await update.message.reply_text("*❌This wallet is already added.*", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            "*❌Invalid wallet address.*\n✅Please send a valid Stellar wallet address starting with 'G'.", parse_mode="Markdown")

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
            balances = account["balances"]

            # Extract XAi balance by checking for the XAI asset
            xai_balance = next(
                (b["balance"] for b in balances if b.get("asset_code") == "XAI" and b.get("asset_issuer") == "GDW4UCJVOUIRLXVY4FWSXQJBCIA3QZPFMVRL3KMAIMTCXASWGBJFRXAI"),
                "0"  # Default to "0" if the asset is not found
            )

            # Calculate the tier for XAi
            xai_tier, xai_payment = calculate_payment(float(xai_balance))

            # Display the balances and tiers correctly
            await query.edit_message_text(
                f"👝 <b>Wallet:</b> {wallet_address}\n"
                f"📊 <b>XAi Balance:</b> {xai_balance} XAi\n"
                f"🌐 <b>XAi Dividend Tier:</b> {xai_tier}\n",
                parse_mode="HTML"
            )
        except Exception as e:
            await query.edit_message_text(f"Error fetching wallet data: {e}")

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

# Fix to show the correct balance when calculating dividends
async def handle_dividends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await update.message.reply_text(
            "*❌ Please add a wallet first by clicking on 💼 WALLET.*", parse_mode="Markdown"
        )
        return
    
    # Process each wallet and calculate dividends
    for wallet_address in wallets:
        try:
            # Fetch account details from the Stellar network
            account = server.accounts().account_id(wallet_address).call()
            balances = account["balances"]
            
            # Extract XAi balance using the correct asset code and issuer
            xai_balance = next(
                (b["balance"] for b in balances if b.get("asset_code") == "XAI" and b.get("asset_issuer") == "GDW4UCJVOUIRLXVY4FWSXQJBCIA3QZPFMVRL3KMAIMTCXASWGBJFRXAI"), 
                "0"  # Default to "0" if XAI asset is not found
            )

            # Convert the balance to a float for calculations
            xai_balance = float(xai_balance)
            
            # Calculate XAi dividend tier and payments
            xai_tier, xai_dividends = calculate_payment(xai_balance)
            
            # Format the message
            message = (
                f"👝 <b>Wallet:</b> {wallet_address}\n"
                f"📊 <b>XAi Balance:</b> {xai_balance:.2f} XAi\n"
                f"🌐 <b>XAi Dividend Tier:</b> {xai_tier}\n"
                f"{xai_dividends}"  # This will have HTML content returned by calculate_payment
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

# Token prices
XAI_PRICE = 3  # 1 XAI = 3 XLM
TESLA_PRICE = 1500  # 1 TESLA = 1500 XLM
XELON_PRICE = 0.8  # 1 XELON = 0.8 XLM
TBC_PRICE = 100  # 1 TBC = 100 XLM
NLINK_PRICE = 250  # 1 NLINK = 250 XLM
STARLINK_PRICE = 50  # 1 STARLINK = 50 XLM
HYPER_PRICE = 75  # 1 HYPER = 75 XLM
X_PRICE = 10  # 1 X = 10 XLM

# Calculate payment and tier
def calculate_payment(balance: float) -> tuple:
    balance_in_xlm = balance * XELON_PRICE  # Convert XELON balance to XLM

    if 1 <= balance <= 150:
        dividend_rate = 0.035  # 3.5%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '1', (
            f'<b>👑 3.5% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.035:.2f} XLM)\n'
            f'<b>© 6% TESLA</b>: {(balance_in_xlm * 0.06 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.06:.2f} XLM)\n'
            f'<b>🔥 4% XELON</b>: {balance * 0.04:.2f} XELON ({balance_in_xlm * 0.04:.2f} XLM)'
       )
    elif 151 <= balance <= 600:
        dividend_rate = 0.052  # 5.2%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '2', (
            f'<b>👑 5.2% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.052:.2f} XLM)\n'
            f'<b>© 9% TESLA</b>: {(balance_in_xlm * 0.09 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.09:.2f} XLM)\n'
            f'<b>🔥 6% XELON</b>: {balance * 0.06:.2f} XELON ({balance_in_xlm * 0.06:.2f} XLM)\n'
            f'<b>⚙️ 4.5% TBC</b>: {(balance_in_xlm * 0.045 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.045:.2f} XLM)'
       )
    elif 601 <= balance <= 1200:
        dividend_rate = 0.08  # 8%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '3', (
            f'<b>👑 8% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.08:.2f} XLM)\n'
            f'<b>© 13% TESLA</b>: {(balance_in_xlm * 0.13 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.13:.2f} XLM)\n'
            f'<b>🔥 12% XELON</b>: {balance * 0.12:.2f} XELON ({balance_in_xlm * 0.12:.2f} XLM)\n'
            f'<b>⚙️ 7% TBC</b>: {(balance_in_xlm * 0.07 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.07:.2f} XLM)\n'
            f'<b>🧠 2% NLINK</b>: {(balance_in_xlm * 0.02 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.02:.2f} XLM)'
       )
    elif 1201 <= balance <= 6000:
        dividend_rate = 0.105  # 10.5%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '4', (
            f'<b>👑 10.5% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.105:.2f} XLM)\n'
            f'<b>© 22% TESLA</b>: {(balance_in_xlm * 0.22 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.22:.2f} XLM)\n'
            f'<b>🔥 17% XELON</b>: {balance * 0.17:.2f} XELON ({balance_in_xlm * 0.17:.2f} XLM)\n'
            f'<b>⚙️ 9% TBC</b>: {(balance_in_xlm * 0.09 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.09:.2f} XLM)\n'
            f'<b>🧠 3% NLINK</b>: {(balance_in_xlm * 0.03 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.03:.2f} XLM)\n'
            f'<b>✖ 0.07% X</b>: {(balance_in_xlm * 0.0007 / X_PRICE):.5f} X ({balance_in_xlm * 0.0007:.2f} XLM)'
       )
    elif 6001 <= balance <= 12000:
        dividend_rate = 0.16  # 16%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '5', (
            f'<b>👑 16% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.16:.2f} XLM)\n'
            f'<b>© 42% TESLA</b>: {(balance_in_xlm * 0.42 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.42:.2f} XLM)\n'
            f'<b>🔥 35% XELON</b>: {balance * 0.35:.2f} XELON ({balance_in_xlm * 0.35:.2f} XLM)\n'
            f'<b>⚙️ 12% TBC</b>: {(balance_in_xlm * 0.12 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.12:.2f} XLM)\n'
            f'<b>🧠 6% NLINK</b>: {(balance_in_xlm * 0.06 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.06:.2f} XLM)\n'
            f'<b>✖ 0.25% X</b>: {(balance_in_xlm * 0.0025 / X_PRICE):.5f} X ({balance_in_xlm * 0.0025:.2f} XLM)\n'
            f'<b>⭐️ 2.5% STARLINK</b>: {(balance_in_xlm * 0.025 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.025:.2f} XLM)'
       )
    elif 12001 <= balance <= 28000:
        dividend_rate = 0.28  # 28%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '6', (
            f'<b>👑 28% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.28:.2f} XLM)\n'
            f'<b>© 65% TESLA</b>: {(balance_in_xlm * 0.65 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 0.65:.2f} XLM)\n'
            f'<b>🔥 52% XELON</b>: {balance * 0.52:.2f} XELON ({balance_in_xlm * 0.52:.2f} XLM)\n'
            f'<b>⚙️ 22% TBC</b>: {(balance_in_xlm * 0.22 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.22:.2f} XLM)\n'
            f'<b>🧠 12% NLINK</b>: {(balance_in_xlm * 0.12 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.12:.2f} XLM)\n'
            f'<b>✖ 0.7% X</b>: {(balance_in_xlm * 0.007 / X_PRICE):.5f} X ({balance_in_xlm * 0.007:.2f} XLM)\n'
            f'<b>⭐️ 5% STARLINK</b>: {(balance_in_xlm * 0.05 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.05:.2f} XLM)\n'
            f'<b>🆎 6% HYPER</b>: {(balance_in_xlm * 0.06 / HYPER_PRICE):.5f} HYPER ({balance_in_xlm * 0.06:.2f} XLM)'
       )
    elif 28001 <= balance <= 60000:
        dividend_rate = 0.55  # 55%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '7', (
            f'<b>👑 55% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 0.55:.2f} XLM)\n'
            f'<b>© 105% TESLA</b>: {(balance_in_xlm * 1.05 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 1.05:.2f} XLM)\n'
            f'<b>🔥 90% XELON</b>: {balance * 0.9:.2f} XELON ({balance_in_xlm * 0.9:.2f} XLM)\n'
            f'<b>⚙️ 32% TBC</b>: {(balance_in_xlm * 0.32 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.32:.2f} XLM)\n'
            f'<b>🧠 18% NLINK</b>: {(balance_in_xlm * 0.18 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.18:.2f} XLM)\n'
            f'<b>✖ 1.2% X</b>: {(balance_in_xlm * 0.012 / X_PRICE):.5f} X ({balance_in_xlm * 0.012:.2f} XLM)\n'
            f'<b>⭐️ 7% STARLINK</b>: {(balance_in_xlm * 0.07 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.07:.2f} XLM)\n'
            f'<b>🆎 9% HYPER</b>: {(balance_in_xlm * 0.09 / HYPER_PRICE):.5f} HYPER ({balance_in_xlm * 0.09:.2f} XLM)'
       )
    elif 60001 <= balance <= 120000:
        dividend_rate = 1.10  # 110%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '8', (
            f'<b>👑 110% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 1.1:.2f} XLM)\n'
            f'<b>© 215% TESLA</b>: {(balance_in_xlm * 2.15 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 2.15:.2f} XLM)\n'
            f'<b>🔥 150% XELON</b>: {balance * 1.5:.2f} XELON ({balance_in_xlm * 1.5:.2f} XLM)\n'
            f'<b>⚙️ 55% TBC</b>: {(balance_in_xlm * 0.55 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 0.55:.2f} XLM)\n'
            f'<b>🧠 25% NLINK</b>: {(balance_in_xlm * 0.25 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.25:.2f} XLM)\n'
            f'<b>✖ 2.5% X</b>: {(balance_in_xlm * 0.025 / X_PRICE):.5f} X ({balance_in_xlm * 0.025:.2f} XLM)\n'
            f'<b>⭐️ 10% STARLINK</b>: {(balance_in_xlm * 0.1 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.1:.2f} XLM)\n'
            f'<b>🆎 12% HYPER</b>: {(balance_in_xlm * 0.12 / HYPER_PRICE):.5f} HYPER ({balance_in_xlm * 0.12:.2f} XLM)'
       )
    elif 120001 <= balance <= 300000:
        dividend_rate = 3.70  # 370%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '9', (
            f'<b>👑 370% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 3.7:.2f} XLM)\n'
            f'<b>© 515% TESLA</b>: {(balance_in_xlm * 5.15 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 5.15:.2f} XLM)\n'
            f'<b>🔥 220% XELON</b>: {balance * 2.2:.2f} XELON ({balance_in_xlm * 2.2:.2f} XLM)\n'
            f'<b>⚙️ 115% TBC</b>: {(balance_in_xlm * 1.15 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 1.15:.2f} XLM)\n'
            f'<b>🧠 35% NLINK</b>: {(balance_in_xlm * 0.35 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.35:.2f} XLM)\n'
            f'<b>✖ 5.5% X</b>: {(balance_in_xlm * 0.055 / X_PRICE):.5f} X ({balance_in_xlm * 0.055:.2f} XLM)\n'
            f'<b>⭐️ 15% STARLINK</b>: {(balance_in_xlm * 0.15 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.15:.2f} XLM)\n'
            f'<b>🆎 18% HYPER</b>: {(balance_in_xlm * 0.18 / HYPER_PRICE):.5f} HYPER ({balance_in_xlm * 0.18:.2f} XLM)'
       )
    elif balance > 300001:
        dividend_rate = 10.50  # 1050%
        dividend_return = balance_in_xlm * dividend_rate / XAI_PRICE
        return '10', (
            f'<b>👑 1050% xAI</b>: {dividend_return:.2f} XAi ({balance_in_xlm * 10.5:.2f} XLM)\n'
            f'<b>© 2100% TESLA</b>: {(balance_in_xlm * 21.0 / TESLA_PRICE):.5f} TESLA ({balance_in_xlm * 21.0:.2f} XLM)\n'
            f'<b>🔥 275% XELON</b>: {balance * 2.75:.2f} XELON ({balance_in_xlm * 2.75:.2f} XLM)\n'
            f'<b>⚙️ 320% TBC</b>: {(balance_in_xlm * 3.20 / TBC_PRICE):.5f} TBC ({balance_in_xlm * 3.20:.2f} XLM)\n'
            f'<b>🧠 50% NLINK</b>: {(balance_in_xlm * 0.50 / NLINK_PRICE):.5f} NLINK ({balance_in_xlm * 0.50:.2f} XLM)\n'
            f'<b>✖ 7% X</b>: {(balance_in_xlm * 0.07 / X_PRICE):.5f} X ({balance_in_xlm * 0.07:.2f} XLM)\n'
            f'<b>⭐️ 25% STARLINK</b>: {(balance_in_xlm * 0.25 / STARLINK_PRICE):.5f} STARLINK ({balance_in_xlm * 0.25:.2f} XLM)\n'
            f'<b>🆎 30% HYPER</b>: {(balance_in_xlm * 0.30 / HYPER_PRICE):.5f} HYPER ({balance_in_xlm * 0.30:.2f} XLM)'
       )
    else:
        return '❌No Tier', '<b>Your balance is too low to qualify for a tier.</b>'

def main():
    application = ApplicationBuilder().token("7053305969:AAGEO15sSkMXQGZoKi-3NodCMr_OuYr-opw").build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))

    # Message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
   )

    # Callback query handler for inline button clicks
    application.add_handler(CallbackQueryHandler(handle_wallet_click))

    application.run_polling()

if __name__ == "__main__":
    main()
