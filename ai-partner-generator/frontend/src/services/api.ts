import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface GenerateRequest {
  gender: string;
  mbtiType: string;
  birthDate: string;
  zodiacSign: string;
  birthTime: string;
  birthPlace: string;
  currentResidence: string;
  interests: string[];
  customFeatures: string;
}

export interface GenerateResponse {
  imageUrl: string;
  description: string;
  success: boolean;
  errorMessage: string;
}

export interface UploadResponse {
  imageUrl: string;
  message: string;
}

/**
 * 生成 AI 伴侣图片
 */
export const generatePartner = async (request: GenerateRequest): Promise<GenerateResponse> => {
  const response = await api.post<GenerateResponse>('/generate', request);
  return response.data;
};

/**
 * 上传参考图片
 */
export const uploadImage = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * 计算星座
 */
export const calculateZodiac = async (date: string): Promise<string> => {
  const response = await api.get<{ zodiacSign: string }>('/zodiac', {
    params: { date },
  });
  return response.data.zodiacSign;
};
