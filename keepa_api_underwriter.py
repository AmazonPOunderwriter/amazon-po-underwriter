# Keepa API Underwriter Script
# Requirements: keepa (install with pip install keepa), pandas
# Input: List of UPCs or ASINs, Cost data
# Output: Underwritten purchase order recommendation

import keepa
import pandas as pd

# ========== CONFIGURATION ==========
KEEPA_API_KEY = '39i4m975lhef66iq8lcroumgrdaqk88c9cf47ehmlanjtucl276b7ub5dpshamrh'
EXTRA_COST_PER_UNIT = 0.72
FBA_FEE_DEFAULT = 4.15
REFERRAL_FEE_PERCENT = 0.15
ROI_THRESHOLD = 18
SALES_THRESHOLD = 50

# ========== SETUP ==========
api = keepa.Keepa(KEEPA_API_KEY)

# ========== FUNCTIONS ==========
def fetch_keepa_data(asin_list):
    print("Fetching Keepa data...")
    products = api.query(asin_list, domain='US', history=False)
    return products

def parse_product_data(products, cost_df):
    rows = []
    for product in products:
        try:
            asin = product['asin']
            title = product['title']
            upc = product.get('upc') or 'N/A'
            avg_30d_buybox = product.get('buyBox30', None)
            avg_rank = product.get('avg30', None)
            bought_last_30 = product.get('salesRankDrops30', 0)  # approx sales velocity

            cost_row = cost_df[cost_df['UPC'] == upc]
            cost = cost_row['Cost'].values[0] if not cost_row.empty else 0
            total_cost = cost + EXTRA_COST_PER_UNIT

            price = avg_30d_buybox / 100 if avg_30d_buybox else None
            referral_fee = price * REFERRAL_FEE_PERCENT if price else 0
            total_fees = referral_fee + FBA_FEE_DEFAULT
            net_profit = price - total_fees - total_cost if price else 0
            roi = (net_profit / total_cost) * 100 if total_cost else 0
            order_qty = round(bought_last_30 * 0.5)

            if roi >= ROI_THRESHOLD and bought_last_30 >= SALES_THRESHOLD:
                rows.append({
                    'ASIN': asin,
                    'UPC': upc,
                    'Title': title,
                    'Cost': cost,
                    'Total Unit Cost': total_cost,
                    'Expected Selling Price': price,
                    'FBA Fee': FBA_FEE_DEFAULT,
                    'Referral Fee': referral_fee,
                    'Total Amazon Fees': total_fees,
                    'Net Profit': net_profit,
                    'ROI (%)': roi,
                    'Estimated Monthly Sales': bought_last_30,
                    'Target Order Qty (50%)': order_qty
                })
        except Exception as e:
            print(f"Error parsing product {product.get('asin')}: {e}")
    return pd.DataFrame(rows)

# ========== USAGE ==========
# Example:
# asin_list = ['B003BVIAVG', 'B06XSJ9BY9']
# cost_df = pd.read_excel("CostFile.xlsx")
# result_df = parse_product_data(fetch_keepa_data(asin_list), cost_df)
# result_df.to_excel("PO_Recommendation_from_Keepa.xlsx", index=False)
