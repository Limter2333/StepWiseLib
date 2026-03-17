import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Heart, Calendar, MapPin, Image as ImageIcon } from 'lucide-react';

const MBTI_TYPES = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
];

const INTERESTS_OPTIONS = [
  '阅读', '音乐', '电影', '旅行',
  '运动', '烹饪', '摄影', '绘画',
  '游戏', '舞蹈', '园艺', '手工'
];

interface PartnerFormProps {
  onSubmit: (data: FormData) => void;
  loading: boolean;
}

interface FormData {
  gender: string;
  mbtiType: string;
  birthDate: string;
  useLunar: boolean;
  birthTime: string;
  unknownBirthTime: boolean;
  birthPlace: string;
  currentResidence: string;
  interests: string[];
  customFeatures: string;
  zodiacSign: string;
}

export function PartnerForm({ onSubmit, loading }: PartnerFormProps) {
  const [formData, setFormData] = useState<FormData>({
    gender: '',
    mbtiType: '',
    birthDate: '',
    useLunar: false,
    birthTime: '',
    unknownBirthTime: false,
    birthPlace: '',
    currentResidence: '',
    interests: [],
    customFeatures: '',
    zodiacSign: '',
  });

  const [randomInterests, setRandomInterests] = useState<string[]>([]);

  // 生成随机兴趣
  const generateRandomInterests = () => {
    const shuffled = [...INTERESTS_OPTIONS].sort(() => 0.5 - Math.random());
    setRandomInterests(shuffled.slice(0, 6));
  };

  // 初始化随机兴趣
  React.useEffect(() => {
    generateRandomInterests();
  }, []);

  // 处理兴趣选择
  const handleInterestToggle = (interest: string) => {
    setFormData(prev => {
      const exists = prev.interests.includes(interest);
      if (exists) {
        return { ...prev, interests: prev.interests.filter(i => i !== interest) };
      } else {
        if (prev.interests.length >= 3) {
          alert('最多选择 3 个兴趣爱好');
          return prev;
        }
        return { ...prev, interests: [...prev.interests, interest] };
      }
    });
  };

  // 处理日期变化，计算星座
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setFormData(prev => ({ ...prev, birthDate: date }));
    
    // 计算星座
    if (date) {
      const [year, month, day] = date.split('-').map(Number);
      const zodiac = calculateZodiac(month, day);
      setFormData(prev => ({ ...prev, zodiacSign: zodiac }));
    }
  };

  // 计算星座函数
  const calculateZodiac = (month: number, day: number) => {
    const dates = [20, 19, 21, 20, 21, 22, 23, 23, 23, 24, 22, 22];
    const signs = ['摩羯座', '水瓶座', '双鱼座', '白羊座', '金牛座', '双子座',
                   '巨蟹座', '狮子座', '处女座', '天秤座', '天蝎座', '射手座', '摩羯座'];
    
    if (day < dates[month - 1]) {
      return signs[month - 1];
    } else {
      return signs[month];
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      {/* 性别选择 */}
      <div className="space-y-2">
        <Label>性别</Label>
        <div className="flex gap-4">
          <Button
            type="button"
            variant={formData.gender === 'male' ? 'default' : 'outline'}
            onClick={() => setFormData(prev => ({ ...prev, gender: 'male' }))}
            className="flex-1"
          >
            男
          </Button>
          <Button
            type="button"
            variant={formData.gender === 'female' ? 'default' : 'outline'}
            onClick={() => setFormData(prev => ({ ...prev, gender: 'female' }))}
            className="flex-1"
          >
            女
          </Button>
        </div>
      </div>

      {/* MBTI 类型选择 */}
      <div className="space-y-2">
        <Label>MBTI 类型</Label>
        <select
          value={formData.mbtiType}
          onChange={(e) => setFormData(prev => ({ ...prev, mbtiType: e.target.value }))}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          required
        >
          <option value="">请选择 MBTI 类型</option>
          {MBTI_TYPES.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
      </div>

      {/* 出生日期 */}
      <div className="space-y-2">
        <Label>
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            出生日期
          </div>
        </Label>
        <Input
          type="date"
          value={formData.birthDate}
          onChange={handleDateChange}
          required
        />
        {formData.birthDate && (
          <p className="text-sm text-muted-foreground">
            星座：<span className="font-medium">{formData.zodiacSign}</span>
          </p>
        )}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="useLunar"
            checked={formData.useLunar}
            onChange={(e) => setFormData(prev => ({ ...prev, useLunar: e.target.checked }))}
            className="h-4 w-4"
          />
          <Label htmlFor="useLunar" className="text-sm font-normal">
            使用农历（自动转换为公历）
          </Label>
        </div>
      </div>

      {/* 出生时间 */}
      <div className="space-y-2">
        <Label>出生时间</Label>
        <div className="flex items-center gap-2 mb-2">
          <input
            type="checkbox"
            id="unknownTime"
            checked={formData.unknownBirthTime}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              unknownBirthTime: e.target.checked,
              birthTime: e.target.checked ? '' : prev.birthTime 
            }))}
            className="h-4 w-4"
          />
          <Label htmlFor="unknownTime" className="text-sm font-normal">
            未知出生时间
          </Label>
        </div>
        {!formData.unknownBirthTime && (
          <Input
            type="time"
            value={formData.birthTime}
            onChange={(e) => setFormData(prev => ({ ...prev, birthTime: e.target.value }))}
          />
        )}
      </div>

      {/* 出身地点 */}
      <div className="space-y-2">
        <Label>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            出身地点（精确到区/县）
          </div>
        </Label>
        <Input
          placeholder="例如：北京市朝阳区"
          value={formData.birthPlace}
          onChange={(e) => setFormData(prev => ({ ...prev, birthPlace: e.target.value }))}
          required
        />
      </div>

      {/* 当前居住地 */}
      <div className="space-y-2">
        <Label>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            当前居住地点（精确到区/县）
          </div>
        </Label>
        <Input
          placeholder="例如：上海市浦东新区"
          value={formData.currentResidence}
          onChange={(e) => setFormData(prev => ({ ...prev, currentResidence: e.target.value }))}
          required
        />
      </div>

      {/* 兴趣爱好 */}
      <div className="space-y-2">
        <Label>
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4" />
            兴趣爱好（最多 3 个）
          </div>
        </Label>
        <div className="grid grid-cols-3 gap-2">
          {randomInterests.map((interest) => (
            <Button
              key={interest}
              type="button"
              variant={formData.interests.includes(interest) ? 'default' : 'outline'}
              onClick={() => handleInterestToggle(interest)}
              className="text-sm"
            >
              {interest}
            </Button>
          ))}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={generateRandomInterests}
          className="mt-2"
        >
          换一批
        </Button>
        <div className="flex flex-wrap gap-2 mt-2">
          {formData.interests.map((interest) => (
            <span
              key={interest}
              className="inline-flex items-center gap-1 bg-primary text-primary-foreground px-2 py-1 rounded text-xs"
            >
              {interest}
              <button
                type="button"
                onClick={() => handleInterestToggle(interest)}
                className="hover:bg-primary-foreground hover:text-primary rounded-full p-0.5"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* 自定义特征 */}
      <div className="space-y-2">
        <Label>
          <div className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            自定义特征描述
          </div>
        </Label>
        <textarea
          value={formData.customFeatures}
          onChange={(e) => setFormData(prev => ({ ...prev, customFeatures: e.target.value }))}
          placeholder="描述您希望的理想对象特征..."
          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>

      {/* 提交按钮 */}
      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? '生成中...' : '生成 AI 伴侣'}
      </Button>
    </form>
  );
}
