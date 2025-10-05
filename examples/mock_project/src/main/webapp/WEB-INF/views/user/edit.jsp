<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="form" uri="http://www.springframework.org/tags/form" %>
<jsp:include page="../common/header.jsp" />

<div class="content">
    <h2>Edit User</h2>

    <form:form id="userForm" modelAttribute="user" action="${pageContext.request.contextPath}/user/save" method="post">
        <form:hidden path="id" />

        <div class="form-group">
            <label for="username">Username:</label>
            <form:input path="username" id="username" required="true" />
            <form:errors path="username" cssClass="error" />
        </div>

        <div class="form-group">
            <label for="email">Email:</label>
            <form:input path="email" id="email" type="email" required="true" />
            <form:errors path="email" cssClass="error" />
        </div>

        <div class="form-group">
            <label for="status">Status:</label>
            <form:select path="status" id="status">
                <form:option value="ACTIVE">Active</form:option>
                <form:option value="INACTIVE">Inactive</form:option>
                <form:option value="LOCKED">Locked</form:option>
            </form:select>
        </div>

        <div class="form-actions">
            <button type="submit">Save</button>
            <button type="button" onclick="history.back()">Cancel</button>
        </div>
    </form:form>
</div>

<script>
// Validate form before submit
$('#userForm').submit(function(e) {
    var username = $('#username').val();
    var email = $('#email').val();

    if (!username || username.length < 3) {
        alert('Username must be at least 3 characters');
        e.preventDefault();
        return false;
    }

    if (!validateEmail(email)) {
        alert('Please enter a valid email address');
        e.preventDefault();
        return false;
    }

    return true;
});

function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}
</script>

<jsp:include page="../common/footer.jsp" />
