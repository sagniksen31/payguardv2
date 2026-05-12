import logging
import random
from typing import Any

from fastapi import APIRouter, HTTPException

from historical_log_generator import generate_historical_logs


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/live-batch")
def get_live_batch() -> list[dict[str, Any]]:
    try:
        seed = random.randint(0, 999999)
        df = generate_historical_logs(
            n_days=1,
            n_atms=5,
            seed=seed,
        )

        df = df[(df["issue_type"] != "") & (df["issue_type"].notna())].copy()

        if len(df) > 0:
            df = df.sample(
                n=min(3, max(1, len(df))),
                random_state=seed,
            )

        return df.to_dict(orient="records")
    except Exception as exc:
        logger.exception("Live batch endpoint failed")
        raise HTTPException(status_code=500, detail=f"Live batch failed: {exc}") from exc
