package com.example.service;

import com.example.mapper.OrderMapper;
import com.example.mapper.UserMapper;
import com.example.model.Order;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Order Service
 * Business logic for order management
 */
@Service
@Transactional
public class OrderService {

    @Autowired
    private OrderMapper orderMapper;

    @Autowired
    private UserMapper userMapper;

    /**
     * Get all orders
     */
    public List<Order> getAllOrders() {
        return orderMapper.selectAllOrders();
    }

    /**
     * Filter orders by criteria
     */
    public List<Order> filterOrders(String status, Date startDate, Date endDate) {
        return orderMapper.filterOrders(status, startDate, endDate);
    }

    /**
     * Get order by order number
     */
    public Order getOrderByNo(String orderNo) {
        return orderMapper.selectOrderByNo(orderNo);
    }

    /**
     * Create new order
     */
    @Transactional
    public String createOrder(Map<String, Object> orderData) {
        String orderNo = generateOrderNo();

        Order order = new Order();
        order.setOrderNo(orderNo);
        order.setUserId((Long) orderData.get("userId"));
        order.setTotalAmount((BigDecimal) orderData.get("totalAmount"));
        order.setStatus("PENDING");
        order.setCreateTime(new Date());

        orderMapper.insertOrder(order);

        // Insert order items
        List<Map<String, Object>> items = (List<Map<String, Object>>) orderData.get("items");
        for (Map<String, Object> item : items) {
            orderMapper.insertOrderItem(orderNo, item);
        }

        // Call procedure to calculate order
        orderMapper.callCalculateOrderProcedure(orderNo);

        return orderNo;
    }

    /**
     * Cancel order
     */
    @Transactional
    public void cancelOrder(String orderNo) {
        Order order = orderMapper.selectOrderByNo(orderNo);

        if (order == null) {
            throw new RuntimeException("Order not found: " + orderNo);
        }

        if ("COMPLETED".equals(order.getStatus())) {
            throw new RuntimeException("Cannot cancel completed order");
        }

        orderMapper.updateOrderStatus(orderNo, "CANCELLED");
    }

    /**
     * Update order status
     */
    @Transactional
    public void updateOrderStatus(String orderNo, String status) {
        orderMapper.updateOrderStatus(orderNo, status);

        // If completed, update user points
        if ("COMPLETED".equals(status)) {
            Order order = orderMapper.selectOrderByNo(orderNo);
            userMapper.updateUserPoints(order.getUserId(), order.getTotalAmount());
        }
    }

    /**
     * Generate unique order number
     */
    private String generateOrderNo() {
        return "ORD" + System.currentTimeMillis() + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
    }

    /**
     * Get user orders
     */
    public List<Order> getUserOrders(Long userId) {
        return orderMapper.selectOrdersByUserId(userId);
    }

    /**
     * Calculate order statistics
     */
    public Map<String, Object> getOrderStatistics(Date startDate, Date endDate) {
        return orderMapper.calculateOrderStatistics(startDate, endDate);
    }
}
