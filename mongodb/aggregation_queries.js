/**
 * MongoDB Aggregation Pipelines for E-Commerce Data Analytics
 * Every pipeline maps directly to an essential business question.
 */

/**
 * Global match stage to exclude soft-deleted records from analytical aggregations.
 * Preserves historical records where is_deleted is undefined, includes active records
 * with is_deleted: false, and safely excludes soft-deleted records with is_deleted: true.
 */
const MATCH_ACTIVE_ORDERS = {
    $match: {
        is_deleted: { $ne: true }
    }
};

/**
 * 1. Executive KPIs Pipeline
 * Business Question: What is our total revenue, gross merchandise value, order volume, and unit sales?
 */
const pipelineExecutiveKPIs = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: "$order_id",
            order_net_revenue: { $sum: "$net_sales" },
            total_items_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            gross_merchandise_value: { $sum: "$gross_amount" },
            line_net_revenue: { $sum: "$net_sales" },
            total_cogs: { $sum: "$cogs" },
            total_gross_profit: { $sum: "$gross_profit" }
        }
    },
    {
        $group: {
            _id: null,
            total_orders_count: { $sum: { $cond: [{ $ne: ["$_id", null] }, 1, 0] } },
            aov_revenue: {
                $sum: { $cond: [{ $ne: ["$_id", null] }, "$order_net_revenue", 0] }
            },
            total_items_sold: { $sum: "$total_items_sold" },
            gross_merchandise_value: { $sum: "$gross_merchandise_value" },
            net_realized_revenue: { $sum: "$line_net_revenue" },
            total_cogs: { $sum: "$total_cogs" },
            total_gross_profit: { $sum: "$total_gross_profit" }
        }
    },
    {
        $project: {
            _id: 0,
            total_orders_count: 1,
            total_items_sold: 1,
            gross_merchandise_value: { $round: ["$gross_merchandise_value", 2] },
            net_realized_revenue: { $round: ["$net_realized_revenue", 2] },
            total_cogs: { $round: ["$total_cogs", 2] },
            total_gross_profit: { $round: ["$total_gross_profit", 2] },
            average_order_value: {
                $cond: [
                    { $gt: ["$total_orders_count", 0] },
                    { $round: [{ $divide: ["$aov_revenue", "$total_orders_count"] }, 2] },
                    0
                ]
            },
            gross_profit_margin_pct: {
                $cond: [
                    { $ne: ["$net_realized_revenue", 0] },
                    { $round: [{ $multiply: [{ $divide: ["$total_gross_profit", "$net_realized_revenue"] }, 100] }, 2] },
                    0
                ]
            }
        }
    }
];

/**
 * 2. Monthly Sales & Revenue Trend Pipeline
 * Business Question: How are sales and revenue trending across months?
 */
const pipelineMonthlySalesTrend = [
    MATCH_ACTIVE_ORDERS,
    {
        $set: {
            _normalized_order_date: {
                $convert: { input: "$order_date", to: "date", onError: null, onNull: null }
            }
        }
    },
    { $match: { _normalized_order_date: { $ne: null } } },
    {
        $group: {
            _id: {
                year: { $year: "$_normalized_order_date" },
                month: { $month: "$_normalized_order_date" }
            },
            order_ids: { $addToSet: "$order_id" },
            units_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            gross_gmv: { $sum: "$gross_amount" },
            net_revenue: { $sum: "$net_sales" },
            gross_profit: { $sum: "$gross_profit" }
        }
    },
    {
        $project: {
            _id: 0,
            year: "$_id.year",
            month_number: "$_id.month",
            year_month: {
                $dateToString: {
                    format: "%Y-%m",
                    date: {
                        $dateFromParts: {
                            year: "$_id.year",
                            month: "$_id.month",
                            day: 1
                        }
                    }
                }
            },
            order_count: { $size: { $setDifference: ["$order_ids", [null]] } },
            units_sold: 1,
            gross_gmv: { $round: ["$gross_gmv", 2] },
            net_revenue: { $round: ["$net_revenue", 2] },
            gross_profit: { $round: ["$gross_profit", 2] },
            average_order_value: {
                $cond: [
                    { $gt: [{ $size: { $setDifference: ["$order_ids", [null]] } }, 0] },
                    { $round: [{ $divide: ["$net_revenue", { $size: { $setDifference: ["$order_ids", [null]] } }] }, 2] },
                    0
                ]
            }
        }
    },
    { $sort: { year: 1, month_number: 1 } }
];

