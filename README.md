# AitiGuruTechTask

## Task 1
<img width="2194" height="1288" alt="SQL Import (postgresql) (2)" src="https://github.com/user-attachments/assets/c4cd1778-d9ea-4437-9de6-cef65633067e" />



## Task2
### 2.1
SELECT 
    clients.name AS client_name,
    SUM(order_items.total_price) AS total_sum
FROM clients
JOIN orders ON clients.id = orders.client_id
JOIN order_items ON orders.id = order_items.order_id
GROUP BY clients.id
ORDER BY total_sum DESC;
### 2.2
SELECT 
    parent.name AS category_name,
    COUNT(child.id) AS child_count
FROM categories parent
LEFT JOIN categories child ON parent.id = child.parent_id
GROUP BY parent.id
ORDER BY child_count DESC;

### 2.3
#### 2.3.1
CREATE VIEW top_5_products_last_month AS
SELECT 
    nomenclature.name AS product_name,
    COALESCE(categories.path[1], 'Без категории') AS top_level_category,
    SUM(order_items.quantity) AS total_quantity_sold
FROM order_items
JOIN nomenclature ON order_items.nomenclature_id = nomenclature.id
LEFT JOIN categories ON nomenclature.category_id = categories.id
JOIN orders ON order_items.order_id = orders.id
WHERE orders.order_date >= NOW() - INTERVAL '1 month'
GROUP BY 
    nomenclature.id, 
    nomenclature.name, 
    categories.path[1]
ORDER BY total_quantity_sold DESC
LIMIT 5;

#### 2.3.2

Самая главная проблема view - необходимость каждый раз с нуля пересчитывать агрегации с нуля. Решением этой проблемы может стать Materialized View, который будет хранить уже обработанные данные, а обработка будет происходить по заданному триггеру, например, каждый день в самое незагруженное время для системы. При большом объеме данных это будет экономить время и системные ресурсы.
Для схемы данных критически важным является добавление индексов на часто используемые поля. Так же можно переделать сущность categories, например в поле path использовать ltree вместо более простого text[], для более удобной и быстрой работой с деревом.
