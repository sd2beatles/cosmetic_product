conversion_qeury='''
    WITH conversion_rate as (
    SELECT  user_id,
            COUNT(DISTINCT user_id) as access_cnts,
            MAX(case when action='purchase' THEN 1 ELSE 0 END) as is_purchase
    FROM cosmetic.`transaction` 
    GROUP BY user_id)
    SELECT u.country as country,
            SUM(access_cnts) as total_access_cnts,
            SUM(is_purchase) as total_purchase
    FROM conversion_rate as c
    LEFT JOIN cosmetic.`user` as u
    ON c.user_id=u.user_id
    GROUP BY u.country;
    '''
product_query='''
    WITH product_url AS(
    SELECT short_term,
            long_term,
            main,
            category,
            product_type,
            FROM cosmetic.`transaction`),
        stats AS(
        SELECT main,category,product_type,
            COUNT(DISTINCT short_term) AS access_cnts,
            COUNT(DISTINCT long_term) AS access_users,
            COUNT(*) AS page_view,
            COUNT(*)/nullif(COUNT(distinct long_term),0) AS  pv_per_user      
            FROM product_url
            WHERE main IS NOT NULL
            GROUP BY main,category,product_type
        )
    SELECT *,
            CONCAT(CAST(EXTRACT(YEAR FROM current_date()) AS string),'-',
            LPAD(CAST(EXTRACT(MONTH FROM current_date()) AS string),2,'0')) AS satmp
    FROM stats;
'''

view_query='''
   select  access_day as stamp
            count(distinct long_term) as access_users,
            count(distinct short_term) as access_cnts,
            count(*) as page_views,
            count(*)/nullif(count(distinct long_term),0) as pv_per_user
    from count_stats
    group by access_day
    order by access_day
    ;
'''
