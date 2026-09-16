
USE Ecommerce;
GO
-- 1️⃣ السؤال: ما هي المؤشرات المالية والتنفيذية العامة للشركة؟ (Executive KPIs)
SELECT 
    COUNT(DISTINCT o.OrderID) AS TotalOrders,
    COUNT(DISTINCT o.CustomerID) AS ActiveCustomersCount,
    SUM(o.Quantity) AS TotalUnitsSold,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS TotalRevenue,
    FORMAT(AVG(o.TotalAmount), 'C', 'en-US') AS AverageOrderValue,
    COUNT(DISTINCT o.EmployeeID) AS ActiveSalesRepsCount
FROM dbo.Orders o;
GO

SELECT TOP 10 
    p.ProductID,
    p.ProductName,
    p.Category,
    p.Price AS UnitPrice,
    p.Rating,
    SUM(o.Quantity) AS TotalUnitsSold,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS TotalRevenueGenerated
FROM dbo.Products p
JOIN dbo.Orders o ON p.ProductID = o.ProductID
GROUP BY p.ProductID, p.ProductName, p.Category, p.Price, p.Rating
ORDER BY SUM(o.TotalAmount) DESC;
GO


-- 3️⃣ السؤال: ما هو ترتيب تصنيفات الكتب وحصة كل تصنيف من أرباح الشركة؟ (Category Share %)
WITH CategorySales AS (
    SELECT 
        p.Category,
        COUNT(DISTINCT o.OrderID) AS OrdersCount,
        SUM(o.Quantity) AS UnitsSold,
        SUM(o.TotalAmount) AS CategoryRevenue
    FROM dbo.Products p
    JOIN dbo.Orders o ON p.ProductID = o.ProductID
    GROUP BY p.Category
)
SELECT 
    Category,
    OrdersCount,
    UnitsSold,
    FORMAT(CategoryRevenue, 'C', 'en-US') AS Revenue,
    ROUND((CategoryRevenue / (SELECT SUM(TotalAmount) FROM dbo.Orders)) * 100, 2) AS RevenueSharePercentage
FROM CategorySales
ORDER BY CategoryRevenue DESC;
GO


-- 4️⃣ السؤال: من هم كبار العملاء الأكثر إنفاقاً في الشركة (Top 10 VIP Customers)؟
SELECT TOP 10 
    c.CustomerID,
    c.FullName AS CustomerName,
    c.Country,
    c.Email,
    COUNT(o.OrderID) AS TotalOrdersPlaced,
    SUM(o.Quantity) AS TotalBooksBought,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS TotalSpent
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.FullName, c.Country, c.Email
ORDER BY SUM(o.TotalAmount) DESC;
GO


-- 5️⃣ السؤال: تقسيم العملاء إلى شرائح تسويقية (Customer Segmentation Analysis)
WITH CustomerTiers AS (
    SELECT 
        c.CustomerID,
        SUM(o.TotalAmount) AS TotalSpent,
        CASE 
            WHEN SUM(o.TotalAmount) >= 300 THEN '👑 VIP Tier (>= $300)'
            WHEN SUM(o.TotalAmount) >= 150 THEN '🥇 Gold Tier ($150 - $299)'
            WHEN SUM(o.TotalAmount) >= 75  THEN '🥈 Silver Tier ($75 - $149)'
            ELSE '🥉 Bronze Tier (< $75)'
        END AS TierName
    FROM dbo.Customers c
    JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
    GROUP BY c.CustomerID
)
SELECT 
    TierName,
    COUNT(CustomerID) AS NumberOfCustomers,
    FORMAT(SUM(TotalSpent), 'C', 'en-US') AS TotalRevenue,
    FORMAT(AVG(TotalSpent), 'C', 'en-US') AS AvgRevenuePerCustomer
FROM CustomerTiers
GROUP BY TierName
ORDER BY SUM(TotalSpent) DESC;
GO


-- 6️⃣ السؤال: ما هي أفضل 10 دول من حيث إجمالي المبيعات وعدد الطلبات؟ (Top 10 Markets)
SELECT TOP 10 
    c.Country,
    COUNT(DISTINCT c.CustomerID) AS UniqueCustomers,
    COUNT(o.OrderID) AS TotalOrders,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS CountryRevenue,
    FORMAT(AVG(o.TotalAmount), 'C', 'en-US') AS AvgOrderValue
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.Country
ORDER BY SUM(o.TotalAmount) DESC;
GO


