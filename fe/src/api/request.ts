import type { AxiosError, AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request: AxiosInstance = axios.create({
  // Production is served by Nginx on the same origin, so requests remain
  // behind its HTTPS/authentication boundary. Local development keeps the
  // existing standalone FastAPI address.
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '' : 'http://localhost:5005'),
  timeout: 60000,
})
async function requestHandler(config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> {
  return config
}

export interface ResponseBody<T = any> {
  code: number
  data: T
  message: string
}
function responseHandler(response: any): ResponseBody<any> | AxiosResponse<any> | Promise<any> | any {
  const resData = response.data
  // 如果是Blob格式直接返回
  if (resData instanceof Blob)
    return resData

  if (resData.code === 200) {
    return resData
  }
  else {
    const message = resData.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  }
}
function errorHandler(error: AxiosError): Promise<any> {
  console.log('HTTP ERROR:', error)

  const { data, statusText } = error.response as AxiosResponse<ResponseBody>
  ElMessage.error(data?.message || statusText)

  return Promise.reject(error)
}
request.interceptors.request.use(requestHandler)

request.interceptors.response.use(responseHandler, errorHandler)

export default request
