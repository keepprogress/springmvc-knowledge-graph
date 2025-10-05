<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ include file="../common/header.jsp" %>

<div class="content">
    <h2>User List</h2>

    <!-- Search Form -->
    <form id="searchForm" action="${pageContext.request.contextPath}/user/search" method="post">
        <input type="text" name="username" placeholder="Username">
        <input type="text" name="email" placeholder="Email">
        <button type="submit">Search</button>
    </form>

    <!-- User Table -->
    <table id="userTable">
        <thead>
            <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach items="${users}" var="user">
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.status}</td>
                    <td>
                        <button onclick="editUser(${user.id})">Edit</button>
                        <button onclick="deleteUser(${user.id})">Delete</button>
                    </td>
                </tr>
            </c:forEach>
        </tbody>
    </table>

    <!-- Add User Button -->
    <button id="addUserBtn">Add New User</button>
</div>

<script>
// AJAX call to load users
function loadUsers(page) {
    $.ajax({
        url: '${pageContext.request.contextPath}/user/list',
        type: 'GET',
        data: { page: page, size: 10 },
        success: function(data) {
            // Update table
            updateUserTable(data);
        },
        error: function(xhr, status, error) {
            alert('Failed to load users: ' + error);
        }
    });
}

// AJAX call to delete user
function deleteUser(userId) {
    if (confirm('Are you sure to delete this user?')) {
        $.ajax({
            url: '${pageContext.request.contextPath}/user/delete/' + userId,
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    alert('User deleted successfully');
                    loadUsers(1);
                } else {
                    alert('Failed to delete user: ' + response.message);
                }
            }
        });
    }
}

// AJAX call to edit user
function editUser(userId) {
    $.get('${pageContext.request.contextPath}/user/get/' + userId, function(user) {
        // Populate edit form
        $('#editUserId').val(user.id);
        $('#editUsername').val(user.username);
        $('#editEmail').val(user.email);
        $('#editDialog').dialog('open');
    });
}

// Submit edit form via AJAX
$('#editForm').submit(function(e) {
    e.preventDefault();
    $.post('${pageContext.request.contextPath}/user/update', $(this).serialize(), function(response) {
        if (response.success) {
            alert('User updated successfully');
            $('#editDialog').dialog('close');
            loadUsers(1);
        }
    });
});
</script>

<%@ include file="../common/footer.jsp" %>
