import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Heart, Calendar, MapPin, Image as ImageIcon, ChevronLeft, ChevronRight, User } from 'lucide-react';
import { LocationSelector } from './LocationSelector';
import { saveUserStep } from '@/services/api';

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

interface FormData {
  username?: string;
  gender: string;
  targetGender: string;
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
  userUuid?: string;
}

interface MultiStepFormProps {
  onSubmit: (data: FormData) => void;
  loading: boolean;
}

type StepType = 'username' | 'basic' | 'birth' | 'location' | 'interests' | 'custom';

const steps: { type: StepType; title: string; description: string }[] = [
  { type: 'username', title: '用户名', description: '请输入您的用户名' },
  { type: 'basic', title: '基本信息', description: '填写您的基本个人信息' },
  { type: 'birth', title: '出生信息', description: '填写出生日期和时间' },
  { type: 'location', title: '地理位置', description: '填写出生地和居住地' },
  { type: 'interests', title: '兴趣爱好', description: '选择您的兴趣爱好' },
  { type: 'custom', title: '自定义特征', description: '描述您希望的理想对象特征' },
];

export function MultiStepForm({ onSubmit, loading }: MultiStepFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<FormData>({
    username: '',
    gender: '',
    targetGender: '',
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
    userUuid: '',
  });
  const [randomInterests, setRandomInterests] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);

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
      const [, month, day] = date.split('-').map(Number);
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

  // 验证当前步骤
  const validateStep = (step: number): boolean => {
    const stepType = steps[step].type;
    
    switch (stepType) {
      case 'username':
        if (!formData.username || formData.username.trim() === '') {
          alert('请填写用户名');
          return false;
        }
        break;
      case 'basic':
        if (!formData.gender || !formData.mbtiType) {
          alert('请填写完整的基本信息');
          return false;
        }
        break;
      case 'birth':
        if (!formData.birthDate) {
          alert('请选择出生日期');
          return false;
        }
        break;
      case 'location':
        if (!formData.birthPlace || !formData.currentResidence) {
          alert('请填写完整的地理位置信息');
          return false;
        }
        break;
      case 'interests':
        if (formData.interests.length === 0) {
          alert('请至少选择一个兴趣爱好');
          return false;
        }
        break;
    }
    return true;
  };

  // 保存用户信息到数据库
  const saveUserInfo = async () => {
    try {
      setIsSaving(true);
      const response = await saveUserStep({
        username: formData.username || '',
        step: currentStep,
        data: formData,
        userUuid: formData.userUuid || '',
      });
      
      // 如果后端返回了 userUuid，保存到前端状态
      if (response && response.data && response.data.userUuid) {
        setFormData(prev => ({ ...prev, userUuid: response.data.userUuid }));
        console.log('用户信息已保存，userUuid:', response.data.userUuid);
      } else {
        console.log('用户信息已保存');
      }
    } catch (error) {
      console.error('保存用户信息失败:', error);
      // 不阻断用户操作，继续下一步
    } finally {
      setIsSaving(false);
    }
  };

  const handleNext = async () => {
    if (!validateStep(currentStep)) {
      return;
    }
    
    // 点击下一步时保存用户信息
    await saveUserInfo();
    
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep(currentStep)) {
      return;
    }
    onSubmit(formData);
  };

  const renderStep = () => {
    const stepType = steps[currentStep].type;

    switch (stepType) {
      case 'username':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4" />
                  用户名
                </div>
              </Label>
              <Input
                id="username"
                placeholder="请输入您的用户名"
                value={formData.username}
                onChange={(e) => setFormData(prev => ({ ...prev, username: e.target.value }))}
                className="h-12 text-base"
              />
            </div>
          </div>
        );

      case 'basic':
        return (
          <div className="space-y-6">
            {/* 性别选择 */}
            <div className="space-y-3">
              <Label>您的性别</Label>
              <div className="flex gap-4">
                <Button
                  type="button"
                  variant={formData.gender === 'male' ? 'default' : 'outline'}
                  onClick={() => {
                    const newGender = 'male';
                    // 自动设置目标性别为异性
                    setFormData(prev => ({ 
                      ...prev, 
                      gender: newGender,
                      targetGender: prev.targetGender || 'female' // 默认为异性
                    }))
                  }}
                  className="flex-1 h-12 text-base"
                >
                  男
                </Button>
                <Button
                  type="button"
                  variant={formData.gender === 'female' ? 'default' : 'outline'}
                  onClick={() => {
                    const newGender = 'female';
                    // 自动设置目标性别为异性
                    setFormData(prev => ({ 
                      ...prev, 
                      gender: newGender,
                      targetGender: prev.targetGender || 'male' // 默认为异性
                    }))
                  }}
                  className="flex-1 h-12 text-base"
                >
                  女
                </Button>
              </div>
            </div>

            {/* 目标性别选择 */}
            <div className="space-y-3">
              <Label>希望的对象性别</Label>
              <div className="flex gap-4">
                <Button
                  type="button"
                  variant={formData.targetGender === 'male' ? 'default' : 'outline'}
                  onClick={() => setFormData(prev => ({ ...prev, targetGender: 'male' }))}
                  className="flex-1 h-12 text-base"
                >
                  男
                </Button>
                <Button
                  type="button"
                  variant={formData.targetGender === 'female' ? 'default' : 'outline'}
                  onClick={() => setFormData(prev => ({ ...prev, targetGender: 'female' }))}
                  className="flex-1 h-12 text-base"
                >
                  女
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {formData.gender && formData.targetGender && formData.gender !== formData.targetGender 
                  ? '✓ 已为您选择异性' 
                  : formData.gender && formData.targetGender && formData.gender === formData.targetGender
                  ? '○ 您选择了同性'
                  : '请选择您希望的对象性别'}
              </p>
            </div>

            {/* MBTI 类型选择 */}
            <div className="space-y-3">
              <Label>MBTI 类型</Label>
              <select
                value={formData.mbtiType}
                onChange={(e) => setFormData(prev => ({ ...prev, mbtiType: e.target.value }))}
                className="flex h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-base"
              >
                <option value="">请选择 MBTI 类型</option>
                {MBTI_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        );

      case 'birth':
        return (
          <div className="space-y-6">
            {/* 出生日期 */}
            <div className="space-y-3">
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
                className="h-12 text-base"
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
            <div className="space-y-3">
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
                  className="h-12 text-base"
                />
              )}
            </div>
          </div>
        );

      case 'location':
        return (
          <div className="space-y-6">
            {/* 出身地点 */}
            <div className="space-y-3">
              <Label>
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  出身地点
                </div>
              </Label>
              <LocationSelector
                value={formData.birthPlace}
                onChange={(value) => setFormData(prev => ({ ...prev, birthPlace: value }))}
              />
            </div>

            {/* 当前居住地 */}
            <div className="space-y-3">
              <Label>
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  当前居住地点
                </div>
              </Label>
              <LocationSelector
                value={formData.currentResidence}
                onChange={(value) => setFormData(prev => ({ ...prev, currentResidence: value }))}
              />
            </div>
          </div>
        );

      case 'interests':
        return (
          <div className="space-y-6">
            {/* 兴趣爱好 */}
            <div className="space-y-4">
              <Label>
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4" />
                  兴趣爱好（最多 3 个）
                </div>
              </Label>
              <div className="grid grid-cols-3 gap-3">
                {randomInterests.map((interest) => (
                  <Button
                    key={interest}
                    type="button"
                    variant={formData.interests.includes(interest) ? 'default' : 'outline'}
                    onClick={() => handleInterestToggle(interest)}
                    className="h-12 text-sm"
                  >
                    {interest}
                  </Button>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => generateRandomInterests()}
                className="mt-2"
              >
                换一批
              </Button>
              <div className="flex flex-wrap gap-2 mt-4">
                {formData.interests.map((interest) => (
                  <span
                    key={interest}
                    className="inline-flex items-center gap-1 bg-primary text-primary-foreground px-3 py-2 rounded text-sm"
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
          </div>
        );

      case 'custom':
        return (
          <div className="space-y-4">
            {/* 自定义特征 */}
            <div className="space-y-3">
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
                className="flex min-h-[150px] w-full rounded-md border border-input bg-background px-3 py-2 text-base resize-none"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-2xl mx-auto">
      {/* 进度指示器 */}
      <div className="mb-10">
        <div className="flex justify-between mb-4">
          {steps.map((step, index) => (
            <div
              key={step.type}
              className={`flex flex-col items-center ${
                index <= currentStep ? 'text-primary' : 'text-muted-foreground'
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-colors shadow-sm ${
                  index < currentStep
                    ? 'bg-primary text-primary-foreground'
                    : index === currentStep
                    ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2'
                    : 'bg-muted'
                }`}
              >
                {index < currentStep ? '✓' : index + 1}
              </div>
              <span className="text-xs mt-2 font-medium hidden md:block">{step.title}</span>
            </div>
          ))}
        </div>
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full h-1 bg-muted rounded-full"></div>
          </div>
          <div
            className="absolute inset-0 flex items-center transition-all duration-500 ease-in-out"
            style={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
          >
            <div className="w-full h-1 bg-primary rounded-full"></div>
          </div>
        </div>
      </div>

      {/* 步骤标题 */}
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold mb-2">{steps[currentStep].title}</h3>
        <p className="text-base text-muted-foreground">{steps[currentStep].description}</p>
      </div>

      {/* 步骤内容 */}
      <div className="min-h-[350px] bg-muted/30 rounded-xl p-6">
        {renderStep()}
      </div>

      {/* 导航按钮 */}
      <div className="flex gap-4 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={handlePrev}
          disabled={currentStep === 0 || isSaving}
          className="flex-1 h-12 text-base"
        >
          <ChevronLeft className="w-5 h-5 mr-2" />
          上一步
        </Button>
        {currentStep < steps.length - 1 ? (
          <Button
            type="button"
            variant="default"
            onClick={handleNext}
            disabled={isSaving}
            className="flex-1 h-12 text-base"
          >
            {isSaving ? '保存中...' : '下一步'}
            {!isSaving && <ChevronRight className="w-5 h-5 ml-2" />}
          </Button>
        ) : (
          <Button
            type="submit"
            variant="default"
            disabled={loading || isSaving}
            className="flex-1 h-12 text-base"
          >
            {loading ? '生成中...' : '生成 AI 伴侣'}
          </Button>
        )}
      </div>
    </form>
  );
}
