"""运维入口：查询某个商户某天的结算状态，手动触发重推。"""

from datetime import date

from fastapi import FastAPI

app = FastAPI(title="settlekit")


@app.get("/settlements/{merchant_id}/{settle_date}")
def settlement_status(merchant_id: str, settle_date: date) -> dict[str, str]:
    return {"merchant_id": merchant_id, "settle_date": settle_date.isoformat(), "status": "pending"}


@app.post("/settlements/{merchant_id}/{settle_date}/resend")
def resend(merchant_id: str, settle_date: date) -> dict[str, str]:
    return {"merchant_id": merchant_id, "settle_date": settle_date.isoformat(), "status": "queued"}
