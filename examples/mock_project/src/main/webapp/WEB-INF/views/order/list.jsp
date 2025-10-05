<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ include file="../common/header.jsp" %>

<div class="content">
    <h2>Order List</h2>

    <!-- Filter Form -->
    <form id="filterForm">
        <select name="status" id="statusFilter">
            <option value="">All Status</option>
            <option value="PENDING">Pending</option>
            <option value="PROCESSING">Processing</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
        </select>
        <input type="date" name="startDate" id="startDate">
        <input type="date" name="endDate" id="endDate">
        <button type="button" onclick="filterOrders()">Filter</button>
    </form>

    <!-- Order Table -->
    <table id="orderTable">
        <thead>
            <tr>
                <th>Order No</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Create Date</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach items="${orders}" var="order">
                <tr>
                    <td>${order.orderNo}</td>
                    <td>${order.customerName}</td>
                    <td><fmt:formatNumber value="${order.totalAmount}" pattern="#,##0.00"/></td>
                    <td>${order.status}</td>
                    <td><fmt:formatDate value="${order.createTime}" pattern="yyyy-MM-dd HH:mm"/></td>
                    <td>
                        <button onclick="viewOrder('${order.orderNo}')">View</button>
                        <button onclick="cancelOrder('${order.orderNo}')">Cancel</button>
                    </td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
</div>

<script>
var ctx = '${pageContext.request.contextPath}';

// Filter orders via AJAX
function filterOrders() {
    var status = $('#statusFilter').val();
    var startDate = $('#startDate').val();
    var endDate = $('#endDate').val();

    $.ajax({
        url: ctx + '/order/filter',
        type: 'POST',
        data: {
            status: status,
            startDate: startDate,
            endDate: endDate
        },
        success: function(data) {
            updateOrderTable(data.orders);
        }
    });
}

// View order details
function viewOrder(orderNo) {
    window.location.href = ctx + '/order/detail/' + orderNo;
}

// Cancel order
function cancelOrder(orderNo) {
    if (confirm('Cancel order ' + orderNo + '?')) {
        $.post(ctx + '/order/cancel', { orderNo: orderNo }, function(response) {
            if (response.success) {
                alert('Order cancelled');
                location.reload();
            } else {
                alert('Failed: ' + response.message);
            }
        });
    }
}

function updateOrderTable(orders) {
    var tbody = $('#orderTable tbody');
    tbody.empty();
    $.each(orders, function(i, order) {
        var row = '<tr>' +
            '<td>' + order.orderNo + '</td>' +
            '<td>' + order.customerName + '</td>' +
            '<td>' + order.totalAmount.toFixed(2) + '</td>' +
            '<td>' + order.status + '</td>' +
            '<td>' + order.createTime + '</td>' +
            '<td><button onclick="viewOrder(\'' + order.orderNo + '\')">View</button></td>' +
            '</tr>';
        tbody.append(row);
    });
}
</script>

<%@ include file="../common/footer.jsp" %>
