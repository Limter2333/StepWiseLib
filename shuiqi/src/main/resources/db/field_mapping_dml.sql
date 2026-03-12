-- ----------------------------
-- Records of field_mapping
-- ----------------------------

-- 用户相关字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('姓名', 'name', 'VARCHAR', 100, 0, NULL, '用户真实姓名', 'user_info', 'business_db'),
    ('年龄', 'age', 'INT', 11, 1, NULL, '用户年龄', 'user_info', 'business_db'),
    ('性别', 'gender', 'TINYINT', 1, 0, '0', '性别：0-未知，1-男，2-女', 'user_info', 'business_db'),
    ('手机号码', 'phone_number', 'VARCHAR', 20, 0, NULL, '用户手机号码', 'user_info', 'business_db'),
    ('邮箱', 'email', 'VARCHAR', 100, 1, NULL, '用户电子邮箱', 'user_info', 'business_db'),
    ('地址', 'address', 'VARCHAR', 500, 1, NULL, '用户详细地址', 'user_info', 'business_db'),
    ('邮编', 'zip_code', 'VARCHAR', 10, 1, NULL, '邮政编码', 'user_info', 'business_db'),
    ('身份证号', 'id_card_number', 'VARCHAR', 18, 0, NULL, '公民身份号码', 'user_info', 'business_db'),
    ('出生日期', 'birthday', 'DATE', NULL, 1, NULL, '出生年月日', 'user_info', 'business_db'),
    ('民族', 'ethnicity', 'VARCHAR', 20, 1, '汉', '民族', 'user_info', 'business_db'),
    ('国籍', 'nationality', 'VARCHAR', 50, 0, '中国', '国籍', 'user_info', 'business_db'),
    ('婚姻状况', 'marital_status', 'VARCHAR', 20, 1, NULL, '婚姻状况：未婚/已婚/离异/丧偶', 'user_info', 'business_db'),
    ('学历', 'education', 'VARCHAR', 20, 1, NULL, '最高学历', 'user_info', 'business_db'),
    ('职业', 'occupation', 'VARCHAR', 100, 1, NULL, '从事职业', 'user_info', 'business_db'),
    ('工作单位', 'company', 'VARCHAR', 200, 1, NULL, '工作单位名称', 'user_info', 'business_db'),
    ('职位', 'position', 'VARCHAR', 100, 1, NULL, '担任职位', 'user_info', 'business_db');

-- 联系方式相关字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('手机号', 'mobile', 'VARCHAR', 20, 0, NULL, '移动电话号码', 'contact_info', 'business_db'),
    ('电话', 'telephone', 'VARCHAR', 20, 1, NULL, '固定电话号码', 'contact_info', 'business_db'),
    ('固定电话', 'landline', 'VARCHAR', 20, 1, NULL, '固定电话', 'contact_info', 'business_db'),
    ('传真', 'fax', 'VARCHAR', 20, 1, NULL, '传真号码', 'contact_info', 'business_db'),
    ('QQ 号', 'qq_number', 'VARCHAR', 20, 1, NULL, 'QQ 号码', 'contact_info', 'business_db'),
    ('微信号', 'wechat_id', 'VARCHAR', 100, 1, NULL, '微信号码', 'contact_info', 'business_db');

-- 订单相关字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('订单编号', 'order_no', 'VARCHAR', 64, 0, NULL, '订单唯一编号', 'order_info', 'business_db'),
    ('订单金额', 'order_amount', 'DECIMAL', 10, 0, NULL, '订单总金额', 'order_info', 'business_db'),
    ('下单时间', 'order_time', 'DATETIME', NULL, 0, NULL, '下单时间', 'order_info', 'business_db'),
    ('支付状态', 'payment_status', 'TINYINT', 1, 0, '0', '支付状态：0-未支付，1-已支付，2-已退款', 'order_info', 'business_db'),
    ('收货地址', 'shipping_address', 'VARCHAR', 500, 0, NULL, '收货详细地址', 'order_info', 'business_db'),
    ('收货人', 'receiver_name', 'VARCHAR', 100, 0, NULL, '收货人姓名', 'order_info', 'business_db'),
    ('收货人电话', 'receiver_phone', 'VARCHAR', 20, 0, NULL, '收货人联系电话', 'order_info', 'business_db'),
    ('物流单号', 'tracking_no', 'VARCHAR', 100, 1, NULL, '物流配送单号', 'order_info', 'business_db'),
    ('订单状态', 'order_status', 'TINYINT', 1, 0, '0', '订单状态：0-待付款，1-待发货，2-待收货，3-已完成，4-已取消', 'order_info', 'business_db'),
    ('备注', 'remark', 'VARCHAR', 1000, 1, NULL, '订单备注信息', 'order_info', 'business_db');

