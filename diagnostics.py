import os
import re

def scan_for_errors(file_path):
    errors = []
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
        # Check for missing error handlers in telegram.ext.Application
        if "ApplicationBuilder" in code and "add_error_handler" not in code:
            errors.append("Missing error handler (add_error_handler) in ApplicationBuilder bot")
        # Check for timeout settings in ApplicationBuilder
        if "ApplicationBuilder" in code and "request_kwargs" not in code:
            errors.append("No timeout settings (request_kwargs) in ApplicationBuilder bot")
        # Check for unhandled exceptions
        if "try:" not in code and "except" not in code:
            errors.append("No exception handling found; recommend wrapping handlers in try/except")
        # Check for network requests without retries
        if "requests." in code and "Session" not in code:
            errors.append("Plain requests call found; recommend using requests.Session with retries for robustness")
    return errors

def auto_fix_code(file_path):
    fixed = False
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    # Auto-add error handler for telegram.ext.Application
    if "ApplicationBuilder" in code and "add_error_handler" not in code:
        if "def main()" in code:
            main_match = re.search(r"def main\(\):(.+?)app\.run_polling\(\)", code, re.DOTALL)
            if main_match:
                main_block = main_match.group(1)
                # Add error handler before run_polling
                error_handler_code = """
    # Global error handler for logging and user notification
    async def error_handler(update, context):
        import logging
        logging.error("Exception while handling update:", exc_info=context.error)
        if update and update.effective_message:
            await update.effective_message.reply_text("⚠️ Network error. Please try again.")
    app.add_error_handler(error_handler)
"""
                new_main_block = main_block + error_handler_code
                code = code.replace(main_block, new_main_block)
                fixed = True
    # Auto-add timeout settings for ApplicationBuilder
    if "ApplicationBuilder" in code and "request_kwargs" not in code:
        code = code.replace(
            "ApplicationBuilder().token(BOT_TOKEN).build()",
            "ApplicationBuilder().token(BOT_TOKEN).request_kwargs({'read_timeout': 30, 'connect_timeout': 30}).build()"
        )
        fixed = True
    # Add try/except in message handler example
    if "async def handle_message" in code and "try:" not in code:
        code = re.sub(
            r"async def handle_message\((.+?)\):\n",
            r"async def handle_message(\1):\n    try:\n",
            code
        )
        # Add except block after likely endpoint
        code = re.sub(
            r"(await update\.message\.reply_text.+?)(\n)",
            r"\1\n    except Exception as e:\n        import logging\n        logging.error(e)\n        await update.message.reply_text('⚠️ An error occurred.')\n",
            code,
            flags=re.DOTALL
        )
        fixed = True
    # Add retries for requests
    if "requests." in code and "Session" not in code:
        code = code.replace(
            "import requests",
            "import requests\nfrom requests.adapters import HTTPAdapter\nfrom requests.packages.urllib3.util.retry import Retry"
        )
        if "def upload_to_transfer_sh" in code:
            code = code.replace(
                "with open(file_path, \"rb\") as f:",
                "session = requests.Session()\n    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])\n    session.mount('https://', HTTPAdapter(max_retries=retries))\n    with open(file_path, \"rb\") as f:"
            )
            code = code.replace(
                "response = requests.put(",
                "response = session.put("
            )
        fixed = True
    # Write changes if any fixes applied
    if fixed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
    return fixed

def main():
    print("🔍 Scanning for errors in Python source files...")
    py_files = [f for f in os.listdir(".") if f.endswith(".py")]
    for file_path in py_files:
        errors = scan_for_errors(file_path)
        if errors:
            print(f"❗ In {file_path}:")
            for e in errors:
                print(f"  - {e}")
            fixed = auto_fix_code(file_path)
            if fixed:
                print(f"✅ Auto-fixed issues in {file_path}.")
            else:
                print(f"⚠️ Could not auto-fix {file_path}. See errors above.")
        else:
            print(f"✅ {file_path} OK (no common issues found).")
    print("🔧 Diagnostics and auto-fix complete.")

if __name__ == "__main__":
    main()