/**
 * 3. Category Performance Pipeline (with Join to Products)
 * Business Question: Which apparel product categories generate the highest revenue and volume?
 */
const pipelineCategoryPerformance = [
    MATCH_ACTIVE_ORDERS,
    {
        $lookup: {
            from: "products",
            localField: "product_id",
            foreignField: "product_id",
            as: "product_info"
        }
    },
    { $unwind: "$product_info" },
    {
        $group: {
            _id: "$product_info.category",
            order_ids: { $addToSet: "$order_id" },
            total_units_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            gross_sales: { $sum: "$gross_amount" },
            net_revenue: { $sum: "$net_sales" },
            total_profit: { $sum: "$gross_profit" }
        }
    },
    {
        $project: {
            _id: 0,
            category: "$_id",
            order_count: { $size: { $setDifference: ["$order_ids", [null]] } },
            total_units_sold: 1,
            gross_sales: { $round: ["$gross_sales", 2] },
            net_revenue: { $round: ["$net_revenue", 2] },
            total_profit: { $round: ["$total_profit", 2] },
            average_selling_price: {
                $cond: [
                    { $ne: ["$total_units_sold", 0] },
                    { $round: [{ $divide: ["$net_revenue", "$total_units_sold"] }, 2] },
                    0
                ]
            }
        }
    },
    { $sort: { net_revenue: -1 } }
];

/**
 * 4. Top 10 High-Value Products Pipeline
 * Business Question: Which individual product SKUs contribute the most to top-line sales?
 */
const pipelineTopProducts = [
    MATCH_ACTIVE_ORDERS,
    {
        $lookup: {
            from: "products",
            localField: "product_id",
            foreignField: "product_id",
            as: "product_info"
        }
    },
    { $unwind: "$product_info" },
    {
        $group: {
            _id: "$product_id",
            product_name: { $first: "$product_info.product_name" },
            category: { $first: "$product_info.category" },
            size: { $first: "$product_info.size" },
            units_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            net_revenue: { $sum: "$net_sales" },
            gross_profit: { $sum: "$gross_profit" }
        }
    },
    {
        $project: {
            _id: 0,
            product_id: "$_id",
            product_name: 1,
            category: 1,
            size: 1,
            units_sold: 1,
            net_revenue: { $round: ["$net_revenue", 2] },
            gross_profit: { $round: ["$gross_profit", 2] }
        }
    },
    { $sort: { net_revenue: -1 } },
    { $limit: 10 }
];

/**
 * 5. Top 10 High-Spending Customers Pipeline
 * Business Question: Who are our highest-value customers by total lifetime spend?
 */
const pipelineTopCustomers = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: "$customer_id",
            total_orders: { $addToSet: "$order_id" },
            total_items: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            total_net_spend: { $sum: "$net_sales" },
            ship_city: { $first: "$ship_city" },
            ship_state: { $first: "$ship_state" }
        }
    },
    {
        $lookup: {
            from: "customers",
            localField: "_id",
            foreignField: "customer_id",
            as: "customer_info"
        }
    },
    { $unwind: "$customer_info" },
    {
        $project: {
            _id: 0,
            customer_id: "$_id",
            customer_name: "$customer_info.customer_name",
            customer_segment: "$customer_info.customer_segment",
            is_b2b: "$customer_info.is_b2b",
            city: "$ship_city",
            state: "$ship_state",
            orders_placed: { $size: { $setDifference: ["$total_orders", [null]] } },
            total_items: 1,
            total_net_spend: { $round: ["$total_net_spend", 2] }
        }
    },
    { $sort: { total_net_spend: -1 } },
    { $limit: 10 }
];

/**
 * 6. Customer Segmentation & Value Concentration Pipeline
 * Business Question: How is revenue distributed across customer tiers?
 */
