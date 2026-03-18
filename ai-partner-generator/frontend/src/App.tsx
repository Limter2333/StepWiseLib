import { useState } from 'react';
import { MultiStepForm } from '@/components/MultiStepForm';
import { ResultDisplay } from '@/components/ResultDisplay';
import { generatePartner, type GenerateRequest } from '@/services/api';
import { Heart, Sparkles } from 'lucide-react';

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ imageUrl: string; description: string } | null>(null);

  const handleSubmit = async (data: any) => {
    setLoading(true);
    
    try {
      const request: GenerateRequest = {
        userUuid: data.userUuid,
        username: data.username,
        gender: data.gender,
        targetGender: data.targetGender,
        mbtiType: data.mbtiType,
        birthDate: data.birthDate,
        zodiacSign: data.zodiacSign,
        birthTime: data.unknownBirthTime ? '' : data.birthTime,
        birthPlace: data.birthPlace,
        currentResidence: data.currentResidence,
        interests: data.interests,
        customFeatures: data.customFeatures,
      };

      const response = await generatePartner(request);
      
      if (response.success) {
        setResult({
          imageUrl: response.imageUrl,
          description: response.description,
        });
      } else {
        alert(response.errorMessage || '生成失败，请重试');
      }
    } catch (error) {
      console.error('生成失败:', error);
      alert('网络错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = () => {
    setResult(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-center gap-2">
          <Heart className="w-6 h-6 text-pink-500 fill-pink-500" />
          <h1 className="text-xl font-bold bg-gradient-to-r from-pink-500 to-purple-600 bg-clip-text text-transparent">
            AI 伴侣生成器
          </h1>
          <Sparkles className="w-6 h-6 text-purple-500" />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {!result ? (
          <div className="bg-white rounded-lg shadow-lg p-6 md:p-8">
            <div className="mb-6 text-center">
              <h2 className="text-2xl font-bold mb-2">发现您的理想伴侣</h2>
              <p className="text-muted-foreground">
                根据您的个人信息和偏好，AI 将为您生成可能的理想对象类型
              </p>
            </div>
            <MultiStepForm onSubmit={handleSubmit} loading={loading} />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-6 md:p-8">
            <div className="mb-6 text-center">
              <h2 className="text-2xl font-bold mb-2">生成结果</h2>
              <p className="text-muted-foreground">
                这是根据您的特征生成的理想伴侣形象
              </p>
            </div>
            <ResultDisplay
              imageUrl={result.imageUrl}
              description={result.description}
              onRegenerate={handleRegenerate}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center text-sm text-muted-foreground">
        <p>© 2024 AI Partner Generator · 仅供娱乐</p>
      </footer>
    </div>
  );
}

export default App;
