import requests

# import re
#
# def clean_html_simple(content: str) -> str:
#     if not content:
#         return ""
#
#     # حذف تمام تگ‌هایی که با w: شروع میشن (تگ‌های Word)
#     content = re.sub(r"<w:[^>]+>", "", content)
#
#     # حذف تگ‌های XML اضافی (مثلاً <o:p> و مشابه)
#     content = re.sub(r"<[^>]*:[^>]+>", "", content)
#
#     return content


def send_sms(phone_number, message):
    url = "https://api.ghasedak.io/v2/sms/send/simple"
    headers = {
        "apikey": "YOUR_API_KEY",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "message": message,
        "receptor": phone_number,
        "linenumber": "10008566"  # شماره خط اختصاصی شما
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()