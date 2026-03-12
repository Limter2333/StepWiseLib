package com.github.Sheven.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.github.Sheven.dto.FieldInfoResponse;
import com.github.Sheven.entity.FieldManager;

import java.util.List;

/**
 * 字段管理服务接口
 */
public interface FieldManagerService extends IService<FieldManager> {

    /**
     * 根据多个英文字段名查询字段信息
     * @param nameSList 英文字段名列表
     * @return 字段信息列表（包含未找到的字段）
     */
    List<FieldInfoResponse> queryFieldInfos(String[] nameSList);

    /**
     * 保存字段信息
     * @param fieldManager 字段信息
     * @return 是否成功
     */
    boolean saveField(FieldManager fieldManager);

    /**
     * 批量保存字段信息
     * @param fieldManagers 字段信息列表
     * @return 成功数量
     */
    int batchSaveFields(List<FieldManager> fieldManagers);

    /**
     * 删除字段信息
     * @param id 字段 ID
     * @return 是否成功
     */
    boolean deleteField(Long id);

    /**
     * 获取所有字段信息
     * @return 字段列表
     */
    List<FieldManager> listAll();
}
