"""
Amazon E-Commerce Data Analytics Pipeline
Performs end-to-end data cleaning, transformation, validation, normalization, and generation of:
- Cleaned dataset (CSV & Excel)
- Updated dataset with newly added business transactions
- Star-schema dimensional model (dim_customers, dim_products, dim_dates, fact_orders)
- Formatted Excel workbooks with KPIs, Pivot Summaries, and Data Dictionary
"""

import os
import random
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Set deterministic seed for reproducibility
random.seed(42)
np.random.seed(42)

# File paths
RAW_FILE = 'data/raw/amazon_sales_raw.csv'
CLEANED_CSV = 'data/cleaned/amazon_sales_cleaned.csv'
UPDATED_CSV = 'data/updated/amazon_sales_with_new_data.csv'
DIM_CUSTOMERS_CSV = 'data/cleaned/dim_customers.csv'
DIM_PRODUCTS_CSV = 'data/cleaned/dim_products.csv'
DIM_DATES_CSV = 'data/cleaned/dim_dates.csv'
FACT_ORDERS_CSV = 'data/cleaned/fact_orders.csv'

RAW_EXCEL = 'excel/raw_data.xlsx'
CLEANED_EXCEL = 'excel/cleaned_data.xlsx'
ANALYTICS_MODEL_EXCEL = 'excel/amazon_sales_analytics_model.xlsx'
DATA_DICT_EXCEL = 'excel/data_dictionary.xlsx'

# State mapping dictionary for data cleaning
STATE_MAPPING = {
    'ANDAMAN & NICOBAR': 'Andaman & Nicobar Islands',
    'ANDHRA PRADESH': 'Andhra Pradesh',
    'APO': 'Military/APO',
    'AR': 'Arunachal Pradesh',
    'ARUNACHAL PRADESH': 'Arunachal Pradesh',
    'Arunachal Pradesh': 'Arunachal Pradesh',
    'Arunachal pradesh': 'Arunachal Pradesh',
    'ASSAM': 'Assam',
    'BIHAR': 'Bihar',
    'Bihar': 'Bihar',
    'bihar': 'Bihar',
    'CHANDIGARH': 'Chandigarh',
    'Chandigarh': 'Chandigarh',
    'CHHATTISGARH': 'Chhattisgarh',
    'DADRA AND NAGAR': 'Dadra and Nagar Haveli and Daman and Diu',
    'DELHI': 'Delhi',
    'Delhi': 'Delhi',
    'delhi': 'Delhi',
    'New Delhi': 'Delhi',
    'GOA': 'Goa',
    'Goa': 'Goa',
    'goa': 'Goa',
    'Gujarat': 'Gujarat',
    'HARYANA': 'Haryana',
    'HIMACHAL PRADESH': 'Himachal Pradesh',
    'JAMMU & KASHMIR': 'Jammu & Kashmir',
    'JHARKHAND': 'Jharkhand',
    'KARNATAKA': 'Karnataka',
    'KERALA': 'Kerala',
    'LADAKH': 'Ladakh',
    'LAKSHADWEEP': 'Lakshadweep',
    'MADHYA PRADESH': 'Madhya Pradesh',
    'MAHARASHTRA': 'Maharashtra',
    'MANIPUR': 'Manipur',
    'Manipur': 'Manipur',
    'MEGHALAYA': 'Meghalaya',
    'Meghalaya': 'Meghalaya',
    'MIZORAM': 'Mizoram',
    'Mizoram': 'Mizoram',
    'NAGALAND': 'Nagaland',
    'NL': 'Nagaland',
    'Nagaland': 'Nagaland',
    'ODISHA': 'Odisha',
    'Odisha': 'Odisha',
    'Orissa': 'Odisha',
    'orissa': 'Odisha',
    'PB': 'Punjab',
    'PUNJAB': 'Punjab',
    'Punjab': 'Punjab',
    'punjab': 'Punjab',
    'Punjab/Mohali/Zirakpur': 'Punjab',
    'PUDUCHERRY': 'Puducherry',
    'Pondicherry': 'Puducherry',
    'Puducherry': 'Puducherry',
    'RAJASTHAN': 'Rajasthan',
    'RJ': 'Rajasthan',
    'Rajasthan': 'Rajasthan',
    'Rajshthan': 'Rajasthan',
    'Rajsthan': 'Rajasthan',
    'rajasthan': 'Rajasthan',
    'rajsthan': 'Rajasthan',
    'SIKKIM': 'Sikkim',
    'Sikkim': 'Sikkim',
    'TAMIL NADU': 'Tamil Nadu',
    'TELANGANA': 'Telangana',
    'TRIPURA': 'Tripura',
    'UTTAR PRADESH': 'Uttar Pradesh',
    'UTTARAKHAND': 'Uttarakhand',
    'WEST BENGAL': 'West Bengal'
}

# Regional grouping for geographic analysis
REGION_MAPPING = {
    'Delhi': 'North',
    'Haryana': 'North',
    'Punjab': 'North',
    'Himachal Pradesh': 'North',
    'Jammu & Kashmir': 'North',
    'Ladakh': 'North',
    'Uttarakhand': 'North',
    'Uttar Pradesh': 'North',
    'Chandigarh': 'North',
    'Rajasthan': 'North',
    'Karnataka': 'South',
    'Tamil Nadu': 'South',
    'Telangana': 'South',
    'Andhra Pradesh': 'South',
    'Kerala': 'South',
    'Puducherry': 'South',
    'Lakshadweep': 'South',
    'Andaman & Nicobar Islands': 'South',
    'Maharashtra': 'West',
    'Gujarat': 'West',
    'Goa': 'West',
    'Dadra and Nagar Haveli and Daman and Diu': 'West',
    'West Bengal': 'East',
    'Bihar': 'East',
    'Jharkhand': 'East',
    'Odisha': 'East',
    'Madhya Pradesh': 'Central',
    'Chhattisgarh': 'Central',
    'Assam': 'North-East',
    'Arunachal Pradesh': 'North-East',
    'Manipur': 'North-East',
    'Meghalaya': 'North-East',
    'Mizoram': 'North-East',
    'Nagaland': 'North-East',
    'Sikkim': 'North-East',
    'Tripura': 'North-East',
    'Military/APO': 'Other',
    'Unknown': 'Other'
}

