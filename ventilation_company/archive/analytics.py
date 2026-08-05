"""
Модуль аналітики виробництва
"""

from ventilation_company.database import execute_query


class ProductionAnalytics:
    def __init__(self):
        pass

    def get_projects_stats(self, year=None, month=None):
        total_query = "SELECT COUNT(*), COUNT(DISTINCT client) FROM projects"
        total_row = execute_query(total_query, fetch_one=True)
        status_query = "SELECT status, COUNT(*) FROM projects GROUP BY status"
        status_rows = execute_query(status_query)
        type_query = "SELECT ventilation_type, COUNT(*) FROM projects GROUP BY ventilation_type"
        type_rows = execute_query(type_query)
        return {
            "total_projects": total_row[0],
            "total_clients": total_row[1],
            "by_status": {row[0]: row[1] for row in status_rows},
            "by_type": {row[0]: row[1] for row in type_rows},
        }

    def get_financial_stats(self, year=None, month=None):
        query = """
            SELECT COUNT(*) as total_calculations, SUM(materials_cost) as total_materials,
                   SUM(components_cost) as total_components, SUM(works_cost) as total_works,
                   SUM(total_cost) as total_cost, SUM(final_price) as total_revenue, SUM(profit) as total_profit
            FROM calculations
        """
        row = execute_query(query, fetch_one=True)
        return {
            "total_calculations": row[0] or 0,
            "total_materials": round(row[1] or 0, 2),
            "total_components": round(row[2] or 0, 2),
            "total_works": round(row[3] or 0, 2),
            "total_cost": round(row[4] or 0, 2),
            "total_revenue": round(row[5] or 0, 2),
            "total_profit": round(row[6] or 0, 2),
            "avg_profit_margin": round((row[6] / row[5] * 100) if row[5] else 0, 2),
        }

    def get_top_projects(self, limit=10):
        query = """
            SELECT p.project_number, p.name, p.client, c.final_price, c.profit
            FROM calculations c
            JOIN projects p ON c.project_id = p.id
            ORDER BY c.profit DESC
            LIMIT ?
        """
        return execute_query(query, (limit,))

    def get_client_analysis(self):
        query = """
            SELECT p.client, COUNT(*) as projects_count, SUM(c.final_price) as total_revenue
            FROM projects p
            LEFT JOIN calculations c ON p.id = c.project_id
            WHERE p.client != ''
            GROUP BY p.client
            ORDER BY total_revenue DESC
        """
        return execute_query(query)

    def print_dashboard(self):
        projects = self.get_projects_stats()
        financial = self.get_financial_stats()
        top_projects = self.get_top_projects(5)
        clients = self.get_client_analysis()
        print("\n" + "=" * 80)
        print("АНАЛІТИЧНА ПАНЕЛЬ".center(80))
        print("=" * 80)
        print("\nПРОЄКТИ")
        print(f"   Всього проєктів: {projects['total_projects']}")
        print(f"   Унікальних замовників: {projects['total_clients']}")
        print("   За статусами:")
        for status, count in projects["by_status"].items():
            print(f"      * {status}: {count}")
        print("   За типами вентиляції:")
        for vtype, count in projects["by_type"].items():
            print(f"      * {vtype}: {count}")
        print("\nФІНАНСИ")
        print(f"   Загальна виручка: {financial['total_revenue']:,.2f} грн")
        print(f"   Загальна собівартість: {financial['total_cost']:,.2f} грн")
        print(f"   Загальний прибуток: {financial['total_profit']:,.2f} грн")
        print(f"   Середня рентабельність: {financial['avg_profit_margin']:.2f}%")
        print(f"   Витрати на матеріали: {financial['total_materials']:,.2f} грн")
        print(f"   Витрати на комплектуючі: {financial['total_components']:,.2f} грн")
        print(f"   Витрати на роботи: {financial['total_works']:,.2f} грн")
        print("\nТОП-5 ПРОЄКТІВ ЗА ПРИБУТКОМ")
        print(f"   {'№':<4} {'Проєкт':<20} {'Замовник':<20} {'Виручка':<15} {'Прибуток':<15}")
        print("   " + "-" * 74)
        for i, proj in enumerate(top_projects, 1):
            print(f"   {i:<4} {proj[0]:<20} {str(proj[2]):<20} {proj[3]:<15.2f} {proj[4]:<15.2f}")
        print("\nЗАМОВНИКИ")
        print(f"   {'Замовник':<30} {'Проєктів':<12} {'Виручка':<15}")
        print("   " + "-" * 57)
        for client in clients[:5]:
            print(f"   {str(client[0]):<30} {client[1]:<12} {client[2] or 0:<15.2f}")
        print("\n" + "=" * 80)
