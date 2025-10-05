<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>System Header</title>
    <link rel="stylesheet" href="${pageContext.request.contextPath}/static/css/common.css">
    <script src="${pageContext.request.contextPath}/static/js/jquery-3.6.0.min.js"></script>
</head>
<body>
<div class="header">
    <h1>SpringMVC Knowledge Graph Mock System</h1>
    <nav>
        <a href="${pageContext.request.contextPath}/user/list">User Management</a>
        <a href="${pageContext.request.contextPath}/order/list">Order Management</a>
    </nav>
</div>
