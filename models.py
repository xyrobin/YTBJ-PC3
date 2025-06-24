import oracledb
from config import conn_str as DB_CONFIG
from datetime import datetime, timedelta


class ProductionOrder:
    @staticmethod
    def get_connection():
        return oracledb.connect(DB_CONFIG)

    @staticmethod
    def get_unplanned_orders():
        """获取所有待排产工单（工单计划状态=0），按最早生产日期升序排序"""
        with ProductionOrder.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SCGDH, GSXS, ZZSCRQ, JHRQ
                FROM uf_SCGDWH 
                WHERE GDJHZT = 0 
                ORDER BY ZZSCRQ
            """)
            columns = [col[0].lower() for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def get_scheduled_orders():
        """获取已经排产的工单（工单计划状态=1）"""
        with ProductionOrder.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SCGDH, GSXS, PCRQ, BC
                FROM uf_SCGDWH 
                WHERE GDJHZT = 1
            """)
            columns = [col[0].lower() for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    @staticmethod
    def update_order_schedule(order_no, plan_date, shift):
        """更新工单排产信息"""
        with ProductionOrder.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE uf_SCGDWH 
                SET GDJHZT = 1, 
                    PCRQ = :plan_date,
                    BC = :shift
                WHERE SCGDH = :order_no
            """, {'order_no': order_no, 'plan_date': plan_date, 'shift': shift})
            conn.commit()

    @staticmethod
    def reset_order_schedule(order_no):
        """重置工单排产信息"""
        with ProductionOrder.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE uf_SCGDWH 
                SET GDJHZT = 0, 
                    PCRQ = NULL,
                    BC = NULL
                WHERE SCGDH = :order_no
            """, {'order_no': order_no})
            conn.commit()

    @staticmethod
    def get_schedule_slots():
        """获取未来三天的排产情况"""
        slots = []
        today = datetime.now().date()

        scheduled_orders = ProductionOrder.get_scheduled_orders()

        for i in range(3):
            date = today + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')

            # Initialize shifts
            shift_a = {'hours_used': 0, 'orders': []}
            shift_b = {'hours_used': 0, 'orders': []}

            # Filter orders for this date
            for order in scheduled_orders:
                if order['pcrq'] == date_str:
                    if order['bc'].upper() == 'A':
                        shift_a['orders'].append(order)
                        shift_a['hours_used'] += order['gsxs']
                    elif order['bc'].upper() == 'B':
                        shift_b['orders'].append(order)
                        shift_b['hours_used'] += order['gsxs']

            slots.append({
                'date': date_str,
                'shift_a': shift_a,
                'shift_b': shift_b
            })

        return slots
