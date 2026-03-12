package com.github.Sheven.controller;

import com.github.Sheven.dto.FieldInfoResponse;
import com.github.Sheven.dto.FieldQueryRequest;
import com.github.Sheven.entity.FieldManager;
import com.github.Sheven.service.FieldManagerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 字段管理控制器
 */
@RestController
@RequestMapping("/api/field")
@CrossOrigin(origins = "*")
public class FieldManagerController {

    @Autowired
    private FieldManagerService fieldManagerService;

    /**
     * 批量查询字段信息
     * @param request 请求参数，包含英文字段名列表
     * @return 字段信息列表
     */
    @PostMapping("/query")
    public List<FieldInfoResponse> queryFieldInfos(@RequestBody FieldQueryRequest request) {
        return fieldManagerService.queryFieldInfos(request.getNameSList());
    }

    /**
     * 保存字段信息
     * @param fieldManager 字段信息
     * @return 是否成功
     */
    @PostMapping("/save")
    public boolean saveField(@RequestBody FieldManager fieldManager) {
        return fieldManagerService.saveField(fieldManager);
    }

    /**
     * 批量保存字段信息
     * @param fieldManagers 字段信息列表
     * @return 成功数量
     */
    @PostMapping("/batch-save")
    public int batchSaveFields(@RequestBody List<FieldManager> fieldManagers) {
        return fieldManagerService.batchSaveFields(fieldManagers);
    }

    /**
     * 删除字段信息
     * @param id 字段 ID
     * @return 是否成功
     */
    @DeleteMapping("/delete/{id}")
    public boolean deleteField(@PathVariable Long id) {
        return fieldManagerService.deleteField(id);
    }

    /**
     * 获取所有字段信息
     * @return 字段列表
     */
    @GetMapping("/list")
    public List<FieldManager> listAll() {
        return fieldManagerService.listAll();
    }
}
