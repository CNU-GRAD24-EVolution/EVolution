import axios from 'axios';

// API 기본 URL 설정
const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// axios 인스턴스 생성
const apiClient = axios.create({
  baseURL,
  timeout: 10000, // 10초 타임아웃
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (필요시 토큰 등 추가)
apiClient.interceptors.request.use(
  (config) => {
    // 요청 전 처리 로직
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 공통 에러 처리 로직
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
