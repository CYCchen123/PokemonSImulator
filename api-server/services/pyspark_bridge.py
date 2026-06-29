"""
PySpark Bridge (Person B)

通过 Spark REST API 提交批处理任务并查询结果。
也支持通过 subprocess spark-submit 方式提交。

用法:
    from services.pyspark_bridge import SparkBridge
    bridge = SparkBridge()
    result = await bridge.submit_job("batch/static_data_crud.py", ["--mode", "read"])
"""
import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional
import httpx
from config import SPARK_MASTER_URL, SPARK_REST_URL, HDFS_NAMENODE, HDFS_PORT

logger = logging.getLogger(__name__)

# Spark 作业目录（相对于项目根目录）
SPARK_JOBS_DIR = Path(__file__).resolve().parent.parent.parent / "spark-jobs"


class SparkBridge:
    """PySpark 任务提交与查询桥接"""

    def __init__(self):
        self.master_url = SPARK_MASTER_URL or "spark://100.107.105.99:7077"
        self.rest_url = SPARK_REST_URL or "http://100.107.105.99:6066"
        self.hdfs_namenode = f"hdfs://{HDFS_NAMENODE}:{HDFS_PORT or 8020}"

    async def health(self) -> bool:
        """检查 Spark Master 是否可达。"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"http://{self.master_url.split('//')[1].split(':')[0]}:8080/json/"
                )
                return resp.status_code == 200
        except Exception:
            return False

    def submit_job_sync(self, job_script: str, args: list[str] = None,
                         spark_args: list[str] = None) -> dict:
        """
        通过 spark-submit 同步提交任务（阻塞等待结果）。

        Args:
            job_script: 作业脚本路径 (相对于 spark-jobs/)
            args: 作业参数
            spark_args: spark-submit 额外参数

        Returns:
            {"ok": True, "stdout": "...", "stderr": "..."} 或 {"ok": False, "error": "..."}
        """
        script_path = SPARK_JOBS_DIR / job_script
        if not script_path.exists():
            return {"ok": False, "error": f"Job not found: {script_path}"}

        cmd = [
            "spark-submit",
            "--master", self.master_url,
            "--deploy-mode", "client",
        ]
        if spark_args:
            cmd.extend(spark_args)
        cmd.append(str(script_path))
        if args:
            cmd.extend(args)

        logger.info(f"提交 Spark 作业: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 分钟超时
                cwd=str(SPARK_JOBS_DIR.parent),
            )
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout[-5000:],  # 截断输出
                "stderr": result.stderr[-2000:],
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Job timed out (5 min)"}
        except FileNotFoundError:
            return {"ok": False, "error": "spark-submit not found. Is Spark installed?"}

    async def submit_job_async(self, job_script: str, args: list[str] = None) -> dict:
        """异步提交 Spark 作业（不阻塞）。"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.submit_job_sync, job_script, args
        )

    # ============================================================
    # 预定义查询
    # ============================================================

    async def query_species(self, species_id: int = None,
                             type_filter: str = None,
                             limit: int = 50) -> dict:
        """查询宝可梦数据。"""
        args = ["--mode", "read", "--table", "species", "--limit", str(limit)]
        if species_id:
            args.extend(["--id", str(species_id)])
        if type_filter:
            args.extend(["--type", type_filter])
        return await self.submit_job_async("batch/static_data_crud.py", args)

    async def query_moves(self, move_id: int = None,
                           move_type: str = None) -> dict:
        """查询技能数据。"""
        args = ["--mode", "read", "--table", "moves"]
        if move_id:
            args.extend(["--id", str(move_id)])
        if move_type:
            args.extend(["--type", move_type])
        return await self.submit_job_async("batch/static_data_crud.py", args)

    async def compute_usage_stats(self, start_date: str, end_date: str,
                                   limit: int = 20) -> dict:
        """计算宝可梦使用率统计。"""
        return await self.submit_job_async("batch/pokemon_usage.py", [
            "--hdfs-path", f"{self.hdfs_namenode}/user/pokemon/raw/battles/",
            "--start-date", start_date,
            "--end-date", end_date,
        ])

    async def compute_moves_analysis(self, species_id: int = None) -> dict:
        """技能分析。"""
        args = []
        if species_id:
            args.extend(["--species-id", str(species_id)])
        return await self.submit_job_async("batch/moves_analysis.py", args)
