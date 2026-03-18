import axios from 'axios';

const API_BASE_URL = '/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface GenerateRequest {
  userUuid?: string;
  username?: string;
  gender: string;
  targetGender?: string;
  mbtiType: string;
  birthDate: string;
  zodiacSign: string;
  birthTime: string;
  birthPlace: string;
  currentResidence: string;
  interests?: string[];
  customFeatures?: string;
}

export interface SaveInterestsRequest {
  interests: string[];
}

export interface SaveCustomFeaturesRequest {
  customFeatures: string;
}

export interface SaveUserStepRequest {
  username: string;
  step: number;
  data: any;
  userUuid?: string;
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

/**
 * 保存兴趣爱好
 */
export const saveInterests = async (request: SaveInterestsRequest): Promise<{ success: boolean }> => {
  const response = await api.post<{ success: boolean }>('/interests', request);
  return response.data;
};

/**
 * 保存自定义特征
 */
export const saveCustomFeatures = async (request: SaveCustomFeaturesRequest): Promise<{ success: boolean }> => {
  const response = await api.post<{ success: boolean }>('/custom-features', request);
  return response.data;
};

/**
 * 保存用户步骤信息
 */
export const saveUserStep = async (request: SaveUserStepRequest): Promise<{ success: boolean; data?: any }> => {
  const response = await api.post<{ success: boolean; data?: any }>('/user/step', request);
  return response.data;
};
