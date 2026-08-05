"""
Модуль ціноутворення
"""
from ventilation_company.config import MARKUP_PERCENTAGE, VAT_RATE


class PricingEngine:
    def __init__(self, base_cost):
        self.base_cost = base_cost

    def cost_plus_pricing(self, markup_percent=None):
        markup = markup_percent if markup_percent is not None else MARKUP_PERCENTAGE
        markup_amount = self.base_cost * (markup / 100)
        price_without_vat = self.base_cost + markup_amount
        vat_amount = price_without_vat * (VAT_RATE / 100)
        final_price = price_without_vat + vat_amount
        profit = markup_amount
        return {
            "method": "cost_plus",
            "base_cost": round(self.base_cost, 2),
            "markup_percent": markup,
            "markup_amount": round(markup_amount, 2),
            "price_without_vat": round(price_without_vat, 2),
            "vat_rate": VAT_RATE,
            "vat_amount": round(vat_amount, 2),
            "final_price": round(final_price, 2),
            "profit": round(profit, 2),
            "profit_margin": round((profit / final_price) * 100, 2) if final_price > 0 else 0
        }

    def competitive_pricing(self, competitor_price, target_margin_percent=20):
        target_price = self.base_cost / (1 - target_margin_percent / 100)
        recommended_price = min(competitor_price * 0.95, target_price)
        if recommended_price < self.base_cost * 1.1:
            recommended_price = self.base_cost * 1.1
            warning = "Cina nyzhche minimalno dopustymoji! Vstanovleno minimum 10%."
        else:
            warning = None
        vat_amount = recommended_price * (VAT_RATE / 100)
        final_price = recommended_price + vat_amount
        profit = recommended_price - self.base_cost
        return {
            "method": "competitive",
            "competitor_price": round(competitor_price, 2),
            "target_margin_percent": target_margin_percent,
            "recommended_price_without_vat": round(recommended_price, 2),
            "vat_amount": round(vat_amount, 2),
            "final_price": round(final_price, 2),
            "profit": round(profit, 2),
            "profit_margin": round((profit / recommended_price) * 100, 2),
            "warning": warning
        }

    def value_based_pricing(self, client_value, value_share_percent=30):
        price_without_vat = client_value * (value_share_percent / 100)
        min_price = self.base_cost * 1.15
        if price_without_vat < min_price:
            price_without_vat = min_price
            warning = f"Cina na osnovi cinnosti nyzhche minimumu. Vstanovleno {min_price:.2f} hrn"
        else:
            warning = None
        vat_amount = price_without_vat * (VAT_RATE / 100)
        final_price = price_without_vat + vat_amount
        profit = price_without_vat - self.base_cost
        return {
            "method": "value_based",
            "client_value": round(client_value, 2),
            "value_share_percent": value_share_percent,
            "price_without_vat": round(price_without_vat, 2),
            "vat_amount": round(vat_amount, 2),
            "final_price": round(final_price, 2),
            "profit": round(profit, 2),
            "profit_margin": round((profit / price_without_vat) * 100, 2),
            "warning": warning
        }

    def compare_methods(self, competitor_price=None, client_value=None):
        results = {"cost_plus": self.cost_plus_pricing()}
        if competitor_price:
            results["competitive"] = self.competitive_pricing(competitor_price)
        if client_value:
            results["value_based"] = self.value_based_pricing(client_value)
        return results

    def print_comparison(self, competitor_price=None, client_value=None):
        results = self.compare_methods(competitor_price, client_value)
        print("\n" + "=" * 80)
        print("PORIVNJANNJA METODIV CINOUTVORENNJA".center(80))
        print("=" * 80)
        print(f"  Bazova sobivartist: {self.base_cost:.2f} hrn")
        print("-" * 80)
        for method, result in results.items():
            print(f"\n  Metod: {method.upper()}")
            print(f"     Cina bez PDV: {result['price_without_vat']:.2f} hrn")
            print(f"     PDV ({VAT_RATE}%): {result['vat_amount']:.2f} hrn")
            print(f"     Kinceva cina: {result['final_price']:.2f} hrn")
            print(f"     Prybutok: {result['profit']:.2f} hrn")
            print(f"     Marzha: {result['profit_margin']:.2f}%")
            if result.get("warning"):
                print(f"     {result['warning']}")
        print("=" * 80)
