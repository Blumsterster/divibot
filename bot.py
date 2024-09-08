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

# Initialize Stellar server and asset
server = Server("https://horizon.stellar.org")
asset = Asset(
    "XELON", "GDPK4GJW4VOYBMDNYNMWMRCEQFDESBNGLBTTI5VZ5LRSJBPVZTTELONX"
)

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
        "🔭*Welcome to the Musk’s lab!*🥼 \n\n🤖My name is *DiviBot* and my purpose here is to help you manage your dividends and track ROI seamlessly. \n\n⚖️With *DiviBot* you can get real-time updates and make smart investment decisions. You can always use my knowledges to check for the dividend tiers. \n\n🌎Join my creator’s Telegram channel for insights, and use the buy link to easily purchase *XELON’s* and grow your portfolio by upgrading your tiers!",
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


# Tiers and benefits handler
async def handle_tiers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tiers_message = (
        "📈 <b>Dividend Tiers and Benefits:</b>\n\n"
        "1️⃣ <b>Tier 1</b> (Balance: 1875 - 3000 XELON)\n"
        "• <b>Dividend Rate:</b> 70%\n"
        "• <b>Benefit:</b> 70% daily returns on balance.\n\n"
        
        "2️⃣ <b>Tier 2</b> (Balance: 3001 - 4500 XELON)\n"
        "• <b>Dividend Rate:</b> 85%\n"
        "• <b>Benefit:</b> 85% daily returns on balance.\n\n"
        
        "3️⃣ <b>Tier 3</b> (Balance: 4501 - 5200 XELON)\n"
        "• <b>Dividend Rate:</b> 100%\n"
        "• <b>Benefit:</b> 100% daily returns on balance.\n\n"
        
        "4️⃣ <b>Tier 4</b> (Balance: 5201 - 7100 XELON)\n"
        "• <b>Dividend Rate:</b> 115%\n"
        "• <b>Benefit:</b> 115% daily returns on balance.\n\n"
        
        "5️⃣ <b>Tier 5</b> (Balance: 7101 - 9200 XELON)\n"
        "• <b>Dividend Rate:</b> 130%\n"
        "• <b>Benefit:</b> 130% daily returns on balance.\n\n"
        
        "6️⃣ <b>Tier 6</b> (Balance: 9201 - 11500 XELON)\n"
        "• <b>Dividend Rate:</b> 150%\n"
        "• <b>Benefit:</b> 150% daily returns on balance.\n\n"
        
        "7️⃣ <b>Tier 7</b> (Balance: 11501 - 13000 XELON)\n"
        "• <b>Dividend Rate:</b> 180%\n"
        "• <b>Benefit:</b> 180% daily returns on balance.\n\n"
        
        "8️⃣ <b>Tier 8</b> (Balance: 13001 - 15700 XELON)\n"
        "• <b>Dividend Rate:</b> 210%\n"
        "• <b>Benefit:</b> 210% daily returns on balance.\n\n"
        
        "9️⃣ <b>Tier 9</b> (Balance: 15701 - 18600 XELON)\n"
        "• <b>Dividend Rate:</b> 250%\n"
        "• <b>Benefit:</b> 250% daily returns on balance.\n\n"
        
        "🔟 <b>Tier 10</b> (Balance: 18601+ XELON)\n"
        "• <b>Dividend Rate:</b> 300%\n"
        "• <b>Benefit:</b> 300% daily returns on balance.\n\n"

        "• <b>Check our Website Calculator: elonwhip.org</b>"
    )

    await update.message.reply_text(tiers_message, parse_mode="HTML")


# Wallet button handler
async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await update.message.reply_text(
            "*❌There is no wallet recorded for your account.\n✅Please send your Stellar PUBLIC KEY to add it.*", parse_mode="Markdown")
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
            "*❌Invalid wallet address. \n✅Please send a valid Stellar wallet address starting with 'G'.*", parse_mode="Markdown")

