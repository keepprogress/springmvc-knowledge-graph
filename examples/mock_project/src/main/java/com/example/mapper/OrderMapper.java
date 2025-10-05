package com.example.mapper;

import com.example.model.Order;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * Order Mapper Interface
 */
@Mapper
public interface OrderMapper {

    /**
     * Select all orders
     */
    List<Order> selectAllOrders();

    /**
     * Filter orders by criteria
     */
    List<Order> filterOrders(@Param("status") String status,
                            @Param("startDate") Date startDate,
                            @Param("endDate") Date endDate);

    /**
     * Select order by order number
     */
    Order selectOrderByNo(@Param("orderNo") String orderNo);

    /**
     * Insert new order
     */
    int insertOrder(Order order);

    /**
     * Insert order item
     */
    int insertOrderItem(@Param("orderNo") String orderNo, @Param("item") Map<String, Object> item);

    /**
     * Update order status
     */
    int updateOrderStatus(@Param("orderNo") String orderNo, @Param("status") String status);

    /**
     * Select orders by user ID
     */
    List<Order> selectOrdersByUserId(@Param("userId") Long userId);

    /**
     * Calculate order statistics
     */
    Map<String, Object> calculateOrderStatistics(@Param("startDate") Date startDate,
                                                  @Param("endDate") Date endDate);

    /**
     * Call stored procedure to calculate order
     */
    void callCalculateOrderProcedure(@Param("orderNo") String orderNo);
}
