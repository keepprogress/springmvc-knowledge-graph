<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>
<%@ include file="../common/header.jsp" %>

<!DOCTYPE html>
<html>
<head>
    <title>User List</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
</head>
<body>
    <h1>User Management</h1>

    <!-- Static include example -->
    <%@ include file="../common/navigation.jsp" %>

    <!-- Dynamic include example -->
    <jsp:include page="../common/sidebar.jsp" />

    <!-- Form example -->
    <form action="${pageContext.request.contextPath}/user/search" method="POST">
        <input type="text" name="username" required />
        <input type="email" name="email" />
        <select name="status">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
        </select>
        <button type="submit">Search</button>
    </form>

    <!-- EL Expression examples -->
    <p>Welcome, ${user.name}!</p>
    <p>Total users: ${userCount}</p>
    <p>Spring EL: #{systemProperties['user.home']}</p>

    <!-- Java Scriptlet examples -->
    <%
        String message = "Hello from scriptlet";
        int count = 0;
        for (int i = 0; i < 10; i++) {
            count++;
        }
    %>

    <!-- Expression scriptlet -->
    <p>Message: <%= message %></p>

    <!-- AJAX call examples -->
    <script>
        $(document).ready(function() {
            // jQuery $.ajax()
            $.ajax({
                url: '/api/users',
                type: 'GET',
                success: function(data) {
                    console.log(data);
                }
            });

            // jQuery $.get()
            $.get('/user/detail/' + userId, function(response) {
                $('#userInfo').html(response);
            });

            // jQuery $.post()
            $.post('${ctx}/user/save', formData, function(result) {
                alert('Saved!');
            });

            // Fetch API
            fetch('/api/users/123')
                .then(response => response.json())
                .then(data => console.log(data));

            // XMLHttpRequest
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/user/delete');
            xhr.send();
        });

        // JavaScript location
        function goToProfile() {
            location.href = '${pageContext.request.contextPath}/user/profile';
        }

        // window.open
        function openPopup() {
            window.open('/user/help', 'Help', 'width=500,height=400');
        }
    </script>

    <!-- Links -->
    <a href="/user/add">Add User</a>
    <a href="${ctx}/user/edit/${user.id}">Edit</a>
    <a href="userDetail.jsp?id=123">Details</a>

    <!-- JSTL import -->
    <c:import url="../common/footer.jsp" />
</body>
</html>
