"""HTTP 入口：按表名和过滤条件导出 CSV。"""

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from exportkit.csv_writer import iter_csv

app = FastAPI(title="exportkit")


@app.get("/exports/{table}")
def export_table(table: str) -> StreamingResponse:
    header = ["id", "name", "created_at"]
    rows: list[list[object]] = []  # 由 exportkit.query 按过滤条件取数
    return StreamingResponse(
        iter_csv(header, rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{table}.csv"'},
    )