CATEGORY_CODES = {
    'T-shirt': 'TSH',
    'Shirt': 'SHT',
    'Blazzer': 'BLZ',
    'Trousers': 'TRS',
    'Perfume': 'PRF',
    'Wallet': 'WLT',
    'Socks': 'SOK',
    'Shoes': 'SHS',
    'Watch': 'WTC'
}

FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Reyansh', 'Ayaan', 'Krishna', 'Ishaan',
    'Shaurya', 'Atharv', 'Advik', 'Pranav', 'Advaith', 'Aaryan', 'Dhruv', 'Kabir', 'Rudra', 'Rohan',
    'Diya', 'Saanvi', 'Ananya', 'Aadhya', 'Pari', 'Anika', 'Navya', 'Angel', 'Avani', 'Myra',
    'Sara', 'Isha', 'Aarohi', 'Riya', 'Sneha', 'Tanvi', 'Pooja', 'Neha', 'Kavya', 'Priya',
    'Amit', 'Rahul', 'Vikram', 'Rajesh', 'Suresh', 'Manish', 'Deepak', 'Sanjay', 'Alok', 'Manoj'
]

LAST_NAMES = [
    'Sharma', 'Verma', 'Patel', 'Mehta', 'Gupta', 'Singh', 'Kumar', 'Joshi', 'Reddy', 'Nair',
    'Rao', 'Bose', 'Chatterjee', 'Das', 'Sen', 'Mukherjee', 'Kapoor', 'Malhotra', 'Bhatia', 'Aggarwal',
    'Chopra', 'Saxena', 'Iyer', 'Menon', 'Pillai', 'Gowda', 'Hegde', 'Deshmukh', 'Kulkarni', 'Patil',
    'Jadhav', 'Shinde', 'Pawar', 'Chauhan', 'Yadav', 'Mishra', 'Pandey', 'Dubey', 'Tiwari', 'Tripathi'
]