const pipelineCustomerSegmentation = [
    {
        $group: {
            _id: "$customer_segment",
            customer_count: { $sum: 1 },
            total_orders_sum: { $sum: "$total_orders" },
            total_lifetime_spend: { $sum: "$total_spend" },
            avg_spend_per_customer: { $avg: "$total_spend" }
        }
    },
    {
        $project: {
            _id: 0,
            customer_segment: "$_id",
            customer_count: 1,
            total_orders_sum: 1,
            total_lifetime_spend: { $round: ["$total_lifetime_spend", 2] },
            avg_spend_per_customer: { $round: ["$avg_spend_per_customer", 2] }
        }
    },
    { $sort: { total_lifetime_spend: -1 } }
];

/**
 * 7. Order Status & Fulfillment Funnel Pipeline
 * Business Question: What percentage of orders are delivered, shipped, cancelled, or returned?
 */
const pipelineOrderStatusFunnel = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: "$order_status_group",
            order_items_count: { $sum: 1 },
            gross_gmv: { $sum: "$gross_amount" },
            net_revenue: { $sum: "$net_sales" }
        }
    },
    {
        $project: {
            _id: 0,
            order_status_group: "$_id",
            order_items_count: 1,
            gross_gmv: { $round: ["$gross_gmv", 2] },
            net_revenue: { $round: ["$net_revenue", 2] }
        }
    },
    { $sort: { order_items_count: -1 } }
];

/**
 * 8. Geographic & Regional Sales Pipeline
 * Business Question: Which states and regions drive the highest revenue?
 */
const pipelineRegionalSales = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: { region: "$region", state: "$ship_state" },
            order_ids: { $addToSet: "$order_id" },
            net_revenue: { $sum: "$net_sales" },
            units_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            }
        }
    },
    {
        $project: {
            _id: 0,
            region: "$_id.region",
            state: "$_id.state",
            order_count: { $size: { $setDifference: ["$order_ids", [null]] } },
            units_sold: 1,
            net_revenue: { $round: ["$net_revenue", 2] }
        }
    },
    { $sort: { net_revenue: -1 } }
];

/**
 * 9. Fulfilment Channel Comparison Pipeline
 * Business Question: How does Amazon FBA perform versus Merchant Easy Ship?
 */
const pipelineFulfilmentChannel = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: "$fulfilment_method",
            order_ids: { $addToSet: "$order_id" },
            total_items_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            gross_amount: { $sum: "$gross_amount" },
            net_revenue: { $sum: "$net_sales" }
        }
    },
    {
        $project: {
            _id: 0,
            fulfilment_method: "$_id",
            order_count: { $size: { $setDifference: ["$order_ids", [null]] } },
            total_items_sold: 1,
            gross_amount: { $round: ["$gross_amount", 2] },
            net_revenue: { $round: ["$net_revenue", 2] }
        }
    },
    { $sort: { net_revenue: -1 } }
];

/**
 * 10. Low-Performing / Tail SKUs Pipeline
 * Business Question: Which products suffer from low demand or zero sales?
 */
const pipelineUnderperformingProducts = [
    MATCH_ACTIVE_ORDERS,
    {
        $group: {
            _id: "$product_id",
            units_sold: {
                $sum: {
                    $cond: [
                        { $in: ["$order_status_group", ["Delivered", "Shipped"]] },
                        { $ifNull: ["$quantity", 0] },
                        0
                    ]
                }
            },
            net_revenue: { $sum: "$net_sales" },
            order_count: { $sum: 1 }
        }
    },
    {
        $lookup: {
            from: "products",
            localField: "_id",
            foreignField: "product_id",
            as: "product_info"
        }
    },
    { $unwind: "$product_info" },
    {
        $project: {
            _id: 0,
            product_id: "$_id",
            product_name: "$product_info.product_name",
            category: "$product_info.category",
            size: "$product_info.size",
            units_sold: 1,
            net_revenue: { $round: ["$net_revenue", 2] },
            order_count: 1
        }
    },
    { $sort: { units_sold: 1, net_revenue: 1 } },
    { $limit: 10 }
];

module.exports = {
    MATCH_ACTIVE_ORDERS,
    pipelineExecutiveKPIs,
    pipelineMonthlySalesTrend,
    pipelineCategoryPerformance,
    pipelineTopProducts,
    pipelineTopCustomers,
    pipelineCustomerSegmentation,
    pipelineOrderStatusFunnel,
    pipelineRegionalSales,
    pipelineFulfilmentChannel,
    pipelineUnderperformingProducts
};
