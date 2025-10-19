import requests
import os
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def fetch_customer_info():
    ACCOUNT_NO = os.environ["ACCOUNT_NO"]
    URL = "https://prepaid.desco.org.bd/api/unified/customer/getCustomerInfo"
    params = {'accountNo': ACCOUNT_NO}

    try:
        res = requests.get(url=URL, params=params, verify=False)
        data = res.json()
        inner_data = data.get("data")
        if inner_data is not None:
            customer_name = inner_data.get("customerName")
            return customer_name
        else:
            return None
    except Exception as err:
        print(f"Could not fetch customer info, {err}")
        return None


def fetch_balance():
    ACCOUNT_NO = os.environ["ACCOUNT_NO"]
    URL = "https://prepaid.desco.org.bd/api/unified/customer/getBalance"
    params = {'accountNo': ACCOUNT_NO}

    try:
        res = requests.get(url=URL, params=params, verify=False)
        data = res.json()
        inner_data = data.get("data")
        if inner_data is not None:
            balance = inner_data.get("balance")
            reading_time = inner_data.get("readingTime")
            return balance, reading_time
        else:
            return None, None
    except Exception as err:
        print(f"Could not fetch balance, {err}")
        return None, None


def fetch_recharge_history():
    ACCOUNT_NO = os.environ["ACCOUNT_NO"]
    URL = "https://prepaid.desco.org.bd/api/unified/customer/getRechargeHistory"
    
    # Get today's date and 6 months ago
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    
    params = {
        'accountNo': ACCOUNT_NO,
        'dateFrom': date_from,
        'dateTo': date_to
    }

    try:
        res = requests.get(url=URL, params=params, verify=False)
        data = res.json()
        recharge_list = data.get("data")
        
        if recharge_list and len(recharge_list) > 0:
            # Get the most recent recharge (first item in the list)
            recent_recharge = recharge_list[0]
            recharge_amount = recent_recharge.get("totalAmount")
            recharge_date_str = recent_recharge.get("rechargeDate")
            
            # Convert recharge date to 12-hour format with AM/PM
            if recharge_date_str:
                try:
                    # Parse the date string (format: "2025-10-08 13:53:33.0")
                    recharge_datetime = datetime.strptime(recharge_date_str, "%Y-%m-%d %H:%M:%S.%f")
                    # Format to 12-hour with AM/PM
                    recharge_date = recharge_datetime.strftime("%d %B %Y, %I:%M %p")
                except ValueError:
                    # If parsing fails, return original date
                    recharge_date = recharge_date_str
            else:
                recharge_date = None
            
            return recharge_amount, recharge_date
        else:
            return None, None
    except Exception as err:
        print(f"Could not fetch recharge history, {err}")
        return None, None


def telegram_notify(customer_name, balance, reading_time, recharge_amount, recharge_date):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False, "Telegram not configured (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Create professional message
    message = "📊 *DESCO Prepaid Electricity Account Statement*\n\n"
    
    if customer_name:
        message += f"Dear *{customer_name}*,\n\n"
    else:
        message += "Dear Valued Customer,\n\n"
    
    message += f"Your current account balance is: *৳{balance}*\n"
    
    if reading_time:
        message += f"Last Reading Date: {reading_time}\n"
    
    # Show recent recharge information
    if recharge_amount and recharge_date:
        message += f"\n💳 *Last Recharge:*\n"
        message += f"Amount: ৳{recharge_amount}\n"
        message += f"Date: {recharge_date}\n"
    
    # Show recharge warning only if balance is less than 250
    if balance < 250:
        message += "\n⚠️ _Please recharge your account to ensure uninterrupted service._\n\n"
    else:
        message += "\n"
    
    
    try:
        r = requests.post(url, json={
                          "chat_id": chat_id, 
                          "text": message,
                          "parse_mode": "Markdown"}, timeout=20)
        if r.ok:
            return True, "Telegram sent"
        return False, f"Telegram failed: HTTP {r.status_code} {r.text}"
    except Exception as e:
        return False, f"Telegram failed: {e}"


def send_notification(customer_name, balance, reading_time, recharge_amount, recharge_date):
    res = telegram_notify(customer_name, balance, reading_time, recharge_amount, recharge_date)
    print(res)


def main():
    customer_name = fetch_customer_info()
    balance, reading_time = fetch_balance()
    recharge_amount, recharge_date = fetch_recharge_history()
    
    if balance is not None:
        send_notification(customer_name, balance, reading_time, recharge_amount, recharge_date)
    else:
        print("Failed to fetch balance information")


if __name__ == "__main__":
    main()
