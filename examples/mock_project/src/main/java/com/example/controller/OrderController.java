package com.example.controller;

import com.example.service.OrderService;
import com.example.service.UserService;
import com.example.model.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Order Management Controller
 */
@Controller
@RequestMapping("/order")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @Autowired
    private UserService userService;

    /**
     * Order list page
     */
    @GetMapping("/list")
    public String listOrders(Model model) {
        List<Order> orders = orderService.getAllOrders();
        model.addAttribute("orders", orders);
        return "order/list";
    }

    /**
     * Filter orders (AJAX)
     */
    @PostMapping("/filter")
    @ResponseBody
    public Map<String, Object> filterOrders(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) @DateTimeFormat(pattern = "yyyy-MM-dd") Date startDate,
            @RequestParam(required = false) @DateTimeFormat(pattern = "yyyy-MM-dd") Date endDate) {

        List<Order> orders = orderService.filterOrders(status, startDate, endDate);

        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("orders", orders);
        result.put("total", orders.size());

        return result;
    }

    /**
     * Order detail page
     */
    @GetMapping("/detail/{orderNo}")
    public String orderDetail(@PathVariable String orderNo, Model model) {
        Order order = orderService.getOrderByNo(orderNo);
        model.addAttribute("order", order);
        return "order/detail";
    }

    /**
     * Cancel order (AJAX)
     */
    @PostMapping("/cancel")
    @ResponseBody
    public Map<String, Object> cancelOrder(@RequestParam String orderNo) {
        Map<String, Object> result = new HashMap<>();

        try {
            orderService.cancelOrder(orderNo);
            result.put("success", true);
            result.put("message", "Order cancelled");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }

    /**
     * Create order
     */
    @PostMapping("/create")
    @ResponseBody
    public Map<String, Object> createOrder(@RequestBody Map<String, Object> orderData) {
        Map<String, Object> result = new HashMap<>();

        try {
            String orderNo = orderService.createOrder(orderData);
            result.put("success", true);
            result.put("orderNo", orderNo);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }

    /**
     * Update order status
     */
    @PostMapping("/updateStatus")
    @ResponseBody
    public Map<String, Object> updateOrderStatus(@RequestParam String orderNo,
                                                  @RequestParam String status) {
        Map<String, Object> result = new HashMap<>();

        try {
            orderService.updateOrderStatus(orderNo, status);
            result.put("success", true);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }
}