def load_and_clean_data():
    print("Step 1: Loading raw dataset from:", RAW_FILE)
    df = pd.read_csv(RAW_FILE, low_memory=False)
    initial_rows = len(df)
    print(f"Loaded {initial_rows} raw records.")

    # 1. Drop redundant / empty columns
    cols_to_drop = [c for c in ['index', 'New', 'PendingS', 'Unnamed: 22'] if c in df.columns]
    print(f"Dropping redundant columns: {cols_to_drop}")
    df = df.drop(columns=cols_to_drop)

    # 2. Rename columns to clean standard snake_case / PascalCase
    rename_dict = {
        'Order ID': 'Order_ID',
        'Date': 'Order_Date',
        'Status': 'Order_Status',
        'Fulfilment': 'Fulfilment_Method',
        'Sales Channel ': 'Sales_Channel',
        'Sales Channel': 'Sales_Channel',
        'ship-service-level': 'Ship_Service_Level',
        'Category': 'Category',
        'Size': 'Size',
        'Courier Status': 'Courier_Status',
        'Qty': 'Quantity',
        'currency': 'Currency',
        'Amount': 'Gross_Amount',
        'ship-city': 'Ship_City',
        'ship-state': 'Ship_State',
        'ship-postal-code': 'Ship_Postal_Code',
        'ship-country': 'Ship_Country',
        'B2B': 'Is_B2B',
        'fulfilled-by': 'Fulfilled_By'
    }
    df = df.rename(columns=rename_dict)

    # 3. Deduplication (drop duplicate records)
    dups_count = df.duplicated().sum()
    print(f"Removing {dups_count} duplicate rows...")
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Rows after deduplication: {len(df)}")

    # 4. Standardize Dates
    print("Standardizing Order_Date to ISO format YYYY-MM-DD...")
    df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='mixed')
    
    # Extract date parts
    df['Year'] = df['Order_Date'].dt.year
    df['Month_Number'] = df['Order_Date'].dt.month
    df['Month_Name'] = df['Order_Date'].dt.month_name()
    df['Year_Month'] = df['Order_Date'].dt.strftime('%Y-%m')
    df['Quarter'] = df['Order_Date'].dt.to_period('Q').astype(str)
    df['Day_Of_Week'] = df['Order_Date'].dt.day_name()
    df['Day_Of_Month'] = df['Order_Date'].dt.day
    df['Is_Weekend'] = df['Order_Date'].dt.dayofweek.isin([5, 6])
    df['Order_Date_Str'] = df['Order_Date'].dt.strftime('%Y-%m-%d')

    # 5. Standardize Categorical Fields
    df['Category'] = df['Category'].astype(str).str.strip().str.capitalize()
    # Correct common misspelling 'Blazzer' -> 'Blazer' for display or keep standardized
    df['Category'] = df['Category'].replace({'Blazzer': 'Blazer'})
    
    df['Size'] = df['Size'].astype(str).str.strip().str.upper()
    df['Size'] = df['Size'].replace({'FREE': 'Free'})
    
    df['Fulfilment_Method'] = df['Fulfilment_Method'].astype(str).str.strip()
    df['Sales_Channel'] = df['Sales_Channel'].astype(str).str.strip()
    df['Ship_Service_Level'] = df['Ship_Service_Level'].astype(str).str.strip()

    # Standardize Fulfilled_By
    df['Fulfilled_By'] = df['Fulfilled_By'].fillna('')
    df.loc[df['Fulfilment_Method'] == 'Amazon', 'Fulfilled_By'] = 'Amazon FBA'
    df.loc[(df['Fulfilment_Method'] == 'Merchant') & (df['Fulfilled_By'] == ''), 'Fulfilled_By'] = 'Easy Ship'
    df.loc[df['Fulfilled_By'] == 'Easy Ship', 'Fulfilled_By'] = 'Merchant Easy Ship'

    # Standardize Currency
    df['Currency'] = 'INR'

    # 6. Standardize Geography (State, City, Postal Code, Country)
    df['Ship_State'] = df['Ship_State'].fillna('Unknown').astype(str).str.strip()
    df['Ship_State'] = df['Ship_State'].map(lambda x: STATE_MAPPING.get(x, 'Unknown' if str(x).lower() in ['nan', 'none', '', 'unknown'] else str(x).title()))
    df['Region'] = df['Ship_State'].map(lambda x: REGION_MAPPING.get(x, 'Other'))
    
    df['Ship_City'] = df['Ship_City'].fillna('Unknown').astype(str).str.strip().str.title()
    df['Ship_Postal_Code'] = pd.to_numeric(df['Ship_Postal_Code'], errors='coerce').fillna(0).astype(int)
    df['Ship_Country'] = 'IN'
    df['Is_B2B'] = df['Is_B2B'].fillna(False).astype(bool)

    # 7. Standardize Courier Status
    df['Courier_Status'] = df['Courier_Status'].fillna('Unassigned').astype(str).str.strip()

    # 8. Clean and Impute Gross_Amount, Calculate Unit Price
    # Calculate median category price for imputation
    valid_prices = df[(df['Quantity'] > 0) & (~df['Gross_Amount'].isnull()) & (df['Gross_Amount'] > 0)]
    category_median_unit_price = valid_prices.groupby('Category').apply(
        lambda g: (g['Gross_Amount'] / g['Quantity']).median()
    ).to_dict()
    print("Median Unit Prices by Category for Imputation:", category_median_unit_price)

    # Impute missing Gross_Amount
    null_amt_mask = df['Gross_Amount'].isnull()
    zero_qty_mask = df['Quantity'] == 0

    # If Qty is 0, Gross_Amount is 0
    df.loc[null_amt_mask & zero_qty_mask, 'Gross_Amount'] = 0.0

    # If Qty > 0 and Gross_Amount is NaN, impute based on Category median
    for cat, med_price in category_median_unit_price.items():
        impute_mask = null_amt_mask & (~zero_qty_mask) & (df['Category'] == cat)
        df.loc[impute_mask, 'Gross_Amount'] = df.loc[impute_mask, 'Quantity'] * med_price

    df['Gross_Amount'] = df['Gross_Amount'].fillna(0.0).round(2)

    # Calculate Unit Price
    df['Unit_Price'] = np.where(
        df['Quantity'] > 0,
        (df['Gross_Amount'] / df['Quantity']).round(2),
        df['Category'].map(category_median_unit_price).fillna(500.0).round(2)
    )

    # 9. Group Order Status
    status_group_map = {
        'Shipped - Delivered to Buyer': 'Delivered',
        'Shipped': 'Shipped',
        'Shipped - Picked Up': 'Shipped',
        'Shipped - Out for Delivery': 'Shipped',
        'Shipping': 'Shipped',
        'Cancelled': 'Cancelled',
        'Shipped - Returned to Seller': 'Returned',
        'Shipped - Returning to Seller': 'Returned',
        'Shipped - Rejected by Buyer': 'Returned',
        'Shipped - Lost in Transit': 'Returned',
        'Shipped - Damaged': 'Returned',
        'Pending': 'Pending',
        'Pending - Waiting for Pick Up': 'Pending'
    }
    df['Order_Status_Group'] = df['Order_Status'].map(lambda x: status_group_map.get(x, 'Other'))

    # 10. Derive Financial Metrics (Net Sales, COGS, Gross Profit)
    # Net Sales is 0 for Cancelled or Returned orders (delivered/realized revenue)
    df['Net_Sales'] = np.where(
        df['Order_Status_Group'].isin(['Delivered', 'Shipped']),
        df['Gross_Amount'],
        0.0
    ).round(2)

    # COGS (Cost of Goods Sold) estimated at 65% of Net Sales
    df['COGS'] = (df['Net_Sales'] * 0.65).round(2)

    # Gross Profit = Net Sales - COGS
    df['Gross_Profit'] = (df['Net_Sales'] - df['COGS']).round(2)
    df['Profit_Margin_Pct'] = np.where(df['Net_Sales'] > 0, (df['Gross_Profit'] / df['Net_Sales'] * 100).round(2), 0.0)

    # Add tag for historical records
    df['Is_New_Record'] = False

    print(f"Data cleaning and transformation completed. Total records: {len(df)}")
    return df, category_median_unit_price

