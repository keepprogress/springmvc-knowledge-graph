package com.example.mapper;

import com.example.model.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * User Mapper Interface
 *
 * MyBatis mapper for user data access.
 */
@Mapper
public interface UserMapper {

    /**
     * Select all users
     */
    List<User> selectAll();

    /**
     * Select user by ID
     */
    User selectById(@Param("id") Long id);

    /**
     * Select user by username
     */
    User selectByUsername(@Param("username") String username);

    /**
     * Insert new user
     */
    int insert(User user);

    /**
     * Update existing user
     */
    int update(User user);

    /**
     * Delete user by ID
     */
    int deleteById(@Param("id") Long id);

    /**
     * Search users with dynamic criteria
     */
    List<User> search(@Param("username") String username, @Param("email") String email);
}
