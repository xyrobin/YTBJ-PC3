import oracledb
from datetime import datetime
from config import conn_str
import logging


class ProductionOrderService:
    def __init__(self):
        self.connection = oracledb.connect(conn_str)
        self.cursor = self.connection.cursor()

    def get_pending_orders(self):
        # 排产-获取所有待排产工单（状态=待排产）并按最早生产日期升序排序
        query = """
                SELECT a.SCGDH,
                    nvl(a.TZGS,a.GSXS) GSXS,
                    a.JHKSRQ,
                    a.JHKSSJ,
                    a.BC,
                    a.ZZSCRQ,
                    a.ZZSCSJ,
                    nvl(a.JHRQ, a.GDJHQ) JHRQ,
                    a.JHSJ,
                    a.gy GY,
                    decode(a.gy, '摆剪', '摆', '落料', '落', '弧形料R2000', 'R2', '弧形料R3000', 'R3', ' ') GYSX,
                    a.bm BM,
                    decode(a.bm, '内板', '内', '外板', '外', ' ') BMSX,
                    a.pzdl PZDL,
                    decode(a.pzdl, '冷轧', '冷', '镀锌', '锌', '酸洗', '酸', '铝硅', '硅', ' ') PZDLSX,
                    a.sdgx SDGX,
                    a.xdgx XDGX,
                    a.ywy YWY,
                    a.ylkw YLKW,
                    b.bz BZ,
                    nvl(b.tlzs,c.ylzs) TLZS,
                    nvl(b.tlzl,c.ylzl) TLZL,
                    nvl(b.KHMC,c.khmc) KHMC,
                    b.PH PH,
                    nvl(b.gg,c.gg) GG,
                    nvl(b.JHZS,c.cpzs) SL,
                    a.jhbz,
                    decode(substr(a.scgdh, 1, 3), 'YGD', 1, 0) IS_YGD
                FROM A_PC_SCGDWH_TAB a
                left join A_PC_DPCSCGD_VW b
                    on a.scgdh = b.SCGDH
                    left join A_PC_YYGD_TAB c on a.scgdh = c.yygdh
                WHERE a.GDJHZT = '待排产'
                and nvl(a.is_deleted, 0) <> 1
                and (b.GXDL = 'BL' or c.gxdl = '落料')
                order by nvl(a.JHRQ, a.GDJHQ),a.jhsj,a.gy,a.bm,a.pzdl
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_scheduled_orders(self):
        # 排产-获取所有已排产工单（状态=已排产）
        query = """
                SELECT a.SCGDH,
                    nvl(a.TZGS,a.GSXS) GSXS,
                    a.JHKSRQ,
                    a.JHKSSJ,
                    a.BC,
                    a.ZZSCRQ,
                    a.ZZSCSJ,
                    nvl(a.JHRQ, a.GDJHQ) JHRQ,
                    a.JHSJ,
                    a.gy GY,
                    decode(a.gy, '摆剪', '摆', '落料', '落', '弧形料R2000', 'R2', '弧形料R3000', 'R3', ' ') GYSX,
                    a.bm BM,
                    decode(a.bm, '内板', '内', '外板', '外', ' ') BMSX,
                    a.pzdl PZDL,
                    decode(a.pzdl, '冷轧', '冷', '镀锌', '锌', '酸洗', '酸', '铝硅', '硅', ' ') PZDLSX,
                    a.sdgx SDGX,
                    a.xdgx XDGX,
                    a.ywy YWY,
                    a.ylkw YLKW,
                    b.bz BZ,
                    nvl(b.tlzs,c.ylzs) TLZS,
                    nvl(b.tlzl,c.ylzl) TLZL,
                    nvl(b.KHMC,c.khmc) KHMC,
                    b.PH PH,
                    nvl(b.gg,c.gg) GG,
                    nvl(b.JHZS,c.cpzs) SL,
                    a.jhbz,
                    decode(substr(a.scgdh, 1, 3), 'YGD', 1, 0) IS_YGD
                FROM A_PC_SCGDWH_TAB a
                left join A_PC_DPCSCGD_VW b
                    on a.scgdh = b.SCGDH
                    left join A_PC_YYGD_TAB c on a.scgdh = c.yygdh
                WHERE a.GDJHZT = '已排产'
                and nvl(a.is_deleted, 0) <> 1
                and (b.GXDL = 'BL' or c.gxdl = '落料')
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def schedule_order(self, order_no, plan_date, shift, start_time, jhwgrq, jhwgsj):
        # 排产-更新工单状态为已排产
        try:
            # 检查班次是否合法
            if shift not in ["A", "B"]:
                return {"success": False, "message": "无效的班次，必须是A或B"}

            print("计划完工日期：" + jhwgrq)
            print("计划完工时间：" + jhwgsj)
            # 更新工单状态和排产信息
            update_sql = """
            UPDATE A_PC_SCGDWH_TAB
            SET GDJHZT = '已排产', JHKSRQ = :plan_date, BC = :shift, JHKSSJ = :start_time, JHWGRQ = :jhwgrq, JHWGSJ = :jhwgsj
            WHERE SCGDH = :order_no and GDJHZT = '待排产'
            """
            self.cursor.execute(
                update_sql,
                {
                    "plan_date": plan_date,
                    "shift": shift,
                    "start_time": start_time,
                    "order_no": order_no,
                    "jhwgrq": jhwgrq,
                    "jhwgsj": jhwgsj,
                },
            )
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def unschedule_order(self, order_no):
        # 排产-取消排产，将工单状态改回待排产
        try:
            update_sql = """
            UPDATE A_PC_SCGDWH_TAB
            SET GDJHZT = '待排产', JHKSRQ = NULL, BC = NULL, JHKSSJ = NULL, JHWGRQ = NULL, JHWGSJ = NULL
            WHERE SCGDH = :order_no and GDJHZT = '已排产'
            """
            self.cursor.execute(update_sql, {"order_no": order_no})
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def get_all_orders(self, scgdh=None, gdjhzt=None, jhrq=None, ywy=None, jhksrq=None, khmc=None, gg=None):
        # 工单维护-获取所有工单数据，支持筛选
        query = """
        SELECT a.SCGDH, nvl(a.JHRQ, a.GDJHQ) JHRQ, JHSJ, YWY, YLKW, nvl(a.TZGS,a.GSXS) GSXS, 
               JHKSRQ, JHKSSJ, BC, ZZSCRQ, ZZSCSJ, GDJHZT
            FROM A_PC_SCGDWH_TAB a
            left join A_RG_PRODUCTION_BILL_INTEGRATED_TAB b
                on a.scgdh = b.scgdh
            where b.gxdl = 'BL'
            and a.scgdh is not null
            and nvl(a.is_deleted, 0) <> 1
        """
        
        params = {}
        
        # 添加筛选条件
        if scgdh:
            query += " AND a.SCGDH LIKE :scgdh"
            params["scgdh"] = f"%{scgdh}%"
        if gdjhzt:
            query += " AND a.GDJHZT = :gdjhzt"
            params["gdjhzt"] = gdjhzt
        if jhrq:
            query += " AND nvl(a.JHRQ, a.GDJHQ) = :jhrq"
            params["jhrq"] = jhrq
        if ywy:
            query += " AND a.YWY LIKE :ywy"
            params["ywy"] = f"%{ywy}%"
        if jhksrq:
            query += " AND a.JHKSRQ = :jhksrq"
            params["jhksrq"] = jhksrq
        if khmc:
            query += " AND b.KHMC LIKE :khmc"
            params["khmc"] = f"%{khmc}%"
        if gg:
            query += " AND b.QGGGMS LIKE :gg"
            params["gg"] = f"%{gg}%"
        
        query += " ORDER BY jhrq"
        
        self.cursor.execute(query, params)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_order(self, order_data):
        # 工单维护-更新工单数据
        try:
            update_sql = """
            UPDATE A_PC_SCGDWH_TAB
            SET JHRQ = :jhrq, JHSJ = :jhsj, ZZSCRQ = :zzscrq, ZZSCSJ = :zzscsj,jhbz = :jhbz
            WHERE SCGDH = :scgdh and GDJHZT = '待排产'
            and nvl(is_deleted, 0) <> 1
            """
            self.cursor.execute(
                update_sql,
                {
                    "jhrq": order_data.get("jhrq"),
                    "jhsj": order_data.get("jhsj"),
                    "zzscrq": order_data.get("zzscrq"),
                    "zzscsj": order_data.get("zzscsj"),
                    "scgdh": order_data.get("scgdh"),
                    "jhbz": order_data.get("jhbz"),
                },
            )
            self.connection.commit()
            print("更新成功")
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            print("更新失败:", str(e))
            return {"success": False, "message": str(e)}

    def __del__(self):
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "connection") and self.connection:
            self.connection.close()

    def get_order_details(self, order_no):
        # 工单详情页查询
        sql = """
            select t.scgdh scgdh,
                   nvl(jgdwdm, '厂内') jgdw,
                   t.jzmc jzmc,
                   t.gxdlmc gxdl,
                   t.ph ph,
                   t.pzfzmms pzmc,
                   t.qgggms gg,
                   a.pzdl pzdl,
                   a.gy gy,
                   a.bm bm,
                   t.sdjhh sdgx,
                   t.xdjhh xdgx,
                   a.ylkw ylkw,
                   t.jhtlsl ylzs,
                   t.jhtll ylzl,
                   t.jhyjzs cpzs,
                   nvl(a.TZGS,a.GSXS) gs,
                   t.khmc khmc,
                   a.ywy ywy,
                   a.gdjhq gdjhq,
                   nvl(a.JHRQ, a.GDJHQ) jhrq,
                   a.jhsj jhsj,
                   nvl(a.zzscrq, TO_CHAR(TO_DATE(t.cjsj, 'YYYYMMDDHH24MISS'), 'YYYY-MM-DD')) zzscrq,
                   a.zzscsj zzscsj,
                   a.gdjhzt gdjhzt,
                   a.jhksrq jhksrq,
                   a.jhkssj jhkssj,
                   a.jhwgrq jhwgrq,
                   a.jhwgsj jhwgsj,
                   a.bc bc,
                   t.scxqdh scxqdh,
                   t.scxqdzxh scxqdzxh,
                   t.xsddh xsddh,
                   t.xsddzxh xsddzxh,
                   t.bz bz,
                   a.jhbz jhbz
              from A_RG_PRODUCTION_BILL_INTEGRATED_TAB t
              left join A_PC_SCGDWH_TAB a
                on t.scgdh = a.scgdh
             where t.scgdh = :order_no
             and nvl(a.is_deleted, 0) <> 1
        """
        # return self.cursor.execute(sql, (order_no,)).fetchone()
        self.cursor.execute(sql, {"ORDER_NO": order_no})
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]



    # 预约工单处理：
    def get_appointment_orders(self, khmc=None, ywy=None, jhrq=None, yygdh=None,scgdh=None,is_deleted=None,gdjhzt=None):
        # 查询预约工单数据
        query = """
            SELECT a.YYGDH,
                    a.SCGDH,
                    a.JHRQ,
                    a.JHSJ,
                    a.GXDL,
                    a.PZDL,
                    a.KHMC,
                    a.YWY,
                    a.ZZSCRQ,
                    a.ZZSCSJ,
                    a.GG,
                    a.YLZS,
                    a.YLZL,
                    a.CPZS,
                    a.JHBZ,
                    b.gdjhzt,
                    nvl(b.tzgs, b.gsxs) gs,
                    b.jhksrq,
                    b.jhkssj，
                    decode(b.is_deleted, 0, '正常', '失效') is_deleted
                FROM A_PC_YYGD_TAB a
                left join A_PC_SCGDWH_TAB b
                    on a.yygdh = b.scgdh
                where 1=1
        """
        params = {}

        # 添加查询条件
        if khmc:
            query += " AND a.KHMC LIKE :khmc"
            params["khmc"] = f"%{khmc}%"
        if ywy:
            query += " AND a.YWY LIKE :ywy"
            params["ywy"] = f"%{ywy}%"
        if jhrq:
            query += " AND a.JHRQ = :jhrq"
            params["jhrq"] = jhrq
        if yygdh:
            query += " AND a.YYGDH LIKE :yygdh"
            params["yygdh"] = f"%{yygdh}"
        if scgdh:
            query += " AND a.SCGDH LIKE :scgdh"
            params["scgdh"] = f"%{scgdh}"
        if is_deleted:
            query += " AND b.is_deleted = :is_deleted"
            params["is_deleted"] = is_deleted
        if gdjhzt:
            query += " AND b.gdjhzt = :gdjhzt"
            params["gdjhzt"] = gdjhzt
        query += " order by a.YYGDH desc"

        self.cursor.execute(query, params)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def add_appointment_order(self, order_data):
        # 添加预约工单
        try:
            insert_sql = """
                INSERT INTO A_PC_YYGD_TAB (
                     JHRQ, JHSJ, GXDL, KHMC, YWY, 
                    ZZSCRQ, ZZSCSJ, GG, YLZS, YLZL, CPZS, JHBZ, PZDL
                ) VALUES (
                    :jhrq, :jhsj, :gxdl, :khmc, :ywy, 
                    :zzscrq, :zzscsj, :gg, :ylzs, :ylzl, :cpzs, :jhbz, :pzdl
                )
            """

            self.cursor.execute(
                insert_sql,
                {
                    "jhrq": order_data["jhrq"],
                    "jhsj": order_data["jhsj"],
                    "gxdl": order_data["gxdl"],
                    "khmc": order_data["khmc"],
                    "ywy": order_data["ywy"],
                    "zzscrq": order_data["zzscrq"],
                    "zzscsj": order_data["zzscsj"],
                    "gg": order_data["gg"],
                    "ylzs": order_data["ylzs"],
                    "ylzl": order_data["ylzl"],
                    "cpzs": order_data["cpzs"],
                    "jhbz": order_data["jhbz"],
                    "pzdl": order_data["pzdl"],
                },
            )
            self.connection.commit()
            return {"success": True, "yygdh": order_data["yygdh"]}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def update_appointment_order(self, yygdh, order_data):
        # 更新预约工单
        try:
            update_sql = """
                UPDATE A_PC_YYGD_TAB a
                    SET a.SCGDH  = :scgdh,
                        a.JHRQ   = :jhrq,
                        a.JHSJ   = :jhsj,
                        a.GXDL   = :gxdl,
                        a.KHMC   = :khmc,
                        a.YWY    = :ywy,
                        a.ZZSCRQ = :zzscrq,
                        a.ZZSCSJ = :zzscsj,
                        a.GG     = :gg,
                        a.YLZS   = :ylzs,
                        a.YLZL   = :ylzl,
                        a.CPZS   = :cpzs,
                        a.JHBZ   = :jhbz,
                        a.PZDL   = :pzdl
                    WHERE a.YYGDH = :yygdh
                    and a.scgdh = ''
                    AND EXISTS (SELECT 1
                            FROM A_PC_SCGDWH_TAB b
                            WHERE a.YYGDH = b.scgdh
                            AND b.gdjhzt = '待排产'
                            and nvl(b.is_deleted, 0) = 0);
                                """

            self.cursor.execute(
                update_sql,
                {
                    "scgdh": order_data["scgdh"],
                    "jhrq": order_data["jhrq"],
                    "jhsj": order_data["jhsj"],
                    "gxdl": order_data["gxdl"],
                    "khmc": order_data["khmc"],
                    "ywy": order_data["ywy"],
                    "zzscrq": order_data["zzscrq"],
                    "zzscsj": order_data["zzscsj"],
                    "gg": order_data["gg"],
                    "ylzs": order_data["ylzs"],
                    "ylzl": order_data["ylzl"],
                    "cpzs": order_data["cpzs"],
                    "jhbz": order_data["jhbz"],
                    "pzdl": order_data["pzdl"],
                    "yygdh": yygdh,
                },
            )
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def delete_appointment_orders(self, ids):
        # 删除预约工单
        try:
            if not ids or len(ids) == 0:
                return {"success": False, "message": "没有选择要删除的记录"}

            delete_sql = f"DELETE FROM A_PC_YYGD_TAB a WHERE a.YYGDH IN ({','.join([':id' + str(i) for i in range(len(ids))])}) and a.scgdh = '' AND EXISTS (SELECT 1  FROM A_PC_SCGDWH_TAB b WHERE a.YYGDH = b.scgdh AND b.gdjhzt = '待排产')"
            params = {f"id{i}": ids[i] for i in range(len(ids))}

            self.cursor.execute(delete_sql, params)
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def get_appointment_order_detail(self, yygdh):
        # 获取单个预约工单详情
        query = """
            SELECT a.YYGDH,
                    a.SCGDH,
                    a.JHRQ,
                    a.JHSJ,
                    a.GXDL,
                    a.PZDL,
                    a.KHMC,
                    a.YWY,
                    a.ZZSCRQ,
                    a.ZZSCSJ,
                    a.GG,
                    a.YLZS,
                    a.YLZL,
                    a.CPZS,
                    a.JHBZ,
                    b.gdjhzt,
                    nvl(b.tzgs, b.gsxs) gs,
                    b.jhksrq,
                    b.jhkssj,
                    decode(b.is_deleted, 0, '正常', '失效') is_deleted
                FROM A_PC_YYGD_TAB a
                left join A_PC_SCGDWH_TAB b
                    on a.yygdh = b.scgdh
                WHERE  a.YYGDH = :yygdh
        """
        self.cursor.execute(query, {"yygdh": yygdh})
        columns = [col[0].lower() for col in self.cursor.description]
        result = self.cursor.fetchone()
        return dict(zip(columns, result)) if result else None

    def update_order_gs(self, data):
        try:
            sql = "UPDATE A_PC_SCGDWH_TAB SET TZGS = :tzgs, GSTZYY = :gstzyy WHERE scgdh = :scgdh and GDJHZT = '待排产' "
            self.cursor.execute(
                sql,
                {
                    "tzgs": data.get("tzgs"),
                    "gstzyy": data.get("gstzyy"),
                    "scgdh": data.get("scgdh"),
                },
            )
            # 打印实际执行的SQL语句和参数
            print(f"执行的SQL语句: {sql}")
            print(
                f"使用的参数: {{{', '.join([f'{k}: {repr(v)}' for k, v in { 'tzgs': data.get('tzgs'), 'gstzyy': data.get('gstzyy'), 'scgdh': data.get('scgdh') }.items()])}}}"
            )
            self.connection.commit()
            print("更新成功")
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            print("更新失败:", str(e))
            return {"success": False, "message": str(e)}

    # 预约工单绑定生产工单
    def bind_appointment_order(self, yygdh, scgdh):
        try:
            print('预约工单绑定生产工单:',yygdh,scgdh)
            # 检查生产工单号是否已存在
            existing = self.cursor.execute(
                "SELECT COUNT(*) as count FROM A_PC_SCGDWH_TAB WHERE scgdh = :scgdh AND gdjhzt = '待排产' and nvl(is_deleted, 0) = 0 AND yygdh is null ",
                {"scgdh": scgdh},
            )
            print('检查生产工单数量1:',existing)
            result = self.cursor.fetchone()  # 获取查询结果元组，格式如: (count_value,)
            existing = result[0] if result else 0  # 使用索引访问元组元素
            print('检查生产工单数量2:',existing)

            if existing != 1:
                return False

            # 执行数据库绑定方法
            self.cursor.callproc("A_YYGDBD", [yygdh, scgdh])
            return True
        except Exception as e:
            print(f"绑定工单失败: {e}")
            self.connection.rollback()
            return False

    def cancel_appointment_order(self, yygdh):
        # 取消预约工单，设置is_deleted=1
        try:
            update_sql = """
            UPDATE A_PC_SCGDWH_TAB
            SET is_deleted = 1
            WHERE scgdh = :yygdh AND gdjhzt = '待排产'
            """
            self.cursor.execute(update_sql, {'yygdh': yygdh})
            self.connection.commit()
            # 检查是否有记录被更新
            return self.cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            print(f"取消预约工单失败: {e}")
            return False
