import oracledb
from datetime import datetime
from config import conn_str


class ProductionOrderService:
    def __init__(self):
        self.connection = oracledb.connect(conn_str)
        self.cursor = self.connection.cursor()

    def get_pending_orders(self):
        # """获取所有待排产工单（状态=0）并按最早生产日期升序排序"""
        query = """
          SELECT a.SCGDH,
         a.GSXS,
         a.JHKSRQ,
         a.JHKSSJ,
         a.JHJSRQ,
         a.JHJSSJ,
         a.BC,
         a.ZZSCRQ,
         a.ZZSCSJ,
         a.JHRQ,
         a.JHSJ,
         b.KHMC,
         b.PH     PH,
         b.gg     GG,
         b.JHZS   SL
    FROM uf_SCGDWH a
    left join A_PC_DPCSCGD_VW b
      on a.scgdh = b.SCGDH
   WHERE a.GDJHZT = 0
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_scheduled_orders(self):
        # 获取所有已排产工单（状态=1）
        query = """
        SELECT SCGDH, GSXS, JHKSRQ, JHKSSJ 
        FROM uf_SCGDWH 
        WHERE GDJHZT = 1
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def schedule_order(self, order_no, plan_date, shift, start_time):
        # """更新工单状态为已排产"""
        try:
            # 检查班次是否合法
            if shift not in ["A", "B"]:
                return {"success": False, "message": "无效的班次，必须是A或B"}

            # 更新工单状态和排产信息
            update_sql = """
            UPDATE uf_SCGDWH
            SET GDJHZT = 1, JHKSRQ = :plan_date, BC = :shift, JHKSSJ = :start_time
            WHERE SCGDH = :order_no
            """
            self.cursor.execute(
                update_sql,
                {
                    "plan_date": plan_date,
                    "shift": shift,
                    "start_time": start_time,
                    "order_no": order_no,
                },
            )
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def unschedule_order(self, order_no):
        # """取消排产，将工单状态改回待排产"""
        try:
            update_sql = """
            UPDATE uf_SCGDWH
            SET GDJHZT = 0, JHKSRQ = NULL, BC = NULL, JHKSSJ = NULL
            WHERE SCGDH = :order_no
            """
            self.cursor.execute(update_sql, {"order_no": order_no})
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def __del__(self):
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "connection") and self.connection:
            self.connection.close()
