import { useState, useEffect, useMemo } from 'react';
import provincesData from '@/assets/provinces.json';
import citiesData from '@/assets/cities.json';
import areasData from '@/assets/areas.json';

interface Province {
  code: string;
  name: string;
}

interface City {
  code: string;
  name: string;
  provinceCode: string;
}

interface Area {
  code: string;
  name: string;
  cityCode: string;
  provinceCode: string;
}

interface LocationSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export function LocationSelector({ value, onChange }: LocationSelectorProps) {
  const [selectedProvince, setSelectedProvince] = useState<string>('');
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [selectedArea, setSelectedArea] = useState<string>('');
  
  // 缓存当前选中的省份对象
  const currentProvince = useMemo(() => {
    return provincesData.find(p => p.name === selectedProvince);
  }, [selectedProvince]);

  // 使用 useMemo 缓存过滤后的城市数据
  const cities = useMemo(() => {
    if (!currentProvince) return [];
    return (citiesData as City[]).filter(city => city.provinceCode === currentProvince.code);
  }, [currentProvince]);

  // 使用 useMemo 缓存过滤后的区县数据
  const areas = useMemo(() => {
    if (!selectedCity || !currentProvince) return [];
    
    // 通过省份代码和城市名称唯一确定城市
    const city = (citiesData as City[]).find(c => 
      c.provinceCode === currentProvince.code && c.name === selectedCity
    );
    
    if (!city) return [];
    return (areasData as Area[]).filter(area => area.cityCode === city.code);
  }, [selectedCity, currentProvince]);

  // 初始化时解析已有的值
  useEffect(() => {
    if (value) {
      // 查找省份
      for (const province of provincesData) {
        if (value.startsWith(province.name)) {
          setSelectedProvince(province.name);
          
          // 查找该省份下的城市
          const cityList = (citiesData as City[]).filter(city => city.provinceCode === province.code);
          
          // 查找匹配的城市
          for (const city of cityList) {
            if (value.includes(city.name)) {
              setSelectedCity(city.name);
              
              // 查找该城市下的区县
              const areaList = (areasData as Area[]).filter(area => area.cityCode === city.code);
              
              // 查找匹配的区县
              for (const area of areaList) {
                if (value.includes(area.name)) {
                  setSelectedArea(area.name);
                  break;
                }
              }
              break;
            }
          }
          break;
        }
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 处理省份变化
  const handleProvinceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provinceName = e.target.value;
    setSelectedProvince(provinceName);
    setSelectedCity('');
    setSelectedArea('');
    
    // 更新值
    onChange(provinceName);
  };

  // 处理城市变化
  const handleCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const cityName = e.target.value;
    setSelectedCity(cityName);
    setSelectedArea('');
    
    // 更新值
    onChange(`${selectedProvince}${cityName}`);
  };

  // 处理区县变化
  const handleAreaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const areaName = e.target.value;
    setSelectedArea(areaName);
    
    // 更新完整值
    onChange(`${selectedProvince}${selectedCity}${areaName}`);
  };

  return (
    <div className="grid grid-cols-3 gap-2">
      {/* 省份选择 */}
      <select
        value={selectedProvince}
        onChange={handleProvinceChange}
        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
      >
        <option value="">请选择省份</option>
        {provincesData.map((province) => (
          <option key={province.code} value={province.name}>
            {province.name}
          </option>
        ))}
      </select>

      {/* 城市选择 */}
      <select
        value={selectedCity}
        onChange={handleCityChange}
        disabled={!selectedProvince}
        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-50"
      >
        <option value="">请选择城市</option>
        {cities.map((city) => (
          <option key={city.code} value={city.name}>
            {city.name}
          </option>
        ))}
      </select>

      {/* 区县选择 */}
      <select
        value={selectedArea}
        onChange={handleAreaChange}
        disabled={!selectedCity}
        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-50"
      >
        <option value="">请选择区县</option>
        {areas.map((area) => (
          <option key={area.code} value={area.name}>
            {area.name}
          </option>
        ))}
      </select>
    </div>
  );
}
