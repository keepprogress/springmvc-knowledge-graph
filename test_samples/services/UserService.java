package com.example.service;

import com.example.mapper.UserMapper;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * User Service - Business logic layer
 *
 * Handles user management business operations.
 */
@Service
@Transactional
public class UserService {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private EmailService emailService;

    /**
     * Find all users
     */
    public List<User> findAll() {
        return userMapper.selectAll();
    }

    /**
     * Find user by ID
     */
    public User findById(Long id) {
        if (id == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        return userMapper.selectById(id);
    }

    /**
     * Save new user with transaction
     */
    @Transactional(rollbackFor = Exception.class)
    public void save(User user) throws ServiceException {
        try {
            // Validate user
            if (user.getUsername() == null || user.getUsername().isEmpty()) {
                throw new IllegalArgumentException("Username is required");
            }

            // Check duplicate
            User existing = userMapper.selectByUsername(user.getUsername());
            if (existing != null) {
                throw new ServiceException("Username already exists");
            }

            // Save to database
            userMapper.insert(user);

            // Send welcome email
            emailService.sendWelcomeEmail(user.getEmail());

        } catch (IllegalArgumentException e) {
            throw e;
        } catch (Exception e) {
            throw new ServiceException("Failed to save user", e);
        }
    }

    /**
     * Update existing user
     */
    @Transactional
    public void update(User user) {
        userMapper.update(user);
    }

    /**
     * Delete user by ID
     */
    public void deleteById(Long id) {
        userMapper.deleteById(id);
    }

    /**
     * Search users (read-only transaction)
     */
    @Transactional(readonly = true)
    public List<User> search(String username, String email) {
        return userMapper.search(username, email);
    }

    /**
     * Batch import users
     */
    @Transactional(rollbackFor = Exception.class)
    public int batchImport(List<User> users) throws ServiceException {
        int count = 0;
        try {
            for (User user : users) {
                userMapper.insert(user);
                count++;
            }
            return count;
        } catch (Exception e) {
            throw new ServiceException("Batch import failed at user " + count, e);
        }
    }
}
