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
                    a.GSXS,
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
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_scheduled_orders(self):
        # 排产-获取所有已排产工单（状态=已排产）
        query = """
                SELECT a.SCGDH,
                    a.GSXS,
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

    def schedule_order(self, order_no, plan_date, shift, start_time,jhwgrq, jhwgsj):
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
            WHERE SCGDH = :order_no
            """
            self.cursor.execute(
                update_sql,
                {
                    "plan_date": plan_date,
                    "shift": shift,
                    "start_time": start_time,
                    "order_no": order_no,
                    "jhwgrq": jhwgrq,
                    "jhwgsj": jhwgsj
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
            WHERE SCGDH = :order_no
            """
            self.cursor.execute(update_sql, {"order_no": order_no})
            self.connection.commit()
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def get_all_orders(self):
        # 工单维护-获取所有工单数据
        query = """
        SELECT a.SCGDH, nvl(a.JHRQ, a.GDJHQ) JHRQ, JHSJ, YWY, YLKW, GSXS, JHKSRQ, JHKSSJ, BC, ZZSCRQ, ZZSCSJ, GDJHZT
            FROM A_PC_SCGDWH_TAB a
            left join A_RG_PRODUCTION_BILL_INTEGRATED_TAB b
                on a.scgdh = b.scgdh
            where b.gxdl = 'BL'
            and a.scgdh is not null
            ORDER BY SCGDH
        """
        self.cursor.execute(query)
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_order(self, order_data):
        # 工单维护-更新工单数据
        try:
            update_sql = """
            UPDATE A_PC_SCGDWH_TAB
            SET JHRQ = :jhrq, JHSJ = :jhsj, ZZSCRQ = :zzscrq, ZZSCSJ = :zzscsj,jhbz = :jhbz
            WHERE SCGDH = :scgdh
            """
            self.cursor.execute(
                update_sql,
                {
                    "jhrq": order_data.get("jhrq"),
                    "jhsj": order_data.get("jhsj"),
                    "zzscrq": order_data.get("zzscrq"),
                    "zzscsj": order_data.get("zzscsj"),
                    "scgdh": order_data.get("scgdh"),
                    "jhbz": order_data.get("jhbz")
                },
            )
            self.connection.commit()
            print('更新成功');
            return {"success": True}
        except Exception as e:
            self.connection.rollback()
            print('更新失败:', str(e));
            return {"success": False, "message": str(e)}

    def __del__(self):
        if hasattr(self, "cursor") and self.cursor:
            self.cursor.close()
        if hasattr(self, "connection") and self.connection:
            self.connection.close()


    def get_order_details(self, order_no):
        #工单详情页查询
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
                   a.gsxs gs,
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
        """
        # return self.cursor.execute(sql, (order_no,)).fetchone()
        self.cursor.execute(sql, {'ORDER_NO': order_no})
        columns = [col[0].lower() for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]





    # 预约工单处理：
    def get_appointment_orders(self, khmc=None, ywy=None, jhrq=None, yygdh=None):
        # 查询预约工单数据
        query = """
            SELECT YYGDH, SCGDH, JHRQ, JHSJ, GXDL, KHMC, YWY, ZZSCRQ, ZZSCSJ, GG, YLZS, YLZL, CPZS, JHBZ, PZDL
            FROM A_PC_YYGD_TAB
            WHERE 1=1
        """
        params = {}
        
        # 添加查询条件
        if khmc:
            query += " AND KHMC LIKE :khmc"
            params["khmc"] = f"%{khmc}%"
        if ywy:
            query += " AND YWY LIKE :ywy"
            params["ywy"] = f"%{ywy}%"
        if jhrq:
            query += " AND JHRQ = :jhrq"
            params["jhrq"] = jhrq
        if yygdh:
            query += " AND YYGDH LIKE :yygdh"
            params["yygdh"] = f"%{yygdh}"

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
            
            
            self.cursor.execute(insert_sql, {
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
                "pzdl": order_data["pzdl"]
            })
            self.connection.commit()
            return {"success": True, "yygdh": order_data["yygdh"]}
        except Exception as e:
            self.connection.rollback()
            return {"success": False, "message": str(e)}

    def update_appointment_order(self, yygdh, order_data):
        # 更新预约工单
        try:
            update_sql = """
                UPDATE A_PC_YYGD_TAB
                SET SCGDH = :scgdh, JHRQ = :jhrq, JHSJ = :jhsj, 
                    GXDL = :gxdl, KHMC = :khmc, YWY = :ywy, 
                    ZZSCRQ = :zzscrq, ZZSCSJ = :zzscsj, 
                    GG = :gg, YLZS = :ylzs, YLZL = :ylzl, CPZS = :cpzs, JHBZ = :jhbz, PZDL = :pzdl
                WHERE YYGDH = :yygdh
            """
            
            self.cursor.execute(update_sql, {
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
                "yygdh": yygdh
            })
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
                
            delete_sql = f"DELETE FROM A_PC_YYGD_TAB WHERE YYGDH IN ({','.join([':id' + str(i) for i in range(len(ids))])})"
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
            SELECT YYGDH, SCGDH, JHRQ, JHSJ, GXDL, KHMC, YWY, ZZSCRQ, ZZSCSJ, GG, YLZS, YLZL, CPZS, JHBZ 
            FROM A_PC_YYGD_TAB
            WHERE YYGDH = :yygdh
        """
        self.cursor.execute(query, {"yygdh": yygdh})
        columns = [col[0].lower() for col in self.cursor.description]
        result = self.cursor.fetchone()
        return dict(zip(columns, result)) if result else None