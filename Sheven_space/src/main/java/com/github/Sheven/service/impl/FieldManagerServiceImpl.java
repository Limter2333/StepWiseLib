package com.github.Sheven.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.github.Sheven.dto.FieldInfoResponse;
import com.github.Sheven.entity.FieldManager;
import com.github.Sheven.mapper.FieldManagerMapper;
import com.github.Sheven.service.FieldManagerService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * 字段管理服务实现类
 */
@Service
public class FieldManagerServiceImpl extends ServiceImpl<FieldManagerMapper, FieldManager> implements FieldManagerService {

    @Override
    public List<FieldInfoResponse> queryFieldInfos(String[] nameSList) {
        if (nameSList == null || nameSList.length == 0) {
            return new ArrayList<>();
        }

        // 转换为 List 便于处理
        List<String> nameList = Arrays.asList(nameSList);
        
        // 去重并转换为 Set，用于快速查找
        Set<String> uniqueNames = new HashSet<>(nameList);

        // 批量查询数据库
        List<FieldManager> dbFields = baseMapper.selectByNames(new ArrayList<>(uniqueNames));

        // 将查询结果转换为 Map，key 为 NAME_S
        Map<String, FieldManager> fieldMap = dbFields.stream()
                .collect(Collectors.toMap(FieldManager::getNameS, field -> field));

        // 构建响应结果（保持输入顺序）
        List<FieldInfoResponse> responses = new ArrayList<>();
        for (String nameS : nameList) {
            FieldManager field = fieldMap.get(nameS);
            if (field != null) {
                // 找到匹配记录
                responses.add(FieldInfoResponse.builder()
                        .nameS(field.getNameS())
                        .nameCn(field.getNameCn())
                        .itemNo(field.getItemNo())
                        .f1(field.getF1())
                        .f2(field.getF2())
                        .f3(field.getF3())
                        .f4(field.getF4())
                        .found(true)
                        .build());
            } else {
                // 未找到匹配记录，只返回英文字段名
                responses.add(FieldInfoResponse.builder()
                        .nameS(nameS)
                        .nameCn(null)
                        .itemNo(null)
                        .f1(null)
                        .f2(null)
                        .f3(null)
                        .f4(null)
                        .found(false)
                        .build());
            }
        }

        return responses;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveField(FieldManager fieldManager) {
        return this.save(fieldManager);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int batchSaveFields(List<FieldManager> fieldManagers) {
        if (fieldManagers == null || fieldManagers.isEmpty()) {
            return 0;
        }
        
        int count = 0;
        for (FieldManager field : fieldManagers) {
            if (this.save(field)) {
                count++;
            }
        }
        return count;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteField(Long id) {
        return this.removeById(id);
    }

    @Override
    public List<FieldManager> listAll() {
        return this.list(new LambdaQueryWrapper<FieldManager>()
                .orderByDesc(FieldManager::getCreateTime));
    }
}
