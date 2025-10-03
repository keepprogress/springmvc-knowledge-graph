package com.example.controller;

import com.example.service.UserService;
import com.example.model.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.ModelAndView;

import java.util.List;

/**
 * User Management Controller
 *
 * Handles user CRUD operations and search functionality.
 */
@Controller
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserService userService;

    /**
     * Display user list page
     */
    @GetMapping("/list")
    public String listUsers(Model model) {
        List<User> users = userService.findAll();
        model.addAttribute("users", users);
        model.addAttribute("userCount", users.size());
        return "user/list";
    }

    /**
     * Display user detail page
     */
    @GetMapping("/detail/{id}")
    public ModelAndView getUserDetail(@PathVariable("id") Long id) {
        User user = userService.findById(id);
        ModelAndView mav = new ModelAndView("user/detail");
        mav.addObject("user", user);
        return mav;
    }

    /**
     * Display user add form
     */
    @GetMapping("/add")
    public String showAddForm(Model model) {
        model.addAttribute("user", new User());
        return "user/add";
    }

    /**
     * Save new user
     */
    @PostMapping("/save")
    public String saveUser(@RequestParam("username") String username,
                          @RequestParam("email") String email,
                          @RequestParam(value = "status", required = false) String status) {
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setStatus(status != null ? status : "active");

        userService.save(user);

        return "redirect:/user/list";
    }

    /**
     * Update existing user
     */
    @PostMapping("/update")
    @ResponseBody
    public Map<String, Object> updateUser(@RequestBody User user) {
        userService.update(user);

        Map<String, Object> response = new HashMap<>();
        response.put("success", true);
        response.put("message", "User updated successfully");
        return response;
    }

    /**
     * Delete user
     */
    @DeleteMapping("/delete/{id}")
    @ResponseBody
    public String deleteUser(@PathVariable Long id) {
        userService.deleteById(id);
        return "User deleted";
    }

    /**
     * Search users
     */
    @RequestMapping(value = "/search", method = RequestMethod.POST)
    public String searchUsers(@RequestParam("username") String username,
                             @RequestParam(value = "email", required = false) String email,
                             Model model) {
        List<User> results = userService.search(username, email);
        model.addAttribute("users", results);
        return "user/list";
    }
}
