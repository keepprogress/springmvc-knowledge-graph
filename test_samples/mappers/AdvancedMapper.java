package com.example.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import java.util.List;

/**
 * Advanced Mapper Interface - Test Cases
 *
 * Tests for:
 * - Schema-qualified table names
 * - Table aliases (with/without AS)
 * - Various JOIN types (LEFT, INNER, RIGHT, CROSS)
 * - Multiple schemas
 * - Nested fragment includes
 */
@Mapper
public interface AdvancedMapper {

    Object testSchemaQualified(@Param("status") String status);

    Object testTableAliases(@Param("userId") Long userId);

    Object testLeftJoin(@Param("userId") Long userId);

    Object testInnerJoinSchemaAlias(@Param("status") String status);

    Object testMultipleJoins();

    Object testCrossJoin(@Param("type") String type);

    int testInsertSchema(@Param("action") String action, @Param("userId") Long userId);

    int testUpdateAlias(@Param("status") String status, @Param("orderId") Long orderId);

    Object testNestedFragments();

    Object testMultipleSchemas();
}