-- 商品相关字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('商品名称', 'product_name', 'VARCHAR', 200, 0, NULL, '商品名称', 'product_info', 'business_db'),
    ('商品编码', 'product_code', 'VARCHAR', 64, 0, NULL, '商品唯一编码', 'product_info', 'business_db'),
    ('价格', 'price', 'DECIMAL', 10, 0, NULL, '商品单价', 'product_info', 'business_db'),
    ('库存数量', 'stock_quantity', 'INT', 11, 0, '0', '库存数量', 'product_info', 'business_db'),
    ('供应商', 'supplier', 'VARCHAR', 200, 1, NULL, '供应商名称', 'product_info', 'business_db'),
    ('商品分类', 'category', 'VARCHAR', 100, 1, NULL, '商品所属分类', 'product_info', 'business_db'),
    ('品牌', 'brand', 'VARCHAR', 100, 1, NULL, '商品品牌', 'product_info', 'business_db'),
    ('规格', 'specification', 'VARCHAR', 200, 1, NULL, '商品规格型号', 'product_info', 'business_db'),
    ('单位', 'unit', 'VARCHAR', 20, 0, '个', '计量单位', 'product_info', 'business_db'),
    ('重量', 'weight', 'DECIMAL', 10, 1, NULL, '商品重量 (kg)', 'product_info', 'business_db');

-- 账户相关字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('用户名', 'username', 'VARCHAR', 50, 0, NULL, '登录用户名', 'account_info', 'business_db'),
    ('密码', 'password', 'VARCHAR', 255, 0, NULL, '登录密码 (加密)', 'account_info', 'business_db'),
    ('昵称', 'nickname', 'VARCHAR', 100, 1, NULL, '用户昵称', 'account_info', 'business_db'),
    ('头像', 'avatar', 'VARCHAR', 500, 1, NULL, '用户头像 URL', 'account_info', 'business_db'),
    ('签名', 'signature', 'VARCHAR', 500, 1, NULL, '个人签名', 'account_info', 'business_db'),
    ('收入', 'income', 'DECIMAL', 12, 1, NULL, '个人收入', 'account_info', 'business_db'),
    ('存款', 'deposit', 'DECIMAL', 15, 1, NULL, '银行存款', 'account_info', 'business_db'),
    ('房产', 'property', 'VARCHAR', 500, 1, NULL, '房产信息', 'account_info', 'business_db'),
    ('车辆', 'vehicle', 'VARCHAR', 200, 1, NULL, '车辆信息', 'account_info', 'business_db'),
    ('保险', 'insurance', 'VARCHAR', 200, 1, NULL, '保险信息', 'account_info', 'business_db'),
    ('社保', 'social_security', 'VARCHAR', 100, 1, NULL, '社保账号', 'account_info', 'business_db');

-- 其他常用字段
INSERT INTO `field_mapping` (`chinese_name`, `english_name`, `field_type`, `field_length`, `nullable`, `default_value`, `description`, `table_name`, `database_name`)
VALUES
    ('城市', 'city', 'VARCHAR', 100, 1, NULL, '所在城市', 'common_field', 'business_db'),
    ('省份', 'province', 'VARCHAR', 100, 1, NULL, '所在省份', 'common_field', 'business_db'),
    ('国家', 'country', 'VARCHAR', 100, 0, '中国', '所在国家', 'common_field', 'business_db'),
    ('创建时间', 'create_time', 'DATETIME', NULL, 0, 'CURRENT_TIMESTAMP', '记录创建时间', 'common_field', 'business_db'),
    ('更新时间', 'update_time', 'DATETIME', NULL, 0, 'CURRENT_TIMESTAMP', '记录更新时间', 'common_field', 'business_db'),
    ('状态', 'status', 'TINYINT', 1, 0, '1', '状态：0-禁用，1-启用', 'common_field', 'business_db'),
    ('排序', 'sort_order', 'INT', 11, 1, '0', '排序顺序', 'common_field', 'business_db'),
    ('版本号', 'version', 'INT', 11, 0, '0', '版本号 (乐观锁)', 'common_field', 'business_db'),
    ('创建人', 'creator', 'VARCHAR', 50, 1, NULL, '创建人 ID', 'common_field', 'business_db'),
    ('更新人', 'updater', 'VARCHAR', 50, 1, NULL, '更新人 ID', 'common_field', 'business_db');