-- 7️⃣ السؤال: نسبة نمو المبيعات شهرياً (Month-over-Month Growth % MoM)
WITH MonthlySummary AS (
    SELECT 
        YEAR(OrderDate) AS OrderYear,
        MONTH(OrderDate) AS OrderMonthNum,
        DATENAME(MONTH, OrderDate) AS MonthName,
        SUM(TotalAmount) AS MonthlyRevenue
    FROM dbo.Orders
    GROUP BY YEAR(OrderDate), MONTH(OrderDate), DATENAME(MONTH, OrderDate)
)
SELECT 
    OrderYear,
    MonthName,
    FORMAT(MonthlyRevenue, 'C', 'en-US') AS Revenue,
    FORMAT(LAG(MonthlyRevenue) OVER (ORDER BY OrderYear, OrderMonthNum), 'C', 'en-US') AS PreviousMonthRevenue,
    ROUND(
        ((MonthlyRevenue - LAG(MonthlyRevenue) OVER (ORDER BY OrderYear, OrderMonthNum)) 
        / NULLIF(LAG(MonthlyRevenue) OVER (ORDER BY OrderYear, OrderMonthNum), 0)) * 100, 2
    ) AS MoM_GrowthPercentage
FROM MonthlySummary
ORDER BY OrderYear, OrderMonthNum;
GO


-- 8️⃣ السؤال: ما هي أيام الأسبوع الأكثر تحقيقاً للمبيعات؟ (Sales by Day of Week)
SELECT 
    DATENAME(WEEKDAY, OrderDate) AS DayOfWeek,
    COUNT(OrderID) AS TotalOrders,
    SUM(Quantity) AS TotalUnitsSold,
    FORMAT(SUM(TotalAmount), 'C', 'en-US') AS TotalRevenue,
    FORMAT(AVG(TotalAmount), 'C', 'en-US') AS AvgDailyOrderValue
FROM dbo.Orders
GROUP BY DATENAME(WEEKDAY, OrderDate), DATEPART(WEEKDAY, OrderDate)
ORDER BY DATEPART(WEEKDAY, OrderDate);
GO


-- 9️⃣ السؤال: أفضل 10 موظفي مبيعات أداءً وإجمالي العمولات المستحقة؟ (Top Sales Reps)
SELECT TOP 10 
    e.EmployeeID,
    e.FullName AS SalesRep,
    e.JobTitle,
    e.Department,
    e.OfficeLocation,
    e.PerformanceScore,
    COUNT(o.OrderID) AS ClosedOrders,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS SalesRevenueGenerated,
    FORMAT(SUM(ROUND(o.TotalAmount * e.CommissionRate, 2)), 'C', 'en-US') AS TotalCommissionEarned
FROM dbo.Employees e
JOIN dbo.Orders o ON e.EmployeeID = o.EmployeeID
GROUP BY e.EmployeeID, e.FullName, e.JobTitle, e.Department, e.OfficeLocation, e.PerformanceScore
ORDER BY SUM(o.TotalAmount) DESC;
GO


-- 🔟 السؤال: أداء ومبيعات كل قسم من أقسام المبيعات (Department ROI)
SELECT 
    e.Department,
    COUNT(DISTINCT e.EmployeeID) AS RepsCount,
    COUNT(o.OrderID) AS TotalOrders,
    FORMAT(SUM(e.Salary), 'C', 'en-US') AS TotalBaseSalaries,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS DepartmentSalesRevenue,
    FORMAT(SUM(ROUND(o.TotalAmount * e.CommissionRate, 2)), 'C', 'en-US') AS TotalCommissionsPaid
FROM dbo.Employees e
JOIN dbo.Orders o ON e.EmployeeID = o.EmployeeID
GROUP BY e.Department
ORDER BY SUM(o.TotalAmount) DESC;
GO


-- 1️⃣1️⃣ السؤال: تنبيهات المخزون والمنتجات التي توشك على النفاد (Stock Alert)
SELECT 
    p.ProductID,
    p.ProductName,
    p.Category,
    p.StockQuantity AS AvailableStock,
    ISNULL(SUM(o.Quantity), 0) AS TotalUnitsSoldSoFar,
    CASE 
        WHEN p.StockQuantity <= 10 THEN '🚨 CRITICAL: Reorder Immediately'
        WHEN p.StockQuantity <= 15 THEN '⚠️ WARNING: Low Stock'
        ELSE '✅ Stock Healthy'
    END AS InventoryStatus
FROM dbo.Products p
LEFT JOIN dbo.Orders o ON p.ProductID = o.ProductID
GROUP BY p.ProductID, p.ProductName, p.Category, p.StockQuantity
ORDER BY p.StockQuantity ASC;
GO


-- 1️⃣2️⃣ السؤال: مقارنة سلوك الشراء ومؤشرات الإنفاق بين الجنسين (Gender Analytics)
SELECT 
    c.Gender,
    COUNT(DISTINCT c.CustomerID) AS CustomerCount,
    COUNT(o.OrderID) AS TotalOrders,
    SUM(o.Quantity) AS TotalBooksPurchased,
    FORMAT(SUM(o.TotalAmount), 'C', 'en-US') AS TotalRevenue,
    FORMAT(AVG(o.TotalAmount), 'C', 'en-US') AS AverageOrderValue
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.Gender;
GO
