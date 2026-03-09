from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# Bot details
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
Username = '@easycgpabot'
# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I’m your Easy CGPA Bot")
    options = [['CGPA', 'SGPA']]
    reply_markup = ReplyKeyboardMarkup(options, resize_keyboard=True)
    await update.message.reply_text("What do you want to calculate?", reply_markup=reply_markup)

# Handle user input step-by-step
async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Step 0: Ask what user wants
    if 'step' not in context.user_data:
        if text == "CGPA":
            context.user_data['step'] = 'num_semesters'
            await update.message.reply_text("Enter the number of semesters:")
        elif text == "SGPA":
            context.user_data['step'] = 'num_subjects'
            await update.message.reply_text("Enter the number of subjects:")
        else:
            await update.message.reply_text("Please select a valid option from the buttons.")
        return

    # ---------- SGPA Flow ----------
    # Step 1: Number of subjects
    if context.user_data['step'] == 'num_subjects':
        if not text.isnumeric() or int(text) <= 0:
            await update.message.reply_text("That doesn't look like a valid number. Try again.")
            return
        context.user_data['num_subjects'] = int(text)
        context.user_data['current_subject'] = 1
        context.user_data['tcredit'] = 0
        context.user_data['tscore'] = 0
        context.user_data['step'] = 'credit'
        
        # Provide buttons for credits (1–4)
        credit_buttons = [[str(i) for i in range(1, 5)]]
        reply_markup = ReplyKeyboardMarkup(credit_buttons, resize_keyboard=True)
        await update.message.reply_text(f"Enter the credit for subject 1:", reply_markup=reply_markup)
        return

    # Step 2: Subject credit
    if context.user_data['step'] == 'credit':
        if not text.isnumeric() or int(text) not in range(1, 5):
            await update.message.reply_text("Please select a valid credit from the buttons.")
            return
        context.user_data['credit'] = int(text)
        context.user_data['step'] = 'score'
        
        # Provide buttons for scores (0–10)
        score_buttons = [[str(i) for i in range(11)]]
        reply_markup = ReplyKeyboardMarkup(score_buttons, resize_keyboard=True)
        await update.message.reply_text(
            f"Enter the score for subject {context.user_data['current_subject']}:",
            reply_markup=reply_markup
        )
        return

    # Step 3: Subject score
    if context.user_data['step'] == 'score':
        if not text.isnumeric() or int(text) not in range(0, 11):
            await update.message.reply_text("Please select a valid score from the buttons (0–10).")
            return
        score = int(text)
        credit = context.user_data['credit']
        context.user_data['tscore'] += score * credit
        context.user_data['tcredit'] += credit

        # If more subjects left → ask next subject
        if context.user_data['current_subject'] < context.user_data['num_subjects']:
            context.user_data['current_subject'] += 1
            context.user_data['step'] = 'credit'
            
            credit_buttons = [[str(i) for i in range(1, 5)]]
            reply_markup = ReplyKeyboardMarkup(credit_buttons, resize_keyboard=True)
            await update.message.reply_text(
                f"Enter the credit for subject {context.user_data['current_subject']}:",
                reply_markup=reply_markup
            )
        else:
            # All subjects entered → calculate SGPA
            sgpa = context.user_data['tscore'] / context.user_data['tcredit']
            await update.message.reply_text(f"✅ Your SGPA is: {sgpa:.2f}")
            context.user_data.clear()
        return

    # ---------- CGPA Flow ----------
    # Step 1: Number of semesters
    if context.user_data['step'] == 'num_semesters':
        if not text.isnumeric() or int(text) <= 0:
            await update.message.reply_text("That doesn't look like a valid number. Try again.")
            return
        context.user_data['num_semesters'] = int(text)
        context.user_data['current_sem'] = 1
        context.user_data['tcredits'] = 0
        context.user_data['tpoints'] = 0
        context.user_data['step'] = 'sem_credit'
        await update.message.reply_text("Enter the total credits for semester 1:")
        return

    # Step 2: Semester credits
    if context.user_data['step'] == 'sem_credit':
        if not text.isnumeric() or int(text) <= 0:
            await update.message.reply_text("Please enter a valid positive number for credits.")
            return
        context.user_data['sem_credit'] = int(text)
        context.user_data['step'] = 'sem_sgpa'
        await update.message.reply_text("Enter the SGPA of this semester (0–10):")
        return

    # Step 3: Semester SGPA
    if context.user_data['step'] == 'sem_sgpa':
        try:
            sgpa = float(text)
            if sgpa < 0 or sgpa > 10:
                raise ValueError
        except ValueError:
            await update.message.reply_text("Please enter a valid SGPA between 0 and 10.")
            return

        credits = context.user_data['sem_credit']
        context.user_data['tpoints'] += sgpa * credits
        context.user_data['tcredits'] += credits

        # If more semesters left → ask next semester
        if context.user_data['current_sem'] < context.user_data['num_semesters']:
            context.user_data['current_sem'] += 1
            context.user_data['step'] = 'sem_credit'
            await update.message.reply_text(
                f"Enter the total credits for semester {context.user_data['current_sem']}:"
            )
        else:
            # All semesters entered → calculate CGPA
            cgpa = context.user_data['tpoints'] / context.user_data['tcredits']
            await update.message.reply_text(f"🎓 Your CGPA is: {cgpa:.2f}")
            context.user_data.clear()
        return

# Run bot
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
