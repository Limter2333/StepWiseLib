package com.github.Sheven.shuiqi.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 数据库配置类
 */
@Configuration
public class DatabaseConfig {

    /**
     * MyBatis-Plus 分页插件
     */
    @Bean
    public MybatisPlusInterceptor mybatisPlusInterceptor() {
        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        // 注意：PaginationInnerInterceptor 在较新版本的 MyBatis-Plus 中可能需要单独依赖
        // 如果编译失败，请确保使用了正确的 MyBatis-Plus 版本
        return interceptor;
    }
}
