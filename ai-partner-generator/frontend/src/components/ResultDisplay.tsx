import React from 'react';
import { Button } from '@/components/ui/button';
import { Download, RefreshCw, Share2 } from 'lucide-react';

interface ResultDisplayProps {
  imageUrl: string;
  description: string;
  onRegenerate: () => void;
}

export function ResultDisplay({ imageUrl, description, onRegenerate }: ResultDisplayProps) {
  const handleDownload = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'ai-partner.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('下载失败:', error);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: '我的 AI 伴侣',
          text: description,
          url: imageUrl,
        });
      } catch (error) {
        console.error('分享失败:', error);
      }
    } else {
      // 降级方案：复制链接
      await navigator.clipboard.writeText(imageUrl);
      alert('图片链接已复制到剪贴板');
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="bg-card rounded-lg shadow-lg overflow-hidden">
        <div className="aspect-square relative">
          <img
            src={imageUrl}
            alt="AI 生成的伴侣"
            className="w-full h-full object-cover"
          />
        </div>
      </div>

      <div className="bg-muted rounded-lg p-4">
        <h3 className="font-semibold mb-2">生成描述</h3>
        <p className="text-sm text-muted-foreground whitespace-pre-line">
          {description}
        </p>
      </div>

      <div className="flex gap-3">
        <Button onClick={onRegenerate} variant="outline" className="flex-1">
          <RefreshCw className="w-4 h-4 mr-2" />
          重新生成
        </Button>
        <Button onClick={handleDownload} className="flex-1">
          <Download className="w-4 h-4 mr-2" />
          下载图片
        </Button>
        <Button onClick={handleShare} variant="secondary">
          <Share2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
