"""
Модуль статистики виробництва
"""
from ventilation_company.database import execute_query
from datetime import datetime


class ProductionStatistics:
    def __init__(self):
        pass

    def get_production_volume(self, year=None, month=None):
        query = """
            SELECT COUNT(DISTINCT project_id) as projects_count,
                   SUM(completed_quantity) as total_completed,
                   SUM(defects_quantity) as total_defects,
                   SUM(hours_spent) as total_hours
            FROM production
        """
        row = execute_query(query, fetch_one=True)
        total_completed = row[1] or 0
        total_defects = row[2] or 0
        return {
            "projects_count": row[0] or 0,
            "total_completed": round(total_completed, 2),
            "total_defects": round(total_defects, 2),
            "total_hours": round(row[3] or 0, 2),
            "defect_rate": round((total_defects / (total_completed + total_defects) * 100), 2)
                          if (total_completed + total_defects) > 0 else 0
        }

    def get_productivity_by_employee(self):
        query = """
            SELECT responsible_employee, COUNT(*) as operations_count,
                   SUM(completed_quantity) as total_output, SUM(hours_spent) as total_hours,
                   AVG(completed_quantity / NULLIF(hours_spent, 0)) as avg_productivity
            FROM production
            WHERE responsible_employee IS NOT NULL
            GROUP BY responsible_employee
            ORDER BY total_output DESC
        """
        return execute_query(query)

    def get_monthly_production(self, year=None):
        if year is None:
            year = datetime.now().year
        query = """
            SELECT strftime('%m', production_date) as month,
                   COUNT(DISTINCT project_id) as projects,
                   SUM(completed_quantity) as output, SUM(hours_spent) as hours
            FROM production
            WHERE strftime('%Y', production_date) = ?
            GROUP BY month
            ORDER BY month
        """
        return execute_query(query, (str(year),))

    def get_efficiency_metrics(self):
        volume = self.get_production_volume()
        avg_productivity = (volume["total_completed"] / volume["total_hours"]) if volume["total_hours"] > 0 else 0
        avg_time_per_project = (volume["total_hours"] / volume["projects_count"]) if volume["projects_count"] > 0 else 0
        return {
            "avg_productivity_per_hour": round(avg_productivity, 2),
            "avg_time_per_project": round(avg_time_per_project, 2),
            "defect_rate": volume["defect_rate"],
            "total_projects": volume["projects_count"]
        }

    def print_statistics(self):
        volume = self.get_production_volume()
        efficiency = self.get_efficiency_metrics()
        productivity = self.get_productivity_by_employee()
        print("\n" + "=" * 80)
        print("СТАТИСТИКА ВИРОБНИЦТВА".center(80))
        print("=" * 80)
        print(f"\nОБСЯГ ВИРОБНИЦТВА")
        print(f"   Всього проєктів: {volume['projects_count']}")
        print(f"   Виготовлено: {volume['total_completed']:.2f}")
        print(f"   Брак: {volume['total_defects']:.2f} ({volume['defect_rate']:.2f}%)")
        print(f"   Витрачено годин: {volume['total_hours']:.2f}")
        print(f"\nЕФЕКТИВНІСТЬ")
        print(f"   Середня продуктивність: {efficiency['avg_productivity_per_hour']:.2f} од/год")
        print(f"   Середній час на проєкт: {efficiency['avg_time_per_project']:.2f} год")
        print(f"   Рівень браку: {efficiency['defect_rate']:.2f}%")
        print(f"\nПРОДУКТИВНІСТЬ ПО СПІВРОБІТНИКАХ")
        print(f"   {'Співробітник':<25} {'Операцій':<10} {'Виготовлено':<12} {'Годин':<10} {'Продукт.':<10}")
        print("   " + "-" * 67)
        for emp in productivity:
            print(f"   {str(emp[0]):<25} {emp[1]:<10} {emp[2] or 0:<12.2f} {emp[3] or 0:<10.2f} {emp[4] or 0:<10.2f}")
        print("\n" + "=" * 80)

    def add_production_record(self, project_id, stage, completed_quantity,
                               hours_spent, responsible_employee, defects=0, notes=""):
        query = """
            INSERT INTO production
            (project_id, production_date, stage, completed_quantity, defects_quantity,
             hours_spent, responsible_employee, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        execute_query(query, (
            project_id, datetime.now().isoformat(), stage, completed_quantity,
            defects, hours_spent, responsible_employee, notes
        ))
        print("Запис виробництва додано")
