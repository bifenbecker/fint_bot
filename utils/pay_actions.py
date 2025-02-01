import datetime as dt

import aiohttp


async def create_new_bill(amount, user_id, kind, wallet):
    now_ts = int(dt.datetime.now().timestamp())
    label = f"{now_ts}_{user_id}"

    url = "https://yoomoney.ru/quickpay/confirm.xml?"

    payload = {}

    payload["receiver"] = wallet
    payload["quickpay_form"] = "shop"
    payload["targets"] = kind
    payload["paymentType"] = "SB"
    payload["sum"] = amount
    payload["label"] = label

    for value in payload:
        url += str(value).replace("_", "-") + "=" + str(payload[value])
        url += "&"

    url = url[:-1].replace(" ", "%20")

    async with aiohttp.ClientSession() as session:
        resp = await session.post(url, data=payload)
        pay_url = str(resp.url)

    return [label, pay_url]


async def check_bill_for_pay(label, token):
    headers = {
        "Authorization": "Bearer " + str(token),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    payload = {"label": label}
    url = "https://yoomoney.ru/api/operation-history?records=1"

    async with aiohttp.ClientSession(headers=headers) as session:
        resp = await session.post(url, data=payload)
        res = await resp.json()

        status = "not_found"
        for item in res.get("operations"):
            if item["label"] == label:
                status = "found"
                break

    return status