def create_star_schema(df, category_median_unit_price):
    print("\nStep 2: Constructing Normalized Star Schema Dimensions & Fact Tables...")

    # --- 1. DIM_CUSTOMERS ---
    # Create deterministic customer groupings based on (Ship_City, Ship_State, Ship_Postal_Code, Is_B2B)
    cust_groups = df.groupby(['Ship_City', 'Ship_State', 'Ship_Postal_Code', 'Region', 'Is_B2B']).agg(
        Total_Orders=('Order_ID', 'nunique'),
        Total_Spend=('Net_Sales', 'sum'),
        Gross_Spend=('Gross_Amount', 'sum'),
        First_Order_Date=('Order_Date_Str', 'min'),
        Last_Order_Date=('Order_Date_Str', 'max')
    ).reset_index()

    cust_groups['Customer_ID'] = [f"CUST-{10001 + i:05d}" for i in range(len(cust_groups))]
    
    # Generate realistic deterministic customer names
    def gen_name(row, idx):
        if row['Is_B2B']:
            b2b_names = ['Enterprise Solutions Ltd', 'Retail SuperMart India', 'Vogue Apparel Distributors',
                         'Apex Retailers', 'Metro Garment Hub', 'Zenith Fashion Mart', 'National Trade Corp']
            return f"{b2b_names[idx % len(b2b_names)]} ({row['Ship_City']})"
        else:
            fn = FIRST_NAMES[idx % len(FIRST_NAMES)]
            ln = LAST_NAMES[(idx * 7) % len(LAST_NAMES)]
            return f"{fn} {ln}"

    cust_groups['Customer_Name'] = [gen_name(row, i) for i, row in cust_groups.iterrows()]

    # Customer Segmentation
    def assign_segment(row):
        if row['Is_B2B']:
            return 'B2B Wholesale'
        elif row['Total_Spend'] >= 5000:
            return 'VIP Platinum'
        elif row['Total_Spend'] >= 2000:
            return 'Loyal Gold'
        elif row['Total_Spend'] >= 800:
            return 'Regular Silver'
        else:
            return 'Occasional Bronze'

    cust_groups['Customer_Segment'] = cust_groups.apply(assign_segment, axis=1)

    dim_customers = cust_groups[[
        'Customer_ID', 'Customer_Name', 'Customer_Segment', 'Is_B2B',
        'Ship_City', 'Ship_State', 'Region', 'Ship_Postal_Code',
        'Total_Orders', 'Total_Spend', 'Gross_Spend', 'First_Order_Date', 'Last_Order_Date'
    ]].copy()
    dim_customers = dim_customers.rename(columns={
        'Ship_City': 'City',
        'Ship_State': 'State',
        'Ship_Postal_Code': 'Postal_Code'
    })

    # Merge Customer_ID back into df
    df = df.merge(
        cust_groups[['Ship_City', 'Ship_State', 'Ship_Postal_Code', 'Region', 'Is_B2B', 'Customer_ID']],
        on=['Ship_City', 'Ship_State', 'Ship_Postal_Code', 'Region', 'Is_B2B'],
        how='left'
    )

    # --- 2. DIM_PRODUCTS ---
    prod_df = df.groupby(['Category', 'Size']).agg(
        Total_Units_Sold=('Quantity', 'sum'),
        Avg_Selling_Price=('Unit_Price', 'mean'),
        Gross_Revenue=('Gross_Amount', 'sum'),
        Net_Revenue=('Net_Sales', 'sum')
    ).reset_index()

    prod_df['Category_Code'] = prod_df['Category'].map(lambda c: CATEGORY_CODES.get(c, 'GEN'))
    prod_df['Product_ID'] = prod_df.apply(lambda r: f"PROD-{r['Category_Code']}-{r['Size']}", axis=1)
    
    product_names = {
        'T-shirt': "Men's Premium Cotton Crewneck T-Shirt",
        'Shirt': "Men's Classic Regular Fit Formal & Casual Shirt",
        'Blazer': "Slim Fit Designer Party & Formal Blazer",
        'Trousers': "Men's Stretchable Chino & Formal Trousers",
        'Perfume': "Luxury Eau De Parfum Long-Lasting Fragrance",
        'Wallet': "Genuine Leather Bifold RFID Wallet",
        'Socks': "All-Day Comfort Cushioned Ankle Socks (Pack of 3)",
        'Shoes': "Men's Lightweight Breathable Casual Sneakers",
        'Watch': "Stainless Steel Quartz Analog Chronograph Watch"
    }

    prod_df['Product_Name'] = prod_df.apply(
        lambda r: f"{product_names.get(r['Category'], r['Category'])} ({r['Size']})", axis=1
    )
    prod_df['Unit_MSRP'] = prod_df['Avg_Selling_Price'].round(2)
    prod_df['Unit_Cost'] = (prod_df['Unit_MSRP'] * 0.65).round(2)

    dim_products = prod_df[[
        'Product_ID', 'Product_Name', 'Category', 'Size',
        'Unit_MSRP', 'Unit_Cost', 'Total_Units_Sold', 'Gross_Revenue', 'Net_Revenue'
    ]].copy()

    # Merge Product_ID back into df
    df = df.merge(
        prod_df[['Category', 'Size', 'Product_ID']],
        on=['Category', 'Size'],
        how='left'
    )

    # --- 3. DIM_DATES ---
    min_date = df['Order_Date'].min()
    max_date = df['Order_Date'].max() + pd.Timedelta(days=30)  # include updated records
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')

    dim_dates = pd.DataFrame({'Full_Date': date_range})
    dim_dates['Date_Key'] = dim_dates['Full_Date'].dt.strftime('%Y%m%d').astype(int)
    dim_dates['Date_ISO'] = dim_dates['Full_Date'].dt.strftime('%Y-%m-%d')
    dim_dates['Year'] = dim_dates['Full_Date'].dt.year
    dim_dates['Quarter'] = dim_dates['Full_Date'].dt.to_period('Q').astype(str)
    dim_dates['Month_Number'] = dim_dates['Full_Date'].dt.month
    dim_dates['Month_Name'] = dim_dates['Full_Date'].dt.month_name()
    dim_dates['Year_Month'] = dim_dates['Full_Date'].dt.strftime('%Y-%m')
    dim_dates['Day_Of_Month'] = dim_dates['Full_Date'].dt.day
    dim_dates['Day_Of_Week'] = dim_dates['Full_Date'].dt.day_name()
    dim_dates['Is_Weekend'] = dim_dates['Full_Date'].dt.dayofweek.isin([5, 6])

    # --- 4. FACT_ORDERS ---
    df['Order_Item_ID'] = [f"ITEM-{100001 + i:06d}" for i in range(len(df))]

    fact_orders = df[[
        'Order_Item_ID', 'Order_ID', 'Customer_ID', 'Product_ID',
        'Order_Date_Str', 'Year', 'Month_Name', 'Quarter',
        'Order_Status', 'Order_Status_Group', 'Courier_Status',
        'Fulfilment_Method', 'Fulfilled_By', 'Sales_Channel', 'Ship_Service_Level',
        'Quantity', 'Unit_Price', 'Gross_Amount', 'Net_Sales', 'COGS', 'Gross_Profit',
        'Profit_Margin_Pct', 'Is_B2B', 'Ship_City', 'Ship_State', 'Region', 'Ship_Postal_Code',
        'Is_New_Record'
    ]].copy()
    fact_orders = fact_orders.rename(columns={'Order_Date_Str': 'Order_Date'})

    return df, dim_customers, dim_products, dim_dates, fact_orders

