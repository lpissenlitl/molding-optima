# 2024-11-15
ALTER TABLE `yizumi_molding`.`machine_injector` 
ADD COLUMN `serial_no` VARCHAR(45) NULL AFTER `name`;

ALTER TABLE `yizumi_molding`.`admin_user` 
ADD COLUMN `app_id` VARCHAR(45) NULL AFTER `phone`;


ALTER TABLE `yizumi_molding`.`project` 
ADD COLUMN `subrule_no` VARCHAR(45) NULL AFTER `product_small_type`;

ALTER TABLE `yizumi_molding`.`process_index` 
ADD COLUMN `subrule_no` VARCHAR(45) NULL AFTER `mold_trials_no`;

# 2024.12.9
ALTER TABLE `yizumi_molding`.`rule_method` 
ADD COLUMN `priority` DOUBLE NULL COMMENT '优先级0~2' AFTER `rule_type`;


# 2024.12.10 规范asset_no是资产编号,serial_no是设备编码
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0090I0949' WHERE (`id` = '312');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'FF200Z0047' WHERE (`id` = '313');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'FF240Z0041' WHERE (`id` = '319');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0160I0701' WHERE (`id` = '320');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '' WHERE (`id` = '325');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'FF160Z0127' WHERE (`id` = '327');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0120L0005' WHERE (`id` = '328');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = 'KSM260550355', `serial_no` = 'S0120I2970' WHERE (`id` = '335');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0120I3009' WHERE (`id` = '336');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '' WHERE (`id` = '337');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '' WHERE (`id` = '339');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = '' WHERE (`id` = '340');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'BI400-M' WHERE (`id` = '341');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'FF200Z0047' WHERE (`id` = '343');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0120I3447' WHERE (`id` = '344');
UPDATE `yizumi_molding`.`machine` SET `asset_no` = '', `serial_no` = 'S0090I0948' WHERE (`id` = '345');

# 2024.12.11 适配查询
UPDATE `yizumi_molding`.`group` SET `deleted` = '0' WHERE (`id` = '1');


# 2024.12.23 模具机温度
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('151', 'MT0', '3', '0', '100', '10', '参数', '模温机温度1', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('152', 'MT1', '3', '0', '100', '10', '参数', '模温机温度2', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('153', 'MT2', '3', '0', '100', '10', '参数', '模温机温度3', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('154', 'MT3', '3', '0', '100', '10', '参数', '模温机温度4', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('155', 'MT4', '3', '0', '100', '10', '参数', '模温机温度5', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('156', 'MT5', '3', '0', '100', '10', '参数', '模温机温度6', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('157', 'MT6', '3', '0', '100', '10', '参数', '模温机温度7', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('158', 'MT7', '3', '0', '100', '10', '参数', '模温机温度8', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('159', 'MT8', '3', '0', '100', '10', '参数', '模温机温度9', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('160', 'MT9', '3', '0', '100', '10', '参数', '模温机温度10', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('161', 'MT10', '3', '0', '100', '10', '参数', '模温机温度11', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('162', 'MT11', '3', '0', '100', '10', '参数', '模温机温度12', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('163', 'MT12', '3', '0', '100', '10', '参数', '模温机温度13', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('164', 'MT13', '3', '0', '100', '10', '参数', '模温机温度14', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('165', 'MT14', '3', '0', '100', '10', '参数', '模温机温度15', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('166', 'MT15', '3', '0', '100', '10', '参数', '模温机温度16', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('167', 'MT16', '3', '0', '100', '10', '参数', '模温机温度17', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('168', 'MT17', '3', '0', '100', '10', '参数', '模温机温度18', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('169', 'MT18', '3', '0', '100', '10', '参数', '模温机温度19', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');
INSERT INTO `yizumi_molding`.`rule_keyword` (`id`, `name`, `level`, `all_range_min`, `all_range_max`, `action_max_val`, `keyword_type`, `comment`, `created_at`, `updated_at`, `deleted`, `rule_type`, `show_on_page`) VALUES ('170', 'MT19', '3', '0', '100', '10', '参数', '模温机温度20', '2024-10-31 16:52:00', '2024-10-31 16:52:00', '0', '基础库', '1');

# 2025.1.9
INSERT INTO `yizumi`.`admin_permission` (`id`, `created_at`, `updated_at`, `deleted`, `name`, `code`, `sort_index`, `description`, `full_path`, `is_leaf`, `parent_id`, `level`) VALUES ('66', '2022-05-30 08:58:40.982588', '2023-02-08 17:15:47.903969', '0', '辅机列表', 'auxiliary_list', '2', '', '1/32/66/', '0', '32', '1');
INSERT INTO `yizumi`.`admin_permission` (`id`, `created_at`, `updated_at`, `deleted`, `name`, `code`, `sort_index`, `description`, `full_path`, `is_leaf`, `parent_id`, `level`) VALUES ('67', '2022-05-30 08:58:40.993582', '2023-02-08 17:15:47.910950', '0', '查看辅机', 'review_auxiliary', '1', '', '1/32/66/67/', '1', '66', '1');
INSERT INTO `yizumi`.`admin_permission` (`id`, `created_at`, `updated_at`, `deleted`, `name`, `code`, `sort_index`, `description`, `full_path`, `is_leaf`, `parent_id`, `level`) VALUES ('68', '2022-05-30 08:58:41.001572', '2023-02-08 17:15:47.915911', '0', '增加辅机', 'add_auxiliary', '2', '', '1/32/66/68/', '1', '66', '1');
INSERT INTO `yizumi`.`admin_permission` (`id`, `created_at`, `updated_at`, `deleted`, `name`, `code`, `sort_index`, `description`, `full_path`, `is_leaf`, `parent_id`, `level`) VALUES ('69', '2022-05-30 08:58:41.013626', '2023-02-08 17:15:47.921006', '0', '删除辅机', 'delete_auxiliary', '3', '', '1/32/66/69/', '1', '66', '1');
INSERT INTO `yizumi`.`admin_permission` (`id`, `created_at`, `updated_at`, `deleted`, `name`, `code`, `sort_index`, `description`, `full_path`, `is_leaf`, `parent_id`, `level`) VALUES ('70', '2022-05-30 08:58:41.021578', '2023-02-08 17:15:47.927988', '0', '修改辅机', 'update_auxiliary', '4', '', '1/32/66/70/', '1', '66', '1');