# Handle wallet button clicks
async def handle_wallet_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("wallet_"):
        wallet_address = data.split("_", 1)[1]
        try:
            account = server.accounts().account_id(wallet_address).call()
            balances = account["balances"]
            xelon_balance = next(
                (
                    b["balance"]
                    for b in balances
                    if b.get("asset_code") == asset.code
                ),
                "0",
            )
            tier, _ = calculate_payment(float(xelon_balance))
            await query.edit_message_text(
                f"👝*Wallet:* {wallet_address}\n*🏦Balance: {xelon_balance} XELON*\n*🌐Tier:* {tier}", parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(
                f"Error fetching wallet data: {e}"
            )

# Dividends handler
async def handle_dividends(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    wallets = user_wallets.get(user_id, [])
    if not wallets:
        await update.message.reply_text(
            "❌ <b>Please add a wallet first by clicking on 💼 WALLET.</b>", parse_mode="HTML")
        return
    for wallet_address in wallets:
        try:
            account = server.accounts().account_id(wallet_address).call()
            balances = account["balances"]
            xelon_balance = next(
                (
                    b["balance"]
                    for b in balances
                    if b.get("asset_code") == asset.code
                ),
                "0",
            )
            xelon_balance = float(xelon_balance)
            tier, daily_payment = calculate_payment(xelon_balance)
            xelon_to_next_tier = calculate_xelon_to_next_tier(xelon_balance, tier)

            # No need to escape '.' in HTML
            balance_formatted = f"{xelon_balance:.2f}"
            next_tier_formatted = f"{xelon_to_next_tier:.2f}"

            # Use HTML for formatting
            await update.message.reply_text(
                f"👝 <b>Wallet:</b> <code>{wallet_address}</code>\n"
                f"🏦 <b>Balance:</b> <code>{balance_formatted} XELON</code>\n"
                f"🌐 <b>Dividend Tier:</b> <code>{tier}</code>\n"
                f"{daily_payment}\n\n"
                f"🤵 <b>XELON left to next tier:</b> <code>{next_tier_formatted} XELON</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(
                f"Error fetching wallet data for <code>{wallet_address}</code>: <code>{e}</code>", parse_mode="HTML"
            )

# Telegram Channel handler
async def handle_telegram_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛩*Join our Telegram Channel: @whipspacex *\n\n 👑*Join our Whiplash Family: @Whiplash347*", parse_mode="Markdown")

# LOBSTR handler
async def handle_lobstr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("*✅Buy XELON now on LOBSTR:* [https://lobstr.co/trade/XELON](https://lobstr.co/trade/XELON:GDPK4GJW4VOYBMDNYNMWMRCEQFDESBNGLBTTI5VZ5LRSJBPVZTTELONX)", parse_mode="Markdown")

# Calculate payment and tier
def calculate_payment(balance: float) -> tuple:
    # Convert XELON balance to XLM based on the rate of 1 XELON = 0.8 XLM
    balance_in_xlm = balance * 0.8

    if 1875 <= balance <= 3000:
        dividend_rate = 0.70  # 70%
        dividend_return = balance_in_xlm * dividend_rate
        return '1', f'<b>⚪️Dividend Rate: 70%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 3001 <= balance <= 4500:
        dividend_rate = 0.85  # 85%
        dividend_return = balance_in_xlm * dividend_rate
        return '2', f'<b>⚪️Dividend Rate: 85%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 4501 <= balance <= 5200:
        dividend_rate = 1.00  # 100%
        dividend_return = balance_in_xlm * dividend_rate
        return '3', f'<b>⚪️Dividend Rate: 100%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 5201 <= balance <= 7100:
        dividend_rate = 1.15  # 115%
        dividend_return = balance_in_xlm * dividend_rate
        return '4', f'<b>⚪️Dividend Rate: 115%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 7101 <= balance <= 9200:
        dividend_rate = 1.30  # 130%
        dividend_return = balance_in_xlm * dividend_rate
        return '5', f'<b>⚪️Dividend Rate: 130%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 9201 <= balance <= 11500:
        dividend_rate = 1.50  # 150%
        dividend_return = balance_in_xlm * dividend_rate
        return '6', f'<b>⚪️Dividend Rate: 150%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 11501 <= balance <= 13000:
        dividend_rate = 1.80  # 180%
        dividend_return = balance_in_xlm * dividend_rate
        return '7', f'<b>⚪️Dividend Rate: 180%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 13001 <= balance <= 15700:
        dividend_rate = 2.10  # 210%
        dividend_return = balance_in_xlm * dividend_rate
        return '8', f'<b>⚪️Dividend Rate: 210%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif 15701 <= balance <= 18600:
        dividend_rate = 2.50  # 250%
        dividend_return = balance_in_xlm * dividend_rate
        return '9', f'<b>⚪️Dividend Rate: 250%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    elif balance >= 18601:
        dividend_rate = 3.00  # 300%
        dividend_return = balance_in_xlm * dividend_rate
        return '10', f'<b>⚪️Dividend Rate: 300%</b>\n<b>🟢Dividend Return: {dividend_return:.2f} XLM Daily!</b>'
    else:
        return '❌No Tier', '<b>Your balance is too low to qualify for a tier.</b>'

# Calculate XELON needed for next tier
def calculate_xelon_to_next_tier(balance: float, tier: str) -> float:
    next_tier_thresholds = {
        '1': 3001,
        '2': 4501,
        '3': 5201,
        '4': 7101,
        '5': 9201,
        '6': 11501,
        '7': 13001,
        '8': 15701,
        '9': 18601,
        '10': float('inf'),
        'No Tier': 1875,  # Update this to 1875, which is the first tier threshold
    }

    # Handle case where balance is below the threshold for tier 1
    if balance == 0:
        return next_tier_thresholds['No Tier']
    elif balance < next_tier_thresholds['1']:
        return next_tier_thresholds['No Tier'] - balance
    else:
        next_tier_balance = next_tier_thresholds.get(tier, float('inf'))
        return max(0, next_tier_balance - balance)

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
