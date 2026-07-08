-- 初始化用户数据
-- ⚠️ 以下 password_hash 是 BCrypt 格式的占位符，请用 BCryptPasswordEncoder 生成真实哈希后替换。
--    明文参考：admin=admin123, teacher=teacher123
--    生成方式：new BCryptPasswordEncoder().encode("admin123")

-- INSERT IGNORE INTO `user` (`username`, `password_hash`, `role`, `nickname`, `status`) VALUES
-- ('admin',   '<BCrypt hash of admin123>',   'admin',   '管理员', 'enabled'),
-- ('teacher', '<BCrypt hash of teacher123>', 'teacher', '教师',   'enabled');
