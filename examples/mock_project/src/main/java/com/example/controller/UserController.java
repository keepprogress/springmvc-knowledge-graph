package com.example.controller;

import com.example.service.UserService;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.validation.BindingResult;

import javax.validation.Valid;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * User Management Controller
 * Handles user CRUD operations
 */
@Controller
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserService userService;

    /**
     * Show user list page
     */
    @GetMapping("/list")
    public String listUsers(@RequestParam(defaultValue = "1") int page,
                           @RequestParam(defaultValue = "10") int size,
                           Model model) {
        List<User> users = userService.getUserList(page, size);
        int totalCount = userService.getTotalCount();

        model.addAttribute("users", users);
        model.addAttribute("totalCount", totalCount);
        model.addAttribute("currentPage", page);

        return "user/list";
    }

    /**
     * Search users via AJAX
     */
    @PostMapping("/search")
    @ResponseBody
    public Map<String, Object> searchUsers(@RequestParam(required = false) String username,
                                           @RequestParam(required = false) String email) {
        List<User> users = userService.searchUsers(username, email);

        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("users", users);
        result.put("total", users.size());

        return result;
    }

    /**
     * Get user by ID (AJAX)
     */
    @GetMapping("/get/{id}")
    @ResponseBody
    public User getUser(@PathVariable Long id) {
        return userService.getUserById(id);
    }

    /**
     * Show edit user page
     */
    @GetMapping("/edit/{id}")
    public String editUserPage(@PathVariable Long id, Model model) {
        User user = userService.getUserById(id);
        model.addAttribute("user", user);
        return "user/edit";
    }

    /**
     * Save or update user
     */
    @PostMapping("/save")
    public String saveUser(@Valid @ModelAttribute User user, BindingResult result, Model model) {
        if (result.hasErrors()) {
            model.addAttribute("user", user);
            return "user/edit";
        }

        if (user.getId() == null) {
            userService.createUser(user);
        } else {
            userService.updateUser(user);
        }

        return "redirect:/user/list";
    }

    /**
     * Update user via AJAX
     */
    @PostMapping("/update")
    @ResponseBody
    public Map<String, Object> updateUserAjax(@RequestParam Long id,
                                              @RequestParam String username,
                                              @RequestParam String email,
                                              @RequestParam String status) {
        Map<String, Object> result = new HashMap<>();

        try {
            User user = new User();
            user.setId(id);
            user.setUsername(username);
            user.setEmail(email);
            user.setStatus(status);

            userService.updateUser(user);

            result.put("success", true);
            result.put("message", "User updated successfully");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }

    /**
     * Delete user (AJAX)
     */
    @PostMapping("/delete/{id}")
    @ResponseBody
    public Map<String, Object> deleteUser(@PathVariable Long id) {
        Map<String, Object> result = new HashMap<>();

        try {
            userService.deleteUser(id);
            result.put("success", true);
            result.put("message", "User deleted successfully");
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }

    /**
     * Batch delete users
     */
    @PostMapping("/batchDelete")
    @ResponseBody
    public Map<String, Object> batchDeleteUsers(@RequestParam List<Long> ids) {
        Map<String, Object> result = new HashMap<>();

        try {
            int deletedCount = userService.batchDeleteUsers(ids);
            result.put("success", true);
            result.put("deletedCount", deletedCount);
        } catch (Exception e) {
            result.put("success", false);
            result.put("message", e.getMessage());
        }

        return result;
    }
}