def generate_new_records(fact_orders, dim_customers, dim_products, count=150):
    print(f"\nStep 3: Generating {count} realistic newly added business transactions (July 2022)...")
    
    new_rows = []
    top_cust_ids = dim_customers['Customer_ID'].head(500).tolist()
    product_ids = dim_products['Product_ID'].tolist()
    prod_lookup = dim_products.set_index('Product_ID').to_dict(orient='index')
    cust_lookup = dim_customers.set_index('Customer_ID').to_dict(orient='index')

    july_dates = pd.date_range('2022-07-01', '2022-07-15', freq='D').strftime('%Y-%m-%d').tolist()

    for i in range(count):
        item_id = f"ITEM-{200001 + i:06d}"
        order_id = f"NEW-2022-{90001 + i:05d}"
        cust_id = random.choice(top_cust_ids)
        prod_id = random.choice(product_ids)
        order_date = random.choice(july_dates)
        
        cust = cust_lookup[cust_id]
        prod = prod_lookup[prod_id]

        dt = pd.to_datetime(order_date)
        year = dt.year
        month_name = dt.month_name()
        quarter = f"{year}Q{dt.quarter}"

        qty = random.choices([1, 2, 3, 4], weights=[0.80, 0.14, 0.04, 0.02])[0]
        unit_price = prod['Unit_MSRP']
        gross_amount = round(qty * unit_price, 2)
        
        # Realistic status distribution for recent July orders
        status = random.choices(
            ['Shipped - Delivered to Buyer', 'Shipped', 'Pending', 'Cancelled'],
            weights=[0.70, 0.20, 0.06, 0.04]
        )[0]
        
        if status == 'Shipped - Delivered to Buyer':
            status_grp = 'Delivered'
            courier = 'Shipped'
        elif status == 'Shipped':
            status_grp = 'Shipped'
            courier = 'Shipped'
        elif status == 'Pending':
            status_grp = 'Pending'
            courier = 'Unassigned'
        else:
            status_grp = 'Cancelled'
            courier = 'Cancelled'

        fulfilment = random.choices(['Amazon', 'Merchant'], weights=[0.75, 0.25])[0]
        fulfilled_by = 'Amazon FBA' if fulfilment == 'Amazon' else 'Merchant Easy Ship'
        ship_level = 'Expedited' if fulfilment == 'Amazon' else 'Standard'

        net_sales = gross_amount if status_grp in ['Delivered', 'Shipped'] else 0.0
        cogs = round(net_sales * 0.65, 2)
        gross_profit = round(net_sales - cogs, 2)
        profit_pct = round((gross_profit / net_sales * 100), 2) if net_sales > 0 else 0.0

        new_rows.append({
            'Order_Item_ID': item_id,
            'Order_ID': order_id,
            'Customer_ID': cust_id,
            'Product_ID': prod_id,
            'Order_Date': order_date,
            'Year': year,
            'Month_Name': month_name,
            'Quarter': quarter,
            'Order_Status': status,
            'Order_Status_Group': status_grp,
            'Courier_Status': courier,
            'Fulfilment_Method': fulfilment,
            'Fulfilled_By': fulfilled_by,
            'Sales_Channel': 'Amazon.in',
            'Ship_Service_Level': ship_level,
            'Quantity': qty,
            'Unit_Price': unit_price,
            'Gross_Amount': gross_amount,
            'Net_Sales': net_sales,
            'COGS': cogs,
            'Gross_Profit': gross_profit,
            'Profit_Margin_Pct': profit_pct,
            'Is_B2B': cust['Is_B2B'],
            'Ship_City': cust['City'],
            'Ship_State': cust['State'],
            'Region': cust['Region'],
            'Ship_Postal_Code': cust['Postal_Code'],
            'Is_New_Record': True
        })

    new_df = pd.DataFrame(new_rows)
    updated_fact_orders = pd.concat([fact_orders, new_df], ignore_index=True)
    print(f"Combined updated fact table contains {len(updated_fact_orders)} records ({count} new records added).")
    return new_df, updated_fact_orders

