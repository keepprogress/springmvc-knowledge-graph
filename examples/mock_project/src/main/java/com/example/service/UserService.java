package com.example.service;

import com.example.mapper.UserMapper;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;
import java.util.List;

/**
 * User Service
 * Business logic for user management
 */
@Service
@Transactional
public class UserService {

    @Autowired
    private UserMapper userMapper;

    /**
     * Get user list with pagination
     */
    public List<User> getUserList(int page, int size) {
        int offset = (page - 1) * size;
        return userMapper.selectUserList(offset, size);
    }

    /**
     * Get total user count
     */
    public int getTotalCount() {
        return userMapper.countUsers();
    }

    /**
     * Search users by criteria
     */
    public List<User> searchUsers(String username, String email) {
        return userMapper.searchUsers(username, email);
    }

    /**
     * Get user by ID
     */
    public User getUserById(Long id) {
        return userMapper.selectUserById(id);
    }

    /**
     * Create new user
     */
    @Transactional
    public void createUser(User user) {
        user.setCreateTime(new Date());
        user.setUpdateTime(new Date());
        user.setStatus("ACTIVE");

        userMapper.insertUser(user);

        // Call stored procedure to sync user data
        userMapper.callSyncUserDataProcedure(user.getId());
    }

    /**
     * Update existing user
     */
    @Transactional
    public void updateUser(User user) {
        user.setUpdateTime(new Date());
        userMapper.updateUser(user);
    }

    /**
     * Delete user by ID
     */
    @Transactional
    public void deleteUser(Long id) {
        // Soft delete
        userMapper.deleteUser(id);
    }

    /**
     * Batch delete users
     */
    @Transactional
    public int batchDeleteUsers(List<Long> ids) {
        return userMapper.batchDeleteUsers(ids);
    }

    /**
     * Check if username exists
     */
    public boolean usernameExists(String username) {
        return userMapper.countByUsername(username) > 0;
    }

    /**
     * Activate user account
     */
    @Transactional
    public void activateUser(Long id) {
        userMapper.updateUserStatus(id, "ACTIVE");
    }

    /**
     * Lock user account
     */
    @Transactional
    public void lockUser(Long id) {
        userMapper.updateUserStatus(id, "LOCKED");
    }
}
