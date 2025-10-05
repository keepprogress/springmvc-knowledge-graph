package com.example.mapper;

import com.example.model.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.math.BigDecimal;
import java.util.List;

/**
 * User Mapper Interface
 */
@Mapper
public interface UserMapper {

    /**
     * Select user list with pagination
     */
    List<User> selectUserList(@Param("offset") int offset, @Param("size") int size);

    /**
     * Count total users
     */
    int countUsers();

    /**
     * Search users
     */
    List<User> searchUsers(@Param("username") String username, @Param("email") String email);

    /**
     * Select user by ID
     */
    User selectUserById(@Param("id") Long id);

    /**
     * Insert new user
     */
    int insertUser(User user);

    /**
     * Update user
     */
    int updateUser(User user);

    /**
     * Delete user (soft delete)
     */
    int deleteUser(@Param("id") Long id);

    /**
     * Batch delete users
     */
    int batchDeleteUsers(@Param("ids") List<Long> ids);

    /**
     * Count users by username
     */
    int countByUsername(@Param("username") String username);

    /**
     * Update user status
     */
    int updateUserStatus(@Param("id") Long id, @Param("status") String status);

    /**
     * Update user points
     */
    int updateUserPoints(@Param("userId") Long userId, @Param("amount") BigDecimal amount);

    /**
     * Call stored procedure to sync user data
     */
    void callSyncUserDataProcedure(@Param("userId") Long userId);
}