def create_styled_excel_workbook(filepath, sheets_data):
    """
    Utility to create beautifully formatted Excel workbooks with professional styling
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    header_fill_accent = PatternFill(start_color='2F5597', end_color='2F5597', fill_type='solid')
    title_font = Font(name='Calibri', size=14, bold=True, color='1F4E78')
    kpi_val_font = Font(name='Calibri', size=16, bold=True, color='1F4E78')
    kpi_lbl_font = Font(name='Calibri', size=10, italic=True, color='595959')
    kpi_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    for sheet_name, df, is_summary in sheets_data:
        ws = wb.create_sheet(title=sheet_name)
        ws.views.sheetView[0].showGridLines = True

        start_row = 1
        if is_summary:
            ws.cell(row=1, column=1, value=f"E-COMMERCE DATA ANALYTICS: {sheet_name.upper()}").font = title_font
            start_row = 3

        # Write headers
        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=str(col_name))
            cell.font = header_font
            cell.fill = header_fill if not is_summary else header_fill_accent
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border_thin

        # Write data rows
        for row_idx, row_val in enumerate(df.values, start_row + 1):
            for col_idx, val in enumerate(row_val, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                if pd.isna(val):
                    cell.value = ""
                elif isinstance(val, (int, np.integer)):
                    cell.value = int(val)
                    cell.number_format = '#,##0'
                elif isinstance(val, (float, np.floating)):
                    cell.value = float(val)
                    cell.number_format = '#,##0.00'
                elif isinstance(val, bool):
                    cell.value = "TRUE" if val else "FALSE"
                else:
                    cell.value = str(val)
                cell.font = Font(name='Calibri', size=10)
                cell.border = border_thin
                if row_idx % 2 == 0:
                    cell.fill = PatternFill(start_color='F2F5F9', end_color='F2F5F9', fill_type='solid')

        # Adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    wb.save(filepath)
    print(f"Saved styled Excel workbook: {filepath}")

def build_data_dictionary():
    dict_data = [
        # Fact Orders
        {'Table': 'fact_orders', 'Field_Name': 'Order_Item_ID', 'Data_Type': 'String', 'Description': 'Unique surrogate key for each order transaction line item', 'Sample_Value': 'ITEM-100001'},
        {'Table': 'fact_orders', 'Field_Name': 'Order_ID', 'Data_Type': 'String', 'Description': 'Original Amazon purchase order identifier', 'Sample_Value': '405-8078784-5731545'},
        {'Table': 'fact_orders', 'Field_Name': 'Customer_ID', 'Data_Type': 'String (FK)', 'Description': 'Surrogate foreign key linking to dim_customers', 'Sample_Value': 'CUST-10001'},
        {'Table': 'fact_orders', 'Field_Name': 'Product_ID', 'Data_Type': 'String (FK)', 'Description': 'Surrogate foreign key linking to dim_products', 'Sample_Value': 'PROD-TSH-M'},
        {'Table': 'fact_orders', 'Field_Name': 'Order_Date', 'Data_Type': 'Date (YYYY-MM-DD)', 'Description': 'Standardized transaction purchase date', 'Sample_Value': '2022-04-30'},
        {'Table': 'fact_orders', 'Field_Name': 'Order_Status', 'Data_Type': 'String', 'Description': 'Granular fulfillment status from marketplace', 'Sample_Value': 'Shipped - Delivered to Buyer'},
        {'Table': 'fact_orders', 'Field_Name': 'Order_Status_Group', 'Data_Type': 'String', 'Description': 'Categorized status: Delivered, Shipped, Cancelled, Returned, Pending', 'Sample_Value': 'Delivered'},
        {'Table': 'fact_orders', 'Field_Name': 'Courier_Status', 'Data_Type': 'String', 'Description': 'Logistics courier delivery status', 'Sample_Value': 'Shipped'},
        {'Table': 'fact_orders', 'Field_Name': 'Fulfilment_Method', 'Data_Type': 'String', 'Description': 'Fulfillment operational channel (Amazon vs Merchant)', 'Sample_Value': 'Amazon'},
        {'Table': 'fact_orders', 'Field_Name': 'Fulfilled_By', 'Data_Type': 'String', 'Description': 'Logistics execution channel (Amazon FBA vs Merchant Easy Ship)', 'Sample_Value': 'Amazon FBA'},
        {'Table': 'fact_orders', 'Field_Name': 'Quantity', 'Data_Type': 'Integer', 'Description': 'Units purchased in the line item', 'Sample_Value': '1'},
        {'Table': 'fact_orders', 'Field_Name': 'Unit_Price', 'Data_Type': 'Float (INR)', 'Description': 'Calculated average unit selling price in INR', 'Sample_Value': '647.62'},
        {'Table': 'fact_orders', 'Field_Name': 'Gross_Amount', 'Data_Type': 'Float (INR)', 'Description': 'Gross line item transaction value (GMV)', 'Sample_Value': '647.62'},
        {'Table': 'fact_orders', 'Field_Name': 'Net_Sales', 'Data_Type': 'Float (INR)', 'Description': 'Realized net revenue (0 for cancelled/returned orders)', 'Sample_Value': '647.62'},
        {'Table': 'fact_orders', 'Field_Name': 'COGS', 'Data_Type': 'Float (INR)', 'Description': 'Estimated Cost of Goods Sold (65% wholesale cost)', 'Sample_Value': '420.95'},
        {'Table': 'fact_orders', 'Field_Name': 'Gross_Profit', 'Data_Type': 'Float (INR)', 'Description': 'Gross margin contribution in INR (Net_Sales - COGS)', 'Sample_Value': '226.67'},
        {'Table': 'fact_orders', 'Field_Name': 'Is_B2B', 'Data_Type': 'Boolean', 'Description': 'Indicates if the purchase is Business-to-Business wholesale', 'Sample_Value': 'FALSE'},
        {'Table': 'fact_orders', 'Field_Name': 'Ship_City', 'Data_Type': 'String', 'Description': 'Standardized shipping destination city', 'Sample_Value': 'Bengaluru'},
        {'Table': 'fact_orders', 'Field_Name': 'Ship_State', 'Data_Type': 'String', 'Description': 'Standardized Indian state or union territory', 'Sample_Value': 'Karnataka'},
        {'Table': 'fact_orders', 'Field_Name': 'Region', 'Data_Type': 'String', 'Description': 'Geographic regional grouping (North, South, West, East, Central)', 'Sample_Value': 'South'},
        {'Table': 'fact_orders', 'Field_Name': 'Is_New_Record', 'Data_Type': 'Boolean', 'Description': 'Flag identifying newly added business transactions', 'Sample_Value': 'FALSE'},

        # Dim Customers
        {'Table': 'dim_customers', 'Field_Name': 'Customer_ID', 'Data_Type': 'String (PK)', 'Description': 'Primary key for customer entity', 'Sample_Value': 'CUST-10001'},
        {'Table': 'dim_customers', 'Field_Name': 'Customer_Name', 'Data_Type': 'String', 'Description': 'Customer account name or B2B enterprise entity name', 'Sample_Value': 'Aarav Sharma'},
        {'Table': 'dim_customers', 'Field_Name': 'Customer_Segment', 'Data_Type': 'String', 'Description': 'Behavioral RFM spending tier: B2B Wholesale, VIP Platinum, Loyal Gold, Regular Silver, Occasional Bronze', 'Sample_Value': 'Loyal Gold'},
        {'Table': 'dim_customers', 'Field_Name': 'City', 'Data_Type': 'String', 'Description': 'Primary shipping city', 'Sample_Value': 'Mumbai'},
        {'Table': 'dim_customers', 'Field_Name': 'State', 'Data_Type': 'String', 'Description': 'Primary shipping state', 'Sample_Value': 'Maharashtra'},
        {'Table': 'dim_customers', 'Field_Name': 'Region', 'Data_Type': 'String', 'Description': 'Geographical territory', 'Sample_Value': 'West'},
        {'Table': 'dim_customers', 'Field_Name': 'Total_Orders', 'Data_Type': 'Integer', 'Description': 'Lifetime order frequency', 'Sample_Value': '4'},
        {'Table': 'dim_customers', 'Field_Name': 'Total_Spend', 'Data_Type': 'Float (INR)', 'Description': 'Lifetime realized net spend', 'Sample_Value': '2840.00'},

        # Dim Products
        {'Table': 'dim_products', 'Field_Name': 'Product_ID', 'Data_Type': 'String (PK)', 'Description': 'Primary key for product SKU entity', 'Sample_Value': 'PROD-TSH-L'},
        {'Table': 'dim_products', 'Field_Name': 'Product_Name', 'Data_Type': 'String', 'Description': 'Descriptive product title and apparel size', 'Sample_Value': "Men's Premium Cotton Crewneck T-Shirt (L)"},
        {'Table': 'dim_products', 'Field_Name': 'Category', 'Data_Type': 'String', 'Description': 'Merchandise product category', 'Sample_Value': 'T-shirt'},
        {'Table': 'dim_products', 'Field_Name': 'Size', 'Data_Type': 'String', 'Description': 'Apparel sizing variation (XS, S, M, L, XL, XXL, 3XL, Free)', 'Sample_Value': 'L'},
        {'Table': 'dim_products', 'Field_Name': 'Unit_MSRP', 'Data_Type': 'Float (INR)', 'Description': 'Benchmark retail manufacturer selling price', 'Sample_Value': '649.00'},
        {'Table': 'dim_products', 'Field_Name': 'Unit_Cost', 'Data_Type': 'Float (INR)', 'Description': 'Wholesale unit acquisition cost', 'Sample_Value': '421.85'},

        # Dim Dates
        {'Table': 'dim_dates', 'Field_Name': 'Date_Key', 'Data_Type': 'Integer (PK)', 'Description': 'Numeric date key in YYYYMMDD format', 'Sample_Value': '20220430'},
        {'Table': 'dim_dates', 'Field_Name': 'Date_ISO', 'Data_Type': 'Date', 'Description': 'Standard date string in YYYY-MM-DD format', 'Sample_Value': '2022-04-30'},
        {'Table': 'dim_dates', 'Field_Name': 'Year', 'Data_Type': 'Integer', 'Description': 'Calendar year', 'Sample_Value': '2022'},
        {'Table': 'dim_dates', 'Field_Name': 'Quarter', 'Data_Type': 'String', 'Description': 'Fiscal quarter', 'Sample_Value': '2022Q2'},
        {'Table': 'dim_dates', 'Field_Name': 'Month_Name', 'Data_Type': 'String', 'Description': 'Full month title', 'Sample_Value': 'April'},
        {'Table': 'dim_dates', 'Field_Name': 'Day_Of_Week', 'Data_Type': 'String', 'Description': 'Day of the week name', 'Sample_Value': 'Saturday'},
        {'Table': 'dim_dates', 'Field_Name': 'Is_Weekend', 'Data_Type': 'Boolean', 'Description': 'Flag indicating Saturday or Sunday', 'Sample_Value': 'TRUE'}
    ]
    return pd.DataFrame(dict_data)

def main():
    print("=================================================================")
    print("STARTING E-COMMERCE DATA ANALYTICS TRANSFORMATION PIPELINE")
    print("=================================================================")

    # 1. Load and clean data
    cleaned_df, category_median_prices = load_and_clean_data()

    # 2. Build star schema
    full_df, dim_customers, dim_products, dim_dates, fact_orders = create_star_schema(
        cleaned_df, category_median_prices
    )

    # 3. Generate updated transactions
    new_records_df, updated_fact_orders = generate_new_records(
        fact_orders, dim_customers, dim_products, count=150
    )

    # 4. Save clean CSVs
    print("\nStep 4: Exporting CSV data files...")
    cleaned_df.to_csv(CLEANED_CSV, index=False)
    dim_customers.to_csv(DIM_CUSTOMERS_CSV, index=False)
    dim_products.to_csv(DIM_PRODUCTS_CSV, index=False)
    dim_dates.to_csv(DIM_DATES_CSV, index=False)
    fact_orders.to_csv(FACT_ORDERS_CSV, index=False)
    updated_fact_orders.to_csv(UPDATED_CSV, index=False)
    print("CSV files exported successfully!")

    # 5. Create summary tables for Excel Analytical Model
    print("\nStep 5: Generating Executive Analytical Summaries...")
    
    # Executive KPI summary
    total_orders = fact_orders['Order_ID'].nunique()
    total_gross = fact_orders['Gross_Amount'].sum()
    total_net = fact_orders['Net_Sales'].sum()
    total_qty = fact_orders['Quantity'].sum()
    total_cogs = fact_orders['COGS'].sum()
    total_profit = fact_orders['Gross_Profit'].sum()
    aov = total_net / total_orders if total_orders else 0
    deliv_rate = (fact_orders['Order_Status_Group'] == 'Delivered').mean() * 100
    cancel_rate = (fact_orders['Order_Status_Group'] == 'Cancelled').mean() * 100
    return_rate = (fact_orders['Order_Status_Group'] == 'Returned').mean() * 100

    kpi_summary_df = pd.DataFrame([
        {'Metric': 'Total Orders', 'Value': total_orders, 'Unit': 'Orders', 'Description': 'Count of distinct purchase orders'},
        {'Metric': 'Total Units Sold', 'Value': total_qty, 'Unit': 'Units', 'Description': 'Total apparel items purchased'},
        {'Metric': 'Gross Merchandise Value (GMV)', 'Value': total_gross, 'Unit': 'INR', 'Description': 'Total gross order value quoted'},
        {'Metric': 'Net Realized Revenue', 'Value': total_net, 'Unit': 'INR', 'Description': 'Delivered & fulfilled revenue'},
        {'Metric': 'Total Cost of Goods Sold (COGS)', 'Value': total_cogs, 'Unit': 'INR', 'Description': 'Product manufacturing & wholesale cost'},
        {'Metric': 'Total Gross Profit', 'Value': total_profit, 'Unit': 'INR', 'Description': 'Net realized profit margin'},
        {'Metric': 'Average Order Value (AOV)', 'Value': round(aov, 2), 'Unit': 'INR / Order', 'Description': 'Average net revenue per order'},
        {'Metric': 'Delivery Fulfillment Rate', 'Value': round(deliv_rate, 2), 'Unit': '%', 'Description': 'Percentage of orders successfully delivered'},
        {'Metric': 'Cancellation Rate', 'Value': round(cancel_rate, 2), 'Unit': '%', 'Description': 'Percentage of orders cancelled pre-fulfillment'},
        {'Metric': 'Return Rate', 'Value': round(return_rate, 2), 'Unit': '%', 'Description': 'Percentage of orders returned post-shipment'},
        {'Metric': 'Unique Customers', 'Value': len(dim_customers), 'Unit': 'Accounts', 'Description': 'Count of distinct customer profiles'},
        {'Metric': 'Active Product SKUs', 'Value': len(dim_products), 'Unit': 'SKUs', 'Description': 'Count of active category-size variants'}
    ])

    # Monthly Performance Summary
    monthly_summary = fact_orders.groupby(['Year', 'Month_Name']).agg(
        Orders=('Order_ID', 'nunique'),
        Units_Sold=('Quantity', 'sum'),
        Gross_Sales=('Gross_Amount', 'sum'),
        Net_Revenue=('Net_Sales', 'sum'),
        Gross_Profit=('Gross_Profit', 'sum')
    ).reset_index()
    monthly_summary['AOV'] = (monthly_summary['Net_Revenue'] / monthly_summary['Orders']).round(2)
    monthly_summary['Profit_Margin_%'] = (monthly_summary['Gross_Profit'] / monthly_summary['Net_Revenue'] * 100).round(2)

    # Category Performance Summary
    category_summary = fact_orders.merge(dim_products[['Product_ID', 'Category']], on='Product_ID', how='left').groupby('Category').agg(
        Orders=('Order_ID', 'nunique'),
        Units_Sold=('Quantity', 'sum'),
        Gross_Sales=('Gross_Amount', 'sum'),
        Net_Revenue=('Net_Sales', 'sum'),
        Gross_Profit=('Gross_Profit', 'sum')
    ).reset_index().sort_values(by='Net_Revenue', ascending=False)
    category_summary['Revenue_Share_%'] = (category_summary['Net_Revenue'] / total_net * 100).round(2)
    category_summary['Avg_Unit_Price'] = (category_summary['Net_Revenue'] / category_summary['Units_Sold']).round(2)

    # Regional Performance Summary
    regional_summary = fact_orders.groupby('Region').agg(
        Orders=('Order_ID', 'nunique'),
        Net_Revenue=('Net_Sales', 'sum'),
        Gross_Profit=('Gross_Profit', 'sum')
    ).reset_index().sort_values(by='Net_Revenue', ascending=False)
    regional_summary['Revenue_Share_%'] = (regional_summary['Net_Revenue'] / total_net * 100).round(2)

    # Customer Segment Summary
    segment_summary = dim_customers.groupby('Customer_Segment').agg(
        Customer_Count=('Customer_ID', 'count'),
        Total_Orders=('Total_Orders', 'sum'),
        Total_Net_Spend=('Total_Spend', 'sum')
    ).reset_index().sort_values(by='Total_Net_Spend', ascending=False)
    segment_summary['Customer_Share_%'] = (segment_summary['Customer_Count'] / len(dim_customers) * 100).round(2)
    segment_summary['Spend_Share_%'] = (segment_summary['Total_Net_Spend'] / segment_summary['Total_Net_Spend'].sum() * 100).round(2)
    segment_summary['Avg_Spend_Per_Customer'] = (segment_summary['Total_Net_Spend'] / segment_summary['Customer_Count']).round(2)

    # 6. Build Excel Workbooks
    print("\nStep 6: Creating professionally styled Excel Workbooks...")

    # A. Raw Data Sample & Schema Excel
    raw_sample = pd.read_csv(RAW_FILE, nrows=5000, low_memory=False)
    create_styled_excel_workbook(RAW_EXCEL, [
        ('Raw_Dataset_Sample', raw_sample, False)
    ])

    # B. Cleaned Data Sample Excel
    create_styled_excel_workbook(CLEANED_EXCEL, [
        ('Cleaned_Orders_Sample', fact_orders.head(5000), False),
        ('Dim_Products', dim_products, False),
        ('Dim_Customers_Sample', dim_customers.head(1000), False)
    ])

    # C. Amazon Sales Analytics Model Workbook
    create_styled_excel_workbook(ANALYTICS_MODEL_EXCEL, [
        ('Executive_KPIs', kpi_summary_df, True),
        ('Monthly_Sales_Trend', monthly_summary, True),
        ('Category_Performance', category_summary, True),
        ('Regional_Performance', regional_summary, True),
        ('Customer_Segmentation', segment_summary, True),
        ('Top_Products', dim_products.sort_values(by='Net_Revenue', ascending=False).head(20), False)
    ])

    # D. Data Dictionary Excel
    data_dict_df = build_data_dictionary()
    create_styled_excel_workbook(DATA_DICT_EXCEL, [
        ('Data_Dictionary', data_dict_df, True)
    ])

    print("\n=================================================================")
    print("ETL & ANALYTICS DATA PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total Clean Orders: {len(fact_orders):,}")
    print(f"Total Updated Orders: {len(updated_fact_orders):,}")
    print(f"Total Unique Customers: {len(dim_customers):,}")
    print(f"Total Product SKUs: {len(dim_products):,}")
    print(f"Total Net Realized Revenue: INR {total_net:,.2f}")
    print(f"Total Gross Merchandise Value: INR {total_gross:,.2f}")
    print("=================================================================")

if __name__ == '__main__':
    main()
